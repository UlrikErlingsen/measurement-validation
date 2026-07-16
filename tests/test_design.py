from __future__ import annotations

import pandas as pd
import pytest

from measuresignal.design import assess_score_comparability, audit_measure, classify_profile, orient_items
from measuresignal.errors import DataProblem
from measuresignal.examples import demo_dataframe, demo_defaults


def test_reverse_keying_uses_declared_endpoints() -> None:
    frame = pd.DataFrame({"a": [1, 2, 7], "b": [2, 3, 4], "c": [5, 6, 7]})
    oriented = orient_items(
        frame,
        items=["a", "b", "c"],
        reversed_items=["a"],
        scale_min=1,
        scale_max=7,
    )
    assert oriented["a"].tolist() == [7, 6, 1]


def test_demo_audit_reports_range_completeness_and_unique_respondents() -> None:
    defaults = demo_defaults()
    audit = audit_measure(
        demo_dataframe(),
        unit=defaults["unit"],
        items=defaults["items"],
        reversed_items=defaults["reversed_items"],
        scale_min=defaults["scale_min"],
        scale_max=defaults["scale_max"],
    )
    assert audit.summary["item_count"] == 12
    assert audit.summary["complete_rows"] == 409
    assert audit.summary["duplicate_unit_rows"] == 0
    assert audit.summary["out_of_range_cells"] == 0
    assert audit.summary["minimum_unique_values"] == 7


def test_cross_wave_means_are_withheld_without_scalar_invariance() -> None:
    frame = demo_dataframe()
    result = assess_score_comparability(
        frame,
        items=demo_defaults()["items"],
        group_column="collection_wave",
        comparison_intended=True,
        evidence_level="Metric / loading invariance",
        evidence_source="External multi-group CFA",
    )

    assert result.status == "CROSS-GROUP COMPARISON WITHHELD"
    assert result.mean_comparison_allowed is False
    assert len(result.group_summary) == 2
    assert "mean" not in result.group_summary.columns


def test_declared_scalar_invariance_opens_gate_without_claiming_verification() -> None:
    result = assess_score_comparability(
        demo_dataframe(),
        items=demo_defaults()["items"],
        group_column="collection_wave",
        comparison_intended=True,
        evidence_level="Scalar / threshold invariance",
        evidence_source="Preregistered external multi-group CFA report, model M3",
    )

    assert result.status == "EXTERNAL SCALAR INVARIANCE DECLARED"
    assert result.mean_comparison_allowed is True
    assert any("does not verify" in warning or "no CFA" in warning for warning in result.warnings)


def test_audit_flags_duplicates_out_of_range_and_constant_patterns() -> None:
    frame = pd.DataFrame(
        {
            "id": [1, 1, 2, 3],
            "a": [2, 2, 8, 4],
            "b": [2, 2, 3, 5],
            "c": [2, 2, 4, 6],
        }
    )
    audit = audit_measure(frame, unit="id", items=["a", "b", "c"], scale_min=1, scale_max=7)
    assert audit.summary["duplicate_unit_rows"] == 2
    assert audit.summary["out_of_range_cells"] == 1
    assert audit.summary["straightline_rows"] == 2
    assert len(audit.warnings) >= 3


def test_straightline_flags_raw_constant_pattern_despite_reverse_keying() -> None:
    # Row 0 gives the same raw answer (7) to every item, including the reverse-keyed
    # one, so it is a true straightliner even though orientation spreads it to 7,7,1.
    frame = pd.DataFrame(
        {
            "a": [7, 4, 2, 5],
            "b": [7, 5, 3, 4],
            "c_rev": [7, 3, 6, 2],
        }
    )
    audit = audit_measure(
        frame, unit=None, items=["a", "b", "c_rev"], reversed_items=["c_rev"], scale_min=1, scale_max=7
    )
    assert audit.summary["straightline_rows"] == 1
    assert any("Constant response patterns" in warning for warning in audit.warnings)


def test_straightline_does_not_flag_keying_consistent_extreme_responder() -> None:
    # Row 0 answers 7,7,1 with the last item reverse-keyed: oriented it is a constant
    # 7,7,7, but the raw pattern varies, so this honest extreme responder is not flagged.
    frame = pd.DataFrame(
        {
            "a": [7, 4, 2, 5],
            "b": [7, 5, 3, 4],
            "c_rev": [1, 3, 6, 2],
        }
    )
    audit = audit_measure(
        frame, unit=None, items=["a", "b", "c_rev"], reversed_items=["c_rev"], scale_min=1, scale_max=7
    )
    assert audit.summary["straightline_rows"] == 0


def test_orientation_rejects_a_non_numeric_item() -> None:
    frame = pd.DataFrame({"a": ["low", "high"], "b": [1, 2], "c": [2, 3]})
    with pytest.raises(DataProblem, match="no numeric responses"):
        orient_items(frame, items=["a", "b", "c"], reversed_items=[], scale_min=1, scale_max=7)


def test_profile_status_is_a_holdout_next_step_not_a_validity_label() -> None:
    defaults = demo_defaults()
    audit = audit_measure(
        demo_dataframe(),
        unit=defaults["unit"],
        items=defaults["items"],
        reversed_items=defaults["reversed_items"],
        scale_min=defaults["scale_min"],
        scale_max=defaults["scale_max"],
    )
    ready = classify_profile(
        audit=audit,
        planned_factors=3,
        parallel_factors=3,
        overall_kmo=0.85,
        loading_support_rate=0.90,
        cross_loading_rate=0.10,
        minimum_salient_items=4,
        reliability_value=0.82,
        reliability_target=0.70,
    )
    unclear = classify_profile(
        audit=audit,
        planned_factors=3,
        parallel_factors=2,
        overall_kmo=0.85,
        loading_support_rate=0.90,
        cross_loading_rate=0.10,
        minimum_salient_items=4,
        reliability_value=0.82,
        reliability_target=0.70,
    )
    assert ready["status"] == "READY FOR HOLDOUT TEST"
    assert unclear["status"] == "STRUCTURE UNCLEAR"
    assert "valid" not in ready["status"].lower()


def test_improper_solution_is_routed_to_structure_unclear() -> None:
    defaults = demo_defaults()
    audit = audit_measure(
        demo_dataframe(),
        unit=defaults["unit"],
        items=defaults["items"],
        reversed_items=defaults["reversed_items"],
        scale_min=defaults["scale_min"],
        scale_max=defaults["scale_max"],
    )
    # Every other diagnostic is strong enough for the top status; the Heywood flag alone
    # must keep the profile out of READY FOR HOLDOUT TEST.
    decision = classify_profile(
        audit=audit,
        planned_factors=3,
        parallel_factors=3,
        overall_kmo=0.85,
        loading_support_rate=0.90,
        cross_loading_rate=0.10,
        minimum_salient_items=4,
        reliability_value=0.82,
        reliability_target=0.70,
        improper_solution=True,
    )
    assert decision["status"] == "STRUCTURE UNCLEAR"
    assert "improper" in decision["meaning"].lower()
    assert "Heywood" in decision["meaning"]
