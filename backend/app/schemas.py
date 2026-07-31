"""
Pydantic 数据模型
字段名与前端 `frontend/src/stores/dish.ts` 保持一致。
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ===== 业务模型（与前端对齐） =====


class DishStep(BaseModel):
    """单步骤（MVP 字段 + 完整字段）"""

    index: int
    title: str
    description: str = ""  # 简要描述（向后兼容）
    hasTimer: bool = False
    timerSeconds: Optional[int] = None
    substeps: list[str] = Field(default_factory=list)  # 详细子步骤（1.1/1.2/1.3 风格）


class Dish(BaseModel):
    """一道菜"""

    id: str
    name: str
    description: str
    estimatedTime: str
    previewImage: str = ""  # URL（可能为空 → 前端用占位）
    mainIngredients: list[str] = Field(default_factory=list)
    taste: str = ""
    cookingMethod: str = ""
    difficulty: str = ""
    steps: list[DishStep] = Field(default_factory=list)


class CarbRecommendation(BaseModel):
    name: str
    reason: str


class DishScheme(BaseModel):
    """完整菜谱方案"""

    id: str
    dishes: list[Dish]
    carbRecommendation: CarbRecommendation
    createdAt: int  # epoch ms


# ===== 请求 / 响应 =====


class GenerateRequest(BaseModel):
    """前端 POST /api/generate/stream 的请求体"""

    images: list[str] = Field(default_factory=list)  # base64 data URI
    text: str = ""
    history_dish_names: list[str] = Field(default_factory=list)  # 换一批：上一轮菜名（用于去重）

    @field_validator("images")
    @classmethod
    def check_image_count(cls, v: list[str]) -> list[str]:
        if len(v) > 5:
            raise ValueError("最多 5 张图片")
        return v

    @field_validator("text")
    @classmethod
    def check_text_length(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("文字描述最多 500 字")
        return v


# ===== SSE 事件模型 =====

Stage = Literal["intent", "scheme", "image", "tutorial", "done", "error"]


class ProgressEvent(BaseModel):
    """SSE 推送给前端的进度事件"""

    stage: Stage
    percent: int = 0
    message: str = ""
    # 阶段化数据
    dish_id: Optional[str] = None
    url: Optional[str] = None
    steps: Optional[list[DishStep]] = None
    # 完成事件
    scheme: Optional[DishScheme] = None
    # 错误事件
    code: Optional[str] = None


# ===== 错误码 =====

class ErrorCode:
    INGREDIENT_RATIO_LOW = "INGREDIENT_RATIO_LOW"
    PARSE_ERROR = "PARSE_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    INVALID_INPUT = "INVALID_INPUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
