from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Iterator, Optional

import requests

from core.schema.listing import NormalizedListing

from .base import ProviderClient
from .utils import parse_datetime, to_float, to_int


class RPRClient(ProviderClient):
    """Realtors Property Resource (RPR) MLS feed stub."""

    name = "rpr"

    def __init__(self) -> None:
        super().__init__()
        self.base_url = os.getenv("RPR_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("RPR_API_KEY")

    def fetch_updated(
        self, since: Optional[datetime] = None, cursor: Optional[str] = None
    ) -> Iterator[Dict]:
        if not self.base_url or not self.api_key:
            yield from self._sample_payload()
            return

        params = {"updatedSince": since.isoformat() if since else None, "cursor": cursor}
        headers = {"ApiKey": self.api_key}
        response = requests.get(
            f"{self.base_url}/listings",
            headers=headers,
            params={k: v for k, v in params.items() if v},
            timeout=30,
        )
        response.raise_for_status()
        for record in response.json().get("listings", []):
            yield record

    def normalize(self, raw: Dict) -> NormalizedListing:
        geo = raw.get("geo", {})
        primary = geo.get("primaryAddress", {})
        valuation = raw.get("valuation", {})
        return NormalizedListing(
            provider=self.name,
            mls_id=raw.get("listingId"),
            external_id=raw.get("rprPropertyId"),
            url=raw.get("listingUrl"),
            address_line=primary.get("line"),
            city=primary.get("city"),
            state=primary.get("state"),
            postal_code=primary.get("postalCode"),
            county=primary.get("county"),
            latitude=to_float(geo.get("latitude")),
            longitude=to_float(geo.get("longitude")),
            standard_status=raw.get("status") or "Unknown",
            property_type=raw.get("propertyType"),
            list_price=to_float(raw.get("listPrice")),
            close_price=to_float(raw.get("closePrice")),
            beds=to_float(raw.get("beds")),
            baths=to_float(raw.get("bathsTotal")),
            sqft=to_int(raw.get("livingSize")),
            lot_acres=to_float(raw.get("lotSizeAcres")),
            year_built=to_int(raw.get("yearBuilt")),
            amenities=raw.get("features", {}),
            remarks=raw.get("remarks"),
            provider_flags={
                "photo_reuse_allowed": raw.get("photoReuseAllowed", False),
                "remark_reuse_allowed": raw.get("remarkReuseAllowed", False),
            },
            listed_at=parse_datetime(raw.get("listDate")),
            source_updated_at=parse_datetime(raw.get("lastModificationTimestamp")),
            market_estimate=to_float(valuation.get("estimatedValue")),
            market_estimate_confidence=to_float(valuation.get("confidenceScore")),
            source_payload=raw,
        )

    def _sample_payload(self) -> Iterator[Dict]:
        yield {
            "listingId": "RPR-1001",
            "listingUrl": "https://example.com/listing/rpr-1001",
            "status": "Active",
            "propertyType": "Condominium",
            "listPrice": 275000,
            "beds": 2,
            "bathsTotal": 2,
            "livingSize": 1200,
            "geo": {
                "latitude": 40.0021,
                "longitude": -75.256,
                "primaryAddress": {
                    "line": "55 Sample Condo #4B",
                    "city": "Conshohocken",
                    "state": "PA",
                    "postalCode": "19428",
                    "county": "Montgomery",
                },
            },
            "valuation": {"estimatedValue": 280000, "confidenceScore": 0.8},
            "listDate": datetime.utcnow().isoformat(),
        }
