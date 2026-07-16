from __future__ import annotations

from measuresignal.examples import (
    BLANK_TEMPLATE,
    COMMUNICATION_TEMPLATE,
    ITEMS,
    REVERSED_ITEMS,
    contract_template,
    demo_dataframe,
    demo_defaults,
    starter_template,
)


def test_demo_is_deterministic_and_wholly_synthetic_shape() -> None:
    first = demo_dataframe()
    second = demo_dataframe()
    assert first.equals(second)
    assert len(first) == 480
    assert first["respondent_id"].is_unique
    assert set(ITEMS).issubset(first.columns)
    assert set(REVERSED_ITEMS).issubset(ITEMS)
    assert demo_defaults()["planned_factors"] == 3


def test_communication_template_merges_expected_contract_fields() -> None:
    prefill = contract_template(COMMUNICATION_TEMPLATE)
    merged = {**demo_defaults(), **prefill}
    assert merged["construct_name"] == "Communication response"
    assert merged["planned_factors"] == 4
    assert merged["scale_min"] == 1.0
    assert merged["scale_max"] == 7.0
    assert merged["loading_threshold"] == 0.40
    assert merged["cross_loading_threshold"] == 0.30
    assert merged["reliability_target"] == 0.70
    assert merged["minimum_answered"] == 0.80
    assert "oblique" in str(merged["planned_dimensions"]).lower()
    assert "awareness" in str(merged["construct_definition"]).lower()
    assert "excluded" in str(merged["intended_use"]).lower()
    assert merged["items"] == list(ITEMS)
    assert contract_template(BLANK_TEMPLATE) == {}


def test_starter_template_exposes_wide_item_layout() -> None:
    template = starter_template()
    assert template.columns[0] == "respondent_id"
    assert template.columns[1] == "collection_wave"
    assert list(template.columns[2:]) == [f"item_{index}" for index in range(1, 9)]
    assert len(template) == 12
