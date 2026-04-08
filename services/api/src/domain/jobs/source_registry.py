"""
Job source registry.

Maps supported job sources to known company board tokens.
"""

JOB_SOURCE_REGISTRY = {
    "greenhouse": {
        "stripe": {
            "board_token": "stripe",
            "display_name": "Stripe",
        },
        "figma": {
            "board_token": "figma",
            "display_name": "Figma",
        },
        "datadog": {
            "board_token": "datadog",
            "display_name": "Datadog",
        },
        "coinbase": {
            "board_token": "coinbase",
            "display_name": "Coinbase",
        },
    },
    "lever": {
        "netflix": {
            "board_token": "netflix",
            "display_name": "Netflix",
        },
    },
}