# Sources and originality

MeasureSignal is an original software implementation of public measurement and psychometric ideas. Its product structure, interface, prose, code, evidence-profile statuses, synthetic data, illustrations, and export schema were created for this project.

MeasureSignal is independently designed and written from the published measurement and psychometrics literature. It does not reproduce lecture slides, speaker notes, cases, assignments, exercises, assessment questions, screenshots, tables, diagrams, examples, or any institution-specific teaching material, and it has no runtime dependency on such content. General topics encountered in education—scale development, factor analysis, reliability—only define the problem domain.

The demonstration scale is entirely synthetic and generated from a fixed random seed. Its construct—decision-interface evidence confidence—its item names, respondent identifiers, distributions, missingness, and factor pattern do not represent a real organization, respondent, classroom case, published instrument, or empirical claim. It is suitable for software testing and product demonstration, not substantive inference.

## Public methodological foundations

The implementation is informed by published statistical ideas, including:

- Horn's parallel-analysis rationale for factor retention;
- common-factor exploratory analysis and oblique rotation guidance synthesized by Fabrigar and colleagues;
- Cronbach's coefficient alpha;
- the alpha-to-omega reliability discussion by Dunn and colleagues;
- the scale-development and validation overview by Boateng and colleagues.

Full citations and DOI links appear in the README and methods guide. Statistical ideas, equations, and bibliographic facts are not proprietary course content; MeasureSignal implements them independently in open-source Python.

## Claims intentionally withheld

The app does not claim that:

- parallel analysis discovers the true number of constructs;
- exploratory factor analysis confirms a measurement model;
- alpha or omega proves unidimensionality or validity;
- a sample-derived loading threshold is a universal item-quality rule;
- deleting an item that increases alpha improves content coverage;
- one exploratory sample supports invariance, DIF, fairness, or operational use;
- the product replaces psychometric expertise, respondent research, or independent validation.

## Product and license boundary

MeasureSignal is an independent member of the Signal tool suite created by Ulrik Erlingsen. The software and documentation are licensed under AGPL-3.0-or-later. That license applies to this project's expression; it does not claim ownership of published methods, mathematical definitions, or the cited literature.

AI coding assistance was used during development. The implementation was checked through source review, deterministic synthetic recovery, automated unit and page tests, package building, and visual inspection. Users remain responsible for validating methods and decisions in their own setting.
