"""
鉴权工具:创建/校验 JWT,提供 FastAPI 依赖。
"""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config.settings import settings

# tokenUrl 必须能拿到表单式的 login 端点(用于 Swagger 的 Authorize 按钮)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict:
    """
    严格校验:任何错误都 401。
    注意:被 verify_token 引用时已经通过 oauth2_scheme 拿到非空 token。
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict | None:
    """
    软依赖:无 token 时返回 None,不强制 401。
    适合 GET 类公开读接口,需要时由 `require_user` 严格校验。
    """
    if not token:
        return None
    return verify_token(token)


def require_user(user: dict | None = Depends(get_current_user)) -> dict:
    """
    硬依赖:用于写操作和敏感读,无 token 直接 401。
    用法: def write_endpoint(_: dict = Depends(require_user)): ...
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
