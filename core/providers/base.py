from abc import ABC, abstractmethod
from typing import Iterable, Dict, Any

ON_MARKET = {"Active", "ActiveUnderContract", "ComingSoon"}  # configurable

class ProviderClient(ABC):
    name: str

    @abstractmethod
    def fetch_updated_listings(self, since_iso: str) -> Iterable[Dict[str, Any]]:
        # Fetches raw listings updated since the given ISO timestamp
        ...

    @abstractmethod
    def map_to_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        # Normalizes raw provider data into the Listing schema
        ...

    def is_on_market(self, raw: Dict[str, Any]) -> bool:
        # Strict filter for on-market status
        status = (raw.get("StandardStatus") or raw.get("MlsStatus") or "").strip()
        return status in ON_MARKET