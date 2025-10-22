from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterator, Optional

from core.schema.listing import NormalizedListing

from .base import ProviderClient
from .utils import parse_datetime, to_float, to_int


class ZillowPartnerClient(ProviderClient):
    """Stub client for Zillow-provided partner feed (non-scraping)."""

    name = "zillow_partner"

    def fetch_updated(
        self, since: Optional[datetime] = None, cursor: Optional[str] = None
    ) -> Iterator[Dict]:
        # Partner feed integration should be added here once credentials are available.
        yield from self._sample_payload()

    def normalize(self, raw: Dict) -> NormalizedListing:
        address = raw.get("address", {})
        lot_value = to_float(raw.get("lotAreaValue"))
        lot_unit = raw.get("lotAreaUnit")
        lot_sqft = None
        lot_acres = None
        if lot_value is not None:
            if lot_unit == "acres":
                lot_acres = lot_value
                lot_sqft = int(lot_value * 43560)
            else:
                lot_sqft = to_int(lot_value)
                if lot_sqft is not None:
                    lot_acres = lot_sqft / 43560.0

        return NormalizedListing(
            provider=self.name,
            external_id=raw.get("zpid"),
            url=raw.get("detailUrl"),
            address_line=address.get("streetAddress"),
            city=address.get("city"),
            state=address.get("state"),
            postal_code=address.get("zipcode"),
            county=address.get("county"),
            latitude=to_float(raw.get("latitude")),
            longitude=to_float(raw.get("longitude")),
            standard_status=raw.get("status") or "Active",
            property_type=raw.get("homeType"),
            list_price=to_float(raw.get("price")),
            beds=to_float(raw.get("bedrooms")),
            baths=to_float(raw.get("bathrooms")),
            sqft=to_int(raw.get("livingArea")),
            lot_sqft=lot_sqft,
            lot_acres=lot_acres,
            year_built=to_int(raw.get("yearBuilt")),
            amenities=raw.get("features", {}),
            remarks=raw.get("description"),
            provider_flags={"redistribution_allowed": raw.get("partnerSyndication", False)},
            listed_at=parse_datetime(raw.get("datePosted")),
            source_updated_at=parse_datetime(raw.get("dateUpdated")),
            source_payload=raw,
        )

    def _sample_payload(self) -> Iterator[Dict]:
        yield {
            "zpid": "ZILL-9001",
            "detailUrl": "https://www.zillow.com/homedetails/123-Sample-St/000000",
            "status": "For Sale",
            "homeType": "SingleFamily",
            "price": 450000,
            "bedrooms": 4,
            "bathrooms": 2.5,
            "livingArea": 2100,
            "lotAreaValue": 7405,
            "yearBuilt": 1992,
            "address": {
                "streetAddress": "123 Sample St",
                "city": "Pottstown",
                "state": "PA",
                "zipcode": "19464",
                "county": "Montgomery",
            },
            "datePosted": datetime.utcnow().isoformat(),
        }
