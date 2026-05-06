"""
Follow-up cadence constants.

Configurable thresholds for follow-up timing based on application status and history.
"""

# Follow-up cadence thresholds (in days)
CADENCE = {
    'applied_first': 7,            # Days after applying to send first follow-up
    'applied_subsequent': 7,       # Days between applied status follow-ups
    'applied_max_followups': 2,    # Max follow-ups for applied status
    'responded_initial': 1,        # Days after response to send thank-you (urgent)
    'responded_subsequent': 3,     # Days between responded status follow-ups
    'interview_thankyou': 1,       # Days after interview to send thank-you
}

# Actionable application statuses for follow-ups
ACTIONABLE_STATUSES = ['applied', 'responded', 'interview']

# Follow-up type enum
FOLLOWUP_TYPES = {
    'first': 'first',                 # First follow-up after applying
    'subsequent': 'subsequent',       # Subsequent follow-ups after applying
    'thank_you': 'thank_you',         # Thank-you after response or interview
}

# Urgency levels for prioritization
URGENCY_LEVELS = {
    'overdue': 'overdue',             # Past due date
    'urgent': 'urgent',               # Due within 1-2 days
    'waiting': 'waiting',             # Future follow-up
    'cold': 'cold',                   # Max follow-ups reached, no further action
}
