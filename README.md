<p align="center">
  <img src="assets/measuresignal-banner.svg" alt="MeasureSignal — is this score measuring what you think it is?" width="100%">
</p>

<p align="center">
  <a href="https://github.com/UlrikErlingsen/measurement-validation/actions/workflows/tests.yml"><img alt="Tests" src="https://github.com/UlrikErlingsen/measurement-validation/actions/workflows/tests.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-173C3A?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-app-D95B40?logo=streamlit&logoColor=white">
  <a href="LICENSE"><img alt="License: AGPL-3.0-or-later" src="https://img.shields.io/badge/License-AGPL--3.0--or--later-36534E"></a>
</p>

<p align="center"><strong>Open measurement evidence — define the score, diagnose its structure, freeze the next confirmation.</strong></p>

**MeasureSignal** helps researchers, analysts, and insight teams examine whether a multi-item response battery behaves like a defensible measurement instrument in an exploratory sample. It combines a written measurement contract, response and item audit, factorability diagnostics, parallel analysis, common-factor EFA, reliability estimation, transparent scoring recipes, and a reproducible evidence pack.

Everything runs locally with open-source Python packages. There is no account, telemetry, external AI call, remote database, or built-in persistence.

## Read this first

> **The app diagnoses score behavior; it does not manufacture construct validity.** Content coverage, response process, sampling, external relationships, fairness, and independent confirmation remain part of the research program.

MeasureSignal never treats high coefficient alpha as proof that items measure one construct. Reliability is a property of scores for a population and use. A factor solution discovered in one sample remains exploratory until its scoring rule is frozen and evaluated on new data.

## Supported scope

Version 1.2 supports:

- wide data with one row per respondent;
- 3 to 50 numeric candidate items;
- a declared response minimum and maximum;
- declared reverse keying;
- Pearson or Spearman item correlations;
- complete-case exploratory analysis with missingness retained in the audit;
- overall and item-level KMO plus Bartlett's sphericity statistic;
- Horn-style PCA parallel analysis using a fixed random seed and 95th-percentile benchmark;
- principal-axis common-factor analysis with 1 to 8 planned factors (never more than the item count minus one);
- oblimin rotation and factor correlations for multifactor solutions;
- loading, communality, cross-loading, residual-correlation, and factor-coverage diagnostics;
- raw and standardized alpha, percentile-bootstrap alpha intervals, omega total, and mean inter-item correlation;
- corrected item-total correlations and alpha-if-deleted as sensitivities—not deletion instructions;
- aggregate exploratory mean-score recipes with a declared missing-item rule;
- a declared cross-wave/group comparison intent, group completeness audit, and scalar-invariance evidence gate.

It does **not** estimate CFA, bifactor/higher-order models, polychoric or tetrachoric correlations, categorical latent-variable models, IRT, DIF, measurement invariance, test-retest or inter-rater reliability, survey weights, complex samples, multilevel/longitudinal measurement, imputation, predictive validity, or automated item selection. It records external invariance evidence and withholds cross-wave/group construct-mean comparisons until scalar/threshold evidence and its source are declared; it does not verify that declaration.

## Try it in three minutes

1. Start the app and click **Load fictional three-factor demo**.
2. Review the saved contract for an entirely fictional 12-item, three-dimension instrument.
3. Open the audit to inspect missingness, endpoint use, range violations, respondent uniqueness, and constant patterns.
4. Read the tracking-comparability gate: the demo intentionally withholds wave comparisons because no scalar-invariance evidence is declared.
5. Run the declared analysis. Compare the planned three factors with the fixed-seed parallel-analysis signal.
6. Inspect the oblimin pattern matrix, factor correlations, cross-loadings, communalities, and residuals.
7. Read alpha with its bootstrap interval beside omega, then review the exploratory scoring recipe.
8. Export the aggregate evidence record and use it to pre-specify an independent confirmation.

The demonstration is deterministic synthetic data. Its construct, item names, response pattern, and factor structure represent no real respondent, organization, course case, or empirical finding.

## Data layout

Use one row per respondent and one column per item. CSV, XLSX, and JSON are supported.

| respondent_id | item_1 | item_2 | item_3 | item_4_rev |
|---|---:|---:|---:|---:|
| R001 | 6 | 5 | 6 | 2 |
| R002 | 3 | 4 | 3 | 5 |

Keep item columns numeric. Leave missing answers blank. Select reverse-keyed items from the questionnaire key, not because their sample correlations point in an inconvenient direction. See the [data guide](docs/data-guide.md).

## Measurement contract

