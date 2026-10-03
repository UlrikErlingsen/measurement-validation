"""Exploratory dimensionality and score-reliability analysis for Measure Signal."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.multivariate.factor import Factor

from .design import orient_items
from .errors import DataProblem


# Above this many complete rows, parallel analysis draws its random correlation matrices from the Wishart
# distribution of an n-row null sample instead of simulating n × p normal values per replication: identical in
# distribution for Pearson, the standard large-sample approximation for Spearman, and independent of n in cost.
PARALLEL_ROW_SIMULATION_LIMIT = 20_000
# Respondent-by-item cells one alpha bootstrap may resample. Above it, the bootstrap runs on a seeded random
# subsample and its interval is rescaled to the full sample size (see _bootstrap_alpha).
BOOTSTRAP_CELL_BUDGET = 50_000_000
MIN_BOOTSTRAP_SUBSAMPLE = 2_000
# Above this many complete rows, correlations, alpha, standardized alpha, omega and item diagnostics come from one
# item covariance matrix accumulated in row chunks, instead of several full centered copies of the item matrix.
# The estimates are the same; only the memory path differs.
LARGE_SAMPLE_ROWS = 1_000_000
COVARIANCE_CHUNK_ROWS = 250_000


@dataclass(frozen=True)
class MeasurementConfig:
    items: tuple[str, ...]
    reversed_items: tuple[str, ...]
    scale_min: float
    scale_max: float
    planned_factors: int
    correlation: str = "pearson"
    loading_threshold: float = 0.40
    cross_loading_threshold: float = 0.30
    reliability_target: float = 0.70
    minimum_answered: float = 0.80
    parallel_iterations: int = 499
    bootstrap_iterations: int = 499
    seed: int = 260716


@dataclass(frozen=True)
class MeasurementResult:
    config: MeasurementConfig
    correlation_matrix: pd.DataFrame
    retention: pd.DataFrame
    item_structure: pd.DataFrame
    factor_summary: pd.DataFrame
    factor_correlations: pd.DataFrame
    reliability: pd.DataFrame
    item_reliability: pd.DataFrame
    score_summary: pd.DataFrame
    diagnostics: dict[str, object]
    warnings: tuple[str, ...]
    parallel_factors: int


def _complete_data(frame: pd.DataFrame, config: MeasurementConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    oriented = orient_items(
        frame,
        items=config.items,
        reversed_items=config.reversed_items,
        scale_min=config.scale_min,
        scale_max=config.scale_max,
    )
    outside = (oriented.lt(config.scale_min) | oriented.gt(config.scale_max)) & oriented.notna()
    if int(outside.to_numpy().sum()):
        raise DataProblem("Responses outside the declared range must be corrected before modeling.")
    complete = oriented.dropna()
    minimum_rows = max(50, len(config.items) + 10)
    if len(complete) < minimum_rows:
        raise DataProblem(
            f"Only {len(complete)} complete rows remain; at least {minimum_rows} are required for this bounded EFA workflow."
        )
    constant = [item for item in config.items if complete[item].nunique() < 2]
    if constant:
        raise DataProblem("These items are constant in the complete sample: " + ", ".join(constant))
    return oriented, complete


def _covariance(values: np.ndarray) -> np.ndarray:
    """Sample covariance (ddof=1) of the columns; large inputs are centered chunk by chunk, never copied whole."""
    n = values.shape[0]
    if n <= LARGE_SAMPLE_ROWS:
        return np.atleast_2d(np.cov(values, rowvar=False, ddof=1))
    mean = values.mean(axis=0)
    cross = np.zeros((values.shape[1], values.shape[1]))
    for start in range(0, n, COVARIANCE_CHUNK_ROWS):
        block = values[start : start + COVARIANCE_CHUNK_ROWS] - mean
        cross += block.T @ block
    return cross / (n - 1)


def _covariance_to_correlation(covariance: np.ndarray) -> np.ndarray:
    scale = np.sqrt(np.diag(covariance))
    with np.errstate(divide="ignore", invalid="ignore"):
        return covariance / np.outer(scale, scale)


def _correlation(data: pd.DataFrame, method: str) -> np.ndarray:
    normalized = method.strip().lower()
    if normalized not in {"pearson", "spearman"}:
        raise DataProblem("Correlation must be Pearson or Spearman.")
    if len(data) > LARGE_SAMPLE_ROWS:
        # Pearson on average ranks is Spearman's rho, as in pandas; the chunked covariance avoids extra copies.
        values = (data.rank() if normalized == "spearman" else data).to_numpy(float)
        matrix = _covariance_to_correlation(_covariance(values))
    else:
        matrix = data.corr(method=normalized).to_numpy(float)
    if not np.isfinite(matrix).all():
        raise DataProblem("The item correlation matrix contains undefined values.")
    matrix = (matrix + matrix.T) / 2
    np.fill_diagonal(matrix, 1.0)
    eigenvalues = np.linalg.eigvalsh(matrix)
    if float(eigenvalues.min()) <= 1e-8:
        raise DataProblem(
            "The item correlation matrix is singular or nearly singular. Remove duplicate/linear-combination items by design, not by trial and error."
        )
    return matrix


def factorability_diagnostics(correlation: np.ndarray, n: int) -> tuple[float, np.ndarray, float, float, float]:
    """Return overall/item KMO, Bartlett chi-square/p, and determinant."""
    p = correlation.shape[0]
    determinant = float(np.linalg.det(correlation))
    if determinant <= 0:
        raise DataProblem("The correlation determinant is non-positive; factorability diagnostics are undefined.")
    inverse = np.linalg.inv(correlation)
    scaling = np.sqrt(np.outer(np.diag(inverse), np.diag(inverse)))
    partial = -inverse / scaling
    np.fill_diagonal(partial, 0.0)
    corr_sq = correlation**2
    partial_sq = partial**2
    np.fill_diagonal(corr_sq, 0.0)
    numerator_items = corr_sq.sum(axis=0)
    denominator_items = numerator_items + partial_sq.sum(axis=0)
    item_kmo = np.divide(
        numerator_items,
        denominator_items,
        out=np.full(p, np.nan),
        where=denominator_items > 0,
    )
    overall_denominator = float(corr_sq.sum() + partial_sq.sum())
    overall_kmo = float(corr_sq.sum() / overall_denominator) if overall_denominator > 0 else np.nan
    correction = n - 1 - (2 * p + 5) / 6
    bartlett_chi2 = float(-correction * math.log(determinant))
    bartlett_df = p * (p - 1) / 2
    bartlett_p = float(stats.chi2.sf(bartlett_chi2, bartlett_df))
    return overall_kmo, item_kmo, bartlett_chi2, bartlett_p, determinant


def _wishart_null_eigenvalues(n: int, p: int, iterations: int, rng: np.random.Generator) -> np.ndarray:
    """Eigenvalues of null correlation matrices of n independent normal rows, via the Bartlett decomposition.

    The centered cross-product matrix of n rows is Wishart(n - 1, I); its correlation matrix has exactly the
    distribution of ``np.corrcoef`` on simulated data, at O(p²) cost per replication instead of O(n·p²).
    """
    degrees = n - 1
    factor = np.zeros((iterations, p, p))
    rows, columns = np.tril_indices(p, k=-1)
    factor[:, rows, columns] = rng.normal(size=(iterations, len(rows)))
    diagonal = np.arange(p)
    factor[:, diagonal, diagonal] = np.sqrt(rng.chisquare(degrees - diagonal, size=(iterations, p)))
    cross = factor @ np.transpose(factor, (0, 2, 1))
    scale = np.sqrt(np.einsum("kii->ki", cross))
    correlation = cross / scale[:, :, None] / scale[:, None, :]
    return np.linalg.eigvalsh(correlation)[:, ::-1]


def parallel_analysis(
    data: pd.DataFrame,
    *,
    method: str,
    iterations: int,
    seed: int,
    observed_correlation: np.ndarray | None = None,
) -> tuple[pd.DataFrame, int]:
    """Horn-style PCA parallel analysis using a 95th-percentile random benchmark."""
    if not 49 <= iterations <= 5000:
        raise DataProblem("Use 49 to 5,000 parallel-analysis replications.")
    n, p = data.shape
    observed_corr = _correlation(data, method) if observed_correlation is None else observed_correlation
    observed = np.linalg.eigvalsh(observed_corr)[::-1]
    rng = np.random.default_rng(seed)
    if n > PARALLEL_ROW_SIMULATION_LIMIT:
        simulated = _wishart_null_eigenvalues(n, p, iterations, rng)
    else:
        simulated = np.empty((iterations, p), dtype=float)
        for index in range(iterations):
            random_data = rng.normal(size=(n, p))
            if method.lower() == "spearman":
                random_data = np.apply_along_axis(stats.rankdata, 0, random_data)
            random_corr = np.corrcoef(random_data, rowvar=False)
            simulated[index] = np.linalg.eigvalsh(random_corr)[::-1]
    random_mean = simulated.mean(axis=0)
    random_95 = np.quantile(simulated, 0.95, axis=0)
    retained = 0
    for observed_value, benchmark in zip(observed, random_95, strict=True):
        if observed_value > benchmark:
            retained += 1
        else:
            break
    table = pd.DataFrame(
        {
            "component": np.arange(1, p + 1),
            "observed_eigenvalue": observed,
            "random_mean": random_mean,
            "random_95th_percentile": random_95,
            "exceeds_95th_percentile": observed > random_95,
        }
    )
    return table, retained


def _orient_factor_signs(loadings: np.ndarray, phi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    signs = np.ones(loadings.shape[1])
    for column in range(loadings.shape[1]):
        pivot = int(np.argmax(np.abs(loadings[:, column])))
        if loadings[pivot, column] < 0:
            signs[column] = -1.0
    sign_matrix = np.diag(signs)
    return loadings @ sign_matrix, sign_matrix @ phi @ sign_matrix


def _fit_factor_model(
    correlation: np.ndarray,
    *,
    items: tuple[str, ...],
    n: int,
    factors: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if not 1 <= factors <= min(8, len(items) - 1):
        raise DataProblem("The planned factor count must be between 1 and the smaller of 8 or items minus 1.")
    result = Factor(
        corr=correlation,
        n_factor=factors,
        method="pa",
        smc=True,
        endog_names=list(items),
        nobs=n,
    ).fit(maxiter=1000, tol=1e-8)
    if factors > 1:
        result.rotate("oblimin")
    loadings = np.asarray(result.loadings, dtype=float)
    uniqueness = np.asarray(result.uniqueness, dtype=float)
    phi = (
        np.asarray(result.rotation_matrix.T @ result.rotation_matrix, dtype=float)
        if factors > 1
        else np.eye(1)
    )
    order = np.argsort(np.sum(loadings**2, axis=0))[::-1]
    loadings = loadings[:, order]
    phi = phi[np.ix_(order, order)]
    loadings, phi = _orient_factor_signs(loadings, phi)
    return loadings, uniqueness, phi


def _alpha(matrix: np.ndarray) -> float:
    if matrix.ndim != 2 or matrix.shape[1] < 2 or matrix.shape[0] < 3:
        return np.nan
    item_variances = np.var(matrix, axis=0, ddof=1)
    total_variance = float(np.var(matrix.sum(axis=1), ddof=1))
    if total_variance <= 0:
        return np.nan
    k = matrix.shape[1]
    return float(k / (k - 1) * (1 - item_variances.sum() / total_variance))


def _standardized_alpha(matrix: np.ndarray) -> float:
    if matrix.shape[1] < 2:
        return np.nan
    corr = np.corrcoef(matrix, rowvar=False)
    upper = corr[np.triu_indices_from(corr, k=1)]
    mean_r = float(np.nanmean(upper))
    k = matrix.shape[1]
    denominator = 1 + (k - 1) * mean_r
    return float(k * mean_r / denominator) if denominator != 0 else np.nan


def _bootstrap_alpha(
    matrix: np.ndarray,
    *,
    iterations: int,
    seed: int,
    columns: list[int] | None = None,
    full_alpha: float | None = None,
) -> tuple[float, float, int]:
    """Percentile bootstrap interval for alpha, plus the number of rows it resampled.

    When ``iterations × rows × items`` exceeds ``BOOTSTRAP_CELL_BUDGET``, the bootstrap resamples a seeded random
    subsample of ``m`` rows and carries its quantiles ``q`` to the full ``n`` as ``alpha_n + sqrt(m/n)·(q − alpha_m)``
    (alpha is root-n consistent), so large samples get an interval in seconds instead of hours.
    """
    if iterations <= 0:
        return np.nan, np.nan, 0
    n = matrix.shape[0]
    k = matrix.shape[1] if columns is None else len(columns)
    rows = min(n, max(BOOTSTRAP_CELL_BUDGET // max(iterations * k, 1), MIN_BOOTSTRAP_SUBSAMPLE))
    rng = np.random.default_rng(seed)
    sample = matrix[np.sort(rng.choice(n, size=rows, replace=False))] if rows < n else matrix
    if columns is not None:
        sample = sample[:, columns]
    values = []
    for _ in range(iterations):
        sampled = sample[rng.integers(0, rows, rows)]
        value = _alpha(sampled)
        if np.isfinite(value):
            values.append(value)
    if len(values) < max(20, iterations // 2):
        return np.nan, np.nan, rows
    low, high = float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))
    if rows < n:
        full = _alpha(matrix) if full_alpha is None else full_alpha
        center = _alpha(sample)
        if not (np.isfinite(full) and np.isfinite(center)):
            return np.nan, np.nan, rows
        shrink = math.sqrt(rows / n)
        low, high = full + shrink * (low - center), full + shrink * (high - center)
    return low, high, rows


def _omega_from_model(loadings: np.ndarray, uniqueness: np.ndarray, phi: np.ndarray) -> float:
    if (
        loadings.shape[0] < 2
        or np.any(~np.isfinite(uniqueness))
        or np.any(uniqueness <= 0)
        or np.any(uniqueness >= 1)
    ):
        return np.nan
    common = float(np.ones(loadings.shape[0]) @ loadings @ phi @ loadings.T @ np.ones(loadings.shape[0]))
    error = float(uniqueness.sum())
    return float(common / (common + error)) if common + error > 0 else np.nan


def _one_factor_omega(matrix: np.ndarray | None, correlation: np.ndarray | None = None, n: int = 0) -> float:
    corr = np.corrcoef(matrix, rowvar=False) if correlation is None else correlation
    n = matrix.shape[0] if matrix is not None else n
    if corr.shape[0] < 2:
        return np.nan
    if not np.isfinite(corr).all() or float(np.linalg.eigvalsh(corr).min()) <= 1e-8:
        return np.nan
    try:
        loadings, uniqueness, phi = _fit_factor_model(
            corr,
            items=tuple(f"item_{i}" for i in range(corr.shape[0])),
            n=n,
            factors=1,
        )
    except (ValueError, np.linalg.LinAlgError):
        return np.nan
    return _omega_from_model(loadings, uniqueness, phi)


def _alpha_from_covariance(covariance: np.ndarray, n: int) -> float:
    """Raw alpha from the item covariance matrix (identical to ``_alpha`` on the rows)."""
    if covariance.shape[0] < 2 or n < 3:
        return np.nan
    total_variance = float(covariance.sum())
    if total_variance <= 0:
        return np.nan
    k = covariance.shape[0]
    return float(k / (k - 1) * (1 - float(np.trace(covariance)) / total_variance))


def _reliability_row(
    label: str,
    matrix: np.ndarray,
    *,
    omega: float,
    bootstrap_iterations: int,
    seed: int,
    columns: list[int] | None = None,
    covariance: np.ndarray | None = None,
) -> dict[str, object]:
    """One reliability row. With ``covariance`` (large samples) the point estimates come from that matrix and the
    rows of ``matrix[:, columns]`` are touched only by the bootstrap's subsample."""
    k = matrix.shape[1] if columns is None else len(columns)
    if covariance is None:
        corr = np.corrcoef(matrix, rowvar=False) if k >= 2 else np.array([[1.0]])
        alpha = _alpha(matrix)
        standardized = _standardized_alpha(matrix)
    else:
        corr = _covariance_to_correlation(covariance) if k >= 2 else np.array([[1.0]])
        alpha = _alpha_from_covariance(covariance, matrix.shape[0])
        upper = corr[np.triu_indices_from(corr, k=1)]
        mean_r = float(np.nanmean(upper)) if k >= 2 else np.nan
        denominator = 1 + (k - 1) * mean_r
        standardized = float(k * mean_r / denominator) if k >= 2 and denominator != 0 else np.nan
    mean_interitem = float(np.nanmean(corr[np.triu_indices_from(corr, k=1)])) if k >= 2 else np.nan
    alpha_low, alpha_high, bootstrap_rows = _bootstrap_alpha(
        matrix, iterations=bootstrap_iterations, seed=seed, columns=columns, full_alpha=alpha
    )
    return {
        "score": label,
        "items": int(k),
        "complete_n": int(matrix.shape[0]),
        "alpha": alpha,
        "alpha_bootstrap_low": alpha_low,
        "alpha_bootstrap_high": alpha_high,
        "alpha_bootstrap_rows": int(bootstrap_rows),
        "standardized_alpha": standardized,
        "omega_total": omega,
        "mean_interitem_correlation": mean_interitem,
    }


