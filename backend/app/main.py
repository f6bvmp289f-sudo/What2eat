"""
开饭后端 FastAPI 入口
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.exceptions import register_exception_handlers
from app.logging_config import setup_logging
from app.routers import generate, health
from app.services.llm_client import init_llm_clients


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """启动：初始化日志 + LLM client。关闭：清理（如有）。"""
    setup_logging(settings.LOG_LEVEL, json_mode=False)
    logger.info("=== 开饭后端启动 ===")
    try:
        init_llm_clients()
    except Exception as e:
        logger.exception(f"LLM client 初始化失败: {e}")
        # 不阻断启动，让 /ready 端点能返回 not_ready
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
    max_age=3600,
)

# ===== 异常处理 =====
register_exception_handlers(app)

# ===== 路由 =====
app.include_router(health.router, tags=["health"])
app.include_router(generate.router, tags=["generate"])


@app.get("/")
async def root() -> dict:
    return {
        "name": "开饭 Backend",
        "version": "0.1.0",
        "endpoints": ["/health", "/ready", "/api/generate/stream", "/docs"],
    }
