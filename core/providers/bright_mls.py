from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Iterator, Optional

import requests

from core.schema.listing import MediaAsset, NormalizedListing

from .base import ProviderClient
from .utils import parse_datetime, to_float, to_int


class BrightMLSClient(ProviderClient):
    """RESO Web API client for Bright MLS.

    This stub fetches a small sample dataset when credentials are not supplied.
    Replace the `fetch_updated` implementation with the production-grade RESO
    Web API pagination and filtering logic.
    """

    name = "bright_mls"

    def __init__(self) -> None:
        super().__init__()
        self.base_url = os.getenv("BRIGHTMLS_BASE_URL", "").rstrip("/")
        self.client_id = os.getenv("BRIGHTMLS_CLIENT_ID")
        self.client_secret = os.getenv("BRIGHTMLS_CLIENT_SECRET")
        self.access_token = os.getenv("BRIGHTMLS_ACCESS_TOKEN")

    def fetch_updated(
        self, since: Optional[datetime] = None, cursor: Optional[str] = None
    ) -> Iterator[Dict]:
        if not self.base_url or not self.access_token:
            yield from self._sample_payload()
            return

        params = {
            "$top": self.settings.ingestion_chunk_size,
            "$orderby": "ModificationTimestamp desc",
        }
        if since:
            params["$filter"] = f"ModificationTimestamp ge {since.isoformat()}"
        if cursor:
            params["$skiptoken"] = cursor

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(
            f"{self.base_url}/Property",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        for record in payload.get("value", []):
            yield record

    def normalize(self, raw: Dict) -> NormalizedListing:
        media_assets = []
        for media in raw.get("Media", []) or []:
            url = media.get("MediaURL")
            if not url:
                continue
            media_assets.append(
                MediaAsset(
                    url=url,
                    caption=media.get("LongDescription"),
                    attribution=media.get("CopyrightNotice"),
                    license=media.get("MediaCategory"),
                    is_primary=media.get("PrimaryPhotoIndicator", False),
                )
            )

        listed_at = parse_datetime(raw.get("ListingContractDate"))
        return NormalizedListing(
            provider=self.name,
            mls_id=raw.get("ListingId") or raw.get("ListingKey"),
            listing_key=raw.get("ListingKey"),
            url=raw.get("ListingURL") or raw.get("VirtualTourURLUnbranded"),
            address_line=raw.get("UnparsedAddress"),
            unit_number=raw.get("UnitNumber"),
            city=raw.get("City"),
            state=raw.get("StateOrProvince"),
            postal_code=raw.get("PostalCode"),
            county=raw.get("CountyOrParish"),
            latitude=to_float(raw.get("Latitude")),
            longitude=to_float(raw.get("Longitude")),
            standard_status=raw.get("StandardStatus") or raw.get("MlsStatus") or "Unknown",
            status_raw=raw.get("MlsStatus"),
            property_type=raw.get("PropertyType"),
            list_price=to_float(raw.get("ListPrice")),
            close_price=to_float(raw.get("ClosePrice")),
            original_list_price=to_float(raw.get("OriginalListPrice")),
            beds=to_float(raw.get("BedroomsTotal")),
            baths=to_float(raw.get("BathroomsTotalDecimal")),
            stories=to_float(raw.get("StoriesTotal")),
            sqft=to_int(raw.get("LivingArea")),
            lot_sqft=to_int(raw.get("LotSizeSquareFeet")),
            lot_acres=to_float(raw.get("LotSizeAcres")),
            year_built=to_int(raw.get("YearBuilt")),
            parking_spaces=to_int(raw.get("GarageSpaces")),
            hoa_fee=to_float(raw.get("AssociationFee")),
            taxes_annual=to_float(raw.get("TaxAnnualAmount")),
            amenities={
                "garage": raw.get("GarageYN"),
                "basement": raw.get("BasementYN"),
                "cooling": raw.get("Cooling"),
                "heating": raw.get("Heating"),
            },
            features=raw.get("InteriorFeatures") or [],
            condition_notes={"disclosures": raw.get("Disclosures")},
            remarks=raw.get("PublicRemarks"),
            media=media_assets,
            open_houses=raw.get("OpenHouse") or [],
            provider_flags={
                "photo_reuse_allowed": raw.get("SyndicateTo") != "None",
                "remarks_reuse_allowed": raw.get("SyndicateRemarks") not in ("None", False),
            },
            compliance_tags=[],
            risk_assessments={},
            listed_at=listed_at,
            source_updated_at=parse_datetime(raw.get("ModificationTimestamp")),
            source_payload=raw,
        )

    def _sample_payload(self) -> Iterator[Dict]:
        yield {
            "ListingId": "BRIGHT123",
            "ListingKey": "BRIGHT123",
            "ListingURL": "https://example.com/listing/BRIGHT123",
            "UnparsedAddress": "101 Sample Ave",
            "City": "Philadelphia",
            "StateOrProvince": "PA",
            "PostalCode": "19103",
            "CountyOrParish": "Philadelphia",
            "Latitude": 39.9526,
            "Longitude": -75.1652,
            "StandardStatus": "Active",
            "PropertyType": "Residential",
            "ListPrice": 525000,
            "BedroomsTotal": 3,
            "BathroomsTotalDecimal": 2.5,
            "LivingArea": 2100,
            "LotSizeSquareFeet": 1600,
            "YearBuilt": 1920,
            "ModificationTimestamp": datetime.utcnow().isoformat(),
            "AssociationFee": 0,
            "GarageSpaces": 1,
            "PublicRemarks": "Updated townhome close to Rittenhouse Square.",
            "Media": [
                {
                    "MediaURL": "https://example.com/images/bright123.jpg",
                    "LongDescription": "Front exterior",
                    "CopyrightNotice": "Bright MLS",
                    "PrimaryPhotoIndicator": True,
                }
            ],
        }