Before analysis, record:

- construct name, definition, and boundaries;
- target population and administration context;
- intended score use and explicitly excluded uses;
- planned dimensions and theoretical rationale;
- respondent identifier and candidate item columns;
- response endpoints and reverse-keyed items;
- planned factor count and correlation model;
- primary- and cross-loading thresholds;
- use-specific reliability planning target;
- minimum proportion answered for exploratory scoring;
- independent confirmation and validity plan.

These fields keep the analysis from silently redefining the construct around whichever items behave best in the current sample.

The contract page includes an optional **Communication measurement study** starter template (default: Blank). It prefills a four-dimension communication-response contract — awareness, attitude toward the ad, brand attitude and brand fit, and persuasion/purchase intention — with a 1–7 response range, four planned correlated factors (oblique rotation), and standard thresholds, following the advertising-pretesting tradition of MacKenzie and Lutz (1989). It is prefill only: every field stays editable, item selection is never automated, and single-item or near-binary awareness measures should be reported separately rather than forced into the factor battery.

## Dimensionality workflow

The app first audits the response table. Modeling is withheld for out-of-range responses, too few complete rows, constant items, or a singular correlation matrix.

Parallel analysis compares observed correlation-matrix eigenvalues with random-data eigenvalues. The declared model is then fitted separately as common-factor analysis using principal-axis extraction. Multifactor solutions use oblimin rotation because forcing psychologically or managerially related dimensions to be uncorrelated is often implausible. The app reports pattern loadings and factor correlations explicitly.

Parallel analysis is evidence, not an oracle. Construct theory, item content, model residuals, factor coverage, interpretability, and independent replication remain relevant. See [methods](docs/methods.md).

## Reliability and scoring

The app reports alpha for comparability, a bootstrap interval for sampling uncertainty, and omega total from the fitted common-factor covariance. Alpha and omega answer related but different questions and both depend on assumptions. High values can reflect redundant items or a long scale.

Exploratory factor-score recipes are simple means of items assigned to their strongest factor and meeting the declared loading threshold. This is an auditable proposal, not a finalized instrument. Freeze the recipe and confirm it before operational use.

## Evidence-profile statuses

- **DATA CHECK REQUIRED:** range or repeated-identifier problems must be resolved.
- **DATA LIMITED:** the bounded complete-sample minimum or KMO does not support a stable exploratory reading.
- **STRUCTURE UNCLEAR:** retention evidence conflicts with the planned factor count, a factor lacks coverage, cross-loading is extensive, or the solution is statistically improper (a Heywood case).
- **RESPECIFY WITH THEORY:** the pattern is readable, but loading or reliability evidence needs construct-led revision.
- **READY FOR HOLDOUT TEST:** the exploratory recipe is coherent enough to pre-specify for new data. This is not a validity certificate.

See the [decision guide](docs/decision-guide.md).

## Evidence pack

Excel, CSV-ZIP, and JSON exports include:

- source filename, sheet, and SHA-256 fingerprint;
- the full measurement contract and software version;
- aggregate item and response audit;
- factorability diagnostics, correlation matrix, and parallel analysis;
- rotated item structure and factor correlations;
- reliability estimates, item-total sensitivities, and aggregate score summaries;
- the evidence-profile status, warnings, and exact reproducibility settings.

Respondent identifiers, answers, and row-level scores are excluded. Exported text is neutralized against spreadsheet-formula interpretation.

## Run locally

You need Python 3.10 or newer and a local copy of this folder.

**macOS:** double-click `run_app.command`.

**Windows:** double-click `run_app.bat`.

The first launch creates a private `.venv` and downloads open-source dependencies. Later launches reuse it. Or use a terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

MeasureSignal prefers local port `8591` and falls back to another free port on macOS. The launcher accepts `MEASURESIGNAL_PORT`, `MEASURESIGNAL_MAX_UPLOAD_MB`, `MEASURESIGNAL_NO_BROWSER`, and `MEASURESIGNAL_DEBUG` environment variables.

### Docker

```bash
docker build -t measuresignal .
docker run --rm -p 8591:8591 measuresignal
```

Then open `http://127.0.0.1:8591`. The container runs as a non-root user.

## No install? Give this file to an AI

[AI_ANALYST.md](AI_ANALYST.md) is a standalone analysis protocol for a capable AI assistant. It contains the same scope limits, calculations, and honesty rules. A local app is the more private option: a cloud AI sees whatever you upload or paste.

