#  AI Realtor Assistant MVP

This project implements an AI assistant designed to automate compliant listing ingestion, intelligent client matching, and personalized messaging for real estate agents[cite: 2].

##  Core Features Overview

| Feature | Description | Code Modules |
| :--- | :--- | :--- |
| **Ingest** | [cite_start]Compliantly pulls and normalizes listing data from MLS (RESO Web API) and vendors (ATTOM, RPR), ensuring a strictly on-market filter[cite: 3]. | `core/providers`, `apps/workers/ingest.py` |
| **Match** | [cite_start]Learns a per-client **"taste vector"** (weights) from interactions (likes/dwell) to score and rank new listings[cite: 4, 197]. | `core/matching/matcher.py` |
| **Explainable Matching** | [cite_start]Provides "Why this home?" chips (e.g., `+kitchen finishes, -train noise`) for transparency and client feedback[cite: 20]. | `core/matching/explain.py` |
| **CMA** | [cite_start]Selects smart comps, applies adjustments (e.g., $\pm \$12\text{k}$/bed) [cite: 246][cite_start], and generates a **price band & confidence** score[cite: 5, 252]. | `core/cma/engine.py` |
| **Message & Audit** | [cite_start]Drafts summaries in the agent's tone, packages them as a one-pager PDF, and queues them for agent approval[cite: 6]. [cite_start]Logs all data sources and recipients for compliance[cite: 7, 345]. | `core/messaging`, `core/reporters`, `core/compliance` |

---

##  Local Quickstart (SQLite, Python-only)

This is the recommended path for development and testing core logic.

1.  **Clone/Open Project** and ensure you are in the root directory.
2.  **Install Dependencies** (Ensure Python 3 is installed and use `python3` if `python` fails):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Seed Database** (Creates `realtor.db` and populates mock data):
    ```bash
    python scripts/seed.py
    ```
4.  **Run API Server:**
    ```bash
    uvicorn apps.api.main:app --reload --port 8080
    ```

### Testing Endpoints

Access the interactive documentation at: **`http://127.0.0.1:8080/docs`**

| Core Feature | Method | Endpoint / Example |
| :--- | :--- | :--- |
| **Recommendations** | `GET` | `/clients/1/recommendations?limit=5` |
| **Interactions** | `POST` | `/interactions?client_id=1&listing_id=3&action=like` |
| **CMA** | `POST` | `/cma/run` with body `{"subject_listing_id": 1}` |

---

##  Production-Ready Setup (Docker Compose)

For a production environment using a proper database (Postgres), caching (Redis), and email testing (MailHog).

1.  **Prerequisites**: Ensure you have **Docker** installed and running.
2.  **Configure `.env`**: Copy the example file and update the `DATABASE_URL` to point to the Postgres service defined in Docker:
    ```bash
    cp .env.example .env
    # Change DATABASE_URL in .env to:
    # [cite_start]DATABASE_URL=postgresql+psycopg2://realtor:realtor@db:5432/realtor [cite: 376]
    # [cite_start]Add your MLS keys (BRIGHT_RESO_TOKEN [cite: 379][cite_start], ATTOM_TOKEN[cite: 380], etc.)
    ```
3.  **Launch Stack**: Build and run all services from the `infra/docker` directory:
    ```bash
    cd infra/docker
    docker compose up --build -d
    ```

### Docker Service Access

* **API/Docs**: `http://localhost:8080/docs`
* [cite_start]**MailHog UI**: `http://localhost:8025` (View emails sent by the `workers` service) [cite: 445]

[cite_start]The **`workers`** service automatically runs the `ingest` job [cite: 336] [cite_start]and sends the `morning_digest` email for approval[cite: 338, 446].

---

##  Compliance and Attribution

* [cite_start]**Data Sources**: Direct scraping of consumer sites (Zillow/Realtor) is illegal and risks licenses[cite: 8]. [cite_start]Data must come from licensed feeds: Bright MLS/RESO [cite: 9][cite_start], ATTOM [cite: 10][cite_start], RPR[cite: 11].
* [cite_start]**Audit Trail**: The system logs every data source, export, and recipient in the `AuditLog` table[cite: 7, 345].
* [cite_start]**Fair Housing**: Guardrails block protected-class proxies in prompts and run bias checks on feature importances[cite: 21, 346].
* [cite_start]**Media**: Photo/remarks reuse must honor attribution and retention windows specified by MLS agreements[cite: 12, 344].

---

##  Roadmap (v1+)

* [cite_start]Implement the **Isochrone commute** scorer (Valhalla/Mapbox) and **Risk layers** (FEMA flood, wildfire, lead)[cite: 14, 17, 391].
* [cite_start]Integrate proper **LightGBM** ranking with SHAP explanations for enhanced matching[cite: 390].
* [cite_start]Add a React mini-inbox UI for agents to quickly **Approve/Skip** daily digests[cite: 341].