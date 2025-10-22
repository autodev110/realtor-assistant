from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Tuple

from core.cma.engine import compute_cma
from core.config import get_settings
from core.matching.matcher import rank_listings
from core.messaging.compose import compose_message, prepare_listing_context, summarize_highlights
from core.providers import enabled_providers, get_provider
from core.providers.status import allowed_statuses
from core.reporters.pdf import build_pdf_context, render_cma_pdf
from core.storage.db import session_scope
from core.storage.models import (
    CMAReport,
    Client,
    ComparableSale,
    DraftMessage,
    Listing,
    ProviderIngestState,
)
from core.storage.upsert import persist_deal_alert, upsert_listing

settings = get_settings()


def ingest_all_providers() -> None:
    for provider_name in enabled_providers():
        ingest_provider(provider_name)


def ingest_provider(provider_name: str) -> None:
    provider = get_provider(provider_name)
    with session_scope() as session:
        state = (
            session.query(ProviderIngestState)
            .filter(ProviderIngestState.provider == provider_name)
            .one_or_none()
        )
        if not state:
            state = ProviderIngestState(provider=provider_name)
            session.add(state)
            session.flush()

        since = state.last_success_at or datetime.utcnow() - timedelta(days=1)
        cursor = state.last_cursor
        total = 0
        for normalized in provider.stream(since=since, cursor=cursor):
            upsert_listing(session, normalized)
            total += 1
        state.last_success_at = datetime.utcnow()
        session.commit()
    print(f"[ingest] {provider_name} -> {total} listings")


def run_daily_digests(limit: int = 5) -> None:
    with session_scope() as session:
        clients = session.query(Client).all()
        for client in clients:
            generate_client_digest(session, client, limit=limit)
        session.commit()


def generate_client_digest(session, client: Client, limit: int = 5) -> None:
    allowed = list(allowed_statuses())
    query = (
        session.query(Listing)
        .filter(Listing.standard_status.in_(allowed))
        .filter(Listing.county.in_(settings.approved_counties))
    )
    recommendations = rank_listings(client=client, listings=query, limit=limit)
    if not recommendations:
        return

    listing_contexts = []
    listing_ids = []
    for score, listing, reasons in recommendations:
        report = ensure_cma_report(session, listing)
        context = {
            "address_line": listing.address_line,
            "city": listing.city,
            "list_price_cents": listing.list_price_cents or 0,
            "beds": listing.beds,
            "baths": listing.baths,
            "sqft": listing.sqft,
            "url": listing.url,
            "highlights": summarize_highlights(
                {
                    "beds": listing.beds,
                    "baths": listing.baths,
                    "sqft": listing.sqft,
                },
                reasons,
            ),
            "cma_low_cents": report.price_low_cents,
            "cma_high_cents": report.price_high_cents,
            "cma_confidence": report.confidence,
        }
        listing_contexts.append(context)
        listing_ids.append(str(listing.id))

    message = compose_message(
        client_name=client.full_name or client.email,
        listings=[prepare_listing_context(ctx) for ctx in listing_contexts],
        agent_signature=settings.environment.capitalize(),
        tone_data=client.tone_profile,
    )

    draft = DraftMessage(
        client_id=client.id,
        subject=message["subject"],
        body_markdown=message["body_text"],
        body_html=message["body_html"],
        channel="email",
        status="pending_approval",
        listings_context=listing_contexts,
        auto_send=client.auto_send_enabled,
        metadata={"listing_ids": listing_ids},
    )
    session.add(draft)


def ensure_cma_report(session, listing: Listing) -> CMAReport:
    recent_report = (
        session.query(CMAReport)
        .filter(
            CMAReport.subject_listing_id == listing.id,
            CMAReport.generated_at >= datetime.utcnow() - timedelta(days=3),
        )
        .order_by(CMAReport.generated_at.desc())
        .first()
    )
    if recent_report:
        return recent_report

    comparables = list(_select_comparables(session, listing))
    result = compute_cma(listing, comparables)

    report = CMAReport(
        subject_listing_id=listing.id,
        params={
            "radius_miles": settings.cma_radius_miles,
            "days_back": settings.cma_days_back,
            "max_comps": settings.cma_max_comps,
        },
        comps_summary=[],
        price_low_cents=result.price_low_cents,
        price_mid_cents=result.price_mid_cents,
        price_high_cents=result.price_high_cents,
        confidence=result.confidence,
        psf_chart=result.psf_chart,
        narrative=f"Median adjusted price ${result.price_mid_cents / 100:,.0f}",
    )
    session.add(report)
    session.flush()

    for comp in result.comps:
        session.add(
            ComparableSale(
                report_id=report.id,
                subject_listing_id=listing.id,
                comp_listing_id=uuid.UUID(comp.listing_id),
                adjustments=comp.adjustments,
                adjusted_price_cents=comp.adjusted_price_cents,
                distance_miles=comp.distance_miles,
                days_back=comp.days_back,
                similarity_score=comp.similarity_score,
            )
        )

    listing.market_estimate_cents = result.price_mid_cents
    listing.market_estimate_confidence = result.confidence

    if result.deal_alert:
        payload = result.deal_alert.model_dump()
        payload["source_report_id"] = report.id
        persist_deal_alert(session, listing, payload)

    pdf_context = build_pdf_context(
        subject={"address_line": listing.address_line, "city": listing.city},
        comps=[
            {
                "address": listing.address_line,
                "sale_price": comp.raw_price_cents / 100,
                "adjusted_price": comp.adjusted_price_cents / 100,
                "adjustments": {k: f"${v / 100:,.0f}" for k, v in comp.adjustments.items()},
                "distance": comp.distance_miles,
                "days_back": comp.days_back,
            }
            for comp in result.comps
        ],
        band={
            "low_cents": result.price_low_cents,
            "mid_cents": result.price_mid_cents,
            "high_cents": result.price_high_cents,
            "confidence": result.confidence,
        },
    )
    output_path = Path("reports") / f"cma-{report.id}.pdf"
    render_cma_pdf(output_path, pdf_context)
    report.pdf_storage_path = str(output_path)

    session.flush()
    return report


def _select_comparables(session, subject: Listing) -> Iterable[Tuple[Listing, float, int]]:
    radius = settings.cma_radius_miles
    min_sqft = int((subject.sqft or 0) * 0.8) if subject.sqft else None
    max_sqft = int((subject.sqft or 0) * 1.2) if subject.sqft else None

    candidates = (
        session.query(Listing)
        .filter(Listing.id != subject.id)
        .filter(Listing.standard_status.in_(["Closed", "Sold", "Pending"]))
        .filter(Listing.property_type == subject.property_type)
    )

    if min_sqft and max_sqft:
        candidates = candidates.filter(Listing.sqft.between(min_sqft, max_sqft))

    if subject.city:
        candidates = candidates.filter(Listing.city == subject.city)

    candidates = candidates.order_by(Listing.source_updated_at.desc()).limit(50)

    for listing in candidates:
        distance = _haversine(
            subject.latitude,
            subject.longitude,
            listing.latitude,
            listing.longitude,
        )
        if distance is None or distance > radius:
            continue
        comparison_date = listing.off_market_at or listing.source_updated_at or listing.updated_at
        days_back = (
            (datetime.utcnow() - comparison_date).days if comparison_date else settings.cma_days_back
        )
        yield listing, distance, days_back


def _haversine(lat1, lon1, lat2, lon2):
    if not all([lat1, lon1, lat2, lon2]):
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return 3958.8 * c
