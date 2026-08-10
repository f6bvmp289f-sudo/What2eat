"""
菜品配图生成：双通道策略
- 主通道：MiniMax image-01（私有 image_generation 端点，保持现有行为）
- 降级通道：阿里云百炼 DashScope 文生图（用 dashscope SDK，调 z-image-turbo）
- 都失败：返回 None → 前端占位图，不阻塞主流程

按 PRD §3.2.3.1 视觉规范：白底高级白盘俯拍
"""
from typing import Optional

import httpx
from loguru import logger

from app.config import settings
from app.services.prompts import DISH_IMAGE_PROMPT_TEMPLATE


def _build_prompt(dish_name: str, ingredients: list[str] | None) -> str:
    """拼接生图 prompt：菜名 + (可选) mainIngredients。"""
    if ingredients:
        ingredients_text = " with " + ", ".join(ingredients)
    else:
        ingredients_text = ""
    return DISH_IMAGE_PROMPT_TEMPLATE.format(
        dish_name=dish_name,
        ingredients=ingredients_text,
    )


async def _try_minimax_image(prompt: str) -> Optional[str]:
    """调 MiniMax image-01，返回 URL 或 None（带 1 次重试）。

    私有 image_generation 端点（非 OpenAI 兼容协议）。
    """
    payload = {
        "model": settings.MiniMax_IMAGE_MODEL,
        "prompt": prompt,
        "n": 1,
    }
    headers = {
        "Authorization": f"Bearer {settings.MiniMax_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{settings.MiniMax_BASE_URL}/image_generation"

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            # MiniMax 响应格式：{"data": {"image_urls": [...]}}  或  {"image_url": "..."}
            # 兼容多种结构
            if isinstance(data.get("data"), dict):
                urls = data["data"].get("image_urls") or data["data"].get("image_url")
                if isinstance(urls, list) and urls:
                    return urls[0]
                if isinstance(urls, str):
                    return urls
            elif isinstance(data.get("data"), list) and data["data"]:
                first = data["data"][0]
                if isinstance(first, dict):
                    return first.get("url") or first.get("image_url")
                if isinstance(first, str):
                    return first
            elif data.get("image_url"):
                return data["image_url"]

            logger.warning(f"MiniMax image-01 返回格式未识别 (attempt {attempt+1}): {data}")
            return None  # 格式不对就别重试了
        except Exception as e:
            logger.warning(
                f"MiniMax 生图失败 attempt {attempt+1}/2: error={type(e).__name__}: {e}"
            )
    return None


async def _try_dashscope_image(prompt: str) -> Optional[str]:
    """调 DashScope z-image-turbo（直接 HTTP API）。

    z-image-turbo 等新模型走 multimodal-generation 服务。
    真实 URL: https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
    请求体格式：messages 风格（content 必须是 list of dict）。
    返回结构：output.choices[0].message.content 是 list，每项可能是 {"image": url} 或 {"text": "..."}。
    """
    url = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/"
        "multimodal-generation/generation"
    )
    payload = {
        "model": "z-image-turbo",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ]
        },
        "parameters": {"size": "1024*1024", "n": 1},
    }
    headers = {
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning(f"DashScope 提交失败: {type(e).__name__}: {e}")
        return None

    # 解析 output.choices[0].message.content 列表（OpenAI 多模态格式）
    output = data.get("output") or {}
    choices = output.get("choices") or []
    for choice in choices:
        msg = choice.get("message") or {}
        content = msg.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "image" in item:
                    return item["image"]
        elif isinstance(content, dict) and "image" in content:
            return content["image"]

    # 兼容老 SDK 格式
    results = output.get("results") or []
    if isinstance(results, list) and results:
        first = results[0]
        if isinstance(first, dict):
            return first.get("url") or first.get("image")

    logger.warning(f"DashScope 响应无 image 字段: {data}")
    return None


async def generate_dish_image(
    dish_name: str, ingredients: list[str] | None = None
) -> Optional[str]:
    """生成一张菜品配图，返回 URL（可能临时有效）。

    失败返回 None（前端会用占位，不阻塞主流程）。
    通道顺序：MiniMax image-01 → DashScope z-image-turbo（云端降级，目前禁用）。
    """
    prompt = _build_prompt(dish_name, ingredients)

    # 主通道：MiniMax image-01
    url = await _try_minimax_image(prompt)
    if url:
        return url

    # ===== DashScope 降级通道暂不启用（用户要求）=====
    # if settings.DASHSCOPE_API_KEY:
    #     logger.info(f"MiniMax 生图失败，降级到 DashScope z-image-turbo: {dish_name!r}")
    #     url = await _try_dashscope_image(prompt)
    #     if url:
    #         return url
    # =================================================

    logger.warning(f"MiniMax 生图失败，无降级通道: {dish_name!r}")
    return None