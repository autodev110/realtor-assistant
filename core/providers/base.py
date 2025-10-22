from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Iterable, Iterator, Optional

from core.config import get_settings
from core.schema.listing import NormalizedListing

from .status import is_on_market, normalize_status


class ProviderClient(ABC):
    """Base interface for any listing provider integration."""

    name: str

    def __init__(self) -> None:
        self.settings = get_settings()
        self.rate_limit_per_minute = self.settings.provider_rate_limits.get(self.name, 60)

    @abstractmethod
    def fetch_updated(
        self, since: Optional[datetime] = None, cursor: Optional[str] = None
    ) -> Iterator[Dict]:
        """Yield raw provider payloads updated since the datetime or cursor."""

    @abstractmethod
    def normalize(self, raw: Dict) -> NormalizedListing:
        """Map provider payload to NormalizedListing."""

    def stream(
        self, since: Optional[datetime] = None, cursor: Optional[str] = None
    ) -> Iterable[NormalizedListing]:
        interval = max(1.0, 60.0 / max(self.rate_limit_per_minute, 1))
        for raw in self.fetch_updated(since=since, cursor=cursor):
            raw_status = raw.get("StandardStatus") or raw.get("status") or ""
            if not is_on_market(self.name, raw_status):
                continue
            normalized = self.normalize(raw)
            normalized.standard_status = normalize_status(self.name, normalized.standard_status)
            yield normalized
            time.sleep(interval)
