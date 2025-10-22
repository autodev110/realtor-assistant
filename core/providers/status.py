from __future__ import annotations

from typing import Dict, Iterable

from core.config import get_settings


STANDARD_ON_MARKET = {"Active", "ActiveUnderContract", "ComingSoon"}
STANDARD_OFF_MARKET = {
    "Pending",
    "UnderContract",
    "Withdrawn",
    "Closed",
    "OffMarket",
    "Expired",
}

PROVIDER_STATUS_MAP: Dict[str, Dict[str, str]] = {
    "bright_mls": {
        "Active": "Active",
        "Active Under Contract": "ActiveUnderContract",
        "Coming Soon": "ComingSoon",
        "Pending": "Pending",
        "Withdrawn": "Withdrawn",
        "Closed": "Closed",
        "Expired": "Expired",
    },
    "attom": {
        "Active": "Active",
        "Contingent": "ActiveUnderContract",
        "Coming Soon": "ComingSoon",
        "Pending": "Pending",
        "Sold": "Closed",
        "Off Market": "OffMarket",
    },
    "rpr": {
        "Active": "Active",
        "Active Under Contract": "ActiveUnderContract",
        "Coming Soon": "ComingSoon",
        "Pending": "Pending",
        "Sold": "Closed",
        "Withdrawn": "Withdrawn",
        "Expired": "Expired",
    },
    "zillow_partner": {
        "For Sale": "Active",
        "Pending": "Pending",
        "Under Contract": "ActiveUnderContract",
        "Coming Soon": "ComingSoon",
        "Sold": "Closed",
    },
    "realtor_partner": {
        "Active": "Active",
        "Coming Soon": "ComingSoon",
        "Pending": "Pending",
        "Contingent": "ActiveUnderContract",
        "Sold": "Closed",
    },
    "coldwell_banker_partner": {
        "Active": "Active",
        "Coming Soon": "ComingSoon",
        "Pending": "Pending",
        "Under Contract": "ActiveUnderContract",
        "Sold": "Closed",
    },
}


def normalize_status(provider: str, raw_status: str) -> str:
    mapping = PROVIDER_STATUS_MAP.get(provider, {})
    normalized = mapping.get(raw_status, raw_status)
    return normalized.replace(" ", "")


def allowed_statuses() -> Iterable[str]:
    settings = get_settings()
    allowed = {"Active"}
    if settings.allow_active_under_contract:
        allowed.add("ActiveUnderContract")
    if settings.allow_coming_soon:
        allowed.add("ComingSoon")
    return allowed


def is_on_market(provider: str, raw_status: str) -> bool:
    normalized = normalize_status(provider, raw_status)
    return normalized in allowed_statuses()