## Development checks

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m ruff check .
python -m build
```

The suite checks reverse keying, range and response audits, known synthetic factor recovery, KMO/Bartlett calculations, deterministic parallel analysis, Pearson and Spearman paths, singular-matrix refusal, alpha/omega output, privacy-minimized exports, safe spreadsheet handling, deterministic examples, and every Streamlit page.

## Relationship to the Signal suite

- **[WorthSignal](https://github.com/UlrikErlingsen/customer-value-analytics)** asks what customers and relationships are worth.
- **[SegmentSignal](https://github.com/UlrikErlingsen/customer-segmentation)** asks whether customers form stable, useful groups.
- **[ChoiceSignal](https://github.com/UlrikErlingsen/conjoint-analysis)** asks how product attributes drive choice.
- **[PositionSignal](https://github.com/UlrikErlingsen/brand-positioning)** asks where brands sit relative to competitors.
- **[AdoptSignal](https://github.com/UlrikErlingsen/adoption-forecasting)** asks when a new product gets adopted.
- **[AllocSignal](https://github.com/UlrikErlingsen/marketing-mix-allocation)** asks where the next marketing budget should go.
- **[DriverSignal](https://github.com/UlrikErlingsen/survey-driver-analysis)** asks which measured experiences move with satisfaction.
- **[GateSignal](https://github.com/UlrikErlingsen/launch-decision-gate)** asks whether a concept deserves the next bounded investment.
- **[ExperimentSignal](https://github.com/UlrikErlingsen/experiment-analysis)** asks whether an assigned treatment caused a practically meaningful change.
- **[TextSignal](https://github.com/UlrikErlingsen/open-text-analysis)** asks what recurring language patterns appear in open-ended responses.
- **[RecommendSignal](https://github.com/UlrikErlingsen/recommender-evaluation)** compares recommendation policies offline before a finalist is tested live.
- **MeasureSignal** asks whether a proposed multi-item score has a defensible exploratory measurement structure.

MeasureSignal comes before DriverSignal when a downstream model depends on a composite score. It diagnoses the measure; DriverSignal analyzes relationships among already defined measures.

The maintained public suite is listed at [ulrikerlingsen.com](https://ulrikerlingsen.com).

## Method references

- Horn, J. L. (1965). A rationale and test for the number of factors in factor analysis. *Psychometrika, 30*, 179–185. https://doi.org/10.1007/BF02289447
- Fabrigar, L. R., Wegener, D. T., MacCallum, R. C., & Strahan, E. J. (1999). Evaluating the use of exploratory factor analysis in psychological research. *Psychological Methods, 4*, 272–299. https://doi.org/10.1037/1082-989X.4.3.272
- Cronbach, L. J. (1951). Coefficient alpha and the internal structure of tests. *Psychometrika, 16*, 297–334. https://doi.org/10.1007/BF02310555
- Dunn, T. J., Baguley, T., & Brunsden, V. (2014). From alpha to omega. *British Journal of Psychology, 105*, 399–412. https://doi.org/10.1111/bjop.12046
- Boateng, G. O., Neilands, T. B., Frongillo, E. A., Melgar-Quiñonez, H. R., & Young, S. L. (2018). Best practices for developing and validating scales. *Frontiers in Public Health, 6*, 149. https://doi.org/10.3389/fpubh.2018.00149
- Kaiser, H. F. (1974). An index of factorial simplicity. *Psychometrika, 39*(1), 31–36. https://doi.org/10.1007/BF02291575
- Bartlett, M. S. (1950). Tests of significance in factor analysis. *British Journal of Statistical Psychology, 3*(2), 77–85. https://doi.org/10.1111/j.2044-8317.1950.tb00285.x
- McDonald, R. P. (1999). *Test Theory: A Unified Treatment*. Lawrence Erlbaum.
- MacKenzie, S. B., & Lutz, R. J. (1989). An empirical examination of the structural antecedents of attitude toward the ad in an advertising pretesting context. *Journal of Marketing, 53*(2), 48–65. https://doi.org/10.1177/002224298905300204

## Originality and license

MeasureSignal is an independent implementation based on public statistical literature and original synthetic examples. It does not reproduce lecture slides, institution-specific cases, teaching diagrams, exercises, exam questions, screenshots, tables, or any institution-specific teaching material. See [sources and originality](docs/sources-and-originality.md).

The software and documentation are free under **AGPL-3.0-or-later**. The license covers this project's expression, not ownership of published statistical methods.

This application was developed with AI coding assistance and checked through source review, analytical fixtures, deterministic synthetic recovery, automated app tests, and visual inspection. Verify material decisions independently; no warranty is provided.
