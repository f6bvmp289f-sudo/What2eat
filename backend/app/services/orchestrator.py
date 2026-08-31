"""
编排器：端到端菜谱生成主流程
① 意图识别 → ② 概述(菜名清单) → ③ 并行 补全∥教程∥配图 → ④ emit done
"""
import asyncio
import json
import time
from typing import Awaitable, Callable

from loguru import logger

from app.config import settings
from app.schemas import (
    Dish,
    DishScheme,
    DishStep,
    ErrorCode,
    GenerateRequest,
    ProgressEvent,
)
from app.services.cache import get_cache
from app.services.image_gen import generate_dish_image
from app.services.intent import check_intent
from app.services.llm_client import chat_text, parse_json_safely
from app.services.prompts import (
    DISH_DETAIL_SYSTEM,
    SCHEME_OVERVIEW_SYSTEM,
    TUTORIAL_AGENT_SYSTEM,
)


EmitFn = Callable[[ProgressEvent], Awaitable[None]]


# ===== 各阶段 =====


async def stage_intent(req: GenerateRequest, emit: EmitFn) -> tuple[bool, list[str]]:
    """① 意图识别"""
    await emit(ProgressEvent(stage="intent", percent=5, message="正在识别食材…"))
    ok, ingredients = await check_intent(req.images, req.text)
    if not ok:
        await emit(
            ProgressEvent(
                stage="error",
                code=ErrorCode.INGREDIENT_RATIO_LOW,
                message="没看到具体食材哦～请上传买菜清单或描述你想吃的菜",
            )
        )
        return False, []
    msg = "、".join(ingredients[:5]) if ingredients else "已识别"
    await emit(
        ProgressEvent(
            stage="intent",
            percent=15,
            message=f"识别完成：{msg}",
        )
    )
    return True, ingredients


async def stage_overview(
    ingredients: list[str],
    user_text: str,
    emit: EmitFn,
    history_dish_names: list[str] | None = None,
) -> dict:
    """② 主 agent 出菜名清单（快速，不含详细字段）

    history_dish_names：换一批模式下的"已生成菜名"，拼到 user_msg 让 LLM 避免重复。
    """
    await emit(ProgressEvent(stage="scheme", percent=25, message="正在设计菜谱方案…"))

    user_msg_parts = [
        f"【用户食材】{', '.join(ingredients) if ingredients else '（未提供）'}",
        f"【用户意图】{user_text or '（未提供文字）'}",
    ]
    if history_dish_names:
        user_msg_parts.append(
            f"【已生成菜名（请避免重复）】{', '.join(history_dish_names)}"
        )
    user_msg_parts.append("请输出严格 JSON。")
    user_msg = "\n".join(user_msg_parts)

    raw = await chat_text(
        system=SCHEME_OVERVIEW_SYSTEM,
        user=user_msg,
        json_mode=True,
        temperature=0.7,
        max_tokens=1200,  # 只出菜名清单，token 需求小
        model=settings.MiniMax_TEXT_MODEL_MAIN,  # 方案概述用 M2.5（更快）
    )
    logger.debug(f"主 agent 概述输出: {raw[:500]}...")

    data = parse_json_safely(raw)
    # 标准化 dish 基本字段（详细字段由 stage_detail 补全）
    for i, d in enumerate(data.get("dishes", [])):
        d.setdefault("id", f"dish-{i + 1}")
        d.setdefault("name", "")
        d.setdefault("taste", "")
        d.setdefault("cookingMethod", "")
        d.setdefault("mainIngredients", [])

    await emit(
        ProgressEvent(
            stage="scheme",
            percent=45,
            message=f"方案已出炉（{len(data.get('dishes', []))} 道菜）",
        )
    )
    return data


