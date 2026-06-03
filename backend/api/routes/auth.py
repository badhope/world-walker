import hmac
import os

from fastapi import APIRouter, HTTPException

from backend.api.auth import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
def login(username: str, password: str):
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "")
    if not admin_pass:
        raise HTTPException(status_code=500, detail="Admin password not configured")
    # Use constant-time comparison to avoid timing attacks on credentials
    user_ok = hmac.compare_digest(username, admin_user)
    pass_ok = hmac.compare_digest(password, admin_pass)
    if not (user_ok and pass_ok):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": username})
    return {"access_token": token, "token_type": "bearer"}
