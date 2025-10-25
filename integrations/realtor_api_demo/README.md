# Realtor.com Lead Delivery API Demo

This repository demonstrates a webhook receiver that mimics the Realtor.com Lead Delivery API integration. It showcases how to authenticate incoming leads, parse the payload, and hand it off to downstream processing in your own system.

## Project Layout

- `app.py` – Flask application exposing `/realtor-lead/receive`.
- `requirements.txt` – Python dependencies for the demo.
- `sample_lead.json` – Example payload you can use when testing locally.

## Prerequisites

1. **Python 3.9+**
2. **pip** for installing dependencies.
3. **ngrok** account and binary if you want to expose the local server publicly for end‑to‑end tests.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export REALTOR_API_KEY=YOUR_SECRET_API_KEY_HERE_12345  # set any value you like
python app.py
```

The server listens on `http://127.0.0.1:5000/realtor-lead/receive`. Update the `REALTOR_API_KEY` environment variable to whatever key you plan to register with Realtor.com.

## Exposing the Endpoint with ngrok

1. Start ngrok in a separate terminal to tunnel the Flask server:

   ```bash
   ngrok http 5000
   ```

2. ngrok will print a forwarding URL such as `https://<random>.ngrok-free.app`. Append `/realtor-lead/receive` to form the webhook URL you provide to Realtor.com.

## Simulating a Realtor.com Lead

Run this `curl` command from another terminal once both Flask and ngrok are running:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Realtor-API-Key: YOUR_SECRET_API_KEY_HERE_12345" \
  --data @sample_lead.json \
  https://<random>.ngrok-free.app/realtor-lead/receive
```

If the API key and payload are valid you will receive:

```json
{
  "lead_id": "RDC-1234567890",
  "message": "Lead received and processing initiated",
  "status": "success"
}
```

The Flask console logs highlight the authenticated lead and show the payload you can plug into your CRM, queue, or bot workflow. Replace `_persist_lead_payload` inside `app.py` with storage or automation logic to complete the integration.

## Deployment Notes

- Store the API key securely (environment variables, secret manager, etc.).
- Use HTTPS with a trusted certificate for production webhooks.
- Implement idempotency/deduplication logic before persisting leads.
- Consider logging to external monitoring or message queues for resilience.

## Quick Commands Cheat Sheet

If you stop the running terminals, use these commands to spin everything back up. Replace `demo-test-key-001` with your real API key and swap the Cloudflare URL in the sanity check once the tunnel starts.

**Terminal 1 – Flask server**

```bash
cd /Users/dan/Desktop/realtor_api_demo
source .venv/bin/activate
export REALTOR_API_KEY=demo-test-key-001
export PORT=8000
python app.py
```

**Terminal 2 – Cloudflare tunnel**

```bash
cd /Users/dan/Desktop/realtor_api_demo
cloudflared tunnel --url http://localhost:8000
```

**Terminal 3 – Sanity check**

```bash
cd /Users/dan/Desktop/realtor_api_demo
source .venv/bin/activate
curl https://<your-tunnel>.trycloudflare.com/
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Api-Key: demo-test-key-001' \
  --data @sample_lead.json \
  https://<your-tunnel>.trycloudflare.com/realtor-lead/receive
```

## Inspecting Archived Leads

Every authenticated lead is saved as prettified JSON under the `leads/` directory (configurable via `LEAD_ARCHIVE_DIR`). To review the most recent lead without digging through files, hit the helper endpoint while the server is running:

```bash
curl https://<your-tunnel>.trycloudflare.com/realtor-lead/latest
```

The response includes the file path and full payload so you can explore what Realtor.com sent during testing.
