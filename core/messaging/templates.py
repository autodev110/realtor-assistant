LISTING_BLURB = """Hi {{client.name}},
Here are {{count}} homes I think you'll like {{why_note}}.
{% for h in homes -%}
• {{h.street}}, {{h.city}} — ${{"{:,.0f}".format(h.list_price)}} ({{h.beds}} bd / {{h.baths}} ba, {{h.sqft|default('—')}} sf)
Why it fits you: {{h.why|join(', ')}}
Link: {{h.public_url}}
{% endfor %}
Want me to book showings this weekend?
– {{agent_signature}}
""" # [cite: 277, 278, 279, 280, 281, 282, 283, 284, 285, 286]