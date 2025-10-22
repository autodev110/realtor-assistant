import json
from pathlib import Path

from core.providers.bright_mls import BrightMLSClient
from core.providers.status import normalize_status


def test_bright_mls_normalization():
    sample = json.loads(Path("examples/bright_listing.json").read_text())
    client = BrightMLSClient()
    normalized = client.normalize(sample)
    assert normalized.provider == "bright_mls"
    assert normalized.address_line == sample["UnparsedAddress"]
    assert normalize_status("bright_mls", sample["StandardStatus"]) == "Active"
    assert normalized.list_price == sample["ListPrice"]
