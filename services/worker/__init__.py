"""
Worker package bootstrap.

Adds the API service root to the import path so worker modules can reuse
the backend domain and infrastructure code.
"""

from pathlib import Path
import sys

API_ROOT = Path(__file__).resolve().parents[1] / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))