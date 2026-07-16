from __future__ import annotations

from measuresignal.examples import ITEMS, REVERSED_ITEMS, demo_dataframe, demo_defaults, starter_template


def test_demo_is_deterministic_and_wholly_synthetic_shape() -> None:
    first = demo_dataframe()
    second = demo_dataframe()
    assert first.equals(second)
    assert len(first) == 480
    assert first["respondent_id"].is_unique
    assert set(ITEMS).issubset(first.columns)
    assert set(REVERSED_ITEMS).issubset(ITEMS)
    assert demo_defaults()["planned_factors"] == 3


def test_starter_template_exposes_wide_item_layout() -> None:
    template = starter_template()
    assert template.columns[0] == "respondent_id"
    assert list(template.columns[1:]) == [f"item_{index}" for index in range(1, 9)]
    assert len(template) == 12
