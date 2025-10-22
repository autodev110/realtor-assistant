from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterator, Optional

from core.schema.listing import NormalizedListing

from .base import ProviderClient
from .utils import parse_datetime, to_float, to_int


class RealtorPartnerClient(ProviderClient):
    """Stub client for Realtor.com syndication feed."""

    name = "realtor_partner"

    def fetch_updated(
        self, since: Optional[datetime] = None, cursor: Optional[str] = None
    ) -> Iterator[Dict]:
        yield from self._sample_payload()

    def normalize(self, raw: Dict) -> NormalizedListing:
        address = raw.get("address", {})
        return NormalizedListing(
            provider=self.name,
            external_id=raw.get("property_id"),
            url=raw.get("rdc_web_url"),
            address_line=address.get("line"),
            city=address.get("city"),
            state=address.get("state_code"),
            postal_code=address.get("postal_code"),
            county=address.get("county"),
            latitude=to_float(address.get("lat")),
            longitude=to_float(address.get("lon")),
            standard_status=raw.get("prop_status") or "Active",
            property_type=raw.get("prop_type"),
            list_price=to_float(raw.get("price")),
            beds=to_float(raw.get("beds")),
            baths=to_float(raw.get("baths")),
            sqft=to_int(raw.get("building_size", {}).get("size")),
            lot_sqft=to_int(raw.get("lot_size", {}).get("size")),
            year_built=to_int(raw.get("year_built")),
            amenities={"garage": raw.get("garage"), "stories": raw.get("stories")},
            remarks=raw.get("description"),
            provider_flags={"redistribution_allowed": raw.get("is_syndicated", False)},
            listed_at=parse_datetime(raw.get("list_date")),
            source_updated_at=parse_datetime(raw.get("last_update")),
            source_payload=raw,
        )

    def _sample_payload(self) -> Iterator[Dict]:
        yield {
            "property_id": "RDCTEST01",
            "rdc_web_url": "https://www.realtor.com/realestateandhomes-detail/RDCTEST01",
            "prop_status": "Active",
            "prop_type": "townhome",
            "price": 365000,
            "beds": 3,
            "baths": 2,
            "year_built": 2008,
            "address": {
                "line": "789 Example Ct",
                "city": "Allentown",
                "state_code": "PA",
                "postal_code": "18104",
                "county": "Lehigh",
                "lat": 40.602,
                "lon": -75.471,
            },
            "list_date": datetime.utcnow().isoformat(),
        }
