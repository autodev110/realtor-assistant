# Roadmap

## Immediate Enhancements
1. Replace provider stubs with production integrations (Bright MLS RESO tokens, ATTOM listings, RPR feed).
2. Attach Redis-backed rate limit + backoff wrapper to `ingest_provider`.
3. Expand spam filter with lightweight classifier (e.g., Hugging Face distilled model) and quarantine review queue.
4. Harden security: JWT auth for API, encrypted secret storage, HTTPS termination.
5. Flesh out React inbox (apps/web) with inbox, draft approval, deal desk views.

## Near-Term
- Add tenant-aware multi-market support (per-agent data partitions).
- Implement auto-send with configurable guardrails and double-confirmation.
- Introduce valuation regression for better adjustment calibration (LightGBM + SHAP explanations).
- Extend CMA PDFs with charts/graphs and attach to email drafts automatically.
- Integrate schedule polling via Celery beat in production (APScheduler for dev only).

## Long-Term
- Lead scoring & lifecycle automation (nurture sequences, marketing campaigns).
- Commute time & school scoring (Mapbox, GreatSchools, FEMA risk overlays).
- Automated retention policy: purge raw provider payloads and audit export logs per MLS agreements.
- Stress/load testing harness + chaos testing for provider outages.
