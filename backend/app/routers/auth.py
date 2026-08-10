"""
账号路由
- POST /api/auth/register  用户名+密码注册，返回 token
- POST /api/auth/login     用户名+密码登录，返回 token
- GET  /api/auth/me        当前用户信息（需登录）
"""
import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import (
    CurrentUser,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db import get_db

router = APIRouter()


# ===== 请求 / 响应 =====


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=64)


class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=64)


class AuthResponse(BaseModel):
    token: str
    user: "UserInfo"


class UserInfo(BaseModel):
    id: int
    username: str
    created_at: int


AuthResponse.model_rebuild()


# ===== 路由 =====


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest) -> AuthResponse:
    """注册：用户名 2-32 字、密码 6-64 位。返回 access token。"""
    username = req.username.strip()
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名不能为空",
        )
    password_hash, password_salt = hash_password(req.password)
    now = int(time.time() * 1000)
    with get_db() as conn:
        # 检查是否已存在
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该用户名已被注册",
            )
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, password_salt, created_at) "
            "VALUES (?, ?, ?, ?)",
            (username, password_hash, password_salt, now),
        )
        user_id = cur.lastrowid

    token = create_access_token(user_id)
    return AuthResponse(
        token=token,
        user=UserInfo(id=user_id, username=username, created_at=now),
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest) -> AuthResponse:
    """登录：校验用户名 + 密码，返回 access token。"""
    username = req.username.strip()
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, password_salt, created_at "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not verify_password(req.password, row["password_hash"], row["password_salt"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    token = create_access_token(row["id"])
    return AuthResponse(
        token=token,
        user=UserInfo(
            id=row["id"],
            username=row["username"],
            created_at=row["created_at"],
        ),
    )


@router.get("/me", response_model=UserInfo)
async def me(current: CurrentUser = Depends(get_current_user)) -> UserInfo:
    """当前登录用户信息。"""
    return UserInfo(
        id=current.id,
        username=current.username,
        created_at=current.created_at,
    )