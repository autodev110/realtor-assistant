from core.messaging.compose import ToneProfile, compose_message, prepare_listing_context


def test_compose_message_generates_subject_and_body():
    listing = {
        "address_line": "123 Market St",
        "city": "Norristown",
        "list_price_cents": 32500000,
        "beds": 3,
        "baths": 2,
        "sqft": 1800,
        "url": "https://example.com/listing",
        "highlights": ["Garage", "Updated kitchen"],
        "cma_low_cents": 32000000,
        "cma_high_cents": 36000000,
        "cma_confidence": 0.8,
    }
    message = compose_message(
        client_name="Test Client",
        listings=[prepare_listing_context(listing)],
        agent_signature="Dan",
        tone_data=ToneProfile(formality="conversational", emojis=True).__dict__,
    )
    assert "homes worth" in message["subject"].lower()
    assert "Test Client" in message["body_text"]
    assert message["body_html"].startswith("<p>Hi")
