from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Iterator, Optional

import requests

from core.schema.listing import MediaAsset, NormalizedListing

from .base import ProviderClient
from .utils import parse_datetime, to_float, to_int


class AttomClient(ProviderClient):
    """ATTOM Data Solutions listings feed stub."""

    name = "attom"

    def __init__(self) -> None:
        super().__init__()
        self.base_url = os.getenv("ATTOM_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("ATTOM_API_KEY")

    def fetch_updated(
        self, since: Optional[datetime] = None, cursor: Optional[str] = None
    ) -> Iterator[Dict]:
        if not self.base_url or not self.api_key:
            yield from self._sample_payload()
            return

        params = {
            "pageSize": self.settings.ingestion_chunk_size,
            "minLastUpdateDate": since.isoformat() if since else None,
            "page": cursor or 1,
        }
        headers = {"apikey": self.api_key}
        response = requests.get(
            f"{self.base_url}/propertyapi/v1.0.0/property/address",
            headers=headers,
            params={k: v for k, v in params.items() if v is not None},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        for record in payload.get("property", []):
            yield record

    def normalize(self, raw: Dict) -> NormalizedListing:
        address = raw.get("address", {})
        sale = raw.get("sale", {})
        building = raw.get("building", {})
        rooms = building.get("rooms", {})
        lot = raw.get("lot", {})

        return NormalizedListing(
            provider=self.name,
            external_id=str(raw.get("identifier", {}).get("obPropId")),
            url=raw.get("listing", {}).get("listingURL"),
            address_line=address.get("line1"),
            city=address.get("locality"),
            state=address.get("region"),
            postal_code=address.get("postal1"),
            county=address.get("county"),
            latitude=to_float(raw.get("location", {}).get("latitude")),
            longitude=to_float(raw.get("location", {}).get("longitude")),
            standard_status=raw.get("listing", {}).get("status") or "Unknown",
            status_raw=raw.get("listing", {}).get("status"),
            property_type=raw.get("summary", {}).get("propclass"),
            list_price=to_float(sale.get("listprice")),
            close_price=to_float(sale.get("amount")),
            beds=to_float(rooms.get("beds")),
            baths=to_float(rooms.get("bathstotal")),
            stories=to_float(building.get("stories")),
            sqft=to_int(building.get("size", {}).get("universalsize")),
            lot_sqft=to_int(lot.get("lotsize1")),
            lot_acres=to_float(lot.get("lotsize2")),
            year_built=to_int(building.get("construction", {}).get("yearbuilt")),
            parking_spaces=to_int(building.get("parking", {}).get("spaces")),
            taxes_annual=to_float(raw.get("assessment", {}).get("tax", {}).get("taxamt")),
            amenities={
                "pool": raw.get("building", {}).get("pool"),
                "garage": building.get("parking", {}).get("type"),
            },
            features=building.get("interior", {}).get("feature", []),
            remarks=raw.get("listing", {}).get("remarks"),
            media=[
                MediaAsset(url=photo["url"])
                for photo in raw.get("media", {}).get("photos", [])
                if photo.get("url")
            ],
            provider_flags={
                "redistribution_allowed": raw.get("listing", {}).get("isDistributionAllowed", False)
            },
            listed_at=parse_datetime(raw.get("listing", {}).get("listDate")),
            source_updated_at=parse_datetime(raw.get("listing", {}).get("updateDate")),
            source_payload=raw,
        )

    def _sample_payload(self) -> Iterator[Dict]:
        yield {
            "identifier": {"obPropId": "ATTOM-001"},
            "address": {
                "line1": "202 Example Rd",
                "locality": "Norristown",
                "region": "PA",
                "postal1": "19403",
                "county": "Montgomery",
            },
            "location": {"latitude": 40.123, "longitude": -75.344},
            "listing": {"status": "Active", "listDate": datetime.utcnow().isoformat()},
            "summary": {"propclass": "Residential"},
            "sale": {"listprice": 385000},
            "building": {
                "rooms": {"beds": 3, "bathstotal": 2},
                "size": {"universalsize": 1650},
                "construction": {"yearbuilt": 1985},
            },
        }
