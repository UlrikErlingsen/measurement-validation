"""Measure Signal Streamlit UI.

Everything that draws the app runs inside ``render()`` (or the functions it calls), so it runs on every rerun,
both in the standalone ``app.py`` and inside Signal Hub. Module-level code here only defines constants and
functions. ``render()`` never calls ``st.set_page_config`` or ``st.navigation``.
"""

from __future__ import annotations

import hashlib
import inspect
import os
import traceback

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from measuresignal import __version__
from measuresignal.analysis import MeasurementConfig, analyze_measure
from measuresignal.design import (
    INVARIANCE_LEVELS,
    assess_score_comparability,
    audit_measure,
    classify_profile,
)
from measuresignal.errors import DataProblem, friendly_message
from measuresignal.examples import (
    BLANK_TEMPLATE,
    COMMUNICATION_TEMPLATE,
    contract_template,
    demo_dataframe,
    demo_defaults,
    starter_template,
)
from measuresignal.io import (
    build_evidence_pack,
    dataframe_to_xlsx,
    evidence_to_csv_zip,
    evidence_to_excel,
    evidence_to_json,
    read_table,
)
from measuresignal.ui import signal_theme as sig


NS = "measure"


def k(name: str) -> str:
    """Namespace a session-state or widget key with the app slug, so apps can share one Hub session."""
    return f"{NS}:{name}"


SIDEBAR_TAGLINE = "Measurement evidence without the alpha-is-validity shortcut."
MASTHEAD_KICKER = "DEFINE → DIAGNOSE → CONFIRM"
MASTHEAD_PROMISES = ["Item evidence", "Common factors", "Honest scoring"]
FOOTER_LINE = "exploratory measurement evidence; comparisons require invariance"
CAUTION = (
    "**Measure Signal diagnoses score behavior; it does not manufacture construct validity.** Content coverage, "
    "response process, sampling, external relationships, fairness, and independent confirmation remain human research "
    "responsibilities. Reliability is evidence about scores in a population and use—not a permanent instrument stamp."
)
RESULT_KEYS = ("audit", "analysis", "decision", "comparability")


def full_width(widget, *args, **kwargs):
    """Use Streamlit's current width API while retaining older compatibility."""
    try:
        parameters = inspect.signature(widget).parameters
    except (TypeError, ValueError):
        parameters = {}
    width_parameter = parameters.get("width")
    if width_parameter is not None and isinstance(width_parameter.default, str):
        kwargs["width"] = "stretch"
    elif "use_container_width" in parameters:
        kwargs["use_container_width"] = True
    return widget(*args, **kwargs)


def show_error(exc: Exception) -> None:
    """Render a useful error while keeping tracebacks opt-in."""
    st.error(friendly_message(exc))
    if not isinstance(exc, (DataProblem, ValueError)) and os.getenv("MEASURESIGNAL_DEBUG") == "1":
        with st.expander("Technical details"):
            st.code("".join(traceback.format_exception(exc)))


def reset_results() -> None:
    for key in RESULT_KEYS:
        st.session_state.pop(k(key), None)


def _new_contract_form() -> None:
    """Start a fresh set of contract widgets, so they show the newly loaded contract instead of stale input."""
    st.session_state[k("contract_revision")] = st.session_state.get(k("contract_revision"), 0) + 1


def load_demo() -> None:
    frame = demo_dataframe()
    st.session_state[k("data")] = frame
    st.session_state[k("source")] = {
        "source_filename": "measuresignal-fictional-scale-demo.csv",
        "source_sheet": "",
        "source_sha256": hashlib.sha256(frame.to_csv(index=False).encode("utf-8")).hexdigest(),
        "source_type": "deterministic synthetic demonstration",
    }
    st.session_state[k("contract")] = demo_defaults()
    _new_contract_form()
    reset_results()


def _ensure_state() -> None:
    """Preload the fictional demo on the first run, so every page has data to show."""
    if k("data") not in st.session_state:
        load_demo()


def select_index(options: list[object], value: object, fallback: int = 0) -> int:
    return options.index(value) if value in options else min(fallback, len(options) - 1)


