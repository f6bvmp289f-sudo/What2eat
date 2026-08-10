"""
收藏路由
- GET    /api/favorites           拉当前用户的收藏列表（按 created_at desc）
- POST   /api/favorites           收藏一道菜（{scheme_id, dish_id, dish_payload}）
- DELETE /api/favorites/{dish_id} 取消收藏（按 dish_id 维度，同一菜再次收藏幂等）

每条收藏存储一份 dish 的 JSON 快照，删除/修改原 scheme 不影响收藏。
"""
import json
import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import CurrentUser, get_current_user
from app.db import get_db

router = APIRouter()


# ===== 数据模型 =====


class FavoriteIn(BaseModel):
    scheme_id: str
    dish_id: str
    dish_payload: dict  # 完整的 Dish 对象快照


class FavoriteOut(BaseModel):
    id: int
    scheme_id: str
    dish_id: str
    dish_payload: dict
    created_at: int


# ===== 路由 =====


@router.get("", response_model=list[FavoriteOut])
async def list_favorites(
    current: CurrentUser = Depends(get_current_user),
) -> list[FavoriteOut]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, scheme_id, dish_id, dish_payload_json, created_at "
            "FROM favorites WHERE user_id = ? ORDER BY created_at DESC LIMIT 200",
            (current.id,),
        ).fetchall()
    items: list[FavoriteOut] = []
    for r in rows:
        try:
            payload = json.loads(r["dish_payload_json"])
        except json.JSONDecodeError:
            payload = {}
        items.append(
            FavoriteOut(
                id=r["id"],
                scheme_id=r["scheme_id"],
                dish_id=r["dish_id"],
                dish_payload=payload,
                created_at=r["created_at"],
            )
        )
    return items


@router.post("", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    body: FavoriteIn,
    current: CurrentUser = Depends(get_current_user),
) -> FavoriteOut:
    now = int(time.time() * 1000)
    payload_json = json.dumps(body.dish_payload, ensure_ascii=False)

    with get_db() as conn:
        # UNIQUE(user_id, dish_id) 已保证幂等
        # 如果已存在就更新 payload / created_at
        existing = conn.execute(
            "SELECT id FROM favorites WHERE user_id = ? AND dish_id = ?",
            (current.id, body.dish_id),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE favorites SET scheme_id = ?, dish_payload_json = ?, created_at = ? "
                "WHERE id = ?",
                (body.scheme_id, payload_json, now, existing["id"]),
            )
            fav_id = existing["id"]
        else:
            cur = conn.execute(
                "INSERT INTO favorites (user_id, scheme_id, dish_id, dish_payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (current.id, body.scheme_id, body.dish_id, payload_json, now),
            )
            fav_id = cur.lastrowid

    return FavoriteOut(
        id=fav_id,
        scheme_id=body.scheme_id,
        dish_id=body.dish_id,
        dish_payload=body.dish_payload,
        created_at=now,
    )


@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    dish_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> None:
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND dish_id = ?",
            (current.id, dish_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未收藏该菜品",
            )