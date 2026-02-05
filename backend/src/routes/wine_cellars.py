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
    total_capacity: int = 50


class WineCellarUpdate(BaseModel):
    """更新酒窖的請求資料"""
    name: Optional[str] = None
    description: Optional[str] = None
    total_capacity: Optional[int] = None


class WineCellarResponse(BaseModel):
    """酒窖回應"""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    total_capacity: int
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
    """取得使用者的所有酒窖（若無則自動建立預設酒窖）"""
    cellars = db.query(WineCellar).filter(WineCellar.user_id == user_id).all()

    # 若使用者沒有酒窖，自動建立一個預設酒窖
    if not cellars:
        default_cellar = WineCellar(
            user_id=user_id,
            name="我的酒窖",
            description="自動建立的預設酒窖",
            total_capacity=50
        )
        db.add(default_cellar)
        db.commit()
        db.refresh(default_cellar)
        logger.info(f"使用者 {user_id} 自動建立預設酒窖 (ID: {default_cellar.id})")
        cellars = [default_cellar]

    return cellars


@router.post("/wine-cellars", response_model=WineCellarResponse, status_code=status.HTTP_201_CREATED)
async def create_wine_cellar(data: WineCellarCreate, db: DBSession, user_id: CurrentUserId):
    """新增酒窖"""
    cellar = WineCellar(user_id=user_id, **data.model_dump())
    db.add(cellar)
    db.commit()
    db.refresh(cellar)

    logger.info(f"使用者 {user_id} 新增酒窖: {cellar.name} (ID: {cellar.id})")
    return cellar


@router.get("/wine-cellars/{id}", response_model=WineCellarDetailResponse)
async def get_wine_cellar(id: int, db: DBSession, user_id: CurrentUserId):
    """取得單一酒窖（含統計資訊）"""
    cellar = db.query(WineCellar).filter(
        WineCellar.id == id, WineCellar.user_id == user_id
    ).first()

    if not cellar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒窖不存在或無權限存取"
        )

    # 計算統計資訊
    active_wines = [w for w in cellar.wine_items if w.status == 'active']
    
    # 計算容量
    used_capacity = sum(w.space_units * w.quantity for w in active_wines)
    
    # 計算總價值
    total_value = sum(w.total_value for w in active_wines)
    
    # 計算開瓶狀態統計
    unopened_count = sum(1 for w in active_wines if w.bottle_status == 'unopened')
    opened_count = sum(1 for w in active_wines if w.bottle_status == 'opened')
    
    # 計算酒類統計
    wine_type_stats = {}
    for wine in active_wines:
        wine_type = wine.wine_type or "其他"
        if wine_type not in wine_type_stats:
            wine_type_stats[wine_type] = 0
        wine_type_stats[wine_type] += wine.quantity

    return {
        "id": cellar.id,
        "user_id": cellar.user_id,
        "name": cellar.name,
        "description": cellar.description,
        "total_capacity": cellar.total_capacity,
        "created_at": cellar.created_at,
        "updated_at": cellar.updated_at,
        "used_capacity": used_capacity,
        "available_capacity": cellar.total_capacity - used_capacity,
        "total_value": total_value,
        "wine_count": len(active_wines),
        "unopened_count": unopened_count,
        "opened_count": opened_count,
        "wine_type_stats": wine_type_stats,
    }


@router.put("/wine-cellars/{id}", response_model=WineCellarResponse)
async def update_wine_cellar(id: int, data: WineCellarUpdate, db: DBSession, user_id: CurrentUserId):
    """更新酒窖"""
    cellar = db.query(WineCellar).filter(
        WineCellar.id == id, WineCellar.user_id == user_id
    ).first()

    if not cellar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒窖不存在或無權限存取"
        )

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
    cellar = db.query(WineCellar).filter(
        WineCellar.id == id, WineCellar.user_id == user_id
    ).first()

    if not cellar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒窖不存在或無權限存取"
        )

    db.delete(cellar)
    db.commit()

    logger.info(f"使用者 {user_id} 刪除酒窖 (ID: {id})")


@router.get("/wine-cellars/{id}/stats")
async def get_wine_cellar_stats(id: int, db: DBSession, user_id: CurrentUserId):
    """取得酒窖統計摘要"""
    cellar = db.query(WineCellar).filter(
        WineCellar.id == id, WineCellar.user_id == user_id
    ).first()

    if not cellar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒窖不存在或無權限存取"
        )

    active_wines = [w for w in cellar.wine_items if w.status == 'active']
    
    # 按狀態分類
    status_stats = {
        'active': len([w for w in cellar.wine_items if w.status == 'active']),
        'sold': len([w for w in cellar.wine_items if w.status == 'sold']),
        'gifted': len([w for w in cellar.wine_items if w.status == 'gifted']),
        'consumed': len([w for w in cellar.wine_items if w.status == 'consumed']),
    }
    
    # 按開瓶狀態
    bottle_stats = {
        'unopened': len([w for w in active_wines if w.bottle_status == 'unopened']),
        'opened': len([w for w in active_wines if w.bottle_status == 'opened']),
    }
    
    # 按酒類
    wine_type_stats = {}
    for wine in active_wines:
        wine_type = wine.wine_type or "其他"
        if wine_type not in wine_type_stats:
            wine_type_stats[wine_type] = {"count": 0, "value": 0}
        wine_type_stats[wine_type]["count"] += wine.quantity
        wine_type_stats[wine_type]["value"] += wine.total_value
    
    # 按國家
    country_stats = {}
    for wine in active_wines:
        country = wine.country or "未知"
        if country not in country_stats:
            country_stats[country] = 0
        country_stats[country] += wine.quantity

    return {
        "cellar_id": id,
        "cellar_name": cellar.name,
        "total_wines": len(active_wines),
        "total_bottles": sum(w.quantity for w in active_wines),
        "total_value": sum(w.total_value for w in active_wines),
        "capacity_used": sum(w.space_units * w.quantity for w in active_wines),
        "capacity_total": cellar.total_capacity,
        "status_stats": status_stats,
        "bottle_stats": bottle_stats,
        "wine_type_stats": wine_type_stats,
        "country_stats": country_stats,
    }
