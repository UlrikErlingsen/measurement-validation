# Security policy

## Supported version

Security fixes target the latest release on the default branch.

## Reporting

Please report a suspected vulnerability privately through GitHub's security-advisory feature when the repository is published. Never include confidential response data in a public issue.

## Data-handling notes

Measure Signal accepts CSV, XLSX, and JSON tables up to 1000 MB by default (`MEASURESIGNAL_MAX_UPLOAD_MB`; `STREAMLIT_SERVER_MAX_UPLOAD_SIZE` in Docker) and applies row, column and cell limits. Lower the cap for any shared deployment. It does not execute workbook macros. Exported text that could be interpreted as a spreadsheet formula is neutralized. Aggregate evidence exports omit respondent-level identifiers, answers, and scores.

These controls do not turn Measure Signal into a hardened multi-tenant service. A hosted deployment should add authentication, TLS, authorization, rate limiting, secure headers, isolated storage, dependency monitoring, logging appropriate to the data classification, and a documented deletion policy.
