"""
Pytest configuration for the Regional Economic Analysis Platform.

Ensures the project root is on sys.path so ``import backend.api`` works
regardless of where pytest is invoked from.
"""

import os
import sys
from pathlib import Path

# Project root is the parent of the tests/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure default settings
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
