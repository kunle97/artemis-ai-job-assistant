"""
Automation fill constants.

Central place for tunable fill-time behavior values.
"""

HUMAN_SELECT_TYPING_DELAY_MS = 75

# Bound individual Playwright actions so a missing or stale ATS selector does
# not stall every fallback strategy for the library default of 30 seconds.
FILL_ACTION_TIMEOUT_MS = 5_000

# Radio controls are already present when the fill plan runs. Keep each
# activation attempt short so hidden/custom-styled inputs do not consume the
# full page timeout before the next safe strategy is attempted.
RADIO_ACTIVATION_TIMEOUT_MS = 750

# Random pause between form fields to mimic natural pacing without
# materially slowing end-to-end form completion.
INTER_FIELD_DELAY_MIN_MS = 80
INTER_FIELD_DELAY_MAX_MS = 220
