"""
统一异常处理
- 自定义异常类
- 错误处理中间件：统一 4xx/5xx 响应格式
"""
import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger


class KaifanError(Exception):
    """业务异常基类"""

    code: str = "INTERNAL_ERROR"
    message: str = "服务异常"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str | None = None, code: str | None = None):
        if message:
            self.message = message
        if code:
            self.code = code
        super().__init__(self.message)


class IngredientRatioLowError(KaifanError):
    code = "INGREDIENT_RATIO_LOW"
    message = "没看到具体食材，请上传买菜清单或描述你想吃的菜"
    status_code = status.HTTP_400_BAD_REQUEST


class InvalidInputError(KaifanError):
    code = "INVALID_INPUT"
    status_code = status.HTTP_400_BAD_REQUEST


class LLMUnavailableError(KaifanError):
    code = "LLM_UNAVAILABLE"
    message = "AI 服务暂时不可用"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ParseError(KaifanError):
    code = "PARSE_ERROR"
    message = "AI 输出格式异常"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


def _err_payload(code: str, message: str, details: Any = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(KaifanError)
    async def kaifan_error_handler(request: Request, exc: KaifanError):
        logger.warning(f"业务异常: {exc.code} {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=_err_payload(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        # Pydantic 校验错误：取第一个错误信息
        errors = exc.errors()
        first = errors[0] if errors else {}
        loc = ".".join(str(x) for x in first.get("loc", []))
        msg = first.get("msg", "参数校验失败")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_err_payload(
                "INVALID_INPUT",
                f"{loc}: {msg}" if loc else msg,
                details=errors[:5],
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception(f"未处理异常: {type(exc).__name__} {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_err_payload(
                "INTERNAL_ERROR",
                "服务异常，请稍后重试",
            ),
        )
