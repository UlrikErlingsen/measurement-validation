"""Generate the deterministic fictional demonstration and starter template."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    from measuresignal.examples import demo_dataframe, starter_template
    from measuresignal.io import dataframe_to_xlsx

    examples = ROOT / "examples"
    examples.mkdir(parents=True, exist_ok=True)
    demo = demo_dataframe()
    template = starter_template()
    demo.to_csv(examples / "measuresignal-fictional-scale-demo.csv", index=False)
    (examples / "measuresignal-fictional-scale-demo.xlsx").write_bytes(
        dataframe_to_xlsx(demo, "Fictional responses")
    )
    (examples / "measuresignal-starter-template.xlsx").write_bytes(dataframe_to_xlsx(template, "Response data"))
    assert len(demo) == 480
    assert len([column for column in demo.columns if column.startswith(("trace_", "interpret_", "action_"))]) == 12
    assert demo["collection_wave"].nunique() == 2


if __name__ == "__main__":
    main()