async def stage_detail(dish: dict) -> tuple[dict, float]:
    """菜信息补全：description / estimatedTime / difficulty

    放在并行阶段跑，不占主链。返回 (detail, 耗时秒)。
    """
    t0 = time.time()
    user_msg = (
        f"【菜品】{json.dumps({k: dish.get(k) for k in ('name', 'taste', 'cookingMethod', 'mainIngredients')}, ensure_ascii=False)}\n"
        f"请输出严格 JSON。"
    )
    raw = await chat_text(
        system=DISH_DETAIL_SYSTEM,
        user=user_msg,
        json_mode=True,
        temperature=0.5,
        max_tokens=400,
        model=settings.MiniMax_TEXT_MODEL_MAIN,
    )
    data = parse_json_safely(raw)
    return {
        "description": data.get("description", ""),
        "estimatedTime": data.get("estimatedTime", ""),
        "difficulty": data.get("difficulty", ""),
    }, time.time() - t0


async def stage_tutorial(dish: dict, emit: EmitFn) -> tuple[list[DishStep], float]:
    """教程 agent：单道菜详细步骤

    返回 (steps, 耗时秒)
    """
    dish_name = dish.get("name", "未知菜品")
    dish_id = dish.get("id", "")

    t0 = time.time()
    user_msg = (
        f"【菜品方案】{json.dumps(dish, ensure_ascii=False)}\n"
        f"请输出严格 JSON。"
    )

    raw = await chat_text(
        system=TUTORIAL_AGENT_SYSTEM,
        user=user_msg,
        json_mode=True,
        temperature=0.6,
        max_tokens=2048,
    )
    data = parse_json_safely(raw)
    steps_raw = data.get("steps", [])
    steps: list[DishStep] = []
    for i, s in enumerate(steps_raw):
        steps.append(
            DishStep(
                index=i,
                title=s.get("title", f"步骤 {i + 1}"),
                description=s.get("description", ""),
                hasTimer=bool(s.get("hasTimer", False)),
                timerSeconds=s.get("timerSeconds"),
                substeps=s.get("substeps", []) or [],
            )
        )
    return steps, time.time() - t0


async def stage_image(dish: dict, emit: EmitFn) -> tuple[str, float]:
    """配图 agent：z-image-turbo 单张菜品图

    返回 (url, 耗时秒)
    """
    dish_name = dish.get("name", "未知菜品")
    dish_id = dish.get("id", "")

    t0 = time.time()
    await emit(
        ProgressEvent(
            stage="image",
            percent=0,
            message=f"正在为「{dish_name}」画配图…",
            dish_id=dish_id,
        )
    )

    # A/B 测试结论：加 mainIngredients 让图更准
    ingredients = dish.get("mainIngredients") or None
    url = await generate_dish_image(dish_name, ingredients)
    elapsed = time.time() - t0

    # 拿到 URL 后立即 push 给前端（渐进替换占位图）
    if url:
        await emit(
            ProgressEvent(
                stage="image",
                percent=80,
                message=f"「{dish_name}」配图已生成",
                dish_id=dish_id,
                url=url,
            )
        )

    if not url:
        url = ""
    return url, elapsed


# ===== 编排主入口 =====


