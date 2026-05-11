"""
Application analytics domain models.

This subdomain has no new database tables.
Analytics are computed at query-time from the following existing models:

- ``Application``         — application records with lifecycle statuses
- ``ApplicationScore``    — per-application fit scores (global_score field)

Both models are defined in their respective domain modules and are accessed
via the ``ApplicationPatternRepository``.
"""
