# Privacy

MeasureSignal is local-first. The app has no built-in account system, telemetry SDK, advertising, remote database, external AI call, or required API connection. Data entered in the browser is processed by the local Streamlit process and remains in that process unless the user downloads or otherwise moves it.

Response data can contain customer, employee, participant, health, market, or operational information. Remove direct identifiers, contact data, free text, unnecessary protected characteristics, and fields not needed for the declared measurement analysis before upload. The evidence pack deliberately excludes row-level identifiers, answers, and scores, but its aggregate results and source fingerprint may still be confidential.

If someone hosts MeasureSignal, that operator becomes responsible for transport security, authentication, server logs, backups, access control, retention, incident response, and applicable privacy obligations. Local-first defaults do not automatically make a hosted deployment private.
