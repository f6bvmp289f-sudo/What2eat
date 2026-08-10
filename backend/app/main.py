"""
开饭后端 FastAPI 入口
"""
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.db import get_db_path, init_db
from app.exceptions import register_exception_handlers
from app.logging_config import setup_logging
from app.routers import auth as auth_router
from app.routers import favorites as favorites_router
from app.routers import generate, health, history as history_router
from app.services.llm_client import init_llm_clients


def _ensure_jwt_secret() -> None:
    """首次启动若 JWT_SECRET 为空，自动生成并写入 .env（保证重启后 token 仍有效）。"""
    if settings.JWT_SECRET:
        return
    new_secret = secrets.token_urlsafe(48)
    settings.JWT_SECRET = new_secret

    env_path = Path(__file__).resolve().parent.parent / ".env"
    try:
        # 如果 .env 已存在，追加；否则新建
        mode = "a" if env_path.exists() else "w"
        with env_path.open(mode, encoding="utf-8") as f:
            if mode == "a":
                f.write("\n")
            f.write(f"JWT_SECRET={new_secret}\n")
        logger.info("JWT_SECRET 自动生成并写入 .env（请妥善保管 .env）")
    except Exception as e:
        logger.warning(f"JWT_SECRET 写入 .env 失败: {e}（重启后已登录用户需重新登录）")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """启动：初始化日志 + LLM client + DB + JWT secret。关闭：清理（如有）。"""
    setup_logging(settings.LOG_LEVEL, json_mode=False)
    logger.info("=== 开饭后端启动 ===")
    try:
        _ensure_jwt_secret()
        init_db()
    except Exception as e:
        logger.exception(f"启动初始化失败: {e}")
        # 不阻断启动
    try:
        init_llm_clients()
    except Exception as e:
        logger.exception(f"LLM client 初始化失败: {e}")
        # 不阻断启动，让 /ready 端点能返回 not_ready
    logger.info(f"SQLite path: {get_db_path()}")
    yield
    logger.info("=== 开饭后端关闭 ===")


app = FastAPI(
    title="开饭 Backend",
    description="AI 做饭助手后端 - 菜谱生成、意图识别、配图",
    version="0.1.0",
    lifespan=lifespan,
)

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*Authorization"],  # 让前端能从响应头读 token（备用）
    max_age=3600,
)

# ===== 异常处理 =====
register_exception_handlers(app)

# ===== 路由 =====
app.include_router(health.router, tags=["health"])
app.include_router(generate.router, tags=["generate"])
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(history_router.router, prefix="/api/history", tags=["history"])
app.include_router(favorites_router.router, prefix="/api/favorites", tags=["favorites"])


@app.get("/")
async def root() -> dict:
    return {
        "name": "开饭 Backend",
        "version": "0.1.0",
        "endpoints": [
            "/health",
            "/ready",
            "/api/generate/stream",
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/me",
            "/api/history",
            "/api/favorites",
            "/docs",
        ],
    }
