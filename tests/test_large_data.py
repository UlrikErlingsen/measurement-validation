"""Large-data limits: fast checks that the old caps no longer block and the new ones explain themselves."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from measuresignal import analysis
from measuresignal import io as measure_io
from measuresignal.analysis import MeasurementConfig, analyze_measure
from measuresignal.errors import DataProblem
from measuresignal.examples import demo_dataframe, demo_defaults
from measuresignal.io import read_table


def _demo_config(**overrides: object) -> MeasurementConfig:
    defaults = demo_defaults()
    settings: dict[str, object] = {
        "items": tuple(defaults["items"]),
        "reversed_items": tuple(defaults["reversed_items"]),
        "scale_min": defaults["scale_min"],
        "scale_max": defaults["scale_max"],
        "planned_factors": defaults["planned_factors"],
        "parallel_iterations": 49,
        "bootstrap_iterations": 99,
    }
    settings.update(overrides)
    return MeasurementConfig(**settings)


def test_default_limits_match_the_1000_mb_upload_cap() -> None:
    assert measure_io.DEFAULT_MAX_UPLOAD_MB == 1000
    assert measure_io.MAX_ROWS >= 5_000_000
    assert measure_io.MAX_TOTAL_CELLS >= 50 * measure_io.MAX_ROWS


def test_launcher_variable_sets_the_in_code_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEASURESIGNAL_MAX_UPLOAD_MB", "300")
    assert measure_io._configured_upload_mb() == 300
    monkeypatch.setenv("MEASURESIGNAL_MAX_UPLOAD_MB", "lots")
    assert measure_io._configured_upload_mb() == 1000


def test_csv_beyond_the_old_250000_row_limit_loads_compactly() -> None:
    rows = 300_000
    raw = b"respondent_id,q1,q2,q3\n" + b"1,4,5,6\n2,3,2,7\n" * (rows // 2)
    frame, source = read_table(raw, "wave.csv")
    assert len(frame) == rows
    assert frame["q1"].dtype == np.int8
    assert source["source_filename"] == "wave.csv"


def test_size_message_names_the_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(measure_io, "MAX_ROWS", 3)
    with pytest.raises(DataProblem, match="at most 3 rows"):
        read_table(b"a,b\n1,2\n3,4\n5,6\n7,8\n", "survey.csv")


def test_one_byte_limit_covers_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(measure_io, "MAX_UPLOAD_BYTES", 32)
    payload = json.dumps([{"q1": value} for value in range(20)]).encode()
    with pytest.raises(DataProblem, match="1,000 MB local safety limit"):
        read_table(payload, "survey.json")


def test_wishart_benchmark_matches_row_simulation() -> None:
    rng = np.random.default_rng(11)
    wishart = analysis._wishart_null_eigenvalues(400, 5, 2000, rng)
    simulated = np.array(
        [np.linalg.eigvalsh(np.corrcoef(rng.normal(size=(400, 5)), rowvar=False))[::-1] for _ in range(2000)]
    )
    assert np.quantile(wishart, 0.95, axis=0) == pytest.approx(np.quantile(simulated, 0.95, axis=0), abs=0.02)


def test_large_samples_use_the_labelled_wishart_benchmark(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(analysis, "PARALLEL_ROW_SIMULATION_LIMIT", 100)
    result = analyze_measure(demo_dataframe(), _demo_config())
    assert result.diagnostics["parallel_benchmark"].startswith("Wishart null distribution")
    assert any("Wishart distribution" in warning for warning in result.warnings)
    assert result.parallel_factors == 3


def test_large_alpha_bootstrap_uses_a_labelled_rescaled_subsample(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = demo_dataframe()
    full = analyze_measure(frame, _demo_config())
    monkeypatch.setattr(analysis, "BOOTSTRAP_CELL_BUDGET", 10_000)
    monkeypatch.setattr(analysis, "MIN_BOOTSTRAP_SUBSAMPLE", 200)
    sampled = analyze_measure(frame, _demo_config())
    total = sampled.reliability.iloc[0]
    assert total["alpha_bootstrap_rows"] == 200
    assert total["alpha_bootstrap_low"] < total["alpha"] < total["alpha_bootstrap_high"]
    assert total["alpha"] == pytest.approx(full.reliability.iloc[0]["alpha"])
    assert sampled.diagnostics["alpha_bootstrap_basis"].startswith("Seeded subsample")
    assert any("rescaled to the full sample" in warning for warning in sampled.warnings)
    assert full.diagnostics["alpha_bootstrap_basis"] == "Every complete row"


@pytest.mark.parametrize("method", ["pearson", "spearman"])
def test_large_sample_covariance_path_gives_the_same_estimates(monkeypatch: pytest.MonkeyPatch, method: str) -> None:
    frame = demo_dataframe()
    standard = analyze_measure(frame, _demo_config(correlation=method))
    monkeypatch.setattr(analysis, "LARGE_SAMPLE_ROWS", 100)
    monkeypatch.setattr(analysis, "COVARIANCE_CHUNK_ROWS", 37)
    chunked = analyze_measure(frame, _demo_config(correlation=method))
    for name in ("correlation_matrix", "item_structure", "item_reliability", "score_summary"):
        pd.testing.assert_frame_equal(getattr(chunked, name), getattr(standard, name), rtol=1e-8, atol=1e-10)
    point_estimates = ["alpha", "standardized_alpha", "omega_total", "mean_interitem_correlation"]
    pd.testing.assert_frame_equal(chunked.reliability[point_estimates], standard.reliability[point_estimates], rtol=1e-8)