def _score_summary(
    oriented: pd.DataFrame,
    groups: list[tuple[str, list[str]]],
    minimum_answered: float,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for label, items in groups:
        if not items:
            continue
        needed = max(1, int(math.ceil(len(items) * minimum_answered)))
        # Row means accumulated one item at a time: memory stays at a few row-length vectors for any sample size.
        total = np.zeros(len(oriented))
        answered = np.zeros(len(oriented), dtype=np.int64)
        for item in items:
            values = oriented[item].to_numpy(dtype=float)
            present = ~np.isnan(values)
            total += np.where(present, values, 0.0)
            answered += present
        with np.errstate(invalid="ignore", divide="ignore"):
            row_means = total / answered
        scores = pd.Series(row_means[answered >= needed])
        rows.append(
            {
                "score": label,
                "items": len(items),
                "minimum_items_answered": needed,
                "scored_n": int(len(scores)),
                "mean": float(scores.mean()) if len(scores) else np.nan,
                "sd": float(scores.std(ddof=1)) if len(scores) > 1 else np.nan,
                "minimum": float(scores.min()) if len(scores) else np.nan,
                "maximum": float(scores.max()) if len(scores) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def analyze_measure(frame: pd.DataFrame, config: MeasurementConfig) -> MeasurementResult:
    """Run a declared common-factor EFA and score-reliability profile."""
    if not 0.20 <= config.loading_threshold <= 0.80:
        raise DataProblem("Use a primary-loading threshold between 0.20 and 0.80.")
    if not 0.15 <= config.cross_loading_threshold <= config.loading_threshold:
        raise DataProblem("Cross-loading threshold must be between 0.15 and the primary-loading threshold.")
    if not 0.50 <= config.reliability_target <= 0.95:
        raise DataProblem("Use a reliability planning target between 0.50 and 0.95.")
    if not 0.50 <= config.minimum_answered <= 1.0:
        raise DataProblem("Minimum answered proportion must be between 0.50 and 1.00.")
    if not 0 <= config.bootstrap_iterations <= 5000:
        raise DataProblem("Use zero to 5,000 bootstrap replications.")

    oriented, complete = _complete_data(frame, config)
    correlation = _correlation(complete, config.correlation)
    overall_kmo, item_kmo, bartlett_chi2, bartlett_p, determinant = factorability_diagnostics(
        correlation, len(complete)
    )
    retention, retained = parallel_analysis(
        complete,
        method=config.correlation,
        iterations=config.parallel_iterations,
        seed=config.seed,
        observed_correlation=correlation,
    )
    loadings, uniqueness, phi = _fit_factor_model(
        correlation,
        items=config.items,
        n=len(complete),
        factors=config.planned_factors,
    )
    if np.any(uniqueness <= 0) or np.any(uniqueness >= 1):
        heywood = True
    else:
        heywood = False

    factor_names = [f"Factor {index}" for index in range(1, config.planned_factors + 1)]
    absolute = np.abs(loadings)
    primary_index = np.argmax(absolute, axis=1)
    primary_abs = absolute[np.arange(len(config.items)), primary_index]
    if config.planned_factors > 1:
        sorted_abs = np.sort(absolute, axis=1)
        second_abs = sorted_abs[:, -2]
    else:
        second_abs = np.zeros(len(config.items))
    cross_loading = second_abs >= config.cross_loading_threshold

    item_structure = pd.DataFrame({"item": config.items, "KMO_item": item_kmo})
    for index, name in enumerate(factor_names):
        item_structure[name] = loadings[:, index]
    item_structure["primary_factor"] = [factor_names[index] for index in primary_index]
    item_structure["primary_loading_abs"] = primary_abs
    item_structure["second_loading_abs"] = second_abs
    item_structure["cross_loading"] = cross_loading
    item_structure["communality"] = 1 - uniqueness
    item_structure["uniqueness"] = uniqueness
    item_structure["meets_primary_threshold"] = primary_abs >= config.loading_threshold

    factor_rows: list[dict[str, object]] = []
    score_groups: list[tuple[str, list[str]]] = []
    for index, name in enumerate(factor_names):
        assigned_mask = primary_index == index
        salient_mask = assigned_mask & (primary_abs >= config.loading_threshold)
        salient_items = [item for item, keep in zip(config.items, salient_mask, strict=True) if keep]
        score_groups.append((name + " exploratory score", salient_items))
        factor_rows.append(
            {
                "factor": name,
                "assigned_items": int(assigned_mask.sum()),
                "salient_items": int(salient_mask.sum()),
                "mean_primary_loading_abs": float(primary_abs[assigned_mask].mean()) if assigned_mask.any() else np.nan,
                "maximum_factor_correlation_abs": float(
                    np.max(np.abs(np.delete(phi[index], index))) if config.planned_factors > 1 else 0.0
                ),
            }
        )
    factor_summary = pd.DataFrame(factor_rows)
    factor_correlations = pd.DataFrame(phi, index=factor_names, columns=factor_names).reset_index(
        names="factor"
    )

    full_matrix = complete[list(config.items)].to_numpy(float)
    large_sample = len(full_matrix) > LARGE_SAMPLE_ROWS
    # Corrected item-total correlations and alpha-if-deleted (and, for large samples, every reliability point
    # estimate) follow from one item covariance matrix: one pass over the rows instead of one copy per item.
    covariance = _covariance(full_matrix)
    reliability_rows = [
        _reliability_row(
            "Candidate total (descriptive)",
            full_matrix,
            omega=_omega_from_model(loadings, uniqueness, phi),
            bootstrap_iterations=config.bootstrap_iterations,
            seed=config.seed + 1000,
            covariance=covariance if large_sample else None,
        )
    ]
    for factor_number, (label, items) in enumerate(score_groups, start=1):
        if len(items) < 2:
            continue
        if large_sample:
            positions = [config.items.index(item) for item in items]
            subset = covariance[np.ix_(positions, positions)]
            reliability_rows.append(
                _reliability_row(
                    label,
                    full_matrix,
                    omega=_one_factor_omega(None, _covariance_to_correlation(subset), len(full_matrix)),
                    bootstrap_iterations=config.bootstrap_iterations,
                    seed=config.seed + 1000 + factor_number,
                    columns=positions,
                    covariance=subset,
                )
            )
            continue
        matrix = complete[items].to_numpy(float)
        reliability_rows.append(
            _reliability_row(
                label,
                matrix,
                omega=_one_factor_omega(matrix),
                bootstrap_iterations=config.bootstrap_iterations,
                seed=config.seed + 1000 + factor_number,
            )
        )
    reliability = pd.DataFrame(reliability_rows)

    item_reliability_rows: list[dict[str, object]] = []
    for index, item in enumerate(config.items):
        others = [position for position in range(len(config.items)) if position != index]
        rest = covariance[np.ix_(others, others)]
        rest_variance = float(rest.sum())
        item_variance = float(covariance[index, index])
        corrected = (
            float(covariance[index, others].sum()) / math.sqrt(item_variance * rest_variance)
            if rest_variance > 0 and item_variance > 0
            else np.nan
        )
        remaining = len(others)
        alpha_deleted = (
            float(remaining / (remaining - 1) * (1 - float(np.trace(rest)) / rest_variance))
            if remaining >= 2 and rest_variance > 0 and full_matrix.shape[0] >= 3
            else np.nan
        )
        item_reliability_rows.append(
            {
                "item": item,
                "corrected_item_total_correlation": corrected,
                "alpha_if_deleted": alpha_deleted,
                "deletion_is_not_recommendation": True,
            }
        )
    item_reliability = pd.DataFrame(item_reliability_rows)

    common_covariance = loadings @ phi @ loadings.T
    fitted = common_covariance + np.diag(uniqueness)
    residual = correlation - fitted
    off_diagonal = residual[np.triu_indices_from(residual, k=1)]
    rmsr = float(np.sqrt(np.mean(off_diagonal**2)))
    max_residual = float(np.max(np.abs(off_diagonal)))
    loading_support_rate = float((primary_abs >= config.loading_threshold).mean())
    cross_loading_rate = float(cross_loading.mean())
    minimum_salient = int(factor_summary["salient_items"].min())

    warnings: list[str] = []
    if retained != config.planned_factors:
        warnings.append(
            f"Parallel analysis suggests {retained} component(s), while the measurement contract declares {config.planned_factors}."
        )
    if overall_kmo < 0.60:
        warnings.append("Overall KMO is below 0.60; shared variance may be weak for this item pool.")
    if heywood:
        warnings.append("At least one uniqueness estimate is outside (0, 1), indicating an improper or unstable solution.")
    if cross_loading_rate > 0.25:
        warnings.append("More than 25% of items meet the declared cross-loading threshold.")
    if minimum_salient < 3:
        warnings.append("At least one factor has fewer than three items meeting the declared primary-loading threshold.")
    if config.planned_factors > 1 and float(np.max(np.abs(phi - np.eye(len(phi))))) > 0.70:
        warnings.append("At least two exploratory factors correlate above |0.70|; discriminant structure needs scrutiny.")
    if config.correlation.lower() == "pearson" and max(complete.nunique()) <= 7:
        warnings.append(
            "Pearson correlations treat the selected response categories as approximately interval; few-category ordinal data may need polychoric methods."
        )
    parallel_benchmark = (
        f"Wishart null distribution for n = {len(complete):,} rows ({config.parallel_iterations} draws; exact in "
        "distribution for Pearson, large-sample approximation for Spearman)"
        if len(complete) > PARALLEL_ROW_SIMULATION_LIMIT
        else f"Simulated normal data, n = {len(complete):,} rows ({config.parallel_iterations} replications)"
    )
    if len(complete) > PARALLEL_ROW_SIMULATION_LIMIT:
        warnings.append(
            f"Parallel analysis: with more than {PARALLEL_ROW_SIMULATION_LIMIT:,} complete rows the random benchmark "
            "is drawn from the Wishart distribution of a null correlation matrix rather than simulated row by row."
        )
    subsampled = reliability.loc[
        (reliability["alpha_bootstrap_rows"] > 0) & (reliability["alpha_bootstrap_rows"] < reliability["complete_n"])
    ]
    if not subsampled.empty:
        warnings.append(
            f"Alpha bootstrap: {config.bootstrap_iterations:,} resamples of a seeded random subsample of "
            f"{int(subsampled['alpha_bootstrap_rows'].min()):,}–{int(subsampled['alpha_bootstrap_rows'].max()):,} "
            f"of {len(complete):,} complete rows, rescaled to the full sample by sqrt(m/n). Alpha, omega and every "
            "other estimate use all complete rows."
        )
    warnings.append("Internal consistency and factor structure do not establish content, criterion, convergent, or discriminant validity.")

    score_summary = _score_summary(
        oriented,
        [("Candidate total (descriptive)", list(config.items)), *score_groups],
        config.minimum_answered,
    )
    return MeasurementResult(
        config=config,
        correlation_matrix=pd.DataFrame(correlation, index=config.items, columns=config.items).reset_index(
            names="item"
        ),
        retention=retention,
        item_structure=item_structure,
        factor_summary=factor_summary,
        factor_correlations=factor_correlations,
        reliability=reliability,
        item_reliability=item_reliability,
        score_summary=score_summary,
        diagnostics={
            "source_rows": int(len(frame)),
            "complete_analysis_rows": int(len(complete)),
            "complete_case_rate": float(len(complete) / len(frame)),
            "item_count": int(len(config.items)),
            "correlation": config.correlation.lower(),
            "extraction": "principal axis common-factor analysis",
            "rotation": "oblimin" if config.planned_factors > 1 else "none",
            "overall_KMO": overall_kmo,
            "bartlett_chi_square": bartlett_chi2,
            "bartlett_df": int(len(config.items) * (len(config.items) - 1) / 2),
            "bartlett_p_exploratory": bartlett_p,
            "correlation_determinant": determinant,
            "correlation_condition_number": float(np.linalg.cond(correlation)),
            "parallel_components_95th_percentile": int(retained),
            "parallel_benchmark": parallel_benchmark,
            "alpha_bootstrap_basis": (
                "Every complete row"
                if subsampled.empty
                else "Seeded subsample rescaled by sqrt(m/n) (see reliability.alpha_bootstrap_rows)"
            ),
            "planned_factors": int(config.planned_factors),
            "loading_support_rate": loading_support_rate,
            "cross_loading_rate": cross_loading_rate,
            "minimum_salient_items_per_factor": minimum_salient,
            "RMSR_descriptive": rmsr,
            "maximum_absolute_residual_correlation": max_residual,
            "improper_solution": heywood,
        },
        warnings=tuple(warnings),
        parallel_factors=retained,
    )
