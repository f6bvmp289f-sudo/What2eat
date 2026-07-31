"""
结构化日志（loguru + JSON 输出）
- 默认 stdout 输出（开发友好）
- 包含时间戳、级别、消息、模块、extra
"""
import json
import logging
import sys
from pathlib import Path

from loguru import logger


class InterceptHandler(logging.Handler):
    """把标准 logging 桥接到 loguru"""

    def emit(self, record: logging.LogRecord) -> None:
        # 找调用方
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _json_sink(message) -> None:
    """JSON 格式输出（生产用）"""
    record = message.record
    payload = {
        "ts": record["time"].isoformat(),
        "level": record["level"].name,
        "msg": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }
    if record["extra"]:
        payload.update(record["extra"])
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def setup_logging(level: str = "INFO", json_mode: bool = False) -> None:
    """初始化日志"""
    logger.remove()

    if json_mode:
        logger.add(_json_sink, level=level, serialize=False)
    else:
        # 开发：人类可读 + 彩色
        logger.add(
            sys.stdout,
            level=level,
            format=(
                "<green>{time:HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}:{function}:{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True,
        )

    # 桥接标准 logging（uvicorn / fastapi）
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
