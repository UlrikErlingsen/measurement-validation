"""Exploratory dimensionality and score-reliability analysis for MeasureSignal."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.multivariate.factor import Factor

from .design import orient_items
from .errors import DataProblem


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
    complete = oriented.dropna().copy()
    minimum_rows = max(50, len(config.items) + 10)
    if len(complete) < minimum_rows:
        raise DataProblem(
            f"Only {len(complete)} complete rows remain; at least {minimum_rows} are required for this bounded EFA workflow."
        )
    constant = [item for item in config.items if complete[item].nunique() < 2]
    if constant:
        raise DataProblem("These items are constant in the complete sample: " + ", ".join(constant))
    return oriented, complete


def _correlation(data: pd.DataFrame, method: str) -> np.ndarray:
    normalized = method.strip().lower()
    if normalized not in {"pearson", "spearman"}:
        raise DataProblem("Correlation must be Pearson or Spearman.")
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


def parallel_analysis(
    data: pd.DataFrame,
    *,
    method: str,
    iterations: int,
    seed: int,
) -> tuple[pd.DataFrame, int]:
    """Horn-style PCA parallel analysis using a 95th-percentile random benchmark."""
    if not 49 <= iterations <= 5000:
        raise DataProblem("Use 49 to 5,000 parallel-analysis replications.")
    n, p = data.shape
    observed_corr = _correlation(data, method)
    observed = np.linalg.eigvalsh(observed_corr)[::-1]
    simulated = np.empty((iterations, p), dtype=float)
    rng = np.random.default_rng(seed)
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


def _bootstrap_alpha(matrix: np.ndarray, *, iterations: int, seed: int) -> tuple[float, float]:
    if iterations <= 0:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(iterations):
        sampled = matrix[rng.integers(0, matrix.shape[0], matrix.shape[0])]
        value = _alpha(sampled)
        if np.isfinite(value):
            values.append(value)
    if len(values) < max(20, iterations // 2):
        return np.nan, np.nan
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


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


def _one_factor_omega(matrix: np.ndarray) -> float:
    if matrix.shape[1] < 2:
        return np.nan
    corr = np.corrcoef(matrix, rowvar=False)
    if float(np.linalg.eigvalsh(corr).min()) <= 1e-8:
        return np.nan
    try:
        loadings, uniqueness, phi = _fit_factor_model(
            corr,
            items=tuple(f"item_{i}" for i in range(matrix.shape[1])),
            n=matrix.shape[0],
            factors=1,
        )
    except (ValueError, np.linalg.LinAlgError):
        return np.nan
    return _omega_from_model(loadings, uniqueness, phi)


def _reliability_row(
    label: str,
    matrix: np.ndarray,
    *,
    omega: float,
    bootstrap_iterations: int,
    seed: int,
) -> dict[str, object]:
    alpha_low, alpha_high = _bootstrap_alpha(matrix, iterations=bootstrap_iterations, seed=seed)
    corr = np.corrcoef(matrix, rowvar=False) if matrix.shape[1] >= 2 else np.array([[1.0]])
    mean_interitem = (
        float(np.nanmean(corr[np.triu_indices_from(corr, k=1)])) if matrix.shape[1] >= 2 else np.nan
    )
    return {
        "score": label,
        "items": int(matrix.shape[1]),
        "complete_n": int(matrix.shape[0]),
        "alpha": _alpha(matrix),
        "alpha_bootstrap_low": alpha_low,
        "alpha_bootstrap_high": alpha_high,
        "standardized_alpha": _standardized_alpha(matrix),
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
        answered = oriented[items].notna().sum(axis=1)
        scores = oriented[items].mean(axis=1).where(answered >= needed).dropna()
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
    reliability_rows = [
        _reliability_row(
            "Candidate total (descriptive)",
            full_matrix,
            omega=_omega_from_model(loadings, uniqueness, phi),
            bootstrap_iterations=config.bootstrap_iterations,
            seed=config.seed + 1000,
        )
    ]
    for factor_number, (label, items) in enumerate(score_groups, start=1):
        if len(items) < 2:
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
        other = np.delete(full_matrix, index, axis=1)
        total_without = other.sum(axis=1)
        corrected = float(np.corrcoef(full_matrix[:, index], total_without)[0, 1]) if other.shape[1] else np.nan
        item_reliability_rows.append(
            {
                "item": item,
                "corrected_item_total_correlation": corrected,
                "alpha_if_deleted": _alpha(other),
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