def render_welcome() -> None:
    sig.hero(
        NS,
        eyebrow="MEASUREMENT EVIDENCE WORKBENCH",
        title="Is this score measuring",
        em="what you think it is?",
        body=(
            "Turn a wide survey item battery into an auditable exploratory record: define the construct and intended "
            "use, inspect response quality, compare a planned common-factor model with parallel analysis, quantify "
            "score reliability, and freeze a recipe for independent confirmation."
        ),
        pills=[
            "range & missingness audit",
            "KMO + Bartlett",
            "parallel analysis",
            "principal-axis EFA",
            "oblimin rotation",
            "alpha + omega",
        ],
    )
    st.warning(CAUTION)
    sig.cards(
        [
            (
                "01 · DEFINE",
                "Name the intended score",
                "Record construct boundaries, population, planned dimensions, response range, reverse keys, scoring "
                "completeness, and validation plan.",
            ),
            (
                "02 · DIAGNOSE",
                "Read structure, not folklore",
                "Inspect shared variance, parallel-analysis retention, common-factor loadings, factor correlations, "
                "cross-loadings, and residuals.",
            ),
            (
                "03 · CONFIRM",
                "Freeze the next test",
                "Use reliability as one property of scores—not a validity certificate—and carry the exploratory recipe "
                "into genuinely new data.",
            ),
        ]
    )
    st.markdown("### A deliberately bounded release")
    st.write(
        "Measure Signal supports three to fifty numeric multi-item responses in wide, one-row-per-respondent data. "
        "It offers Pearson or Spearman correlations, principal-axis common-factor analysis, oblimin rotation for "
        "multifactor models, Horn-style PCA parallel analysis, alpha with bootstrap intervals, omega total, and "
        "aggregate exploratory score summaries. It does not claim CFA, measurement invariance, IRT, DIF, test-retest, "
        "inter-rater reliability, multilevel structure, survey weights, polychoric correlations, or validity proof."
    )
    st.info(
        "A fictional scale demonstration is preloaded. Replace it by uploading a CSV/XLSX/JSON response table in the "
        "sidebar, or restore it with **Load fictional three-factor demo**."
    )


