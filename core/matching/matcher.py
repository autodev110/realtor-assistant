from __future__ import annotations

from typing import Iterable, List, Tuple

from core.storage.models import Client, Listing

from .explain import explain_listing
from .preferences import PreferenceVector, vector_from_listing, score_listing


def rank_listings(
    *,
    client: Client,
    listings: Iterable[Listing],
    limit: int = 10,
) -> List[Tuple[float, Listing, List[str]]]:
    prefs = PreferenceVector.from_client(client)
    explicit = client.prefs or {}
    scored: List[Tuple[float, Listing, List[str]]] = []
    for listing in listings:
        vector = vector_from_listing(listing, explicit)
        score = score_listing(vector, prefs)
        explanations = explain_listing(vector, prefs)
        scored.append((score, listing, explanations))
    scored.sort(key=lambda entry: entry[0], reverse=True)
    return scored[:limit]
