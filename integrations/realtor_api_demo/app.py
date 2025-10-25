import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("realtor_lead_receiver")

app = Flask(__name__)

# Load the expected API key (falls back to a demo value so the sample works out of the box)
EXPECTED_API_KEY = os.getenv("REALTOR_API_KEY", "YOUR_SECRET_API_KEY_HERE_12345")
# Directory where we'll archive incoming leads for later inspection.
# Detect read-only environments like Vercel
try:
    LEAD_ARCHIVE_DIR = Path(os.getenv("LEAD_ARCHIVE_DIR", "leads"))
    LEAD_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    LEAD_ARCHIVE_DIR = None
    print("⚠️ File system is read-only; lead archiving disabled.")


@app.route("/", methods=["GET"])
def index() -> Any:
    """
    Simple health endpoint so Cloudflare/Realtor connectivity checks see a 200.
    """
    return jsonify({"status": "ready", "message": "Realtor lead receiver online"}), 200


def _is_valid_api_key(received_key: Optional[str]) -> bool:
    """
    Compares the received key against the configured key.
    In production you would rotate and store keys securely (e.g. secrets manager).
    """
    if not EXPECTED_API_KEY:
        logger.error("REALTOR_API_KEY is not configured.")
        return False
    if received_key != EXPECTED_API_KEY:
        logger.warning("Authentication failed: invalid API key received.")
        return False
    return True


def _persist_lead_payload(payload: Dict[str, Any]) -> None:
    """
    Placeholder for whatever downstream workflow you need.
    For the demo we simply log the payload; swapping this for
    a database write or queue publish is the expected next step.
    """
    # Convert to a pretty string so it reads clearly in the console.
    formatted_payload = json.dumps(payload, indent=2)
    logger.info("Lead payload ready for downstream processing:\n%s", formatted_payload)
    if LEAD_ARCHIVE_DIR is not None:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
        lead_id = payload.get("lead_id", "unknown")
        archive_path = LEAD_ARCHIVE_DIR / f"{timestamp}_{lead_id}.json"
        archive_path.write_text(formatted_payload, encoding="utf-8")
        logger.info(f"Lead payload archived at {archive_path}")
    else:
        logger.info("Lead payload logging only (no filesystem access).")


@app.route("/realtor-lead/receive", methods=["POST", "GET"])
def receive_lead() -> Any:
    """
    Webhook endpoint Realtor.com will POST new leads to.
    Handles authentication, validation, minimal processing, and acknowledgment.
    """
    if request.method == "GET":
        # Realtor.com test connection likely sends a GET to verify reachability.
        return jsonify(
            {
                "status": "ready",
                "message": "Realtor lead receiver is online. Use POST to deliver leads.",
            }
        ), 200

    received_key = request.headers.get("X-Realtor-API-Key") or request.headers.get("X-Api-Key")
    if received_key != EXPECTED_API_KEY:
        # Log the incoming headers so we can see how Realtor.com is sending the key.
        logger.warning("Authentication headers received: %s", dict(request.headers))
    if not _is_valid_api_key(received_key):
        return jsonify({"status": "error", "message": "Unauthorized API Key"}), 401

    lead_payload = request.get_json(silent=True)
    if not isinstance(lead_payload, dict):
        logger.warning("Invalid payload received: %s", lead_payload)
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    contact_name = lead_payload.get("lead_contact", {}).get("name", "Unknown")
    logger.info("Authenticated lead received for contact '%s'.", contact_name)

    _persist_lead_payload(lead_payload)

    response_body = {
        "status": "success",
        "message": "Lead received and processing initiated",
        "lead_id": lead_payload.get("lead_id"),
    }
    return jsonify(response_body), 200


@app.route("/realtor-lead/latest", methods=["GET"])
def latest_lead() -> Any:
    """
    Convenience endpoint to inspect the most recent archived lead in this demo.
    """
    if LEAD_ARCHIVE_DIR is None:
        return (
            jsonify(
                {
                    "status": "disabled",
                    "message": "Lead archiving is disabled in this environment.",
                }
            ),
            503,
        )
    lead_files = sorted(LEAD_ARCHIVE_DIR.glob("*.json"))
    if not lead_files:
        return jsonify({"status": "empty", "message": "No leads archived yet"}), 404
    latest_file = lead_files[-1]
    with latest_file.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return jsonify({"source_file": str(latest_file), "payload": payload}), 200


# For Vercel's serverless runtime
app = app
