import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.auth import create_access_token
from backend.api.limiter import limiter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", summary="管理员登录(返回 JWT)")
@limiter.limit("5/minute")  # 每分钟最多 5 次,防暴力破解
def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    接收 application/x-www-form-urlencoded 或 multipart/form-data,
    强制走 body,密码不进 URL/log。
    OAuth2PasswordRequestForm 字段:username / password / grant_type / scope
    """
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "")
    if not admin_pass:
        # 未配置口令时直接 503,而不是 500,更符合语义
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin password not configured; set ADMIN_PASSWORD env",
        )
    user_ok = hmac.compare_digest(form.username or "", admin_user)
    pass_ok = hmac.compare_digest(form.password or "", admin_pass)
    if not (user_ok and pass_ok):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": admin_user})
    return {"access_token": token, "token_type": "bearer"}