def render_contract() -> None:
    sig.header(
        "Step 1",
        "Measurement contract",
        "Define the score and its use before inspecting which items load cleanly in this sample.",
    )
    if k("data") not in st.session_state:
        st.info("Load or upload response data first.")
        return
    data: pd.DataFrame = st.session_state[k("data")]
    current = dict(st.session_state.get(k("contract"), {}))
    columns = list(map(str, data.columns))
    numeric_candidates = [
        column for column in columns if pd.to_numeric(data[column], errors="coerce").notna().sum() >= 3
    ]
    if len(numeric_candidates) < 3:
        st.error("Fewer than three numeric item candidates were detected.")
        return

    st.markdown("#### Start from a template")
    template_choice = st.selectbox(
        "Start from a template",
        [BLANK_TEMPLATE, COMMUNICATION_TEMPLATE],
        index=0,
        key=k("contract_template"),
        help="Templates prefill the wording and settings below; they never choose your item columns.",
    )
    if template_choice != BLANK_TEMPLATE:
        current.update(contract_template(template_choice))
        st.info(
            "Template values are prefilled below and every field stays fully editable. Nothing is stored until you "
            "press **Save measurement contract**. One honest caveat: a single yes/no awareness question is not a "
            "multi-item scale — keep near-binary awareness measures out of the factor battery and report them separately."
        )
    # Contract widgets are keyed per loaded contract and template, so a new dataset or template prefills them afresh
    # while edits survive ordinary reruns.
    form = f"{st.session_state.get(k('contract_revision'), 0)}:{template_choice}"

    st.markdown("#### Data roles and keying")
    col1, col2 = st.columns(2)
    with col1:
        unit_options = ["(use row number)", *columns]
        unit_value = current.get("unit") or "(use row number)"
        unit = st.selectbox(
            "Respondent identifier",
            unit_options,
            index=select_index(unit_options, unit_value),
            key=k(f"contract_unit:{form}"),
            help="Used only to audit repeated respondent rows; identifiers are excluded from evidence exports.",
        )
        default_items = [item for item in current.get("items", []) if item in numeric_candidates]
        items = st.multiselect(
            "Candidate scale items · choose 3–50",
            numeric_candidates,
            default=default_items,
            max_selections=50,
            key=k(f"contract_items:{form}"),
        )
    with col2:
        reversed_items = st.multiselect(
            "Reverse-keyed items",
            items,
            default=[item for item in current.get("reversed_items", []) if item in items],
            key=k(f"contract_reversed:{form}"),
            help="Orientation is max + min − response. Keying must come from the questionnaire, not the observed sign.",
        )
        c1, c2 = st.columns(2)
        scale_min = c1.number_input(
            "Response minimum", value=float(current.get("scale_min", 1.0)), step=1.0, key=k(f"contract_min:{form}")
        )
        scale_max = c2.number_input(
            "Response maximum", value=float(current.get("scale_max", 7.0)), step=1.0, key=k(f"contract_max:{form}")
        )

    st.markdown("#### Cross-wave or group comparability")
    comparison_intended = st.toggle(
        "I intend to compare this construct score across waves or groups",
        value=bool(current.get("comparison_intended", False)),
        key=k(f"contract_comparison:{form}"),
        help="Mean comparisons require stronger evidence than finding a similar-looking factor pattern.",
    )
    comparison_options = ["(no wave/group column)", *columns]
    current_group = current.get("comparison_group") or "(no wave/group column)"
    comparison_group = st.selectbox(
        "Wave or group column",
        comparison_options,
        index=select_index(comparison_options, current_group),
        key=k(f"contract_group:{form}"),
    )
    invariance_evidence_level = st.selectbox(
        "Strongest externally established invariance evidence",
        list(INVARIANCE_LEVELS),
        index=select_index(list(INVARIANCE_LEVELS), current.get("invariance_evidence_level", "None established")),
        key=k(f"contract_invariance_level:{form}"),
        help="Scalar/threshold invariance is the usual minimum for comparing construct means. This app records but does not test it.",
    )
    invariance_evidence_source = st.text_area(
        "Evidence source, model, estimator, and any partial-invariance decisions",
        value=str(current.get("invariance_evidence_source", "")),
        height=72,
        placeholder="Example: preregistered multi-group CFA report, model specification, date, and decision notes",
        key=k(f"contract_invariance_source:{form}"),
    )
    st.info(
        "Measure Signal does not run CFA or measurement-invariance tests. It withholds cross-wave/group construct-score "
        "comparisons unless scalar/threshold evidence and its source are explicitly declared."
    )

    st.markdown("#### Construct and intended use")
    construct_name = st.text_input(
        "Construct / instrument name", value=str(current.get("construct_name", "")), key=k(f"contract_name:{form}")
    )
    construct_definition = st.text_area(
        "Construct definition and boundaries",
        value=str(current.get("construct_definition", "")),
        height=92,
        key=k(f"contract_definition:{form}"),
    )
    col1, col2 = st.columns(2)
    with col1:
        target_population = st.text_area(
            "Target population and administration context",
            value=str(current.get("target_population", "")),
            height=92,
            key=k(f"contract_population:{form}"),
        )
        intended_use = st.text_area(
            "Intended score use and explicitly excluded uses",
            value=str(current.get("intended_use", "")),
            height=92,
            key=k(f"contract_use:{form}"),
        )
    with col2:
        planned_dimensions = st.text_area(
            "Planned dimensions and theoretical rationale",
            value=str(current.get("planned_dimensions", "")),
            height=92,
            key=k(f"contract_dimensions:{form}"),
        )
        validation_plan = st.text_area(
            "Independent confirmation and validity plan",
            value=str(current.get("validation_plan", "")),
            height=92,
            key=k(f"contract_validation:{form}"),
        )

    st.markdown("#### Declared analysis settings")
    col1, col2, col3 = st.columns(3)
    with col1:
        max_factors = max(1, min(8, len(items) - 1)) if items else 1
        planned_factors = st.number_input(
            "Planned factors",
            min_value=1,
            max_value=max_factors,
            value=min(int(current.get("planned_factors", 1)), max_factors),
            key=k(f"contract_factors:{form}:{max_factors}"),
        )
        correlation = st.radio(
            "Item correlation",
            ["pearson", "spearman"],
            index=select_index(["pearson", "spearman"], current.get("correlation", "pearson")),
            horizontal=True,
            key=k(f"contract_correlation:{form}"),
        )
    with col2:
        loading_threshold = st.slider(
            "Primary-loading threshold",
            min_value=0.20,
            max_value=0.80,
            value=float(current.get("loading_threshold", 0.40)),
            step=0.05,
            key=k(f"contract_loading:{form}"),
        )
        cross_loading_threshold = st.slider(
            "Cross-loading threshold",
            min_value=0.15,
            max_value=float(loading_threshold),
            value=min(float(current.get("cross_loading_threshold", 0.30)), float(loading_threshold)),
            step=0.05,
            key=k(f"contract_cross_loading:{form}"),
        )
    with col3:
        reliability_target = st.slider(
            "Reliability planning target",
            min_value=0.50,
            max_value=0.95,
            value=float(current.get("reliability_target", 0.70)),
            step=0.05,
            key=k(f"contract_reliability:{form}"),
            help="A use-specific planning threshold, not a universal pass mark.",
        )
        minimum_answered = st.slider(
            "Minimum proportion answered for a score",
            min_value=0.50,
            max_value=1.00,
            value=float(current.get("minimum_answered", 0.80)),
            step=0.05,
            key=k(f"contract_answered:{form}"),
        )
    with st.expander("Reproducibility settings"):
        c1, c2 = st.columns(2)
        parallel_iterations = c1.select_slider(
            "Parallel-analysis replications",
            options=[99, 299, 499, 999],
            value=int(current.get("parallel_iterations", 499)),
            key=k(f"contract_parallel:{form}"),
        )
        bootstrap_iterations = c2.select_slider(
            "Alpha-bootstrap replications",
            options=[0, 99, 299, 499, 999],
            value=int(current.get("bootstrap_iterations", 499)),
            key=k(f"contract_bootstrap:{form}"),
        )

    if st.button("Save measurement contract", type="primary", key=k("save_contract")):
        if len(items) < 3:
            st.error("Choose at least three candidate items.")
            return
        if scale_max <= scale_min:
            st.error("Response maximum must exceed response minimum.")
            return
        st.session_state[k("contract")] = {
            "unit": None if unit == "(use row number)" else unit,
            "items": list(items),
            "reversed_items": list(reversed_items),
            "scale_min": float(scale_min),
            "scale_max": float(scale_max),
            "planned_factors": int(planned_factors),
            "correlation": correlation,
            "loading_threshold": float(loading_threshold),
            "cross_loading_threshold": float(cross_loading_threshold),
            "reliability_target": float(reliability_target),
            "minimum_answered": float(minimum_answered),
            "parallel_iterations": int(parallel_iterations),
            "bootstrap_iterations": int(bootstrap_iterations),
            "construct_name": construct_name,
            "construct_definition": construct_definition,
            "target_population": target_population,
            "intended_use": intended_use,
            "planned_dimensions": planned_dimensions,
            "validation_plan": validation_plan,
            "comparison_group": None if comparison_group == "(no wave/group column)" else comparison_group,
            "comparison_intended": bool(comparison_intended),
            "invariance_evidence_level": invariance_evidence_level,
            "invariance_evidence_source": invariance_evidence_source,
        }
        reset_results()
        st.success("Measurement contract saved. Continue to the response and item audit.")


