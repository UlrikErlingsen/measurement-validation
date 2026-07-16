from __future__ import annotations

from io import BytesIO
import json
import zipfile

import pandas as pd

from measuresignal.analysis import MeasurementConfig, analyze_measure
from measuresignal.design import audit_measure, classify_profile
from measuresignal.examples import demo_dataframe, demo_defaults
from measuresignal.io import (
    build_evidence_pack,
    dataframe_to_xlsx,
    evidence_to_csv_zip,
    evidence_to_excel,
    evidence_to_json,
    read_table,
    safe_frame,
)


def completed_pack() -> dict[str, object]:
    frame = demo_dataframe()
    defaults = demo_defaults()
    audit = audit_measure(
        frame,
        unit=defaults["unit"],
        items=defaults["items"],
        reversed_items=defaults["reversed_items"],
        scale_min=defaults["scale_min"],
        scale_max=defaults["scale_max"],
    )
    config = MeasurementConfig(
        items=tuple(defaults["items"]),
        reversed_items=tuple(defaults["reversed_items"]),
        scale_min=defaults["scale_min"],
        scale_max=defaults["scale_max"],
        planned_factors=defaults["planned_factors"],
        parallel_iterations=49,
        bootstrap_iterations=49,
    )
    analysis = analyze_measure(frame, config)
    decision = classify_profile(
        audit=audit,
        planned_factors=3,
        parallel_factors=analysis.parallel_factors,
        overall_kmo=analysis.diagnostics["overall_KMO"],
        loading_support_rate=analysis.diagnostics["loading_support_rate"],
        cross_loading_rate=analysis.diagnostics["cross_loading_rate"],
        minimum_salient_items=analysis.diagnostics["minimum_salient_items_per_factor"],
        reliability_value=analysis.reliability["omega_total"].dropna().min(),
        reliability_target=0.70,
    )
    return build_evidence_pack(
        source={"source_filename": "demo.csv", "source_sha256": "abc"},
        contract=defaults,
        audit=audit,
        analysis=analysis,
        decision=decision,
    )


def test_read_csv_json_and_xlsx() -> None:
    frame = pd.DataFrame({"respondent_id": [1, 2], "item_1": [3.0, 4.0], "item_2": [5.0, 6.0]})
    csv_frame, csv_meta = read_table(frame.to_csv(index=False).encode(), "study.csv")
    json_frame, _ = read_table(frame.to_json(orient="records").encode(), "study.json")
    xlsx_frame, xlsx_meta = read_table(dataframe_to_xlsx(frame), "study.xlsx")
    pd.testing.assert_frame_equal(csv_frame, json_frame, check_dtype=False)
    pd.testing.assert_frame_equal(csv_frame, xlsx_frame, check_dtype=False)
    assert csv_meta["source_sha256"]
    assert xlsx_meta["source_sheet"] == "Response data"


def test_spreadsheet_formula_text_is_neutralized() -> None:
    safe = safe_frame(pd.DataFrame({"label": ["=1+1", "+cmd", "ordinary"], "value": [-2, 3, 4]}))
    assert safe["label"].tolist() == ["'=1+1", "'+cmd", "ordinary"]
    assert safe["value"].tolist() == [-2, 3, 4]


def test_evidence_exports_are_readable_and_exclude_raw_respondents() -> None:
    pack = completed_pack()
    json_bytes = evidence_to_json(pack)
    payload = json.loads(json_bytes)
    assert payload["schema"] == "measuresignal.evidence.v1"
    assert "tables" in payload
    assert "MS0001" not in json_bytes.decode()
    workbook = pd.ExcelFile(BytesIO(evidence_to_excel(pack)), engine="openpyxl")
    assert "Measurement contract" in workbook.sheet_names
    assert "reliability" in workbook.sheet_names
    with zipfile.ZipFile(BytesIO(evidence_to_csv_zip(pack))) as archive:
        assert "manifest.json" in archive.namelist()
        assert "item_structure.csv" in archive.namelist()
