# Changelog

## 1.3.0 — 2026-10-02

Signal brand refresh and Signal Hub entry point. The analysis, statistics, measurement contract, decision statuses and evidence-pack contents are unchanged.

### Brand

- Display name written **Measure Signal** (with a space) in the app, README, docs, AI analyst protocol, launchers, export labels and metadata. Package, file, schema and environment-variable names stay `measuresignal` / `MEASURESIGNAL_*`.
- The app uses the shared `signal_theme` module (Organic Signal design, Research family colour `#a06f1f`, Figtree): sidebar lockup, masthead, hero, cards, page headers, notes, footer, Plotly template and the mark as favicon replace the pasted styles.
- Charts keep their meaning with theme colours: observed eigenvalues as the estimate and the random-data 95th percentile as the dashed threshold; the loading heatmap uses the shared diverging scale around zero; alpha and omega bars use colorway hues.
- New banner, social preview and marks in `assets/`; the old banner SVG is removed. `.streamlit/config.toml` uses the family colours.
- README follows the Signal template; bug-report, feature-request and config issue templates added.

### Signal Hub contract

- `measuresignal.ui` exposes `APP_INFO` and `render()`, so Signal Hub can embed the app; `app.py` is now a thin standalone entry point.
- The fictional demo is preloaded on first run; **Load fictional three-factor demo** restores it.
- All session-state and widget keys are namespaced `measure:` (the page selector is `measure:page`).
- `streamlit` and `plotly` moved to a `ui` extra (also in `test`); the analysis core installs without them. `requirements.txt` still lists everything.
- New tests: no Streamlit/Plotly import outside `measuresignal.ui`, `render()` runs from a script without a page config and from a packaged copy without repo-root files, every widget key is namespaced, the shared shell and README template order.
- `CITATION.cff` uses the valid `cff-version: 1.2.0`.

## 1.2.1 — 2026-07-16

### Security

- Export sanitizer now also neutralizes formula-like column headers and strips control characters; Docker images keep application code root-owned; defusedxml hardens workbook XML parsing.

## 1.2.0 — 2026-07-16

- Added an optional "Communication measurement study" contract template (default Blank) that prefills a four-dimension communication-response contract — awareness, attitude toward the ad, brand attitude and brand fit, persuasion/purchase intention — with 1–7 endpoints, four planned correlated factors, and standard thresholds. Prefill only; every field stays editable.
- Documented the template in methods, README, and the AI analyst protocol, including the caveat that single-item or near-binary awareness measures often do not belong in an EFA battery.
- Added an explicit cross-wave invariance guard to the scoring page, methods, and AI analyst protocol: wave-to-wave score movement must not be read as construct change until invariance is tested in a confirmatory framework.
- Added MacKenzie & Lutz (1989) to the cited sources.

## 1.1.0 — 2026-07-16

- Added a cross-wave/group comparability contract and group-level completeness audit.
- Withholds construct-score mean comparisons until external scalar/threshold invariance evidence and its source are declared.
- Records—but does not claim to verify—external invariance evidence and exports no cross-group score means while the gate is closed.

## 1.0.0 — 2026-07-16

- Added a written measurement contract for construct boundaries, population, use, keying, thresholds, and confirmation plans.
- Added wide-form response and item audits for range, missingness, endpoints, observed categories, repeated identifiers, and constant response patterns.
- Added Pearson and Spearman correlation paths with KMO, Bartlett, determinant, and singularity checks.
- Added deterministic Horn-style PCA parallel analysis and principal-axis common-factor EFA with oblimin rotation.
- Added pattern loadings, factor correlations, communalities, uniquenesses, cross-loading, coverage, and residual diagnostics.
- Added raw and standardized alpha, bootstrap alpha intervals, omega total, item-total correlations, and alpha-if-deleted sensitivities.
- Added transparent aggregate scoring proposals and bounded evidence-profile statuses.
- Added privacy-minimized Excel, CSV-ZIP, and JSON evidence exports without respondent-level answers or scores.
- Added an entirely original deterministic fictional scale, starter workbook, standalone AI protocol, governance documents, and automated tests.
