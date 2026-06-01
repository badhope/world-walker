import hmac
import hashlib
import os
import joblib


def _get_signing_key():
    key_str = os.getenv("MODEL_SIGNING_KEY", "")
    if key_str:
        return key_str.encode("utf-8")
    return None


def _compute_hmac(filepath: str, key: bytes) -> str:
    h = hmac.new(key, digestmod=hashlib.sha256)
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def save_with_signature(obj, filepath: str, key: bytes | None = None):
    if key is None:
        key = _get_signing_key()
    joblib.dump(obj, filepath)
    if key:
        sig = _compute_hmac(filepath, key)
        with open(filepath + '.sig', 'w') as f:
            f.write(sig)


def load_with_signature(filepath: str, key: bytes | None = None):
    if key is None:
        key = _get_signing_key()
    if key:
        sig_path = filepath + '.sig'
        if not os.path.exists(sig_path):
            raise ValueError(f"Missing signature file for: {filepath}")
        with open(sig_path) as f:
            expected = f.read().strip()
        actual = _compute_hmac(filepath, key)
        if not hmac.compare_digest(expected, actual):
            raise ValueError(f"Model signature verification failed for: {filepath}")
    return joblib.load(filepath)