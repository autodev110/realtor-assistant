from __future__ import annotations

from typing import Dict, Iterable, List

from core.config import get_settings

from .attom import AttomClient
from .bright_mls import BrightMLSClient
from .coldwell_banker_partner import ColdwellBankerPartnerClient
from .realtor_partner import RealtorPartnerClient
from .rpr import RPRClient
from .zillow_partner import ZillowPartnerClient

ProviderClass = {
    "bright_mls": BrightMLSClient,
    "attom": AttomClient,
    "rpr": RPRClient,
    "zillow_partner": ZillowPartnerClient,
    "realtor_partner": RealtorPartnerClient,
    "coldwell_banker_partner": ColdwellBankerPartnerClient,
}


def get_provider(name: str):
    if name not in ProviderClass:
        raise KeyError(f"Unknown provider '{name}'")
    return ProviderClass[name]()


def enabled_providers() -> List[str]:
    settings = get_settings()
    return [name for name in settings.ingestion_providers if name in ProviderClass]


def all_clients() -> Iterable:
    for name in enabled_providers():
        yield get_provider(name)
