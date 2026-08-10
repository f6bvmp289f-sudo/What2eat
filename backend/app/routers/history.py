"""
历史方案路由
- GET    /api/history         拉当前用户的方案列表（按 created_at desc）
- POST   /api/history         写入一条方案（流式 done 时调用）
- DELETE /api/history/{id}    删除一条

payload 用 JSON 字符串存储整个 DishScheme 对象（MVP 阶段足够）。
"""
import json
import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import CurrentUser, get_current_user
from app.db import get_db

router = APIRouter()


# ===== 数据模型 =====


class SchemeIn(BaseModel):
    """POST body：前端传完整 DishScheme JSON"""

    id: str
    dishes: list[dict]
    carbRecommendation: dict
    createdAt: int


class SchemeOut(BaseModel):
    """返回：直接从 DB 读出来后组装"""

    id: str
    payload: dict
    created_at: int


# ===== 路由 =====


@router.get("", response_model=list[SchemeOut])
async def list_history(current: CurrentUser = Depends(get_current_user)) -> list[SchemeOut]:
    """拉当前用户的方案列表。"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, payload_json, created_at FROM schemes "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
            (current.id,),
        ).fetchall()

    items: list[SchemeOut] = []
    for r in rows:
        try:
            payload = json.loads(r["payload_json"])
        except json.JSONDecodeError:
            payload = {}
        items.append(
            SchemeOut(
                id=r["id"],
                payload=payload,
                created_at=r["created_at"],
            )
        )
    return items


@router.post("", response_model=SchemeOut, status_code=status.HTTP_201_CREATED)
async def add_history(
    body: SchemeIn,
    current: CurrentUser = Depends(get_current_user),
) -> SchemeOut:
    """写入一条历史方案（同 id 覆盖更新）。"""
    payload_json = json.dumps(
        {
            "id": body.id,
            "dishes": body.dishes,
            "carbRecommendation": body.carbRecommendation,
            "createdAt": body.createdAt,
        },
        ensure_ascii=False,
    )
    with get_db() as conn:
        conn.execute(
            "INSERT INTO schemes (id, user_id, payload_json, created_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "  payload_json = excluded.payload_json, "
            "  user_id = excluded.user_id",
            (body.id, current.id, payload_json, body.createdAt or int(time.time() * 1000)),
        )
    return SchemeOut(id=body.id, payload=json.loads(payload_json), created_at=body.createdAt)


@router.delete("/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history(
    scheme_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> None:
    """删除一条历史（只能删自己的）。"""
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM schemes WHERE id = ? AND user_id = ?",
            (scheme_id, current.id),
        )
        if cur.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="历史记录不存在",
            )