"""
Local conftest.py for fuzz tests.
Adds the project root to sys.path BEFORE the test module is imported,
ensuring `from backend.api.main import app` works.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """Hook to ensure sys.path is set early."""
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
