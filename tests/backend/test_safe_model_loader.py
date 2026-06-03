"""
Unit tests for backend.utils.safe_model_loader.

Covers the four security properties we promise in the module docstring:
  T1: legitimate model (hash matches) loads.
  T2: model file not listed in SHA256SUMS is rejected.
  T3: tampered model (hash mismatch) is rejected.
  T4: model file larger than MAX_MODEL_SIZE_MB is rejected.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from backend.utils.safe_model_loader import (
    DEFAULT_SHA256SUMS_PATH,
    MAX_MODEL_SIZE_MB,
    load_model,
)

REPO_MODELS = Path(__file__).resolve().parents[2] / "models"


@pytest.fixture
def temp_manifest(tmp_path: Path) -> Path:
    """Create a temporary SHA-256 manifest pointing at a real model file."""
    src = REPO_MODELS / "linear_regression.pkl"
    dst = tmp_path / "linear_regression.pkl"
    shutil.copy(src, dst)
    import hashlib

    digest = hashlib.sha256(dst.read_bytes()).hexdigest()
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text(f"{digest}  linear_regression.pkl\n", encoding="utf-8")
    return manifest


def test_legitimate_model_loads(temp_manifest: Path) -> None:
    """T1: file listed in manifest with matching hash must load."""
    model_path = temp_manifest.parent / "linear_regression.pkl"
    obj = load_model(model_path, manifest=temp_manifest)
    assert obj is not None


def test_unlisted_model_rejected(tmp_path: Path) -> None:
    """T2: file not listed in manifest must be rejected."""
    src = REPO_MODELS / "linear_regression.pkl"
    target = tmp_path / "rogue.pkl"
    shutil.copy(src, target)
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="not listed"):
        load_model(target, manifest=manifest)


def test_tampered_model_rejected(temp_manifest: Path) -> None:
    """T3: file whose content changed after manifest was written must be rejected."""
    model_path = temp_manifest.parent / "linear_regression.pkl"
    with open(model_path, "ab") as fh:
        fh.write(b"\x00\x00tampered")
    with pytest.raises(ValueError, match="mismatch"):
        load_model(model_path, manifest=temp_manifest)
    # Restore for hygiene (fixture cleanup)
    REPO_FILE = REPO_MODELS / "linear_regression.pkl"
    if REPO_FILE.exists():
        # copy back the original bytes
        with open(model_path, "wb") as fh:
            fh.write(REPO_FILE.read_bytes())


def test_oversized_model_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4: file larger than MAX_MODEL_SIZE_MB must be rejected."""
    # Create a 1-byte file but pretend the cap is 0 bytes
    src = REPO_MODELS / "linear_regression.pkl"
    target = tmp_path / "tiny.pkl"
    shutil.copy(src, target)
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text(f"{'a' * 64}  tiny.pkl\n", encoding="utf-8")
    monkeypatch.setattr("backend.utils.safe_model_loader.MAX_MODEL_SIZE_BYTES", 0)
    with pytest.raises(ValueError, match="exceeds"):
        load_model(target, manifest=manifest)


def test_default_manifest_exists() -> None:
    """The committed SHA256SUMS file must exist at DEFAULT_SHA256SUMS_PATH."""
    assert DEFAULT_SHA256SUMS_PATH.exists(), (
        f"models/SHA256SUMS not found at {DEFAULT_SHA256SUMS_PATH}. Run: cd models && sha256sum *.pkl > SHA256SUMS"
    )


def test_default_manifest_covers_all_pkl() -> None:
    """Every .pkl in models/ must be listed in SHA256SUMS."""
    sums_lines = DEFAULT_SHA256SUMS_PATH.read_text(encoding="utf-8").splitlines()
    listed = {line.split(None, 1)[1].strip() for line in sums_lines if line.strip()}
    actual = {p.name for p in REPO_MODELS.glob("*.pkl")}
    missing = actual - listed
    extra = listed - actual
    assert not missing, f"Missing from SHA256SUMS: {missing}"
    assert not extra, f"Listed but file missing: {extra}"


def test_constant_time_comparison() -> None:
    """_consteq must reject mismatches of any length without leaking via short-circuit."""
    from backend.utils.safe_model_loader import _consteq

    assert _consteq("abc", "abc") is True
    assert _consteq("abc", "abd") is False
    assert _consteq("abc", "abcd") is False  # length differs → False
    assert _consteq("", "") is True


def test_allow_unverified_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ALLOW_UNVERIFIED_MODELS=1 lets the load through with only a warning."""
    src = REPO_MODELS / "linear_regression.pkl"
    target = tmp_path / "unlisted.pkl"
    shutil.copy(src, target)
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text("", encoding="utf-8")

    monkeypatch.setenv("ALLOW_UNVERIFIED_MODELS", "1")
    obj = load_model(target, manifest=manifest)
    assert obj is not None


def test_max_model_size_constant_reasonable() -> None:
    """Sanity check the constant is not absurdly small or large."""
    assert 1 <= MAX_MODEL_SIZE_MB <= 1024
