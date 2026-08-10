"""
SQLite 数据库封装
- 单文件数据库 backend/data/kaifan.db
- 启动时 init_db() 自动建表
- 提供 get_db() 上下文管理器
- 用户数据：users / schemes / favorites
"""
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from loguru import logger

# ===== 路径配置 =====
# 数据库文件固定放在 backend/data/kaifan.db（已 gitignore）
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _BACKEND_ROOT / "data"
_DB_PATH = _DATA_DIR / "kaifan.db"


def get_db_path() -> Path:
    return _DB_PATH


# ===== 连接管理 =====

# SQLite 多线程说明：
# - FastAPI 通常单进程多线程（uvicorn 默认）
# - SQLite 写串行化，必须串行调用写连接
# - 用 Lock 保护写连接，读连接可以并发
_write_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    """打开一个数据库连接（每次新建，复用关闭）"""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        str(_DB_PATH),
        timeout=10.0,           # 写锁等待超时
        detect_types=0,
        check_same_thread=False,  # 允许多线程共享连接
    )
    conn.row_factory = sqlite3.Row  # 行返回 dict-like
    # 启用外键约束 + WAL 模式（提升并发读性能）
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """获取数据库连接的上下文管理器（自动提交/回滚/关闭）。"""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ===== 表结构 =====

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,        -- pbkdf2_hmac hex
    password_salt   TEXT NOT NULL,        -- hex 盐
    created_at      INTEGER NOT NULL      -- epoch ms
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE TABLE IF NOT EXISTS schemes (
    id              TEXT PRIMARY KEY,     -- 业务 scheme id（与 DishScheme.id 对应）
    user_id         INTEGER NOT NULL,
    payload_json    TEXT NOT NULL,        -- 整个 DishScheme JSON
    created_at      INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_schemes_user ON schemes(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS favorites (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    scheme_id       TEXT NOT NULL,        -- 冗余：来源方案 id（删除方案不影响收藏）
    dish_id         TEXT NOT NULL,        -- 业务 dish id
    dish_payload_json TEXT NOT NULL,      -- 收藏时的 Dish 快照
    created_at      INTEGER NOT NULL,
    UNIQUE(user_id, dish_id),             -- 同一菜不重复收藏
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id, created_at DESC);
"""


def init_db() -> None:
    """启动时调用：建表 + 写日志"""
    try:
        with get_db() as conn:
            conn.executescript(_SCHEMA)
        logger.info(f"SQLite 初始化完成 path={_DB_PATH}")
    except Exception as e:
        logger.exception(f"SQLite 初始化失败: {e}")
        raise