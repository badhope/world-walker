"""
模型签名 / 完整性校验工具。

- 训练侧:`save_with_signature` 必须有 key,否则拒绝保存,避免脏数据下盘。
- 推理侧:`load_with_signature` 必须有 key 且签名文件存在,否则拒绝加载。
- 逃生口:开发环境显式设置 `ALLOW_UNSIGNED_MODELS=1`,本模块会回退到「仅写警告」,
  不会向上抛错,只用于本地实验;生产部署严禁开启。
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os

import joblib

logger = logging.getLogger(__name__)

ENV_SIGNING_KEY = "MODEL_SIGNING_KEY"
ENV_ALLOW_UNSIGNED = "ALLOW_UNSIGNED_MODELS"


def _get_signing_key() -> bytes | None:
    key_str = os.getenv(ENV_SIGNING_KEY, "").strip()
    return key_str.encode("utf-8") if key_str else None


def _unsigned_allowed() -> bool:
    return os.getenv(ENV_ALLOW_UNSIGNED, "").strip().lower() in {"1", "true", "yes", "on"}


def _compute_hmac(filepath: str, key: bytes) -> str:
    h = hmac.new(key, digestmod=hashlib.sha256)
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def save_with_signature(obj, filepath: str, key: bytes | None = None) -> None:
    """
    保存模型并生成 HMAC-SHA256 签名。
    没有任何 key 时,默认直接抛错(防止无签名模型下盘污染生产目录);
    开发环境可设置 `ALLOW_UNSIGNED_MODELS=1` 关闭此校验。
    """
    if key is None:
        key = _get_signing_key()

    if key is None:
        if _unsigned_allowed():
            logger.warning(
                "ALLOW_UNSIGNED_MODELS=1: saving %s WITHOUT signature (dev only).",
                filepath,
            )
            joblib.dump(obj, filepath)
            return
        raise RuntimeError(
            f"Refusing to save model without signature: set {ENV_SIGNING_KEY} "
            f"(production) or {ENV_ALLOW_UNSIGNED}=1 (dev only)."
        )

    joblib.dump(obj, filepath)
    sig = _compute_hmac(filepath, key)
    sig_path = filepath + ".sig"
    with open(sig_path, "w", encoding="utf-8") as f:
        f.write(sig)
    logger.debug("Saved model + signature: %s", filepath)


def load_with_signature(filepath: str, key: bytes | None = None):
    """
    加载模型并强制校验 HMAC 签名。
    无 key 或签名文件缺失/不匹配时,默认抛错;开发环境可设置
    `ALLOW_UNSIGNED_MODELS=1` 关闭此校验。
    """
    if key is None:
        key = _get_signing_key()

    if key is None:
        if _unsigned_allowed():
            logger.warning(
                "ALLOW_UNSIGNED_MODELS=1: loading %s WITHOUT signature verification (dev only).",
                filepath,
            )
            return joblib.load(filepath)
        raise RuntimeError(
            f"Refusing to load model without signature: set {ENV_SIGNING_KEY} "
            f"(production) or {ENV_ALLOW_UNSIGNED}=1 (dev only)."
        )

    sig_path = filepath + ".sig"
    if not os.path.exists(sig_path):
        raise RuntimeError(f"Missing signature file for model: {sig_path}")

    with open(sig_path, encoding="utf-8") as f:
        expected = f.read().strip()
    actual = _compute_hmac(filepath, key)
    if not hmac.compare_digest(expected, actual):
        raise RuntimeError(f"Model signature mismatch for: {filepath}")

    return joblib.load(filepath)


__all__ = [
    "save_with_signature",
    "load_with_signature",
    "ENV_SIGNING_KEY",
    "ENV_ALLOW_UNSIGNED",
]
