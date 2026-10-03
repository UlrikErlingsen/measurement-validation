# Security policy

## Supported version

Security fixes target the latest release on the default branch.

## Reporting

Please report a suspected vulnerability privately through GitHub's security-advisory feature when the repository is published. Never include confidential response data in a public issue.

## Data-handling notes

Run locally, Measure Signal has no built-in size limit on CSV, XLSX, and JSON tables (Streamlit's upload cap is `MEASURESIGNAL_MAX_UPLOAD_MB`, or `STREAMLIT_SERVER_MAX_UPLOAD_SIZE` in Docker, default 10,000 MB). Any shared or public deployment should set `SIGNAL_PUBLIC=1`, which applies upload, row, column and item caps, and lower the upload cap. It does not execute workbook macros. Exported text that could be interpreted as a spreadsheet formula is neutralized. Aggregate evidence exports omit respondent-level identifiers, answers, and scores.

These controls do not turn Measure Signal into a hardened multi-tenant service. A hosted deployment should add authentication, TLS, authorization, rate limiting, secure headers, isolated storage, dependency monitoring, logging appropriate to the data classification, and a documented deletion policy.
