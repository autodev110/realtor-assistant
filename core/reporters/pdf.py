from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, PackageLoader, select_autoescape

try:
    from weasyprint import HTML  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    HTML = None

PDF_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; }
    h1 { font-size: 24px; margin-bottom: 4px; }
    h2 { font-size: 18px; margin-top: 24px; }
    table { border-collapse: collapse; width: 100%; margin-top: 12px; }
    th, td { border: 1px solid #ccc; padding: 8px; font-size: 12px; text-align: left; }
    .band { margin-top: 16px; font-size: 16px; }
    .confidence { color: #1b6ac9; font-weight: bold; }
  </style>
</head>
<body>
  <h1>{{ subject.address_line or subject.city }}</h1>
  <div class="band">
    Recommended price band: <strong>${{ band.low }}</strong> – <strong>${{ band.high }}</strong><br/>
    Median estimate: <strong>${{ band.mid }}</strong> (<span class="confidence">confidence {{ band.confidence }}</span>)
  </div>

  <h2>Top Comparable Sales</h2>
  <table>
    <thead>
      <tr>
        <th>Address</th>
        <th>Sale Price</th>
        <th>Adj. Price</th>
        <th>Adjustments</th>
        <th>Distance (mi)</th>
        <th>Days Back</th>
      </tr>
    </thead>
    <tbody>
    {% for comp in comps %}
      <tr>
        <td>{{ comp.address }}</td>
        <td>${{ comp.sale_price }}</td>
        <td>${{ comp.adjusted_price }}</td>
        <td>
          {% for key, value in comp.adjustments.items() %}
            {{ key }}: {{ value }}
          {% endfor %}
        </td>
        <td>{{ comp.distance }}</td>
        <td>{{ comp.days_back }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""


def _currency(value_cents: int) -> str:
    return f"{value_cents / 100:,.0f}"


def render_cma_pdf(output_path: Path, context: Dict) -> Path:
    env = Environment(autoescape=select_autoescape())
    template = env.from_string(PDF_TEMPLATE)
    html = template.render(context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if HTML:
        HTML(string=html).write_pdf(str(output_path))
    else:
        output_path.write_text(html, encoding="utf-8")
    return output_path


def build_pdf_context(subject: Dict, comps: List[Dict], band: Dict) -> Dict:
    return {
        "subject": subject,
        "comps": comps,
        "band": {
            "low": _currency(band["low_cents"]),
            "mid": _currency(band["mid_cents"]),
            "high": _currency(band["high_cents"]),
            "confidence": f"{int(band['confidence'] * 100)}%",
        },
    }