def render_audit() -> None:
    sig.header(
        "Step 2",
        "Response & item audit",
        "Diagnostics flag data conditions. They cannot identify careless respondents or validate item meaning on their own.",
    )
    if k("data") not in st.session_state or k("contract") not in st.session_state:
        st.info("Load data and save the measurement contract first.")
        return
    data: pd.DataFrame = st.session_state[k("data")]
    contract = st.session_state[k("contract")]
    try:
        audit = audit_measure(
            data,
            unit=contract.get("unit"),
            items=contract["items"],
            reversed_items=contract.get("reversed_items", []),
            scale_min=float(contract["scale_min"]),
            scale_max=float(contract["scale_max"]),
        )
        st.session_state[k("audit")] = audit
        comparability = assess_score_comparability(
            data,
            items=contract["items"],
            group_column=contract.get("comparison_group"),
            comparison_intended=bool(contract.get("comparison_intended", False)),
            evidence_level=str(contract.get("invariance_evidence_level", "None established")),
            evidence_source=str(contract.get("invariance_evidence_source", "")),
        )
        st.session_state[k("comparability")] = comparability
    except Exception as exc:
        show_error(exc)
        return

    summary = audit.summary
    columns = st.columns(4)
    columns[0].metric("Respondents", f"{int(summary['source_rows']):,}")
    columns[1].metric("Complete rows", f"{int(summary['complete_rows']):,}")
    columns[2].metric("Complete-case rate", f"{100 * float(summary['complete_case_rate']):.1f}%")
    columns[3].metric("Constant patterns", f"{int(summary['straightline_rows']):,}")
    if audit.warnings:
        for warning in audit.warnings:
            st.warning(warning)
    else:
        st.success("No automatic range, uniqueness, missingness, endpoint, or response-pattern flag was triggered.")

    st.markdown("#### Cross-wave/group comparability gate")
    if comparability.mean_comparison_allowed:
        st.success(f"**{comparability.status}.** {comparability.meaning}")
    elif bool(contract.get("comparison_intended", False)):
        st.error(f"**{comparability.status}.** {comparability.meaning}")
    else:
        st.info(f"**{comparability.status}.** {comparability.meaning}")
    st.write(f"**Required next action:** {comparability.action}")
    if not comparability.group_summary.empty:
        group_display = comparability.group_summary.copy()
        for column in ("complete_item_rate", "maximum_item_missing_rate"):
            group_display[column] = (100 * group_display[column]).round(1)
        full_width(st.dataframe, group_display, hide_index=True)
        st.caption("Rates are percentages. No construct-score means or group differences are calculated on this gate.")
    for warning in comparability.warnings:
        st.warning(warning)

    tab1, tab2 = st.tabs(["Item distributions", "Response completeness"])
    with tab1:
        display = audit.item_audit.copy()
        for column in ["missing_rate", "floor_rate_oriented", "ceiling_rate_oriented"]:
            display[column] = (100 * display[column]).round(1)
        full_width(st.dataframe, display.round(3), hide_index=True)
        st.caption("Rates are percentages. Reverse-keyed item summaries are shown after declared orientation.")
    with tab2:
        response = audit.response_audit.copy()
        response["share"] = (100 * response["share"]).round(1)
        full_width(st.dataframe, response, hide_index=True)
        st.caption("A constant pattern is a review flag, not proof of low effort or invalid responding.")

    if st.button("Run declared measurement analysis", type="primary", key=k("run_measurement")):
        try:
            config = MeasurementConfig(
                items=tuple(contract["items"]),
                reversed_items=tuple(contract.get("reversed_items", [])),
                scale_min=float(contract["scale_min"]),
                scale_max=float(contract["scale_max"]),
                planned_factors=int(contract["planned_factors"]),
                correlation=str(contract.get("correlation", "pearson")),
                loading_threshold=float(contract.get("loading_threshold", 0.40)),
                cross_loading_threshold=float(contract.get("cross_loading_threshold", 0.30)),
                reliability_target=float(contract.get("reliability_target", 0.70)),
                minimum_answered=float(contract.get("minimum_answered", 0.80)),
                parallel_iterations=int(contract.get("parallel_iterations", 499)),
                bootstrap_iterations=int(contract.get("bootstrap_iterations", 499)),
            )
            analysis = analyze_measure(data, config)
            factor_reliability = analysis.reliability[
                analysis.reliability["score"].str.startswith("Factor ")
            ]["omega_total"].dropna()
            reliability_value = (
                float(factor_reliability.min())
                if len(factor_reliability)
                else float(analysis.reliability["omega_total"].iloc[0])
            )
            decision = classify_profile(
                audit=audit,
                planned_factors=int(config.planned_factors),
                parallel_factors=int(analysis.parallel_factors),
                overall_kmo=float(analysis.diagnostics["overall_KMO"]),
                loading_support_rate=float(analysis.diagnostics["loading_support_rate"]),
                cross_loading_rate=float(analysis.diagnostics["cross_loading_rate"]),
                minimum_salient_items=int(analysis.diagnostics["minimum_salient_items_per_factor"]),
                reliability_value=reliability_value,
                reliability_target=float(config.reliability_target),
                improper_solution=bool(analysis.diagnostics["improper_solution"]),
            )
            st.session_state[k("analysis")] = analysis
            st.session_state[k("decision")] = decision
            st.success("Measurement analysis complete. Continue to dimensionality.")
        except Exception as exc:
            show_error(exc)


