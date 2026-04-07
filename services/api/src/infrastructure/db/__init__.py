"""
Database initialization module.

Imports all models so SQLAlchemy metadata is aware of them.
This is important for table creation and future migrations.
"""

# Models are registered in src/main.py to avoid circular imports.