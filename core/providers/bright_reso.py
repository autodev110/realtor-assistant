import requests, os
from .base import ProviderClient
from datetime import datetime

class BrightRESOClient(ProviderClient):
    name = "bright_mls" [cite: 137]
    
    def __init__(self):
        self.base = os.getenv("BRIGHT_RESO_BASE") [cite: 139]
        self.token = os.getenv("BRIGHT_RESO_TOKEN") [cite: 140]

    def fetch_updated_listings(self, since_iso: str):
        # Real impl: $filter=ModificationTimestamp ge since_iso AND StandardStatus in (...) [cite: 142]
        # Include $select fields to minimize payload. [cite: 143]
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"$top": 500, "$orderby": "ModificationTimestamp desc",
                  "$filter": f"ModificationTimestamp ge {since_iso}"} [cite: 145, 146]
        
        # This is a stub: actual implementation needs paging and robust error handling
        r = requests.get(f"{self.base}/Property", headers=headers, params=params, timeout=30)
        r.raise_for_status()
        
        for row in r.json().get("value", []):
            if self.is_on_market(row):
                yield row [cite: 150, 151]

def map_to_schema(self, raw):
        # Maps RESO fields to the internal Listing model
        media = []
        for p in (raw.get("Media") or []):
            media.append({
                "url": p.get("MediaURL"), 
                "caption": p.get("LongDescription"),
                "attribution": p.get("CopyrightNotice"),
                "license": p.get("License")
            }) 
        
        return dict(
            mls_id = raw.get("ListingId") or raw.get("ListingKey"), 
            status = raw.get("StandardStatus"), 
            property_type = raw.get("PropertyType"), 
            street = raw.get("UnparsedAddress"), city = raw.get("City"), 
            state = raw.get("StateOrProvince"), postal = raw.get("PostalCode"),
            lat = raw.get("Latitude"), lon = raw.get("Longitude"),
            list_price = raw.get("ListPrice"), close_price = raw.get("ClosePrice"),
            beds = raw.get("BedroomsTotal"), baths = raw.get("BathroomsTotalDecimal"),
            sqft = raw.get("LivingArea"), lot_sqft = raw.get("LotSizeSquareFeet"),
            year_built = raw.get("YearBuilt"), hoa_fee = raw.get("AssociationFee"),
            features = {"garage": raw.get("GarageYN"), "basement": raw.get("BasementYN")},
            media = media, 
            raw = raw
        )