def retention_figure(frame: pd.DataFrame) -> go.Figure:
    roles = sig.roles(NS)
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=frame["component"],
            y=frame["observed_eigenvalue"],
            mode="lines+markers",
            name="Observed",
            line={"color": roles["estimate"], "width": 3},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["component"],
            y=frame["random_95th_percentile"],
            mode="lines+markers",
            name="Random 95th percentile",
            line={"color": roles["threshold"], "dash": "dash", "width": 2},
        )
    )
    figure.update_layout(
        template=sig.template(NS),
        height=410,
        margin={"l": 35, "r": 20, "t": 25, "b": 50},
        xaxis_title="Ordered component",
        yaxis_title="Correlation-matrix eigenvalue",
    )
    return figure


def loadings_figure(frame: pd.DataFrame) -> go.Figure:
    factor_columns = [column for column in frame.columns if column.startswith("Factor ")]
    steps = len(sig.DIVERGING) - 1
    figure = go.Figure(
        go.Heatmap(
            z=frame[factor_columns].to_numpy(float),
            x=factor_columns,
            y=frame["item"],
            zmin=-1,
            zmax=1,
            zmid=0,
            colorscale=[[index / steps, colour] for index, colour in enumerate(sig.DIVERGING)],
            colorbar={"title": "Loading"},
            hovertemplate="%{y}<br>%{x}: %{z:.3f}<extra></extra>",
        )
    )
    figure.update_layout(
        template=sig.template(NS),
        height=max(390, 34 * len(frame)),
        margin={"l": 20, "r": 25, "t": 20, "b": 45},
    )
    return figure


