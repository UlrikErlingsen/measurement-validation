# MeasureSignal data guide

## One row, one respondent

Use wide data: one row per independent respondent and one numeric column per candidate item. A respondent identifier is optional but recommended because it lets the audit detect repeated rows. Remove names, email addresses, free text, and other direct identifiers before upload.

If the same person appears repeatedly or respondents are nested in teams, this release is not design-matched. Repeated waves may be named in a wave/group column for the comparability gate, but the exploratory factor model still treats rows as independent and the app does not fit a longitudinal model. Reshape only when one row genuinely represents one independent response occasion; otherwise use a multilevel or longitudinal measurement model.

## Candidate items

Select 3 to 50 numeric items intended to represent one scale or a related set of dimensions. Keep the original questionnaire wording and item key outside the data file as study documentation. Column names should be unique and interpretable, but they do not need to contain the item text.

Do not mix known outcomes, demographics, behavioral variables, attention checks, or unrelated constructs into the candidate item set merely because they are numeric. The item pool should follow the construct definition written before analysis.

Example layout:

| respondent_id | trace_1 | trace_2_rev | interpret_1 | action_1 |
|---|---:|---:|---:|---:|
| R001 | 6 | 2 | 5 | 6 |
| R002 | 3 | 5 | 4 | 3 |

## Response range and keying

Declare the minimum and maximum values that were actually offered to respondents. A seven-point scale coded 1 through 7 has minimum 1 and maximum 7 even when no one chose every category.

Mark reverse-keyed items from the questionnaire key, not from the observed correlations. MeasureSignal orients a declared reverse-keyed item as:

`oriented response = minimum + maximum - original response`

Correct data-entry or keying problems at the source. Responses outside the declared range stop modeling because a reverse-key formula cannot make invalid source values valid.

## Missing answers

Leave unanswered items blank. Do not replace missing responses with zero unless zero was an offered, substantively meaningful category. The audit uses all rows to describe item missingness and answer counts; factor and reliability calculations use rows complete on every selected item.

Complete-case analysis is intentionally transparent but can change the target population and can be biased when missingness is systematic. This release does not impute answers. If complete-case retention is poor, investigate administration and missingness before interpreting a factor solution.

The exploratory score recipe is different from the model sample rule. It can require a declared proportion of assigned items to be answered and then average the available oriented responses. That recipe is reported, not applied to exported respondent rows.

## Numeric coding and correlation choice

Pearson correlations treat response differences as approximately interval-scaled. Spearman correlations use ranks and are less sensitive to monotonic nonlinear spacing, but they are not polychoric correlations and do not create a categorical latent-variable model. Either choice needs a reason tied to the response format and intended interpretation.

Avoid silently converting text labels with an arbitrary alphabetical order. Map ordered categories to documented numeric codes before upload. Binary items, sparse ordered categories, nominal indicators, and mixed item types require methods outside version 1.1.

## What this release does not ingest correctly

Use another workflow for:

- long-form item-response tables;
- multiple raters, repeated administrations, or clustered respondents;
- sampling weights or complex survey designs;
- item parcels supplied in place of the underlying items;
- forced-choice, ipsative, ranking, count, nominal, or free-text responses;
- planned IRT, DIF, invariance, multilevel, or longitudinal analysis.

The wave/group field is metadata for a comparison safeguard, not an invariance estimator. If mean comparison is intended, document the external multi-group/longitudinal model, estimator, evidence level, source, and any partial-invariance decision in the measurement contract.

## File handling and privacy

CSV, XLSX, and JSON tables are supported up to 50 MB, 250,000 rows, and 500 columns. The app reads values, not workbook macros. Analysis is local and in memory. Aggregate evidence exports exclude identifiers, answers, and row-level scores, but their summaries and source fingerprint can still be sensitive; store them according to the study's governance rules.
