"""
酒窖管理 API 路由

提供酒窖的 CRUD 操作和統計功能。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime

from src.models.wine_cellar import WineCellar
from src.models.wine_item import WineItem
from src.routes.dependencies import DBSession, CurrentUserId

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Wine Cellars"])


# ============ Schemas ============

class WineCellarCreate(BaseModel):
    """建立酒窖的請求資料"""
    name: str = "我的酒窖"
    description: Optional[str] = None
    capacity: int = 50


class WineCellarUpdate(BaseModel):
    """更新酒窖的請求資料"""
    name: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None


class WineCellarResponse(BaseModel):
    """酒窖回應"""
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    capacity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WineCellarDetailResponse(WineCellarResponse):
    """酒窖詳細資訊（含統計）"""
    used_capacity: float
    available_capacity: float
    total_value: float
    wine_count: int
    unopened_count: int
    opened_count: int
    # 按酒類分類的統計
    wine_type_stats: dict


# ============ Routes ============

@router.get("/wine-cellars", response_model=list[WineCellarResponse])
async def list_wine_cellars(db: DBSession, user_id: CurrentUserId):
    """取得使用者的所有酒窖（預設酒窖已在新用戶建立時自動建立）"""
    cellars = db.query(WineCellar).filter(WineCellar.owner_id == user_id).all()

    return cellars


@router.post("/wine-cellars", response_model=WineCellarResponse, status_code=status.HTTP_201_CREATED)
async def create_wine_cellar(data: WineCellarCreate, db: DBSession, user_id: CurrentUserId):
    """新增酒窖"""
    cellar = WineCellar(owner_id=user_id, **data.model_dump())
    db.add(cellar)
    db.commit()
    db.refresh(cellar)

    logger.info(f"使用者 {user_id} 新增酒窖: {cellar.name} (ID: {cellar.id})")
    return cellar


@router.get("/wine-cellars/{id}", response_model=WineCellarDetailResponse)
async def get_wine_cellar(id: int, db: DBSession, user_id: CurrentUserId):
    """取得單一酒窖（含統計資訊）"""
    cellar = _get_cellar_or_404(id, user_id, db)
    stats = _compute_cellar_stats(cellar)

    return {
        "id": cellar.id,
        "owner_id": cellar.owner_id,
        "name": cellar.name,
        "description": cellar.description,
        "total_capacity": cellar.capacity,
        "created_at": cellar.created_at,
        "updated_at": cellar.updated_at,
        **stats,
    }


@router.put("/wine-cellars/{id}", response_model=WineCellarResponse)
async def update_wine_cellar(id: int, data: WineCellarUpdate, db: DBSession, user_id: CurrentUserId):
    """更新酒窖"""
    cellar = _get_cellar_or_404(id, user_id, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cellar, field, value)

    db.commit()
    db.refresh(cellar)

    logger.info(f"使用者 {user_id} 更新酒窖: {cellar.name} (ID: {cellar.id})")
    return cellar


@router.delete("/wine-cellars/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wine_cellar(id: int, db: DBSession, user_id: CurrentUserId):
    """刪除酒窖（會一併刪除所有酒款）"""
    cellar = _get_cellar_or_404(id, user_id, db)

    db.delete(cellar)
    db.commit()

    logger.info(f"使用者 {user_id} 刪除酒窖 (ID: {id})")


@router.get("/wine-cellars/{id}/stats")
async def get_wine_cellar_stats(id: int, db: DBSession, user_id: CurrentUserId):
    """取得酒窖統計摘要"""
    cellar = _get_cellar_or_404(id, user_id, db)
    stats = _compute_cellar_stats(cellar)

    return {
        "cellar_id": id,
        "cellar_name": cellar.name,
        "capacity_total": cellar.capacity,
        **stats,
    }


# ============ Helpers ============

def _get_cellar_or_404(cellar_id: int, user_id: int, db) -> WineCellar:
    """查詢酒窖，不存在或無權限則拋 404"""
    cellar = db.query(WineCellar).filter(
        WineCellar.id == cellar_id, WineCellar.owner_id == user_id
    ).first()
    if not cellar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒窖不存在或無權限存取"
        )
    return cellar


def _compute_cellar_stats(cellar: WineCellar) -> dict:
    """計算酒窖統計數據（共用邏輯）"""
    all_wines = cellar.wine_items or []
    active_wines = [w for w in all_wines if w.status == 'active']

    # 容量與價值
    used_capacity = sum(w.space_units * w.quantity for w in active_wines)
    total_value = sum(w.total_value for w in active_wines)

    # 開瓶狀態
    bottle_stats = {
        'unopened': sum(1 for w in active_wines if w.bottle_status == 'unopened'),
        'opened': sum(1 for w in active_wines if w.bottle_status == 'opened'),
    }

    # 按酒款狀態
    status_stats = {}
    for w in all_wines:
        s = w.status or 'active'
        status_stats[s] = status_stats.get(s, 0) + 1

    # 按酒類
    wine_type_stats = {}
    for w in active_wines:
        wt = w.wine_type or "其他"
        if wt not in wine_type_stats:
            wine_type_stats[wt] = {"count": 0, "value": 0}
        wine_type_stats[wt]["count"] += w.quantity
        wine_type_stats[wt]["value"] += w.total_value

    # 按國家
    country_stats = {}
    for w in active_wines:
        c = w.country or "未知"
        country_stats[c] = country_stats.get(c, 0) + w.quantity

    return {
        "wine_count": len(active_wines),
        "total_bottles": sum(w.quantity for w in active_wines),
        "total_value": total_value,
        "used_capacity": used_capacity,
        "available_capacity": (cellar.capacity or 0) - used_capacity,
        "capacity_used": used_capacity,
        "unopened_count": bottle_stats['unopened'],
        "opened_count": bottle_stats['opened'],
        "bottle_stats": bottle_stats,
        "status_stats": status_stats,
        "wine_type_stats": wine_type_stats,
        "country_stats": country_stats,
    }

