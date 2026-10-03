# Changelog

## 1.4.0 — 2026-10-03

### Larger datasets

- Larger datasets: run locally, Measure Signal has no built-in limit on file size, rows, columns or items (was 50 MB, 250,000 rows, 500 columns and 50 items); memory is the limit, and running out of memory gives a plain message. A public demo (`SIGNAL_PUBLIC=1`) keeps those values as demo limits, all in the new `measuresignal.limits` module, with messages that say the downloaded app has none; the item picker is uncapped locally. CSV is read in 250,000-row chunks and numbers are stored in the smallest lossless type, while every statistic still runs in double precision. Uploaded frames are no longer copied once more after reading.
- The audit's constant-pattern check is vectorized (row maximum equals row minimum) instead of a row-by-row `nunique`; the same rows are flagged.
- Parallel analysis above 20,000 complete rows draws its random benchmark from the Wishart distribution of a null correlation matrix (Bartlett decomposition) instead of simulating every row: identical in distribution for Pearson, the standard large-sample approximation for Spearman. The diagnostics (`parallel_benchmark`) and a warning label it. At 5,000,000 rows the full analysis takes about 6 seconds; version 1.3 needed about 90 seconds for 250,000 rows.
- An alpha bootstrap above 50,000,000 resampled cells uses a seeded subsample of at least 2,000 complete rows and rescales its interval to the full sample by sqrt(m/n). The reliability table (`alpha_bootstrap_rows`), the diagnostics (`alpha_bootstrap_basis`) and a warning record it; point estimates always use every complete row.
- Item-total correlations and alpha-if-deleted come from one item covariance matrix; above 1,000,000 complete rows the correlation matrix, alpha, standardized alpha, factor-score omega and score means are also computed without full copies of the item matrix (chunked covariance, column-wise row means). Results are unchanged.
- The app keeps the audit for the current data and contract instead of recomputing it on every rerun, computes the numeric item candidates once per table, and no longer re-reads and re-hashes an unchanged upload on each rerun.
- Launchers default `MEASURESIGNAL_MAX_UPLOAD_MB` to 10000 (the Windows launcher now honours the variable too) and the Docker image sets `STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10000`. Signal Hub mode (`SIGNAL_HUB=1`) is unchanged.

### Suite

- Suite: Rival, Reach, Learn and Blueprint Signal added to the suite table (README) and to the theme copy's app list; `.streamlit/config.toml` carries Signal Hub's 10,000 MB upload cap.

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
