"""
Job source registry.

Maps supported job sources to known company board tokens.

NOTE: This static dict is the seed source for the job_sources DB table.
      See ATMS-134 — once the DB migration is complete this module will no
      longer be imported at runtime.  Board tokens are the slug used by each
      ATS (verified against public job-board URLs where possible).
"""

# ---------------------------------------------------------------------------
# Greenhouse  –  https://boards.greenhouse.io/{board_token}/jobs
# ---------------------------------------------------------------------------
_GREENHOUSE: dict = {
    # Fintech / Payments
    "stripe": {"board_token": "stripe", "display_name": "Stripe"},
    "coinbase": {"board_token": "coinbase", "display_name": "Coinbase"},
    "brex": {"board_token": "brex", "display_name": "Brex"},
    "robinhood": {"board_token": "robinhood", "display_name": "Robinhood"},
    "chime": {"board_token": "chime", "display_name": "Chime"},
    "gusto": {"board_token": "gusto", "display_name": "Gusto"},
    # Cloud / Infra / DevTools
    "datadog": {"board_token": "datadog", "display_name": "Datadog"},
    "cloudflare": {"board_token": "cloudflare", "display_name": "Cloudflare"},
    "elastic": {"board_token": "elastic", "display_name": "Elastic"},
    "fastly": {"board_token": "fastly", "display_name": "Fastly"},
    "checkr": {"board_token": "checkr", "display_name": "Checkr"},
    "pagerduty": {"board_token": "pagerduty", "display_name": "PagerDuty"},
    "mongodb": {"board_token": "mongodb", "display_name": "MongoDB"},
    "airtable": {"board_token": "airtable", "display_name": "Airtable"},
    "flexport": {"board_token": "flexport", "display_name": "Flexport"},
    "lattice": {"board_token": "lattice", "display_name": "Lattice"},
    # Consumer / Marketplace
    "airbnb": {"board_token": "airbnb", "display_name": "Airbnb"},
    "lyft": {"board_token": "lyft", "display_name": "Lyft"},
    "doordash": {"board_token": "doordashusa", "display_name": "DoorDash"},
    "instacart": {"board_token": "instacart", "display_name": "Instacart"},
    "reddit": {"board_token": "reddit", "display_name": "Reddit"},
    "discord": {"board_token": "discord", "display_name": "Discord"},
    "squarespace": {"board_token": "squarespace", "display_name": "Squarespace"},
    # SaaS / Productivity
    "figma": {"board_token": "figma", "display_name": "Figma"},
    "asana": {"board_token": "asana", "display_name": "Asana"},
    "dropbox": {"board_token": "dropbox", "display_name": "Dropbox"},
    "intercom": {"board_token": "intercom", "display_name": "Intercom"},
    "hubspot": {"board_token": "hubspot", "display_name": "HubSpot"},
    "amplitude": {"board_token": "amplitude", "display_name": "Amplitude"},
    "mixpanel": {"board_token": "mixpanel", "display_name": "Mixpanel"},
    "twilio": {"board_token": "twilio", "display_name": "Twilio"},
    # AI / ML
    "anthropic": {"board_token": "anthropic", "display_name": "Anthropic"},
    "scaleai": {"board_token": "scaleai", "display_name": "Scale AI"},
    # Moved from Lever
    "samsara": {"board_token": "samsara", "display_name": "Samsara"},
    "opendoor": {"board_token": "opendoor", "display_name": "Opendoor"},
    "pendo": {"board_token": "pendo", "display_name": "Pendo"},
    "duolingo": {"board_token": "duolingo", "display_name": "Duolingo"},
    # Moved from Ashby (corrected token)
    "dbtlabs": {"board_token": "dbtlabsinc", "display_name": "dbt Labs"},
    "togetherai": {"board_token": "togetherai", "display_name": "Together AI"},
}

# ---------------------------------------------------------------------------
# Lever  –  https://api.lever.co/v0/postings/{board_token}
# ---------------------------------------------------------------------------
_LEVER: dict = {
    # Entertainment / Consumer
    "spotify": {"board_token": "spotify", "display_name": "Spotify"},
    # Analytics / BI (moved from Ashby)
    "metabase": {"board_token": "metabase", "display_name": "Metabase"},
}

# ---------------------------------------------------------------------------
# Ashby  –  https://api.ashbyhq.com/posting-api/job-board/{board_token}
# ---------------------------------------------------------------------------
_ASHBY: dict = {
    # Dev Tools / Infra
    "linear": {"board_token": "linear", "display_name": "Linear"},
    "vercel": {"board_token": "vercel", "display_name": "Vercel"},
    "airbyte": {"board_token": "airbyte", "display_name": "Airbyte"},
    "temporal": {"board_token": "temporal", "display_name": "Temporal"},
    "prefect": {"board_token": "prefect", "display_name": "Prefect"},
    "kaizenlabs": {"board_token": "kaizenlabs", "display_name": "Kaizen Labs"},
    # Fintech / HR
    "ramp": {"board_token": "ramp", "display_name": "Ramp"},
    "mercury": {"board_token": "mercury", "display_name": "Mercury"},
    "deel": {"board_token": "deel", "display_name": "Deel"},
    # AI / ML
    "mistral": {"board_token": "mistral", "display_name": "Mistral AI"},
    "perplexity": {"board_token": "perplexity", "display_name": "Perplexity AI"},
    # Moved from Greenhouse
    "notion": {"board_token": "notion", "display_name": "Notion"},
    "cohere": {"board_token": "cohere", "display_name": "Cohere"},
    "plaid": {"board_token": "plaid", "display_name": "Plaid"},
    # Moved from Lever
    "1password": {"board_token": "1password", "display_name": "1Password"},
    # Moved from Greenhouse
    "benchling": {"board_token": "benchling", "display_name": "Benchling"},
    "confluent": {"board_token": "confluent", "display_name": "Confluent"},
}

JOB_SOURCE_REGISTRY: dict = {
    "greenhouse": _GREENHOUSE,
    "lever": _LEVER,
    "ashby": _ASHBY,
}