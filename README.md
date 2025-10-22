# Realtor Assistant Bot

Production-grade scaffold for an intelligent real estate assistant that keeps listings compliant, learns every client's preferences, runs quick CMAs, drafts agent-quality messaging, and flags undervalued opportunities for admin review.

```
                ┌────────────────────────────┐
                │        React Inbox         │
                │ (apps/web - optional UI)   │
                └────────────┬───────────────┘
                             │ REST / Webhooks
┌────────────────────────────┴─────────────────────────────┐
│                    FastAPI Application                   │
│  • Email webhook + deal alerts + approval endpoints      │
│  • Preference retraining + Draft review API              │
└──────────────┬──────────────────────┬────────────────────┘
               │                      │
               │                      │ Prometheus / Sentry
               │                      ▼
               │            infra/monitoring.py
               │
               │  Schedules + Celery tasks
               ▼
      apps/workers/ (ingestion, CMA, digests) ──┐
                                                │
                                    ┌───────────┴────────────┐
                                    │   Core Domain Layer    │
                                    │• providers/           │
                                    │• cma/engine.py        │
                                    │• matching/preferences │
                                    │• messaging/compose    │
                                    │• reporters/pdf        │
                                    │• compliance/audit     │
                                    └──────────┬────────────┘
                                               │ SQLAlchemy
                                               ▼
                               PostgreSQL + Redis + deal alerts
```

## Key Capabilities

- **Compliant ingestion** of Bright MLS (RESO), ATTOM, RPR, and partner feeds (Zillow/Realtor/Coldwell Banker stubs). Status mapping + dedupe guard `core/providers/`.
- **Preference learning & explainability** via `core/matching/preferences.py` with cosine similarity, decay, and rationale chips.
- **CMA engine** in `core/cma/engine.py` selects radius/time-window comps, applies adjustments, produces price bands, PSF chart data, and auto-flags deals priced ≤80% of market when no major defects.
- **Messaging pipeline** uses tone profiles and Jinja templates to build reviewable email drafts, optionally enriched with WeasyPrint CMA PDFs (`core/reporters/pdf.py`).
- **Audit & Compliance** guardrails (PII redaction, license flags, audit logs) live in `core/compliance/audit.py`.
- **Admin deal desk**: deal alerts persisted to `deal_alerts` table and surfaced via `/admin/deal-alerts` endpoints.
- **Observability**: `/metrics` Prometheus endpoint + optional Sentry DSN in `infra/monitoring.py`.

## Repo Layout

```
apps/
  api/           FastAPI app + routes (email webhook, drafts, deal alerts, retrain)
  workers/       APScheduler + Celery wrappers + ingestion/CMA/digest tasks
  web/           Placeholder for lightweight React approval UI (optional)
core/
  config.py      Central runtime settings via pydantic-settings
  providers/     MLS/partner provider stubs, status mapping, normalization helpers
  cma/           CMA engine + adjustments + deal detection
  matching/      Preference vectors, scoring, explainability
  messaging/     Tone profiles and Jinja2 message composers
  reporters/     Simple PDF generator (WeasyPrint fallback to HTML)
  storage/       SQLAlchemy models, session helpers, upsert logic
  compliance/    Audit logging + PII masking helpers
infra/
  docker/        Dockerfile + docker-compose stack (API, worker, Postgres, Redis, Mailhog)
  monitoring.py  Prometheus middleware + Sentry init stub
scripts/
  bootstrap_demo.py  Seed sample clients/listings + generate initial drafts
examples/
  (added via tests/fixtures) sample payloads and CMA datasets
```

## Prerequisites

- Python **3.11+**
- Postgres 14+ (dev can use SQLite via `DATABASE_URL`)
- Redis 6+ for Celery/queues (optional but wired into Docker stack)
- Node/Yarn only if you plan to build the optional React inbox

## Local Development (no Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python scripts/bootstrap_demo.py
uvicorn apps.api.main:app --reload --port 8080
```

Visit:
- API Docs: http://127.0.0.1:8080/docs
- Prometheus metrics: http://127.0.0.1:8080/metrics
- Deal alerts: `GET /admin/deal-alerts`

Background jobs (optional during dev):

```bash
python -m apps.workers.scheduler  # APScheduler loop
```

## Docker Compose Stack

```bash
cp .env.example .env
cd infra/docker
docker compose up --build
```

Services:
- `api`: FastAPI application (port 8080)
- `worker`: APScheduler worker for ingestion + digests
- `db`: Postgres (user/pass `realtor`)
- `redis`: Broker/cache (Celery ready)
- `mailhog`: test SMTP inbox (ports 1025/8025)

## Environment Variables (fill in `.env`)

- **Provider credentials**: `BRIGHTMLS_*`, `ATTOM_API_KEY`, `RPR_API_KEY`, plus partner feed keys when available.
- **Messaging**: `SMTP_*` for outbound mail, `LLM_API_KEY` for optional tone polishing.
- **Monitoring**: set `SENTRY_DSN` to enable error reporting; toggle Prometheus with `PROMETHEUS_ENABLED`.
- **Feature toggles**: adjust `ALLOW_ACTIVE_UNDER_CONTRACT`, `ALLOW_COMING_SOON`, `DEAL_DISCOUNT_THRESHOLD`.

## Workflows

1. **Email intake** (`POST /webhook/email`): classifies spam/auto-replies, attaches to `email_envelopes`, auto-creates clients when needed.
2. **Ingestion jobs** (`apps/workers/tasks.ingest_provider`): call RESO/partner APIs, normalize via `NormalizedListing`, dedupe by provider+ID/address, persist to Postgres.
3. **CMA generation**: `ensure_cma_report` pulls comps within radius/days window, computes adjustments, stores `CMAReport` + `ComparableSale`, renders PDF/HTML, and flags deals stored in `deal_alerts`.
4. **Preference updates**: interactions feed `retrain` endpoint or scheduler, updating client `preference_vector` with decay + cosine scoring.
5. **Draft assembly**: `generate_client_digest` ranks listings, attaches CMA stats, renders tone-aware copy, and saves drafts for approval. Optional auto-send respects `client.auto_send_enabled` with audit logging.

## Admin Deal Desk

- Review flagged opportunities via `GET /admin/deal-alerts` (filtered by `acknowledged`).
- Acknowledge/annotate using `POST /admin/deal-alerts/{id}/acknowledge`.
- Alerts exclude properties with recorded mechanical/electrical/structural issues to prevent false positives.

## Testing & Quality

```bash
pytest
flake8
black --check .
isort --check-only .
```

CI workflow (`.github/workflows/ci.yml`) runs lint + tests on push/PR.

## Next Steps / Ideas

1. **Inbox UI** (`apps/web`): React mini-dashboard for quarantine inbox, draft approvals, deal alert triage.
2. **Provider integrations**: swap stubs with production adapters (Bright MLS RESO, ATTOM property API, RPR).
3. **LLM polish**: plug in agent tone fine-tuning via `LLM_PROVIDER` (OpenAI, Anthropic, etc.) while enforcing PII guardrails.
4. **Rate limiting & retries**: extend `apps/workers/tasks.ingest_provider` with Redis-based buckets and tenacity-style backoff.
5. **Security hardening**: adopt AWS Secrets Manager or Vault for secrets, enable HTTPS/TLS termination in front of FastAPI.
6. **Analytics**: push metrics to Grafana/Prometheus and wire alerting on ingestion failures or CMA anomalies.

Happy shipping! Fill in credentials, wire your infra, and the scaffold is ready for production hardening.
