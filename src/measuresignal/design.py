"""Response audit and transparent evidence-profile rules for MeasureSignal."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .errors import DataProblem


@dataclass(frozen=True)
class AuditResult:
    summary: dict[str, object]
    item_audit: pd.DataFrame
    response_audit: pd.DataFrame
    warnings: tuple[str, ...]


def orient_items(
    frame: pd.DataFrame,
    *,
    items: list[str] | tuple[str, ...],
    reversed_items: list[str] | tuple[str, ...],
    scale_min: float,
    scale_max: float,
) -> pd.DataFrame:
    """Convert selected items to numeric and reverse declared keys."""
    if scale_max <= scale_min:
        raise DataProblem("The response maximum must be greater than the response minimum.")
    if len(items) < 3:
        raise DataProblem("Choose at least three candidate scale items.")
    if len(items) > 50:
        raise DataProblem("Version 1.0 supports at most 50 items in one measurement model.")
    if len(set(items)) != len(items):
        raise DataProblem("Each item may appear only once in the measurement model.")
    missing = [item for item in items if item not in frame.columns]
    if missing:
        raise DataProblem("These selected items are missing: " + ", ".join(missing))
    invalid_reverse = sorted(set(reversed_items) - set(items))
    if invalid_reverse:
        raise DataProblem("Reverse-key selections are not in the item set: " + ", ".join(invalid_reverse))

    oriented = frame[list(items)].apply(pd.to_numeric, errors="coerce")
    empty = [item for item in items if oriented[item].notna().sum() == 0]
    if empty:
        raise DataProblem("These items contain no numeric responses: " + ", ".join(empty))
    for item in reversed_items:
        oriented[item] = scale_min + scale_max - oriented[item]
    return oriented


def audit_measure(
    frame: pd.DataFrame,
    *,
    unit: str | None,
    items: list[str] | tuple[str, ...],
    reversed_items: list[str] | tuple[str, ...] = (),
    scale_min: float,
    scale_max: float,
) -> AuditResult:
    """Audit range, missingness, response patterns, and item distributions."""
    if frame.empty:
        raise DataProblem("The dataset has no rows.")
    oriented = orient_items(
        frame,
        items=items,
        reversed_items=reversed_items,
        scale_min=scale_min,
        scale_max=scale_max,
    )
    original_numeric = frame[list(items)].apply(pd.to_numeric, errors="coerce")
    out_of_range = (original_numeric.lt(scale_min) | original_numeric.gt(scale_max)) & original_numeric.notna()

    item_rows: list[dict[str, object]] = []
    for item in items:
        values = oriented[item]
        observed = values.dropna()
        n = int(len(observed))
        item_rows.append(
            {
                "item": item,
                "keying": "reverse" if item in reversed_items else "forward",
                "observed_n": n,
                "missing_rate": float(values.isna().mean()),
                "unique_values": int(observed.nunique()),
                "mean_oriented": float(observed.mean()) if n else np.nan,
                "sd_oriented": float(observed.std(ddof=1)) if n > 1 else np.nan,
                "skew_oriented": float(observed.skew()) if n > 2 else np.nan,
                "floor_rate_oriented": float((observed == scale_min).mean()) if n else np.nan,
                "ceiling_rate_oriented": float((observed == scale_max).mean()) if n else np.nan,
                "out_of_range_cells": int(out_of_range[item].sum()),
            }
        )
    item_audit = pd.DataFrame(item_rows)

    answered = oriented.notna().sum(axis=1)
    complete = answered == len(items)
    enough_for_pattern = answered >= 3
    # Constant-pattern detection uses the raw (pre-orientation) responses: a respondent
    # who gives the same raw answer to every item is a straightliner even when reverse
    # keying would spread those answers apart after orientation.
    straightline = original_numeric.nunique(axis=1, dropna=True).eq(1) & enough_for_pattern
    response_audit = pd.DataFrame(
        {
            "answered_items": answered.value_counts().sort_index().index.astype(int),
            "respondents": answered.value_counts().sort_index().to_numpy(int),
        }
    )
    response_audit["share"] = response_audit["respondents"] / len(frame)

    duplicate_units = 0
    missing_units = 0
    if unit:
        if unit not in frame.columns:
            raise DataProblem(f"The respondent identifier ‘{unit}’ is not in the data.")
        missing_units = int(frame[unit].isna().sum())
        duplicate_units = int(frame.loc[frame[unit].notna(), unit].duplicated(keep=False).sum())

    max_endpoint = float(
        item_audit[["floor_rate_oriented", "ceiling_rate_oriented"]].max(axis=1).max()
    )
    min_unique = int(item_audit["unique_values"].min())
    warnings: list[str] = []
    if int(out_of_range.to_numpy().sum()):
        warnings.append("At least one response falls outside the declared response range; modeling is withheld.")
    if duplicate_units:
        warnings.append("The selected respondent identifier repeats; independence or the wide-row layout may be false.")
    if missing_units:
        warnings.append("Some rows have no respondent identifier, so uniqueness cannot be fully checked.")
    if float(item_audit["missing_rate"].max()) > 0.20:
        warnings.append("At least one item is missing for more than 20% of respondents.")
    if max_endpoint > 0.50:
        warnings.append("At least one oriented item places more than half of responses at an endpoint.")
    if int(straightline.sum()):
        warnings.append("Constant response patterns are flagged for review; they are not automatically classified as careless.")
    if min_unique < 3:
        warnings.append("At least one item has fewer than three observed response values.")

    return AuditResult(
        summary={
            "source_rows": int(len(frame)),
            "item_count": int(len(items)),
            "complete_rows": int(complete.sum()),
            "complete_case_rate": float(complete.mean()),
            "respondent_to_item_ratio_complete": float(complete.sum() / len(items)),
            "duplicate_unit_rows": duplicate_units,
            "missing_unit_rows": missing_units,
            "straightline_rows": int(straightline.sum()),
            "out_of_range_cells": int(out_of_range.to_numpy().sum()),
            "maximum_item_missing_rate": float(item_audit["missing_rate"].max()),
            "maximum_endpoint_rate": max_endpoint,
            "minimum_unique_values": min_unique,
        },
        item_audit=item_audit,
        response_audit=response_audit,
        warnings=tuple(warnings),
    )


def classify_profile(
    *,
    audit: AuditResult,
    planned_factors: int,
    parallel_factors: int,
    overall_kmo: float,
    loading_support_rate: float,
    cross_loading_rate: float,
    minimum_salient_items: int,
    reliability_value: float,
    reliability_target: float,
    improper_solution: bool = False,
) -> dict[str, str]:
    """Translate diagnostics into a bounded next step, never a validity certificate."""
    summary = audit.summary
    if int(summary["out_of_range_cells"]) > 0 or int(summary["duplicate_unit_rows"]) > 0:
        return {
            "status": "DATA CHECK REQUIRED",
            "meaning": "Range or respondent-uniqueness problems must be resolved before reading the factor solution.",
            "action": "Correct the source data or document why repeated identifiers represent independent units.",
        }
    minimum_rows = max(50, int(summary["item_count"]) + 10)
    if int(summary["complete_rows"]) < minimum_rows or not np.isfinite(overall_kmo) or overall_kmo < 0.50:
        return {
            "status": "DATA LIMITED",
            "meaning": "The complete sample or shared-correlation structure is too weak for a stable exploratory reading.",
            "action": "Improve response completeness, sample coverage, or the item pool before interpreting dimensions.",
        }
    if improper_solution:
        return {
            "status": "STRUCTURE UNCLEAR",
            "meaning": "The factor solution is statistically improper (a Heywood case): at least one uniqueness estimate falls outside (0, 1), so loadings and reliability cannot be read at face value.",
            "action": "Diagnose the improper solution—factor count, item redundancy, sample size, or model misfit—before any scoring or holdout planning.",
        }
    if planned_factors != parallel_factors or minimum_salient_items < 3 or cross_loading_rate > 0.25:
        return {
            "status": "STRUCTURE UNCLEAR",
            "meaning": "Retention, factor coverage, or cross-loading evidence conflicts with the declared structure.",
            "action": "Compare theory-consistent alternatives and collect new data; do not delete items only to optimize this sample.",
        }
    if loading_support_rate >= 0.80 and np.isfinite(reliability_value) and reliability_value >= reliability_target:
        return {
            "status": "READY FOR HOLDOUT TEST",
            "meaning": "The declared exploratory structure is plausible enough to pre-specify for an independent confirmation sample.",
            "action": "Freeze the item wording and scoring rule, then test dimensionality, reliability, and validity on new data.",
        }
    return {
        "status": "RESPECIFY WITH THEORY",
        "meaning": "The dimensional pattern is readable, but loading or reliability evidence is not yet strong enough for scoring confidence.",
        "action": "Review construct coverage, wording, keying, and response process before another planned data collection.",
    }
