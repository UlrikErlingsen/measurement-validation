from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from measuresignal.analysis import (
    MeasurementConfig,
    _alpha,
    analyze_measure,
    factorability_diagnostics,
    parallel_analysis,
)
from measuresignal.errors import DataProblem
from measuresignal.examples import demo_dataframe, demo_defaults


def demo_config(**updates) -> MeasurementConfig:
    defaults = demo_defaults()
    values = {
        "items": tuple(defaults["items"]),
        "reversed_items": tuple(defaults["reversed_items"]),
        "scale_min": defaults["scale_min"],
        "scale_max": defaults["scale_max"],
        "planned_factors": defaults["planned_factors"],
        "parallel_iterations": 99,
        "bootstrap_iterations": 99,
    }
    values.update(updates)
    return MeasurementConfig(**values)


def test_demo_recovers_three_clean_common_factors() -> None:
    result = analyze_measure(demo_dataframe(), demo_config())
    assert result.parallel_factors == 3
    assert result.diagnostics["overall_KMO"] > 0.80
    assert result.diagnostics["loading_support_rate"] == 1.0
    assert result.diagnostics["cross_loading_rate"] == 0.0
    assert result.diagnostics["RMSR_descriptive"] < 0.05

    assignments = result.item_structure.set_index("item")["primary_factor"]
    prefix_factors = {
        prefix: set(assignments[[item for item in assignments.index if item.startswith(prefix)]])
        for prefix in ["trace_", "interpret_", "action_"]
    }
    assert all(len(values) == 1 for values in prefix_factors.values())
    assert len({next(iter(values)) for values in prefix_factors.values()}) == 3


def test_reliability_outputs_alpha_bootstrap_and_omega() -> None:
    result = analyze_measure(demo_dataframe(), demo_config())
    candidate = result.reliability.iloc[0]
    assert 0.80 < candidate["alpha"] < 0.95
    assert candidate["alpha_bootstrap_low"] < candidate["alpha"] < candidate["alpha_bootstrap_high"]
    assert 0.80 < candidate["omega_total"] < 0.98
    assert len(result.reliability) == 4
    assert result.item_reliability["corrected_item_total_correlation"].notna().all()


def test_parallel_analysis_is_deterministic() -> None:
    defaults = demo_defaults()
    complete = demo_dataframe()[defaults["items"]].dropna()
    first, first_count = parallel_analysis(complete, method="pearson", iterations=49, seed=17)
    second, second_count = parallel_analysis(complete, method="pearson", iterations=49, seed=17)
    pd.testing.assert_frame_equal(first, second)
    assert first_count == second_count == 3


def test_factorability_diagnostics_identify_strong_shared_variance() -> None:
    defaults = demo_defaults()
    matrix = demo_dataframe()[defaults["items"]].dropna().corr().to_numpy()
    kmo, item_kmo, chi2, p_value, determinant = factorability_diagnostics(matrix, 409)
    assert kmo > 0.80
    assert np.min(item_kmo) > 0.70
    assert chi2 > 1000
    assert p_value < 1e-10
    assert determinant > 0


def test_alpha_kmo_and_bartlett_match_hand_derived_values() -> None:
    """Every expected value is derived by hand in this test from the published formulas.

    Alpha (Cronbach, 1951) on items [1,2,3,4,5], [2,2,3,4,4], [1,3,3,3,5]:
    sample variances (ddof=1) are 10/4 = 2.5, 4/4 = 1.0, and 8/4 = 2.0;
    the total score [4,7,9,11,14] has variance 58/4 = 14.5;
    alpha = (3/2) * (1 - 5.5/14.5) = 27/29.
    """
    matrix = np.array(
        [
            [1.0, 2.0, 1.0],
            [2.0, 2.0, 3.0],
            [3.0, 3.0, 3.0],
            [4.0, 4.0, 3.0],
            [5.0, 4.0, 5.0],
        ]
    )
    assert _alpha(matrix) == pytest.approx(27 / 29)

    # Compound-symmetry correlation matrix with r = 0.5 for p = 3 items:
    # determinant |R| = (1 - r)^2 (1 + 2r) = 0.25 * 2 = 0.5;
    # R^{-1} = 2(I - J/4) has diagonal 1.5 and off-diagonal -0.5, so every
    # partial correlation is 0.5/1.5 = 1/3.
    # KMO (Kaiser, 1974) = sum(r^2) / [sum(r^2) + sum(partial^2)]
    #                    = (2 * 1/4) / (2 * 1/4 + 2 * 1/9) = 9/13, item-wise and overall.
    correlation = np.array([[1.0, 0.5, 0.5], [0.5, 1.0, 0.5], [0.5, 0.5, 1.0]])
    overall_kmo, item_kmo, chi2, p_value, determinant = factorability_diagnostics(correlation, 100)
    assert determinant == pytest.approx(0.5)
    assert overall_kmo == pytest.approx(9 / 13)
    assert item_kmo == pytest.approx(np.full(3, 9 / 13))

    # Bartlett (1950): chi2 = -[n - 1 - (2p + 5)/6] ln|R| with n = 100 and p = 3
    # gives (99 - 11/6) * ln 2 on p(p - 1)/2 = 3 degrees of freedom.
    expected_chi2 = (99 - 11 / 6) * math.log(2.0)
    assert chi2 == pytest.approx(expected_chi2)
    assert p_value == pytest.approx(float(stats.chi2.sf(expected_chi2, 3)))


def test_spearman_mode_runs_and_retains_the_structure() -> None:
    result = analyze_measure(
        demo_dataframe(),
        demo_config(correlation="spearman", parallel_iterations=49, bootstrap_iterations=0),
    )
    assert result.parallel_factors == 3
    assert result.diagnostics["correlation"] == "spearman"


def test_singular_item_set_is_rejected_instead_of_silently_repaired() -> None:
    rng = np.random.default_rng(4)
    value = rng.normal(size=100)
    frame = pd.DataFrame({"a": value, "b": value, "c": rng.normal(size=100)})
    config = MeasurementConfig(
        items=("a", "b", "c"),
        reversed_items=(),
        scale_min=-5,
        scale_max=5,
        planned_factors=1,
        parallel_iterations=49,
        bootstrap_iterations=0,
    )
    with pytest.raises(DataProblem, match="singular"):
        analyze_measure(frame, config)
