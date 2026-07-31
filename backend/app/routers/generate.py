"""
菜谱生成端点：POST /api/generate/stream
SSE 流式响应，前端通过 ReadableStream 解析。
"""
import asyncio
import json
import time

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from loguru import logger

from app.schemas import GenerateRequest, ProgressEvent
from app.services.orchestrator import orchestrate

router = APIRouter()

# SSE 心跳间隔（秒）
HEARTBEAT_INTERVAL = 15.0


def _sse_format(event: ProgressEvent) -> bytes:
    """SSE 协议：event: <stage>\ndata: <json>\n\n"""
    return f"event: {event.stage}\ndata: {event.model_dump_json()}\n\n".encode("utf-8")


def _sse_heartbeat() -> bytes:
    """SSE 心跳：注释行，浏览器忽略但保持连接"""
    return b": heartbeat\n\n"


@router.post("/api/generate/stream")
async def generate_stream(req: GenerateRequest, request: Request) -> StreamingResponse:
    """接收 {images, text}，流式返回菜谱生成进度。"""

    async def event_generator():
        # 客户端断开检测：检查 request.is_disconnected()
        # 心跳任务
        heartbeat_task: asyncio.Task | None = None

        async def heartbeat_loop(stop_event: asyncio.Event):
            try:
                while not stop_event.is_set():
                    await asyncio.sleep(HEARTBEAT_INTERVAL)
                    if stop_event.is_set():
                        return
                    yield _sse_heartbeat()
            except asyncio.CancelledError:
                return

        async def emit(event: ProgressEvent) -> None:
            # 客户端断开检查
            if await request.is_disconnected():
                logger.info("客户端断开，停止生成")
                raise asyncio.CancelledError("client disconnected")

            data = _sse_format(event)
            # 这里通过一个中间 queue 传递
            await _event_queue.put(data)
            if event.stage in ("done", "error"):
                # 最终事件后停止心跳
                _stop_event.set()

        # 简单实现：先跑完编排，最后 yield 全部事件
        # 心跳用一个 task 在编排期间定时 yield
        # 缺点：心跳不能真正异步 yield，简化做法是丢弃心跳（MVP 阶段）
        _event_queue: asyncio.Queue = asyncio.Queue()
        _stop_event = asyncio.Event()

        async def run_orchestrator():
            try:
                await orchestrate(req, emit)
            except asyncio.CancelledError:
                logger.info("编排被取消（客户端断开）")
            except Exception as e:
                logger.exception(f"编排异常: {e}")
                await emit(
                    ProgressEvent(
                        stage="error",
                        code="INTERNAL_ERROR",
                        message=f"内部错误: {e}",
                    )
                )

        # MVP 简化：先跑编排，每 200ms 检查一次队列
        orch_task = asyncio.create_task(run_orchestrator())
        try:
            while not orch_task.done() or not _event_queue.empty():
                # 心跳
                yield _sse_heartbeat()
                # 等待事件（短超时）
                try:
                    data = await asyncio.wait_for(_event_queue.get(), timeout=HEARTBEAT_INTERVAL)
                    yield data
                except asyncio.TimeoutError:
                    # 超时，循环继续（再发心跳）
                    continue
        finally:
            if not orch_task.done():
                orch_task.cancel()
                try:
                    await orch_task
                except (asyncio.CancelledError, Exception):
                    pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 防止 nginx 缓冲
        },
    )


@router.post("/api/regenerate")
async def regenerate(req: GenerateRequest) -> dict:
    """MVP 占位：换一批菜（清空缓存 + 重新生成）"""
    # MVP 阶段：前端直接清 store + 重新调 /generate/stream
    return {"code": "OK", "message": "前端请清空 dishStore.currentScheme 后重新调 /api/generate/stream"}
