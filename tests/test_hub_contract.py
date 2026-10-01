"""Signal Hub contract: importable UI entry point, Streamlit only under ui/, slug-namespaced state, packaged install."""

import ast
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest
from streamlit.testing.v1 import AppTest

from measuresignal import __version__


ROOT = Path(__file__).parents[1]
PACKAGE = ROOT / "src" / "measuresignal"
UI = PACKAGE / "ui"
UI_ONLY_LIBRARIES = {"streamlit", "plotly"}
PAGES = [
    "Welcome",
    "1 · Measurement contract",
    "2 · Response & item audit",
    "3 · Dimensionality",
    "4 · Reliability & scoring",
    "5 · Decision & export",
    "Methods & limits",
]
RENDER_SCRIPT = """
from measuresignal.ui import render

render()
"""


def _imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def test_ui_entry_point_matches_the_hub_contract() -> None:
    from measuresignal.ui import APP_INFO, render

    assert callable(render)
    assert APP_INFO == {
        "product": "Measure Signal",
        "version": __version__,
        "repo": "measurement-validation",
        "slug": "measure",
    }


def test_only_the_ui_package_imports_streamlit_or_plotly() -> None:
    offenders = {
        str(path.relative_to(PACKAGE)): sorted(_imported_roots(path) & UI_ONLY_LIBRARIES)
        for path in PACKAGE.rglob("*.py")
        if UI not in path.parents and _imported_roots(path) & UI_ONLY_LIBRARIES
    }
    assert not offenders, offenders


def test_core_package_imports_without_streamlit_or_plotly() -> None:
    # A fresh interpreter, so modules already imported by other tests cannot hide a stray import.
    code = (
        f"import sys\nsys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "import measuresignal, measuresignal.analysis, measuresignal.design, measuresignal.errors, "
        "measuresignal.examples, measuresignal.io\n"
        "loaded = sorted(name for name in ('streamlit', 'plotly') if name in sys.modules)\n"
        "assert not loaded, loaded\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr


def test_render_never_sets_page_config_or_navigation() -> None:
    for path in UI.glob("*.py"):
        if path.name == "signal_theme.py":
            continue
        source = path.read_text(encoding="utf-8")
        for call in ("st.set_page_config(", "st.navigation(", "st.Page("):
            assert call not in source, (path.name, call)


def test_render_runs_from_a_script_without_set_page_config() -> None:
    app = AppTest.from_string(RENDER_SCRIPT, default_timeout=120)
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert app.sidebar.radio[0].key == "measure:page"
    assert "measure:data" in app.session_state
    assert "data" not in app.session_state
    body = "\n".join(str(item.value) for item in app.markdown)
    assert "MEASUREMENT EVIDENCE WORKBENCH" in body
    assert f"Measure Signal v{__version__}" in body


@pytest.mark.parametrize("page", PAGES)
def test_every_widget_key_is_namespaced(page: str) -> None:
    app = AppTest.from_string(RENDER_SCRIPT, default_timeout=120)
    app.run()
    app.sidebar.radio[0].set_value(page).run()

    assert not app.exception, [error.value for error in app.exception]
    widgets = [
        *app.radio,
        *app.selectbox,
        *app.multiselect,
        *app.checkbox,
        *app.toggle,
        *app.button,
        *app.slider,
        *app.select_slider,
        *app.number_input,
        *app.text_input,
        *app.text_area,
    ]
    assert widgets
    unkeyed = [(type(widget).__name__, widget.label) for widget in widgets if widget.key is None]
    assert not unkeyed, unkeyed
    assert all(widget.key.startswith("measure:") for widget in widgets)


def test_session_state_and_widget_keys_go_through_the_namespace_helper() -> None:
    source = (UI / "app.py").read_text(encoding="utf-8")
    state_keys = re.findall(r"session_state(?:\[|\.get\(|\.pop\()\s*([^,\])]+)", source)
    widget_keys = re.findall(r"\bkey=([^,)\n]+)", source)
    assert state_keys and widget_keys
    assert all(key.startswith("k(") for key in state_keys), state_keys
    assert all(key.startswith("k(") for key in widget_keys), widget_keys
    assert 'NS = "measure"' in source


def test_ui_reads_no_files_outside_the_package() -> None:
    # Signal Hub installs the release as a normal package: only src/measuresignal/ (plus package data) exists there.
    for path in UI.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "parents[" not in source and ".parent.parent" not in source, path.name
        if path.name != "signal_theme.py":
            assert "__file__" not in source, path.name
    theme = (UI / "signal_theme.py").read_text(encoding="utf-8")
    assert 'ASSETS = Path(__file__).parent / "assets"' in theme
    for mark in ("measuresignal-mark.svg", "measuresignal-mark-64.png"):
        assert (UI / "assets" / "marks" / mark).exists()


def test_render_works_from_a_packaged_copy_without_repo_files(tmp_path: Path) -> None:
    # Copy only what a wheel contains (Python modules + declared package data), then render in a fresh interpreter.
    site = tmp_path / "site"
    for source in PACKAGE.rglob("*"):
        relative = source.relative_to(PACKAGE)
        if "__pycache__" in relative.parts or not source.is_file():
            continue
        if source.suffix == ".py" or relative.parts[:3] == ("ui", "assets", "marks"):
            target = site / "measuresignal" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    code = (
        "import sys\n"
        f"sys.path = [p for p in sys.path if 'measurement-validation' not in p]\n"
        f"sys.path.insert(0, {str(site)!r})\n"
        "import measuresignal\n"
        f"assert measuresignal.__file__.startswith({str(site)!r}), measuresignal.__file__\n"
        "from streamlit.testing.v1 import AppTest\n"
        "from measuresignal.ui import signal_theme as sig\n"
        "assert sig.page_config('measure')['page_icon'].endswith('measuresignal-mark-64.png')\n"
        f"app = AppTest.from_string({RENDER_SCRIPT!r}, default_timeout=120)\n"
        "app.run()\n"
        "assert not app.exception, [e.value for e in app.exception]\n"
        "assert 'measure:data' in app.session_state\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=300, cwd=str(tmp_path)
    )
    assert result.returncode == 0, result.stderr
