from __future__ import annotations

from streamlit.testing.v1 import AppTest

from measuresignal.examples import COMMUNICATION_TEMPLATE, demo_defaults


def app() -> AppTest:
    return AppTest.from_file("app.py", default_timeout=45).run()


def test_welcome_page_and_brand_are_rendered() -> None:
    at = app()
    assert not at.exception
    assert any("MeasureSignal" in markdown.value for markdown in at.markdown)
    assert any("does not manufacture construct validity" in warning.value for warning in at.warning)


def test_every_page_renders_with_fictional_demo() -> None:
    at = app()
    at.button(key="load_demo").click().run()
    for page in [
        "1 · Measurement contract",
        "2 · Response & item audit",
        "3 · Dimensionality",
        "4 · Reliability & scoring",
        "5 · Decision & export",
        "Methods & limits",
    ]:
        at.radio(key="navigation").set_value(page).run()
        assert not at.exception, page


def test_blank_template_leaves_saved_contract_unchanged() -> None:
    at = app()
    at.button(key="load_demo").click().run()
    at.radio(key="navigation").set_value("1 · Measurement contract").run()
    at.selectbox(key="contract_template").set_value("Blank").run()
    assert not at.exception
    assert at.session_state["contract"] == demo_defaults()


def test_communication_template_prefills_contract_page_without_saving() -> None:
    at = app()
    at.button(key="load_demo").click().run()
    at.radio(key="navigation").set_value("1 · Measurement contract").run()
    at.selectbox(key="contract_template").set_value(COMMUNICATION_TEMPLATE).run()
    assert not at.exception
    assert any(text_input.value == "Communication response" for text_input in at.text_input)
    assert any(number_input.value == 4 for number_input in at.number_input)
    assert at.session_state["contract"] == demo_defaults()


def test_demo_analysis_flow_produces_bounded_holdout_status() -> None:
    at = app()
    at.button(key="load_demo").click().run()
    at.radio(key="navigation").set_value("2 · Response & item audit").run()
    at.button(key="run_measurement").click().run(timeout=45)
    assert "analysis" in at.session_state
    assert at.session_state["decision"]["status"] == "READY FOR HOLDOUT TEST"
    assert at.session_state["comparability"].status == "CROSS-GROUP COMPARISON WITHHELD"
    assert at.session_state["comparability"].mean_comparison_allowed is False

    at.radio(key="navigation").set_value("3 · Dimensionality").run()
    assert not at.exception
    assert len(at.metric) >= 4

    at.radio(key="navigation").set_value("4 · Reliability & scoring").run()
    assert not at.exception
    assert len(at.metric) >= 4

    at.radio(key="navigation").set_value("5 · Decision & export").run()
    assert not at.exception
    assert len(at.download_button) >= 4
