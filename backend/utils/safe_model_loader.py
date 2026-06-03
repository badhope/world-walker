"""
Model loading with integrity verification.

When you load a `.pkl` / `.joblib` file, you are executing arbitrary Python
code. This module provides a single safe entry point:

    from backend.utils.safe_model_loader import load_model
    model = load_model("models/random_forest.pkl")

It will:
  1. Verify the SHA-256 hash of the file against `models/SHA256SUMS`
     (unless `verify=False`, which is **not** recommended in production).
  2. Reject the file if any of:
     - the hash does not match
     - the file is not listed in `SHA256SUMS`
     - the file size exceeds `MAX_MODEL_SIZE_MB`
  3. Only then call `joblib.load()`.

This mitigates CVE-class risks such as arbitrary code execution
when a malicious .pkl is substituted in transit / via supply chain.

For HMAC-style signing (release artefacts), see
`backend.utils.model_security.load_with_signature`.

Reference: https://docs.python.org/3/library/pickle.html#restricting-globals
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Models > 100 MB are very unusual for this codebase; flag suspicious files.
MAX_MODEL_SIZE_MB = 100
MAX_MODEL_SIZE_BYTES = MAX_MODEL_SIZE_MB * 1024 * 1024

# Default path to the SHA-256 manifest committed to the repo.
DEFAULT_SHA256SUMS_PATH = Path(__file__).resolve().parents[2] / "models" / "SHA256SUMS"


def _compute_sha256(filepath: Path, chunk_size: int = 1 << 20) -> str:
    """Compute the SHA-256 of a file using 1 MiB streaming chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _load_sha256sums(manifest: Path) -> dict[str, str]:
    """Parse a `sha256sum`-style manifest into {filename: hex_digest}."""
    if not manifest.exists():
        raise FileNotFoundError(
            f"SHA-256 manifest not found at {manifest}. "
            f"Either commit it (recommended) or set ALLOW_UNVERIFIED_MODELS=1."
        )
    out: dict[str, str] = {}
    with open(manifest, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            digest, name = parts
            out[name.strip()] = digest.strip().lower()
    return out


def verify_model_integrity(
    filepath: str | Path,
    manifest: Path | None = None,
) -> bool:
    """
    Check the file against the SHA-256 manifest. Returns True on success,
    raises ValueError on mismatch. Allows override via env var
    `ALLOW_UNVERIFIED_MODELS=1` (use only for development).
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    size = path.stat().st_size
    if size > MAX_MODEL_SIZE_BYTES:
        raise ValueError(
            f"Model {path} is {size / 1024 / 1024:.1f} MB, exceeds "
            f"MAX_MODEL_SIZE_MB={MAX_MODEL_SIZE_MB} (possible zip-bomb / RCE)."
        )

    if os.getenv("ALLOW_UNVERIFIED_MODELS") == "1":
        logger.warning(
            "ALLOW_UNVERIFIED_MODELS=1 set; skipping SHA-256 verification for %s",
            path,
        )
        return True

    manifest = manifest or DEFAULT_SHA256SUMS_PATH
    sums = _load_sha256sums(manifest)
    name = path.name
    if name not in sums:
        raise ValueError(f"Model {name!r} is not listed in {manifest}. Refusing to load an unverified model.")

    actual = _compute_sha256(path)
    expected = sums[name].lower()
    if not _consteq(actual, expected):
        raise ValueError(f"SHA-256 mismatch for {name}: expected {expected}, got {actual}.")
    return True


def _consteq(a: str, b: str) -> bool:
    """Constant-time string comparison to avoid timing side-channels."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def load_model(
    filepath: str | Path,
    *,
    verify: bool = True,
    manifest: Path | None = None,
) -> Any:
    """
    Load a scikit-learn / joblib model with SHA-256 integrity verification.

    >>> from backend.utils.safe_model_loader import load_model
    >>> m = load_model("models/linear_regression.pkl")
    """
    import joblib  # local import: joblib is heavy, defer until needed

    path = Path(filepath)
    if verify:
        verify_model_integrity(path, manifest=manifest)
    return joblib.load(path)


__all__ = [
    "load_model",
    "verify_model_integrity",
    "DEFAULT_SHA256SUMS_PATH",
    "MAX_MODEL_SIZE_MB",
]
