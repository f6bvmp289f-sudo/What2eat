"""
健康检查端点
- GET /health: 进程存活（liveness）
- GET /ready: 服务就绪（readiness，包括 LLM 客户端可用性）
"""
import asyncio

from fastapi import APIRouter
from openai import AsyncOpenAI

from app.config import settings
from app.services.llm_client import get_async_client

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """liveness：只要进程在就返回 200"""
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    """readiness：检查 LLM client 是否可用"""
    try:
        client = get_async_client()
        # 简单 ping：调用 models list（不消耗 token）
        # 用 asyncio.wait_for 加超时
        await asyncio.wait_for(
            client.models.list(),
            timeout=5.0,
        )
        return {
            "status": "ready",
            "model": settings.MiniMax_TEXT_MODEL_TUTORIAL,
            "base_url": settings.MiniMax_BASE_URL,
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e)[:200],
        }
