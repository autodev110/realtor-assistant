from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template

from core.config import get_settings

DEFAULT_TEMPLATE_TEXT = """Hi {{ client_name }},

Here are {{ listings|length }} homes I pulled for you today. {% if tone.verbosity == "detailed" %}Each one ties back to what you've told me matters most.{% endif %}

{% for listing in listings %}
{{ loop.index }}. {{ listing.address_line or listing.city }} — ${{ listing.list_price|int | format_currency }}
   • Beds/Baths: {{ listing.beds or "—" }} bd / {{ listing.baths or "—" }} ba{% if listing.sqft %}, {{ listing.sqft }} sf{% endif %}
   • Highlights: {{ listing.highlights|join(", ") if listing.highlights else "Aligned with your preferences" }}
   • CMA band: {{ listing.cma_low }} – {{ listing.cma_high }} (confidence {{ listing.cma_confidence }})
   {{ listing.url or "" }}

{% endfor %}
{{ tone.signoff }},
{{ agent_signature }}
"""

DEFAULT_TEMPLATE_HTML = """<p>Hi {{ client_name }},</p>
<p>Here are {{ listings|length }} homes I pulled for you today. {% if tone.verbosity == "detailed" %}Each one ties back to what you've told me matters most.{% endif %}</p>
{% for listing in listings %}
<div style="margin-bottom: 16px;">
  <strong>{{ loop.index }}. {{ listing.address_line or listing.city }}</strong> — ${{ listing.list_price|int | format_currency }}<br/>
  <span>Beds/Baths: {{ listing.beds or "—" }} bd / {{ listing.baths or "—" }} ba{% if listing.sqft %}, {{ listing.sqft }} sf{% endif %}</span><br/>
  <span>Highlights: {{ listing.highlights|join(", ") if listing.highlights else "Aligned with your preferences" }}</span><br/>
  <span>CMA band: {{ listing.cma_low }} – {{ listing.cma_high }} (confidence {{ listing.cma_confidence }})</span><br/>
  {% if listing.url %}<a href="{{ listing.url }}">View details</a>{% endif %}
</div>
{% endfor %}
<p>{{ tone.signoff }},<br/>{{ agent_signature }}</p>
"""


def _currency(value: int) -> str:
    dollars = value / 100
    return f"{dollars:,.0f}"


def build_environment(template_dir: Optional[str] = None) -> Environment:
    if template_dir:
        loader = FileSystemLoader(template_dir)
    else:
        loader = None
    env = Environment(loader=loader, undefined=StrictUndefined, autoescape=True)
    env.filters["format_currency"] = _currency
    return env


@dataclass
class ToneProfile:
    formality: str = "professional"
    verbosity: str = "brief"
    emojis: bool = False
    signoff: str = "Best"

    @classmethod
    def from_dict(cls, data: Optional[Dict]) -> "ToneProfile":
        data = data or {}
        return cls(
            formality=data.get("formality", "professional"),
            verbosity=data.get("verbosity", "brief"),
            emojis=data.get("emojis", False),
            signoff=data.get("signoff", "Best"),
        )


def compose_message(
    *,
    client_name: str,
    listings: List[Dict],
    agent_signature: str,
    tone_data: Optional[Dict] = None,
    template_env: Optional[Environment] = None,
) -> Dict[str, str]:
    tone = ToneProfile.from_dict(tone_data)
    env = template_env or build_environment()
    text_template: Template = env.from_string(DEFAULT_TEMPLATE_TEXT)
    html_template: Template = env.from_string(DEFAULT_TEMPLATE_HTML)

    template_context = {
        "client_name": client_name,
        "listings": listings,
        "agent_signature": agent_signature,
        "tone": tone,
    }
    text_body = text_template.render(**template_context)
    if tone.emojis:
        text_body += "\n🙂"
    html_body = html_template.render(**template_context)
    subject = f"{len(listings)} homes worth a look"
    if tone.formality == "formal":
        subject = f"{client_name}, here are {len(listings)} curated listings"

    return {
        "subject": subject,
        "body_text": text_body.strip(),
        "body_html": html_body.strip(),
    }


def summarize_highlights(listing: Dict, reasons: List[str]) -> List[str]:
    highlights = list(reasons)
    if listing.get("beds"):
        highlights.append(f"{listing['beds']} bd")
    if listing.get("baths"):
        highlights.append(f"{listing['baths']} ba")
    if listing.get("sqft"):
        highlights.append(f"{listing['sqft']} sf")
    return highlights[:5]


def prepare_listing_context(listing: Dict) -> Dict:
    context = {
        "address_line": listing.get("address_line"),
        "city": listing.get("city"),
        "list_price": listing.get("list_price_cents", 0),
        "beds": listing.get("beds"),
        "baths": listing.get("baths"),
        "sqft": listing.get("sqft"),
        "url": listing.get("url"),
        "highlights": listing.get("highlights", []),
        "cma_low": _currency(listing.get("cma_low_cents", 0)),
        "cma_high": _currency(listing.get("cma_high_cents", 0)),
        "cma_confidence": f"{int(listing.get('cma_confidence', 0) * 100)}%",
    }
    return context
