# MeasureSignal decision guide

## Before reading the correlations

1. Define the construct and name nearby ideas the score must not silently absorb.
2. State the target population, administration context, intended use, and uses the score must not support.
3. Confirm that the item pool covers the intended content rather than merely repeating one easy-to-write facet.
4. Freeze response endpoints and reverse keying from the questionnaire documentation.
5. Declare the plausible number of dimensions, correlation method, loading rules, reliability planning target, and missing-item scoring rule.
6. Reserve or plan genuinely independent data for confirmation and validity evidence.

If these decisions are reconstructed after seeing the pattern matrix, label them exploratory and carry them forward as hypotheses—not discoveries that have already been confirmed.

## Read the audit before the factor solution

Resolve range violations and repeated respondent identifiers. Investigate item missingness, sparse response use, endpoint concentration, and constant response patterns. These signals can reflect confusing wording, administration problems, a mismatched population, legitimate uniform views, or data processing errors. They are prompts for inquiry, not automatic labels for respondents or items.

Complete-case retention matters because every factor and reliability estimate describes only respondents who answered all selected items. Compare retained and non-retained respondents using ethically appropriate study information outside the app when missingness could be systematic.

## Triangulate dimensionality

Read parallel analysis beside the declared factor count, item content, rotated loadings, factor correlations, communalities, and residuals. A numerical retention rule cannot decide whether two dimensions are substantively distinguishable, whether a factor is a wording artifact, or whether a narrow factor omits essential content.

Useful questions include:

- Does every factor have at least three substantively coherent items?
- Are the strongest loadings large enough under the declared rule?
- Are cross-loadings expected from theory or signs of ambiguous wording?
- Are factors so strongly correlated that the distinction needs an explicit theoretical defense?
- Do low communalities indicate weak representation, or intentionally broad content?
- Do residuals reveal item pairs sharing wording, method, or context beyond the factor model?

Do not keep deleting items until the current sample looks tidy. Each removal changes the construct and makes the same data serve as both discovery and confirmation.

## Read reliability conditionally

Alpha and omega summarize score consistency under different assumptions. Read their uncertainty, item count, factor structure, and intended decision together. A coefficient above a conventional threshold is not a license for high-stakes use; a coefficient below one can sometimes be adequate for early aggregate research but unsuitable for individual decisions.

Item-total correlations and alpha-if-deleted are diagnostics. Before changing an item, ask what content would disappear, whether the wording or key is wrong, and whether the apparent improvement would survive a new sample.

## Interpret the status as a next step

- `DATA CHECK REQUIRED`: correct or explain source-data problems before modeling.
- `DATA LIMITED`: improve completeness, sample support, or item covariance before reading dimensions.
- `STRUCTURE UNCLEAR`: compare theory-led alternatives and collect new data; do not optimize by deletion alone.
- `RESPECIFY WITH THEORY`: revisit construct coverage, wording, response process, keying, and population fit.
- `READY FOR HOLDOUT TEST`: freeze the exploratory recipe and test it independently.

None of these statuses says “valid.” They summarize this bounded workflow using declared, visible rules.

## Freeze a holdout recipe

Before the next collection, document:

- exact item wording, order policy, endpoints, and keying;
- proposed factor membership and scoring weights;
- missing-item handling and any transformations;
- confirmation model, estimator, fit criteria, and alternative-model policy;
- sample and subgroup requirements;
- reliability estimand and uncertainty method;
- external variables, timing, and hypotheses for convergent, discriminant, criterion, or predictive evidence;
- invariance, DIF, fairness, accessibility, and consequence checks relevant to the use;
- conditions that would cause revision, abandonment, or restricted use.

Avoid changing the recipe in the holdout sample and reporting the changed version as confirmed. If changes are necessary, treat that sample as a new discovery sample and obtain another confirmation.

## Match evidence to the intended use

An internal research index, a public benchmark, a screening tool, and an individual high-stakes decision require different evidence. Content expert review and cognitive interviewing often belong before large-sample modeling. CFA can test a frozen structure, but model fit alone does not establish interpretation. External relationships, stability, sensitivity to change, group comparability, and decision consequences should be evaluated when they matter to the claim.

Keep the exported evidence pack with the questionnaire, codebook, analysis plan, item-development record, and confirmation results. It is a reproducible diagnostic record, not a substitute for the study protocol.
