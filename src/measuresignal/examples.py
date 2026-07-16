"""Deterministic, wholly fictional example data for MeasureSignal."""

from __future__ import annotations

import numpy as np
import pandas as pd


ITEMS = (
    "trace_1",
    "trace_2",
    "trace_3",
    "trace_4_rev",
    "interpret_1",
    "interpret_2",
    "interpret_3",
    "interpret_4_rev",
    "action_1",
    "action_2",
    "action_3",
    "action_4_rev",
)
REVERSED_ITEMS = ("trace_4_rev", "interpret_4_rev", "action_4_rev")


def _seven_point(values: np.ndarray) -> np.ndarray:
    thresholds = np.array([-1.15, -0.70, -0.25, 0.25, 0.70, 1.15])
    return np.digitize(values, thresholds).astype(float) + 1


def demo_dataframe(n: int = 480, seed: int = 260716) -> pd.DataFrame:
    """Create a fictional three-dimension response battery with known structure."""
    rng = np.random.default_rng(seed)
    factor_correlation = np.array(
        [
            [1.00, 0.30, 0.25],
            [0.30, 1.00, 0.35],
            [0.25, 0.35, 1.00],
        ]
    )
    latent = rng.multivariate_normal(np.zeros(3), factor_correlation, size=n)
    rows: dict[str, np.ndarray] = {}
    for factor in range(3):
        for item_within in range(4):
            loading = [0.88, 0.82, 0.77, 0.72][item_within]
            cross = 0.08 * latent[:, (factor + 1) % 3]
            continuous = loading * latent[:, factor] + cross + rng.normal(0, 0.58, size=n)
            item = ITEMS[factor * 4 + item_within]
            if item in REVERSED_ITEMS:
                continuous = -continuous
            rows[item] = _seven_point(continuous)

    frame = pd.DataFrame(rows)
    missing = rng.random(frame.shape) < 0.012
    frame = frame.mask(missing)
    frame.insert(0, "respondent_id", [f"MS{index:04d}" for index in range(1, n + 1)])
    frame["collection_wave"] = np.where(np.arange(n) % 2 == 0, "Fictional A", "Fictional B")
    return frame


def demo_defaults() -> dict[str, object]:
    return {
        "unit": "respondent_id",
        "items": list(ITEMS),
        "reversed_items": list(REVERSED_ITEMS),
        "scale_min": 1.0,
        "scale_max": 7.0,
        "planned_factors": 3,
        "correlation": "pearson",
        "loading_threshold": 0.40,
        "cross_loading_threshold": 0.30,
        "reliability_target": 0.70,
        "minimum_answered": 0.80,
        "construct_name": "Decision-interface evidence confidence",
        "construct_definition": (
            "A fictional respondent's perceived ability to trace, interpret, and act on evidence shown by a decision interface."
        ),
        "target_population": "Fictional evaluators of a prototype decision interface",
        "intended_use": "Research-stage subscale scores; no individual classification or high-stakes decision",
        "planned_dimensions": "Traceability; Interpretability; Actionability",
        "validation_plan": "Freeze the exploratory recipe, then evaluate it in an independent holdout sample.",
    }


def starter_template(rows: int = 12) -> pd.DataFrame:
    data: dict[str, object] = {"respondent_id": [f"R{index:03d}" for index in range(1, rows + 1)]}
    for index in range(1, 9):
        data[f"item_{index}"] = [np.nan] * rows
    return pd.DataFrame(data)
