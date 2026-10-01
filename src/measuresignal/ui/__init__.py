"""Measure Signal user interface: the Signal Hub entry point.

The only package under ``measuresignal`` that imports Streamlit or Plotly. ``render()`` draws the whole app on the
current page and never calls ``st.set_page_config``; the standalone ``app.py`` or Signal Hub owns the page config.
"""

from measuresignal import __version__
from measuresignal.ui import signal_theme
from measuresignal.ui.app import render

APP_INFO = {"product": "Measure Signal", "version": __version__, "repo": "measurement-validation", "slug": "measure"}

__all__ = ["APP_INFO", "render", "signal_theme"]