def render_dimensionality() -> None:
    sig.header(
        "Step 3",
        "Dimensionality",
        "The declared common-factor solution is shown beside—not replaced by—the parallel-analysis benchmark.",
    )
    if k("analysis") not in st.session_state:
        st.info("Run the measurement analysis on the audit page first.")
        return
    analysis = st.session_state[k("analysis")]
    diagnostics = analysis.diagnostics
    columns = st.columns(4)
    columns[0].metric("Overall KMO", f"{float(diagnostics['overall_KMO']):.3f}")
    columns[1].metric("Planned factors", f"{int(diagnostics['planned_factors'])}")
    columns[2].metric("Parallel-analysis signal", f"{int(diagnostics['parallel_components_95th_percentile'])}")
    columns[3].metric("RMSR · descriptive", f"{float(diagnostics['RMSR_descriptive']):.3f}")
    for warning in analysis.warnings:
        st.warning(warning)

    st.markdown("#### Retention evidence")
    sig.chart(NS, retention_figure(analysis.retention), key=k("retention_chart"))
    st.caption(
        "Observed PCA eigenvalues are compared with the 95th percentile from random normal data of the same dimensions. "
        "The suggestion is a diagnostic, not an instruction to ignore construct theory."
    )
    st.markdown("#### Rotated common-factor pattern")
    sig.chart(NS, loadings_figure(analysis.item_structure), key=k("loadings_chart"))
    full_width(st.dataframe, analysis.item_structure.round(3), hide_index=True)
    st.caption(
        "For multifactor models, coefficients are oblimin pattern loadings and factors may correlate. A deletion diagnostic "
        "is not an item-deletion recommendation."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Factor coverage")
        full_width(st.dataframe, analysis.factor_summary.round(3), hide_index=True)
    with c2:
        st.markdown("#### Factor correlations")
        full_width(st.dataframe, analysis.factor_correlations.round(3), hide_index=True)
    with st.expander("Factorability and residual diagnostics"):
        diagnostic_table = pd.DataFrame(
            [{"diagnostic": key, "value": str(value)} for key, value in diagnostics.items()]
        )
        full_width(st.dataframe, diagnostic_table, hide_index=True)
        st.caption(
            "Bartlett's test is highly sample-size sensitive. KMO and residual correlations are diagnostics, not universal pass/fail tests."
        )


def reliability_figure(frame: pd.DataFrame) -> go.Figure:
    # Categorical pair from the colorway: the Research hue, then the Decide hue (the colorway puts the most
    # contrasting family second).
    series = sig.colorway(NS)
    figure = go.Figure()
    figure.add_trace(go.Bar(x=frame["score"], y=frame["alpha"], name="Alpha", marker_color=series[0]))
    figure.add_trace(go.Bar(x=frame["score"], y=frame["omega_total"], name="Omega total", marker_color=series[1]))
    figure.update_layout(
        template=sig.template(NS),
        barmode="group",
        height=410,
        yaxis={"title": "Coefficient", "range": [0, 1.05]},
        xaxis={"title": ""},
        margin={"l": 35, "r": 20, "t": 25, "b": 90},
    )
    return figure


def render_reliability() -> None:
    sig.header(
        "Step 4",
        "Reliability & scoring",
        "Internal consistency describes score behavior under assumptions; it is not validity and not item quality by itself.",
    )
    if k("analysis") not in st.session_state:
        st.info("Run the measurement analysis first.")
        return
    analysis = st.session_state[k("analysis")]
    reliability = analysis.reliability
    candidate = reliability.iloc[0]
    columns = st.columns(4)
    columns[0].metric("Candidate alpha", f"{float(candidate['alpha']):.3f}")
    interval = (
        f"[{float(candidate['alpha_bootstrap_low']):.3f}, {float(candidate['alpha_bootstrap_high']):.3f}]"
        if pd.notna(candidate["alpha_bootstrap_low"]) and pd.notna(candidate["alpha_bootstrap_high"])
        else "not computed"
    )
    columns[1].metric("Bootstrap interval", interval)
    columns[2].metric("Candidate omega", f"{float(candidate['omega_total']):.3f}")
    columns[3].metric("Mean inter-item r", f"{float(candidate['mean_interitem_correlation']):.3f}")
    st.warning(CAUTION)
    sig.chart(NS, reliability_figure(reliability), key=k("reliability_chart"))
    full_width(st.dataframe, reliability.round(3), hide_index=True)
    st.markdown("#### Item-total sensitivity")
    full_width(st.dataframe, analysis.item_reliability.round(3), hide_index=True)
    st.caption(
        "Alpha-if-deleted is presented as a sensitivity calculation. Removing items solely to increase alpha can narrow "
        "construct coverage, capitalize on sampling error, and damage comparability."
    )
    st.markdown("#### Aggregate exploratory score preview")
    full_width(st.dataframe, analysis.score_summary.round(3), hide_index=True)
    st.info(
        "Unit-weighted mean scores use items assigned to their strongest factor and meeting the declared loading threshold. "
        "Freeze any proposed recipe and test it on new data before operational use. No respondent-level scores are exported."
    )
    st.caption(
        "Comparing scores across waves, segments, or time assumes measurement invariance, which this exploratory app "
        "does not establish. Do not read wave-to-wave score movement as construct change until invariance is tested "
        "in a confirmatory framework."
    )


def render_decision() -> None:
    sig.header(
        "Step 5",
        "Decision & export",
        "A bounded handoff: what the exploratory sample supports, what it does not, and what must happen next.",
    )
    if k("analysis") not in st.session_state or k("decision") not in st.session_state:
        st.info("Run the declared measurement analysis first.")
        return
    decision = st.session_state[k("decision")]
    analysis = st.session_state[k("analysis")]
    audit = st.session_state[k("audit")]
    contract = st.session_state[k("contract")]
    comparability = st.session_state.get(k("comparability"))
    sig.cards([("EXPLORATORY EVIDENCE PROFILE", str(decision["status"]), str(decision["meaning"]))])
    sig.note("info", f"**Next move:** {decision['action']}")
    st.warning(CAUTION)
    if comparability is not None:
        if comparability.mean_comparison_allowed:
            st.success(f"**Tracking comparability: {comparability.status}.** {comparability.meaning}")
        elif bool(contract.get("comparison_intended", False)):
            st.error(
                f"**Tracking comparability: {comparability.status}.** Cross-wave/group construct-score means and "
                "differences must not be interpreted or exported from this workflow."
            )
    confirmations = pd.DataFrame(
        [
            {"research condition": "Construct and boundaries documented", "documented": bool(contract.get("construct_definition"))},
            {"research condition": "Target population and use documented", "documented": bool(contract.get("target_population") and contract.get("intended_use"))},
            {"research condition": "Dimensions declared before result", "documented": bool(contract.get("planned_dimensions"))},
            {"research condition": "Independent confirmation plan documented", "documented": bool(contract.get("validation_plan"))},
            {
                "research condition": "Cross-wave/group mean comparison cleared by declared scalar evidence",
                "documented": (
                    not bool(contract.get("comparison_intended", False))
                    or bool(comparability and comparability.mean_comparison_allowed)
                ),
            },
        ]
    )
    full_width(st.dataframe, confirmations, hide_index=True)
    if not confirmations["documented"].all():
        st.warning("At least one measurement-contract field is undocumented. Preserve that gap in the evidence record.")

    pack = build_evidence_pack(
        source=dict(st.session_state.get(k("source"), {})),
        contract=contract,
        audit=audit,
        analysis=analysis,
        decision=decision,
        comparability=comparability,
    )
    st.markdown("#### Privacy-minimized evidence pack")
    st.write(
        "Exports contain the source fingerprint, measurement contract, aggregate audit, correlation and retention "
        "evidence, factor pattern, factor correlations, reliability estimates, scoring summary, warnings, and exact "
        "settings. Respondent identifiers, answers, and row-level scores are excluded."
    )
    col1, col2, col3 = st.columns(3)
    col1.download_button(
        "Download Excel evidence pack",
        evidence_to_excel(pack),
        file_name="measuresignal-evidence-pack.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        key=k("download_excel"),
    )
    col2.download_button(
        "Download CSV ZIP",
        evidence_to_csv_zip(pack),
        file_name="measuresignal-evidence-pack.zip",
        mime="application/zip",
        key=k("download_csv_zip"),
    )
    col3.download_button(
        "Download JSON record",
        evidence_to_json(pack),
        file_name="measuresignal-evidence-pack.json",
        mime="application/json",
        key=k("download_json"),
    )


def render_methods() -> None:
    sig.header("Methods & limits", "What Measure Signal calculates")
    st.warning(CAUTION)
    st.markdown(
        """
        ### Measurement is an argument, not one coefficient

        A multi-item score is defensible only relative to a construct definition, target population, administration
        process, scoring rule, and intended interpretation. Factor structure and internal consistency address parts of
        that argument. They do not establish content coverage, response-process quality, criterion relevance, causal
        meaning, fairness, or generalization.

        ### Data and correlation model

        Version 1.3 uses rows complete on every selected item for factor analysis and reliability estimation; the audit
        separately retains all rows to show missingness. Reverse keying is declared from instrument design and applies
        `minimum + maximum - response`. Pearson treats response categories as approximately interval. Spearman replaces
        values by ranks. Neither option is a polychoric correlation model.

        ### Factorability diagnostics

        KMO compares squared item correlations with squared partial correlations. Bartlett's statistic tests whether the
        correlation matrix differs from identity, but becomes sensitive with large samples. These diagnostics describe
        whether common-factor modeling is numerically plausible; they do not select the correct construct.

        ### Retention and common-factor estimation

        Horn-style parallel analysis compares ordered observed correlation-matrix eigenvalues with the 95th percentile
        from random normal data of the same row and item dimensions. This release labels it explicitly as a PCA-eigenvalue
        retention diagnostic. The declared model is estimated separately by principal-axis common-factor analysis.
        Multifactor models receive oblimin rotation so factors may correlate. Pattern loadings, communalities, factor
        correlations, cross-loadings, RMSR, and maximum residual correlation are reported.

        ### Alpha, omega, and scoring

        Raw alpha and standardized alpha summarize internal consistency under restrictive assumptions. A percentile
        bootstrap interval shows sampling variability in raw alpha. Omega total uses the fitted common-factor covariance
        relative to unique variance for a unit-weighted score. High coefficients can arise from redundant items or a long
        battery and do not prove unidimensionality. Alpha-if-deleted is never an automatic deletion rule.

        Exploratory factor-score recipes use simple respondent means over salient, primary-factor items. They are easier
        to audit and transport than sample-specific regression factor scores, but they still require an independently
        confirmed structure and a documented missing-item rule.

        ### Evidence-profile statuses

        `DATA CHECK REQUIRED` flags out-of-range values or repeated respondent identifiers. `DATA LIMITED` withholds a
        confident structural reading when the bounded sample minimum or KMO is inadequate. `STRUCTURE UNCLEAR` marks
        a statistically improper solution (a Heywood case), conflict between the declared factor count and parallel
        analysis, under-covered factors, or extensive cross-loading. `RESPECIFY WITH THEORY` marks weaker loading or
        reliability evidence. `READY FOR HOLDOUT TEST` requires the minimum factor-subscale omega total (the
        candidate-score omega total when no subscale exists) to reach the declared target and means only that the
        exploratory recipe is coherent enough to pre-specify for new data—it is not a validity label.

        ### Explicit non-support in version 1.3

        This release does not implement confirmatory factor analysis, bifactor or higher-order models, categorical/ordinal
        latent-variable estimators, polychoric/tetrachoric correlations, item-response theory, differential item
        functioning, measurement-invariance estimation, survey weights, complex samples, multilevel or longitudinal measurement,
        test-retest or inter-rater reliability, generalizability theory, planned missing-data estimators, imputation,
        predictive validity, known-groups validation, or automatic item generation/deletion.

        ### Primary references

        - Horn, J. L. (1965). *A rationale and test for the number of factors in factor analysis*. Psychometrika, 30, 179–185. https://doi.org/10.1007/BF02289447
        - Fabrigar, L. R., Wegener, D. T., MacCallum, R. C., & Strahan, E. J. (1999). *Evaluating the use of exploratory factor analysis in psychological research*. Psychological Methods, 4, 272–299. https://doi.org/10.1037/1082-989X.4.3.272
        - Cronbach, L. J. (1951). *Coefficient alpha and the internal structure of tests*. Psychometrika, 16, 297–334. https://doi.org/10.1007/BF02310555
        - Dunn, T. J., Baguley, T., & Brunsden, V. (2014). *From alpha to omega*. British Journal of Psychology, 105, 399–412. https://doi.org/10.1111/bjop.12046
        - Boateng, G. O., et al. (2018). *Best practices for developing and validating scales*. Frontiers in Public Health, 6, 149. https://doi.org/10.3389/fpubh.2018.00149
        - Kaiser, H. F. (1974). *An index of factorial simplicity*. Psychometrika, 39(1), 31–36. https://doi.org/10.1007/BF02291575
        - Bartlett, M. S. (1950). *Tests of significance in factor analysis*. British Journal of Statistical Psychology, 3(2), 77–85. https://doi.org/10.1111/j.2044-8317.1950.tb00285.x
        - McDonald, R. P. (1999). *Test Theory: A Unified Treatment*. Lawrence Erlbaum.
        - MacKenzie, S. B., & Lutz, R. J. (1989). *An empirical examination of the structural antecedents of attitude toward the ad in an advertising pretesting context*. Journal of Marketing, 53(2), 48–65. https://doi.org/10.1177/002224298905300204
        """
    )
    st.info(
        "Measure Signal is an independent implementation built from public measurement literature, original prose, and "
        "original synthetic data. It does not reproduce lecture slides, cases, exercises, assessment questions, figures, "
        "tables, screenshots, or institution-specific teaching language."
    )


PAGES = {
    "Welcome": render_welcome,
    "1 · Measurement contract": render_contract,
    "2 · Response & item audit": render_audit,
    "3 · Dimensionality": render_dimensionality,
    "4 · Reliability & scoring": render_reliability,
    "5 · Decision & export": render_decision,
    "Methods & limits": render_methods,
}


def _read_upload(upload) -> None:
    raw = upload.getvalue()
    fingerprint = hashlib.sha256(raw).hexdigest()
    if fingerprint == st.session_state.get(k("upload_fingerprint")):
        return
    try:
        frame, source = read_table(raw, upload.name)
        st.session_state[k("data")] = frame
        st.session_state[k("source")] = source
        st.session_state[k("upload_fingerprint")] = fingerprint
        st.session_state.pop(k("contract"), None)
        _new_contract_form()
        reset_results()
        st.success(f"Loaded {len(frame):,} rows × {len(frame.columns):,} columns.")
    except Exception as exc:
        show_error(exc)


def _sidebar() -> str:
    """Draw the sidebar lockup, data controls, page selector and status captions; return the selected page."""
    sig.sidebar_brand(NS, SIDEBAR_TAGLINE)
    with st.sidebar:
        if st.button("Load fictional three-factor demo", key=k("load_demo")):
            load_demo()
        upload = st.file_uploader("Upload response data", type=["csv", "xlsx", "json"], key=k("upload"))
        if upload is not None:
            _read_upload(upload)
        st.download_button(
            "Download starter template",
            dataframe_to_xlsx(starter_template()),
            file_name="measuresignal-starter-template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=k("download_template"),
        )
        if k("data") in st.session_state:
            data = st.session_state[k("data")]
            st.caption(f"Active data · {len(data):,} rows × {len(data.columns):,} columns")
        page = st.radio("Navigate", list(PAGES), label_visibility="collapsed", key=k("page"))
        st.caption("Local mode · no telemetry · no external AI calls · uploads stay in this Python process")
    return page


def render() -> None:
    """Draw the whole Measure Signal app on the current page. Never calls st.set_page_config or st.navigation."""
    sig.apply(NS)
    _ensure_state()
    page = _sidebar()
    sig.masthead(NS, MASTHEAD_PROMISES, MASTHEAD_KICKER)
    try:
        PAGES[page]()
    except Exception as exc:
        show_error(exc)
    sig.footer(NS, __version__, FOOTER_LINE)
