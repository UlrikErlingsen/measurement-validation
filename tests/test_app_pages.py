from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from measuresignal.examples import COMMUNICATION_TEMPLATE, demo_defaults
APP = str(Path(__file__).parents[1] / "app.py")
NS = "measure"


def k(name: str) -> str:
    return f"{NS}:{name}"


def app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=45).run()


def test_welcome_page_and_brand_are_rendered() -> None:
    at = app()
    assert not at.exception
    assert any("Measure <span>Signal</span>" in markdown.value for markdown in at.markdown)
    assert any("does not manufacture construct validity" in warning.value for warning in at.warning)


def test_fictional_demo_is_preloaded_and_restorable() -> None:
    at = app()
    assert at.session_state[k("contract")] == demo_defaults()
    assert at.session_state[k("source")]["source_type"] == "deterministic synthetic demonstration"
    at.button(key=k("load_demo")).click().run()
    assert not at.exception
    assert at.session_state[k("contract")] == demo_defaults()


def test_every_page_renders_with_fictional_demo() -> None:
    at = app()
    at.button(key=k("load_demo")).click().run()
    for page in [
        "1 · Measurement contract",
        "2 · Response & item audit",
        "3 · Dimensionality",
        "4 · Reliability & scoring",
        "5 · Decision & export",
        "Methods & limits",
    ]:
        at.radio(key=k("page")).set_value(page).run()
        assert not at.exception, page


def test_blank_template_leaves_saved_contract_unchanged() -> None:
    at = app()
    at.button(key=k("load_demo")).click().run()
    at.radio(key=k("page")).set_value("1 · Measurement contract").run()
    at.selectbox(key=k("contract_template")).set_value("Blank").run()
    assert not at.exception
    assert at.session_state[k("contract")] == demo_defaults()


def test_communication_template_prefills_contract_page_without_saving() -> None:
    at = app()
    at.button(key=k("load_demo")).click().run()
    at.radio(key=k("page")).set_value("1 · Measurement contract").run()
    at.selectbox(key=k("contract_template")).set_value(COMMUNICATION_TEMPLATE).run()
    assert not at.exception
    assert any(text_input.value == "Communication response" for text_input in at.text_input)
    assert any(number_input.value == 4 for number_input in at.number_input)
    assert at.session_state[k("contract")] == demo_defaults()


def test_demo_analysis_flow_produces_bounded_holdout_status() -> None:
    at = app()
    at.button(key=k("load_demo")).click().run()
    at.radio(key=k("page")).set_value("2 · Response & item audit").run()
    at.button(key=k("run_measurement")).click().run(timeout=45)
    assert k("analysis") in at.session_state
    assert at.session_state[k("decision")]["status"] == "READY FOR HOLDOUT TEST"
    assert at.session_state[k("comparability")].status == "CROSS-GROUP COMPARISON WITHHELD"
    assert at.session_state[k("comparability")].mean_comparison_allowed is False

    at.radio(key=k("page")).set_value("3 · Dimensionality").run()
    assert not at.exception
    assert len(at.metric) >= 4

    at.radio(key=k("page")).set_value("4 · Reliability & scoring").run()
    assert not at.exception
    assert len(at.metric) >= 4

    at.radio(key=k("page")).set_value("5 · Decision & export").run()
    assert not at.exception
    assert len(at.download_button) >= 4
    body = "\n".join(str(item.value) for item in at.markdown)
    assert "EXPLORATORY EVIDENCE PROFILE" in body
    assert "READY FOR HOLDOUT TEST" in body


def test_audit_runs_once_per_data_and_contract(monkeypatch) -> None:
    # The audit reads every row, so a rerun of the audit page (any widget click) reuses it for large files.
    from measuresignal.ui import app as ui

    calls = []
    original = ui.audit_measure

    def counting_audit(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(ui, "audit_measure", counting_audit)
    at = app()
    at.radio(key=k("page")).set_value("2 · Response & item audit").run()
    at.run()
    assert not at.exception
    assert len(calls) == 1
    at.button(key=k("load_demo")).click().run()
    assert len(calls) == 2  # new data, new audit