async def orchestrate(req: GenerateRequest, emit: EmitFn) -> None:
    """端到端编排：① 意图 → ② 概述 → ③ 并行 补全∥教程∥配图 → ④ done"""
    started_at = time.time()
    timings: dict[str, float] = {}  # 记录每个 stage 的耗时

    # ① 意图
    t0 = time.time()
    ok, ingredients = await stage_intent(req, emit)
    timings["intent"] = time.time() - t0
    if not ok:
        return

    # ② 方案概述（快速出菜名清单）
    t_scheme_start = time.time()
    try:
        overview = await stage_overview(
            ingredients, req.text, emit,
            history_dish_names=req.history_dish_names or None,
        )
    except ValueError as e:
        logger.warning(f"主 agent JSON 解析失败，重试一次: {e}")
        # 重试一次（重置 t0，重试完成后 timings 算总耗时）
        t0 = time.time()
        try:
            overview = await stage_overview(
                ingredients, req.text, emit,
                history_dish_names=req.history_dish_names or None,
            )
        except Exception as e2:
            logger.exception(f"主 agent 重试仍失败: {e2}")
            await emit(
                ProgressEvent(
                    stage="error",
                    code=ErrorCode.PARSE_ERROR,
                    message="AI 输出格式异常，请重试",
                )
            )
            return
        # 包含重试的总耗时 = 第一次 + 重试
        timings["scheme"] = time.time() - t_scheme_start
    except Exception as e:
        logger.exception(f"主 agent 失败: {e}")
        await emit(
            ProgressEvent(
                stage="error",
                code=ErrorCode.LLM_UNAVAILABLE,
                message="AI 服务暂时不可用，请稍后重试",
            )
        )
        return
    else:
        timings["scheme"] = time.time() - t_scheme_start

    dishes_raw = overview.get("dishes", [])
    carb = overview.get("carbRecommendation", {"name": "米饭", "reason": "经典搭配"})

    # ③ 并行：每道菜 补全信息 ∥ 教程 ∥ 配图
    t0 = time.time()

    per_dish_tasks = [
        asyncio.gather(
            stage_detail(d),
            stage_tutorial(d, emit),
            stage_image(d, emit),
        )
        for d in dishes_raw
    ]
    per_dish_results = await asyncio.gather(*per_dish_tasks)
    timings["parallel"] = time.time() - t0
    # 解包 (detail, steps, url) 三元组对应 (dict, 耗时) 元组
    detail_results = [r[0][0] for r in per_dish_results]
    detail_durations = [r[0][1] for r in per_dish_results]
    tutorial_results = [r[1][0] for r in per_dish_results]
    tutorial_durations = [r[1][1] for r in per_dish_results]
    image_results = [r[2][0] for r in per_dish_results]
    image_durations = [r[2][1] for r in per_dish_results]

    # ④ 组装 + emit done
    dishes: list[Dish] = []
    for i, d in enumerate(dishes_raw):
        detail = detail_results[i] if i < len(detail_results) else {}
        dishes.append(
            Dish(
                id=d.get("id", f"dish-{i + 1}"),
                name=d.get("name", ""),
                description=detail.get("description", ""),
                estimatedTime=detail.get("estimatedTime", ""),
                previewImage=image_results[i] if i < len(image_results) else "",
                mainIngredients=d.get("mainIngredients", []),
                taste=d.get("taste", ""),
                cookingMethod=d.get("cookingMethod", ""),
                difficulty=detail.get("difficulty", ""),
                steps=tutorial_results[i] if i < len(tutorial_results) else [],
            )
        )

    # 推进度到 100%
    await emit(
        ProgressEvent(
            stage="tutorial",
            percent=98,
            message="教程已就绪",
        )
    )

    scheme = DishScheme(
        id=f"scheme-{int(time.time() * 1000)}",
        dishes=dishes,
        carbRecommendation=carb,
        createdAt=int(time.time() * 1000),
    )

    # 缓存
    get_cache().put(scheme.id, scheme)

    # emit done
    await emit(ProgressEvent(stage="done", percent=100, message="完成", scheme=scheme))

    # ===== 性能报告 =====
    total = time.time() - started_at
    logger.info("=" * 60)
    logger.info(f"端到端性能报告 scheme_id={scheme.id}")
    logger.info(f"  总耗时:    {total:.2f}s  (dishes={len(dishes)})")
    logger.info(f"  ├─ ① 意图识别:   {timings.get('intent', 0):.2f}s")
    logger.info(f"  ├─ ② 方案生成:   {timings.get('scheme', 0):.2f}s")
    logger.info(f"  └─ ③ 并行阶段:   {timings.get('parallel', 0):.2f}s")
    for i, (d, img_t, tut_t, det_t) in enumerate(zip(dishes, image_durations, tutorial_durations, detail_durations)):
        logger.info(
            f"      ├─ {d.name}  配图={img_t:.2f}s  教程={tut_t:.2f}s  补全={det_t:.2f}s"
        )
    logger.info("=" * 60)
