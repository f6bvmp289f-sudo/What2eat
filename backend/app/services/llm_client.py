"""
MiniMax LLM client 封装
- 同步 / 异步 OpenAI 兼容 SDK（base_url 指向 MiniMax）
- 提供 chat_text / chat_vision 两个核心方法
"""
import json
from typing import Any

from loguru import logger
from openai import AsyncOpenAI, OpenAI

from app.config import settings

_client: OpenAI | None = None
_async_client: AsyncOpenAI | None = None


def init_llm_clients() -> None:
    """在 FastAPI lifespan 启动时调用，初始化同步/异步 client。

    异步客户端额外传 default_headers（Authorization）以兼容 MiniMax 私有端点：
    openai==1.55.0 的 AsyncOpenAI 在 base_url 指向 api.minimaxi.com 时
    默认不发出 Authorization header（同步客户端正常），导致服务端返回 1004。
    """
    global _client, _async_client
    _client = OpenAI(
        api_key=settings.MiniMax_API_KEY,
        base_url=settings.MiniMax_BASE_URL,
        timeout=120.0,
    )
    _async_client = AsyncOpenAI(
        api_key=settings.MiniMax_API_KEY,
        base_url=settings.MiniMax_BASE_URL,
        timeout=120.0,
        default_headers={"Authorization": f"Bearer {settings.MiniMax_API_KEY}"},
    )
    logger.info(f"MiniMax client 初始化完成 base_url={settings.MiniMax_BASE_URL}")


def get_client() -> OpenAI:
    if _client is None:
        init_llm_clients()
    return _client


def get_async_client() -> AsyncOpenAI:
    if _async_client is None:
        init_llm_clients()
    return _async_client


# ===== 核心 API =====

async def chat_text(
    system: str,
    user: str,
    *,
    json_mode: bool = True,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    model: str | None = None,
) -> str:
    """纯文本对话（支持 JSON 模式）。

    返回 LLM 的文本输出。
    `model` 不传时用 settings.MiniMax_TEXT_MODEL_TUTORIAL（默认）。
    """
    client = get_async_client()
    kwargs: dict[str, Any] = {
        "model": model or settings.MiniMax_TEXT_MODEL_TUTORIAL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


async def chat_vision(
    system: str,
    user: str,
    images_b64: list[str],
    *,
    temperature: float = 0.5,
    max_tokens: int = 1024,
) -> str:
    """多模态对话：纯文本 + 1~N 张 base64 图片。

    images_b64 应该是完整 data URI：data:image/jpeg;base64,xxx
    """
    client = get_async_client()

    user_content: list[dict[str, Any]] = [{"type": "text", "text": user}]
    for img_b64 in images_b64:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": img_b64},
            }
        )

    response = await client.chat.completions.create(
        model=settings.MiniMax_TEXT_MODEL_TUTORIAL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


# ===== JSON 解析助手 =====

def parse_json_safely(raw: str) -> dict:
    """LLM 输出的 JSON 解析（带宽松策略：去 markdown code fence、找首个 { / [）。

    解析失败抛 ValueError，调用方应重试。
    """
    s = raw.strip()
    # 去除 <think>...</think> 推理块（MiniMax M2.7 偶尔输出）
    import re
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.DOTALL).strip()
    # 去除 markdown ```json ... ```
    if s.startswith("```"):
        lines = s.split("\n")
        # 去掉第一行 ```json 或 ```
        lines = lines[1:]
        # 去掉最后一行 ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()

    # 直接尝试
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    # 提取第一个 { 或 [ 到末尾
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = s.find(start_char)
        if start == -1:
            continue
        end = s.rfind(end_char)
        if end == -1 or end <= start:
            continue
        candidate = s[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"无法解析 LLM 输出为 JSON: {raw[:200]}")
