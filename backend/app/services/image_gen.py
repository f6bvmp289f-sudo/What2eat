"""
菜品配图生成：调用 MiniMax-image-01
按 PRD §3.2.3.1 视觉规范：白底高级白盘俯拍
"""
import asyncio
import json
from typing import Optional

import httpx
from loguru import logger

from app.config import settings
from app.services.llm_client import parse_json_safely
from app.services.prompts import DISH_IMAGE_PROMPT_TEMPLATE


async def generate_dish_image(dish_name: str, ingredients: list[str] | None = None) -> Optional[str]:
    """生成一张菜品配图，返回 URL（可能临时有效）。

    失败返回 None（前端会用占位，不阻塞主流程）。
    内部：1 次重试，避免 image-01 偶发慢响应超时。

    A/B 测试结论（2026-07-30）：加 mainIngredients 让图更准，且速度几乎无差异。
    """
    # 拼接 prompt：菜名 + (可选) mainIngredients
    if ingredients:
        ingredients_text = " with " + ", ".join(ingredients)
    else:
        ingredients_text = ""
    prompt = DISH_IMAGE_PROMPT_TEMPLATE.format(
        dish_name=dish_name,
        ingredients=ingredients_text,
    )
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

    # 1 次重试（image-01 偶尔慢）
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            # MiniMax 响应格式：{"data": {"image_urls": [...]}}  或  {"image_url": "..."}
            # 兼容两种
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

            # 备选：直接解析
            if data.get("image_url"):
                return data["image_url"]

            logger.warning(f"MiniMax image-01 返回格式未识别 (attempt {attempt+1}): {data}")
            return None  # 格式不对就别重试了
        except Exception as e:
            logger.warning(f"生成菜品图失败 attempt {attempt+1}/2: {dish_name!r}, error={type(e).__name__}: {e}")
            if attempt == 1:
                logger.exception(f"重试后仍失败: {dish_name!r}")
                return None
            # 继续重试
    return None
