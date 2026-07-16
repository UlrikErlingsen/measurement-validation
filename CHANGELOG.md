# Changelog

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
