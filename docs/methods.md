# MeasureSignal methods

## Purpose and boundary

MeasureSignal is a bounded exploratory diagnostic for multi-item scores. It asks whether a declared item pool shows enough shared, interpretable structure to justify freezing a scoring proposal for an independent confirmation sample. It does not establish content, response-process, convergent, discriminant, predictive, criterion, known-groups, fairness, or consequential validity.

The measurement contract is recorded before modeling: construct definition and exclusions, population, context, intended and excluded uses, planned dimensions, response range, keying, item set, correlation method, loading rules, reliability planning target, scoring completeness rule, and confirmation plan. Thresholds are declared decision rules, not universal laws.

### Communication-measurement starter template

The contract page offers an optional prefill template for a communication (advertising) measurement study. It plans four correlated dimensions drawn from the advertising-pretesting literature: awareness of the campaign or brand, attitude toward the ad, brand attitude and brand fit, and persuasion expressed as purchase or usage intention (MacKenzie & Lutz, 1989). These responses are theoretically distinct but causally linked — ad liking is expected to feed brand attitude and intention — so the template plans oblique (oblimin) rotation and factors that may correlate, rather than forcing independence.

The template only prefills wording, endpoints (1–7), the planned factor count (4), and standard thresholds; every field stays editable and item selection remains the user's decision. One honest caveat: awareness is often measured with a single recall/recognition question or a near-binary item. Single-item and near-binary awareness measures often do not belong in an EFA battery built on product-moment correlations — report them separately instead of forcing them into the factor model.

## Orientation and analysis sample

For declared minimum `a`, maximum `b`, and reverse-keyed response `x`, the oriented response is `a + b - x`. Forward-keyed items are unchanged. Modeling stops when an observed response is outside `[a, b]`, an item is constant, fewer than `max(50, item count + 10)` complete rows remain, or the correlation matrix is singular or nearly singular.

The item and response audit uses every source row. Correlations, dimensionality, and reliability use listwise-complete rows across all selected items. No imputation is performed. A complete-case solution describes the retained sample and may not generalize when missingness is systematic.

## Correlation matrix

The user selects Pearson product-moment or Spearman rank correlation. Pearson is appropriate only when treating response increments as approximately interval-scaled is defensible. Spearman captures monotonic rank association but is not equivalent to a polychoric correlation and does not supply an ordinal latent-variable likelihood. Sparse ordinal or binary batteries may need categorical-data methods outside this release.

## Factorability diagnostics

Kaiser–Meyer–Olkin sampling adequacy compares squared zero-order correlations with squared partial correlations. For item `j`:

`KMO_j = sum(r_jk²) / [sum(r_jk²) + sum(p_jk²)]`

The overall KMO uses the corresponding sums over all off-diagonal pairs. Bartlett's sphericity statistic is:

`chi² = -[n - 1 - (2p + 5)/6] ln(|R|)`

with `p(p - 1)/2` degrees of freedom. Both summarize properties of the observed correlation matrix. Neither proves that the construct is valid, that the planned factor count is correct, or that a large sample has substantively useful correlations. MeasureSignal treats overall KMO below 0.50 as a data-limited flag, not as a universal publication rule.

## Parallel analysis

Horn-style parallel analysis is a retention diagnostic. The app computes the ordered eigenvalues of the observed item correlation matrix, generates independent normal random data with the same number of complete rows and items, and repeats the calculation using a fixed seed. An observed eigenvalue is retained while it exceeds the corresponding 95th percentile of the simulated eigenvalues; counting stops at the first failure. Spearman mode ranks each simulated column before correlation.

The displayed parallel analysis is deliberately PCA-based because it evaluates total correlation-matrix eigenvalues. It is not the extraction model. The planned common-factor solution is fitted separately. Parallel analysis can be affected by sample size, item distributions, correlation choice, and simulation specification, so theory, factor coverage, residuals, and replication remain relevant.

## Common-factor model

The exploratory model represents the item correlation matrix as:

`R = L Phi L' + Psi`

where `L` is the loading matrix, `Phi` is the factor-correlation matrix, and diagonal `Psi` contains unique variances. Principal-axis extraction starts with squared multiple correlations as initial communalities. Version 1.2 caps the planned factor count at the smaller of 8 or the item count minus one. A multifactor solution uses oblimin rotation (direct quartimin, γ = 0), allowing dimensions to correlate; the app reports the rotated pattern matrix and `Phi`. Factor order and signs are stabilized for reproducible display, but signs and labels have no inherent psychological direction.

An item is assigned descriptively to the factor with its largest absolute pattern loading. A primary loading is supported when it meets the declared loading threshold. A cross-loading is flagged when a second absolute loading reaches the declared cross-loading threshold. A factor has minimum coverage when at least three items meet the primary threshold. These are transparent workflow rules, not automatic item-retention commands.

Communality is the common variance implied by `L Phi L'`; uniqueness is the fitted item-specific variance. The reproduced correlation matrix is `L Phi L' + Psi`. The app reports the root mean square of off-diagonal residual correlations and their largest absolute value. Small residual summaries do not guarantee local fit, stable parameters, or generalizability.

## Reliability

For `k` items with total-score variance `s_T²` and item variances `s_i²`, raw coefficient alpha is:

`alpha = k/(k - 1) * [1 - sum(s_i²)/s_T²]`

Standardized alpha uses the mean inter-item correlation `r_bar`:

`alpha_std = k r_bar / [1 + (k - 1) r_bar]`

The app adds a percentile bootstrap interval for raw alpha by resampling complete respondents with replacement using a fixed seed. The interval reflects sampling variability under that resampling scheme; it does not capture construct misspecification or dependence.

