"""
鉴权相关工具：
- 密码哈希（pbkdf2_hmac，标准库，无外部依赖）
- JWT 编解码（PyJWT）
- FastAPI 依赖：get_current_user / get_current_user_optional
"""
import hashlib
import hmac
import os
import secrets
import time
from typing import Any, Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.db import get_db


# ===== 密码 =====

# pbkdf2 迭代次数（OWASP 2023 推荐 ≥ 600000；为了快速登录用 200000 平衡性能）
_PBKDF2_ITERATIONS = 200_000
_SALT_BYTES = 16


def hash_password(password: str) -> tuple[str, str]:
    """返回 (hash_hex, salt_hex)。"""
    salt = secrets.token_bytes(_SALT_BYTES)
    h = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return h.hex(), salt.hex()


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """校验密码。"""
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(hash_hex)
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(expected, actual)


# ===== JWT =====


class TokenPayload(BaseModel):
    """JWT payload"""

    sub: str       # user_id（字符串）
    exp: int       # 过期时间 epoch s
    iat: int       # 签发时间 epoch s


def create_access_token(user_id: int) -> str:
    """签发 access token。"""
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + settings.JWT_EXPIRE_DAYS * 24 * 3600,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> TokenPayload:
    """解析 JWT，失败抛 HTTPException 401。"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的登录凭证",
        )


# ===== 用户数据模型 =====


class CurrentUser(BaseModel):
    """已登录的当前用户（注入到受保护接口）"""

    id: int
    username: str
    created_at: int


def _load_user(user_id: int) -> Optional[CurrentUser]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return CurrentUser(id=row["id"], username=row["username"], created_at=row["created_at"])


# ===== FastAPI 依赖 =====


async def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
) -> Optional[CurrentUser]:
    """可选鉴权：拿不到 token 时返回 None（不抛错），用于需要识别身份但不强制登录的接口。"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    payload = decode_token(token)
    try:
        user_id = int(payload.sub)
    except ValueError:
        return None
    return _load_user(user_id)


async def get_current_user(
    user: Optional[CurrentUser] = Depends(get_current_user_optional),
) -> CurrentUser:
    """强制鉴权：未登录抛 401。"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user