Omega total is computed from the fitted common-factor covariance:

`omega_total = 1' L Phi L' 1 / [1' L Phi L' 1 + sum(Psi)]`

For each displayed subscale, a separate one-factor model estimates omega. Alpha and omega depend on the item set, sample, scoring direction, and model assumptions. A high coefficient may result from redundancy or scale length and is not evidence of unidimensionality or validity.

Corrected item–total correlations relate each item to the sum of the other items. Alpha-if-deleted is a sensitivity. Neither should be used as an automatic deletion algorithm: removing an item can narrow content coverage, capitalize on sampling noise, or hide a meaningful secondary dimension.

## Exploratory scoring recipe

Items whose strongest loading reaches the declared primary threshold are grouped by that strongest factor. The proposed factor score is the mean of oriented assigned items when a respondent answered at least the declared proportion. An overall candidate score is the mean of all oriented candidate items under the same rule. The app reports only aggregate score summaries and does not export respondent scores.

This recipe is a proposal generated in the discovery sample. Before operational use, freeze wording, keying, factor membership, missing-item handling, transformations, and interpretation, then evaluate them on independent data. Factor-score or latent-variable estimates may be preferable for some uses.

## Cross-wave/group comparability gate

MeasureSignal does not fit multi-group CFA or test invariance. When a cross-wave or group score comparison is intended, it audits group row counts, complete-item rates, and maximum item missingness but calculates no group construct means. The gate remains `CROSS-GROUP COMPARISON WITHHELD` unless the user declares scalar/threshold (or strict) invariance evidence and supplies its source.

Configural evidence supports a similar broad pattern; metric/loading invariance supports some relationship comparisons. Construct or latent mean comparisons usually require equal item intercepts for continuous indicators or thresholds for categorical indicators. Even declared scalar evidence may be partial, estimator-specific, and conditional on identification, sampling, item wording, response scales, and model fit. The status `EXTERNAL SCALAR INVARIANCE DECLARED` records a user-supplied claim; it is not software verification and may not be sufficient for observed unit-weighted score means.

More generally, comparing scores across waves, segments, or time assumes measurement invariance — that the items relate to the construct in the same way in every group and at every occasion — and this exploratory app does not establish it. A score that moves between waves may reflect a change in the construct, a change in how the items function, or both. Do not read wave-to-wave score movement as construct change until invariance is tested in a confirmatory framework such as multi-group or longitudinal CFA.

## Evidence-profile logic

Statuses describe the next research step:

- `DATA CHECK REQUIRED` for out-of-range values or repeated selected identifiers;
- `DATA LIMITED` when the bounded complete-row minimum is not met or overall KMO is below 0.50;
- `STRUCTURE UNCLEAR` when the solution is statistically improper (a Heywood case with a uniqueness outside (0, 1)), planned and parallel factor counts differ, any factor has fewer than three salient items, or more than 25% of items cross-load;
- `READY FOR HOLDOUT TEST` when at least 80% of items support their primary loading and the reliability gate metric reaches the declared target after the preceding checks. The gate metric is the minimum omega total across the factor subscales (the candidate-score omega total when no subscale with at least two salient items exists) — not alpha;
- `RESPECIFY WITH THEORY` for remaining readable but insufficient profiles.

`READY FOR HOLDOUT TEST` is not a validated-scale label. Confirmation normally requires a pre-specified CFA or other design-matched model, score reliability in the new sample, and evidence connected to the intended interpretation and use. Invariance, DIF, fairness, external validity, and longitudinal stability require separate designs when relevant.

## Reproducibility

The evidence pack records the contract, selected items and keying, thresholds, correlation method, planned factor count, random seed, parallel and bootstrap iterations, source SHA-256 fingerprint, software version, diagnostics, warnings, aggregate tables, and status. It intentionally excludes row-level answers, identifiers, and scores.

## Public foundations

- Horn, J. L. (1965). A rationale and test for the number of factors in factor analysis. *Psychometrika, 30*, 179–185. https://doi.org/10.1007/BF02289447
- Fabrigar, L. R., Wegener, D. T., MacCallum, R. C., & Strahan, E. J. (1999). Evaluating the use of exploratory factor analysis in psychological research. *Psychological Methods, 4*, 272–299. https://doi.org/10.1037/1082-989X.4.3.272
- Cronbach, L. J. (1951). Coefficient alpha and the internal structure of tests. *Psychometrika, 16*, 297–334. https://doi.org/10.1007/BF02310555
- Dunn, T. J., Baguley, T., & Brunsden, V. (2014). From alpha to omega. *British Journal of Psychology, 105*, 399–412. https://doi.org/10.1111/bjop.12046
- Boateng, G. O., Neilands, T. B., Frongillo, E. A., Melgar-Quiñonez, H. R., & Young, S. L. (2018). Best practices for developing and validating scales. *Frontiers in Public Health, 6*, 149. https://doi.org/10.3389/fpubh.2018.00149
- Kaiser, H. F. (1974). An index of factorial simplicity. *Psychometrika, 39*(1), 31–36. https://doi.org/10.1007/BF02291575
- Bartlett, M. S. (1950). Tests of significance in factor analysis. *British Journal of Statistical Psychology, 3*(2), 77–85. https://doi.org/10.1111/j.2044-8317.1950.tb00285.x
- McDonald, R. P. (1999). *Test Theory: A Unified Treatment*. Lawrence Erlbaum.
- MacKenzie, S. B., & Lutz, R. J. (1989). An empirical examination of the structural antecedents of attitude toward the ad in an advertising pretesting context. *Journal of Marketing, 53*(2), 48–65. https://doi.org/10.1177/002224298905300204
