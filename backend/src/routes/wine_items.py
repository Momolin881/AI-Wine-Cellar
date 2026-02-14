"""
酒款管理 API 路由

提供酒款的 CRUD 操作和 AI 酒標辨識功能。
"""

import logging
import traceback
from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from src.models.wine_item import WineItem
from src.models.wine_cellar import WineCellar
from src.routes.dependencies import DBSession, CurrentUserId
from src.services import wine_vision, storage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Wine Items"])


# ============ Schemas ============

class HistoryMatch(BaseModel):
    """歷史比對結果"""
    id: int
    name: str
    brand: Optional[str] = None
    vintage: Optional[int] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[date] = None
    tasting_notes: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    flavor_tags: Optional[str] = None
    aroma: Optional[str] = None
    palate: Optional[str] = None
    finish: Optional[str] = None
    acidity: Optional[int] = None
    tannin: Optional[int] = None
    body: Optional[int] = None
    sweetness: Optional[int] = None
    alcohol_feel: Optional[int] = None
    image_url: Optional[str] = None

class HistoryMatchResponse(BaseModel):
    """歷史比對 API 回應"""
    matched: bool
    history: list[HistoryMatch] = []


class WineItemCreate(BaseModel):
    """建立酒款的請求資料"""
    cellar_id: int
    name: str
    wine_type: str
    brand: Optional[str] = None
    vintage: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    abv: Optional[float] = None
    quantity: int = 1
    space_units: float = 1.0
    container_type: str = "瓶"
    bottle_status: str = "unopened"
    preservation_type: str = "immediate"  # immediate / aging
    remaining_amount: str = "full"
    disposition: str = "personal"  # personal / gift / sale / collection
    purchase_price: Optional[float] = None
    retail_price: Optional[float] = None
    purchase_date: Optional[str] = None
    optimal_drinking_start: Optional[str] = None
    optimal_drinking_end: Optional[str] = None
    storage_location: Optional[str] = None
    storage_temp: Optional[str] = None
    image_url: Optional[str] = None
    cloudinary_public_id: Optional[str] = None
    notes: Optional[str] = None
    tasting_notes: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    flavor_tags: Optional[str] = None
    aroma: Optional[str] = None
    palate: Optional[str] = None
    finish: Optional[str] = None
    acidity: Optional[int] = 3
    tannin: Optional[int] = 3
    body: Optional[int] = 3
    sweetness: Optional[int] = 3
    alcohol_feel: Optional[int] = 3
    recognized_by_ai: int = 0


class WineItemUpdate(BaseModel):
    """更新酒款的請求資料"""
    model_config = {"extra": "ignore"}  # 忽略未知欄位，避免 422 錯誤

    name: Optional[str] = None
    wine_type: Optional[str] = None
    brand: Optional[str] = None
    vintage: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    abv: Optional[float] = None
    quantity: Optional[int] = None
    space_units: Optional[float] = None
    container_type: Optional[str] = None
    bottle_status: Optional[str] = None

    preservation_type: Optional[str] = None
    remaining_amount: Optional[str] = None
    disposition: Optional[str] = None
    purchase_price: Optional[float] = None
    retail_price: Optional[float] = None
    purchase_date: Optional[str] = None
    optimal_drinking_start: Optional[str] = None
    optimal_drinking_end: Optional[str] = None
    storage_location: Optional[str] = None
    storage_temp: Optional[str] = None
    notes: Optional[str] = None
    tasting_notes: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    flavor_tags: Optional[str] = None
    aroma: Optional[str] = None
    palate: Optional[str] = None
    finish: Optional[str] = None
    acidity: Optional[int] = None
    tannin: Optional[int] = None
    body: Optional[int] = None
    sweetness: Optional[int] = None
    alcohol_feel: Optional[int] = None


class WineItemResponse(BaseModel):
    """酒款回應"""
    id: int
    cellar_id: int
    name: str
    wine_type: str
    brand: Optional[str]
    vintage: Optional[int]
    region: Optional[str]
    country: Optional[str]
    abv: Optional[float]
    quantity: int
    space_units: float
    container_type: str
    bottle_status: str

    preservation_type: str
    remaining_amount: str
    disposition: str = "personal"
    split_from_id: Optional[int] = None
    purchase_price: Optional[float]
    retail_price: Optional[float]
    purchase_date: Optional[str]
    optimal_drinking_start: Optional[str]
    optimal_drinking_end: Optional[str]
    storage_location: Optional[str]
    storage_temp: Optional[str]
    image_url: Optional[str]
    cloudinary_public_id: Optional[str]
    notes: Optional[str]
    tasting_notes: Optional[str]
    rating: Optional[int] = None
    review: Optional[str] = None
    flavor_tags: Optional[str] = None
    aroma: Optional[str] = None
    palate: Optional[str] = None
    finish: Optional[str] = None
    acidity: Optional[int] = None
    tannin: Optional[int] = None
    body: Optional[int] = None
    sweetness: Optional[int] = None
    alcohol_feel: Optional[int] = None
    recognized_by_ai: int
    status: str
    created_at: datetime
    updated_at: datetime
    # 計算屬性
    is_optimal_now: bool
    total_value: float

    class Config:
        from_attributes = True


class AIWineRecognitionResponse(BaseModel):
    """AI 酒標辨識回應"""
    name: str
    wine_type: str
    brand: Optional[str] = None
    vintage: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    abv: Optional[float] = None
    container_type: str = "瓶"
    suggested_storage_temp: Optional[str] = None
    description: Optional[str] = None
    image_url: str
    cloudinary_public_id: str


# ============ Helper Functions ============

# 開瓶後建議效期對照表 (天數)
OPENED_SHELF_LIFE_MAP = {
    '啤酒': 1,
    '氣泡酒': 2,
    '香檳': 2,
    '白酒': 4,
    '粉紅酒': 4,
    '紅酒': 5,
    '清酒': 7,
    '甜酒': 14,
    '貴腐酒': 14,
    '波特酒': 30,
    '雪莉酒': 30,
    '威士忌': 730,  # 2年
    '白蘭地': 730,
    '伏特加': 730,
    '蘭姆酒': 730,
    '琴酒': 730,
    '高粱酒': 730,
    '梅酒': 365,
}

def _calculate_open_bottle_expiry(wine_type: str, preservation_type: str, open_date: date) -> date:
    """
    根據酒類和保存類型計算開瓶後的最佳飲用期限
    """
    # 1. 優先查詢對照表
    # 部分比對：例如 "波爾多紅酒" -> 包含 "紅酒"
    expiry_days = 3  # 預設值
    
    # 簡單正規化
    normalized_type = wine_type.strip()
    
    # 精確比對
    if normalized_type in OPENED_SHELF_LIFE_MAP:
        expiry_days = OPENED_SHELF_LIFE_MAP[normalized_type]
    else:
        # 模糊比對
        match_found = False
        for key, days in OPENED_SHELF_LIFE_MAP.items():
            if key in normalized_type:
                expiry_days = days
                match_found = True
                break
        
        # 2. 如果沒對應到，使用保存類型 (Legacy Logic)
        if not match_found:
            if preservation_type == 'aging':
                # 注意：這裡的 aging 對應到舊邏輯的 "陳年型/烈酒"，預設給 2 年
                expiry_days = 730
            else:
                expiry_days = 3

    return open_date + timedelta(days=expiry_days)


def _safe_get(item, attr, default=None):
    """安全取得屬性值，處理資料庫欄位不存在的情況"""
    try:
        return getattr(item, attr, default)
    except Exception:
        return default


def _safe_int(value):
    """安全轉換為整數，處理浮點數轉換"""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _build_wine_item_response(item: WineItem) -> WineItemResponse:
    """將 WineItem ORM 物件轉換為 WineItemResponse"""
    return WineItemResponse(
        id=item.id,
        cellar_id=item.cellar_id,
        name=item.name,
        wine_type=item.wine_type,
        brand=item.brand,
        vintage=item.vintage,
        region=item.region,
        country=item.country,
        abv=item.abv,
        quantity=item.quantity,
        space_units=item.space_units,
        container_type=item.container_type,
        bottle_status=item.bottle_status,

        preservation_type=item.preservation_type,
        remaining_amount=item.remaining_amount,
        disposition=_safe_get(item, 'disposition', 'personal') or 'personal',
        split_from_id=_safe_get(item, 'split_from_id', None),
        purchase_price=item.purchase_price,
        retail_price=item.retail_price,
        purchase_date=str(item.purchase_date) if item.purchase_date else None,
        optimal_drinking_start=str(item.optimal_drinking_start) if item.optimal_drinking_start else None,
        optimal_drinking_end=str(item.optimal_drinking_end) if item.optimal_drinking_end else None,
        storage_location=item.storage_location,
        storage_temp=item.storage_temp,
        image_url=item.image_url,
        cloudinary_public_id=item.cloudinary_public_id,
        notes=item.notes,
        tasting_notes=item.tasting_notes,
        rating=_safe_int(_safe_get(item, 'rating', None)),
        review=_safe_get(item, 'review', None),
        flavor_tags=_safe_get(item, 'flavor_tags', None),
        aroma=_safe_get(item, 'aroma', None),
        palate=_safe_get(item, 'palate', None),
        finish=_safe_get(item, 'finish', None),
        acidity=_safe_int(_safe_get(item, 'acidity', None)),
        tannin=_safe_int(_safe_get(item, 'tannin', None)),
        body=_safe_int(_safe_get(item, 'body', None)),
        sweetness=_safe_int(_safe_get(item, 'sweetness', None)),
        alcohol_feel=_safe_int(_safe_get(item, 'alcohol_feel', None)),
        recognized_by_ai=item.recognized_by_ai,
        status=item.status or 'active',
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_optimal_now=item.is_optimal_now,
        total_value=item.total_value,
    )


# ============ Routes ============

@router.get("/wine-items", response_model=list[WineItemResponse])
async def list_wine_items(
    db: DBSession,
    user_id: CurrentUserId,
    wine_type: Optional[str] = None,
    bottle_status: Optional[str] = None,  # unopened / opened
    status: Optional[str] = 'active',  # active / sold / gifted / consumed / all
):
    """
    列出使用者的所有酒款

    Query 參數:
    - wine_type: 篩選酒類（紅酒、白酒、威士忌等）
    - bottle_status: 篩選開瓶狀態（unopened / opened）
    - status: 篩選狀態（active / sold / gifted / consumed / all）
    """
    query = (
        db.query(WineItem)
        .join(WineCellar, WineItem.cellar_id == WineCellar.id)
        .filter(WineCellar.user_id == user_id)
    )

    # 篩選狀態
    if status and status != 'all':
        query = query.filter(WineItem.status == status)

    # 篩選酒類
    if wine_type:
        query = query.filter(WineItem.wine_type == wine_type)

    # 篩選開瓶狀態
    if bottle_status:
        query = query.filter(WineItem.bottle_status == bottle_status)

    try:
        wine_items = query.all()
        results = []
        for item in wine_items:
            try:
                results.append(_build_wine_item_response(item))
            except Exception as item_error:
                logger.error(f"Error building response for wine item {item.id}: {item_error}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing wine item {item.id}: {str(item_error)}"
                )
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing wine items: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/wine-items/match-history", response_model=HistoryMatchResponse)
def match_wine_history(
    brand: str,
    name: str,
    db: DBSession,
    user_id: CurrentUserId
):
    """
    歷史酒款比對 - 根據品牌和酒名查找過去購買記錄

    用於 AI 辨識後，提示使用者是否套用歷史價格和品飲筆記。
    """
    from src.models.wine_cellar import WineCellar

    # 取得使用者的所有酒窖 IDs
    cellar_ids = [c.id for c in db.query(WineCellar).filter(WineCellar.user_id == user_id).all()]

    if not cellar_ids:
        return HistoryMatchResponse(matched=False, history=[])

    # 查詢相符的歷史酒款（包含已售出、送禮、喝完）
    matches = db.query(WineItem).filter(
        WineItem.cellar_id.in_(cellar_ids),
        WineItem.brand == brand,
        WineItem.name == name
    ).order_by(WineItem.purchase_date.desc()).limit(5).all()

    if not matches:
        return HistoryMatchResponse(matched=False, history=[])

    history = [
        HistoryMatch(
            id=m.id,
            name=m.name,
            brand=m.brand,
            vintage=m.vintage,
            purchase_price=m.purchase_price,
            purchase_date=m.purchase_date,
            notes=m.notes,
            tasting_notes=m.tasting_notes,
            rating=m.rating,
            flavor_tags=m.flavor_tags,
            aroma=m.aroma,
            palate=m.palate,
            finish=m.finish,
            acidity=m.acidity,
            tannin=m.tannin,
            body=m.body,
            sweetness=m.sweetness,
            alcohol_feel=m.alcohol_feel,
            image_url=m.image_url
        )
        for m in matches
    ]

    return HistoryMatchResponse(matched=True, history=history)


@router.get("/wine-items/{id}", response_model=WineItemResponse)
async def get_wine_item(id: int, db: DBSession, user_id: CurrentUserId):
    """取得單一酒款"""
    wine_item = (
        db.query(WineItem)
        .join(WineCellar, WineItem.cellar_id == WineCellar.id)
        .filter(WineItem.id == id, WineCellar.user_id == user_id)
        .first()
    )

    if not wine_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒款不存在或無權限存取"
        )

    return _build_wine_item_response(wine_item)


@router.post("/wine-items", response_model=WineItemResponse, status_code=status.HTTP_201_CREATED)
async def create_wine_item(data: WineItemCreate, db: DBSession, user_id: CurrentUserId):
    """新增酒款"""
    try:
        # 驗證酒窖所有權
        cellar = db.query(WineCellar).filter(
            WineCellar.id == data.cellar_id, WineCellar.user_id == user_id
        ).first()

        if not cellar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="酒窖不存在或無權限存取"
            )

        # 處理資料
        item_data = data.model_dump()
        logger.info(f"建立酒款資料: {item_data}")

        # 處理日期欄位：將字串轉換為 date 物件
        date_fields = ['purchase_date', 'optimal_drinking_start', 'optimal_drinking_end']
        for field in date_fields:
            value = item_data.get(field)
            if value:
                # 如果是字串，轉換為 date 物件
                if isinstance(value, str):
                    try:
                        item_data[field] = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        logger.error(f"日期格式錯誤 ({field}): {value}")
                        item_data[field] = None
            else:
                # 空值處理：purchase_date 移除以使用預設值，其他設為 None
                if field == 'purchase_date':
                    item_data.pop(field, None)
                else:
                    item_data[field] = None

        # 自動拆分：quantity > 1 時建立 N 筆獨立記錄（一筆記錄 = 一瓶酒）
        requested_quantity = item_data.get('quantity', 1)
        item_data['quantity'] = 1

        # 建立主記錄
        primary_item = WineItem(**item_data)
        db.add(primary_item)
        db.flush()  # 取得 primary_item.id，但不 commit

        # 建立額外記錄
        if requested_quantity > 1:
            for _ in range(requested_quantity - 1):
                clone_data = {**item_data, 'split_from_id': primary_item.id}
                db.add(WineItem(**clone_data))

        db.commit()
        db.refresh(primary_item)

        logger.info(
            f"使用者 {user_id} 新增酒款: {primary_item.name} (ID: {primary_item.id})"
            f"{f', 自動拆分為 {requested_quantity} 瓶' if requested_quantity > 1 else ''}"
        )
        return _build_wine_item_response(primary_item)
        
    except HTTPException:
        # 重新拋出 HTTPException
        raise
    except Exception as e:
        db.rollback()
        error_msg = f"建立酒款失敗: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.put("/wine-items/{id}", response_model=WineItemResponse)
async def update_wine_item(
    id: int,
    data: WineItemUpdate,
    db: DBSession,
    user_id: CurrentUserId,
    sync_tasting_notes: bool = False  # 是否同步品飲筆記到同批次酒款
):
    """更新酒款"""
    wine_item = (
        db.query(WineItem)
        .join(WineCellar, WineItem.cellar_id == WineCellar.id)
        .filter(WineItem.id == id, WineCellar.user_id == user_id)
        .first()
    )

    if not wine_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒款不存在或無權限存取"
        )

    # 更新欄位
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wine_item, field, value)

    # 品飲筆記欄位
    tasting_note_fields = ['rating', 'review', 'aroma', 'palate', 'finish', 'flavor_tags', 'acidity', 'tannin', 'body', 'sweetness', 'alcohol_feel']

    # 如果要同步品飲筆記到同批次酒款
    if sync_tasting_notes:
        # 檢查是否有更新品飲筆記欄位
        tasting_updates = {k: v for k, v in update_data.items() if k in tasting_note_fields}

        if tasting_updates:
            # 找出同批次的其他酒款
            # 如果此酒款是主記錄 (split_from_id=NULL)，找所有 split_from_id = 此酒款id 的記錄
            # 如果此酒款是拆分記錄，找主記錄和其他同 split_from_id 的記錄
            batch_items = []

            if wine_item.split_from_id is None:
                # 此酒款是主記錄，找所有從它拆分出來的
                batch_items = db.query(WineItem).filter(
                    WineItem.split_from_id == wine_item.id,
                    WineItem.id != wine_item.id
                ).all()
            else:
                # 此酒款是拆分記錄，找主記錄和同批次的其他記錄
                batch_items = db.query(WineItem).filter(
                    or_(
                        WineItem.id == wine_item.split_from_id,  # 主記錄
                        WineItem.split_from_id == wine_item.split_from_id  # 同批次
                    ),
                    WineItem.id != wine_item.id  # 排除自己
                ).all()

            # 同步品飲筆記到同批次酒款
            for item in batch_items:
                for field, value in tasting_updates.items():
                    setattr(item, field, value)

            if batch_items:
                logger.info(f"同步品飲筆記到 {len(batch_items)} 瓶同批次酒款")

    db.commit()
    db.refresh(wine_item)

    logger.info(f"使用者 {user_id} 更新酒款: {wine_item.name} (ID: {wine_item.id})")

    return _build_wine_item_response(wine_item)


@router.delete("/wine-items/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wine_item(id: int, db: DBSession, user_id: CurrentUserId):
    """刪除酒款"""
    wine_item = (
        db.query(WineItem)
        .join(WineCellar, WineItem.cellar_id == WineCellar.id)
        .filter(WineItem.id == id, WineCellar.user_id == user_id)
        .first()
    )

    if not wine_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒款不存在或無權限存取"
        )

    # 刪除 Cloudinary 圖片
    if wine_item.cloudinary_public_id:
        try:
            storage.delete_image(wine_item.cloudinary_public_id)
        except Exception as e:
            logger.warning(f"刪除 Cloudinary 圖片失敗: {e}")

    db.delete(wine_item)
    db.commit()

    logger.info(f"使用者 {user_id} 刪除酒款: {wine_item.name} (ID: {wine_item.id})")


@router.post("/wine-items/{id}/open", response_model=WineItemResponse)
async def open_wine_bottle(id: int, db: DBSession, user_id: CurrentUserId):
    """
    開瓶 - 將酒款標記為已開瓶
    """
    wine_item = (
        db.query(WineItem)
        .join(WineCellar, WineItem.cellar_id == WineCellar.id)
        .filter(WineItem.id == id, WineCellar.user_id == user_id)
        .first()
    )

    if not wine_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒款不存在或無權限存取"
        )

    wine_item.bottle_status = 'opened'
    wine_item.opened_at = datetime.utcnow()

    # 自動計算最佳飲用期限 (Drink By)
    today = date.today()
    wine_item.optimal_drinking_end = _calculate_open_bottle_expiry(
        wine_item.wine_type, 
        wine_item.preservation_type, 
        today
    )

    db.commit()
    db.refresh(wine_item)

    # 設置開瓶後提醒任務
    from src.services.scheduler import schedule_bottle_opened_reminder
    try:
        schedule_bottle_opened_reminder(wine_item, user_id)
        logger.info(f"已設置開瓶提醒: {wine_item.name}")
    except Exception as e:
        logger.warning(f"設置開瓶提醒失敗: {e}")

    logger.info(f"使用者 {user_id} 開瓶: {wine_item.name} (ID: {wine_item.id})")

    return _build_wine_item_response(wine_item)


@router.post("/wine-items/{id}/update-remaining", response_model=WineItemResponse)
async def update_remaining_amount(
    id: int,
    remaining: str,  # full / 3/4 / 1/2 / 1/4 / empty
    db: DBSession,
    user_id: CurrentUserId
):
    """
    更新剩餘量
    """
    valid_amounts = ['full', '3/4', '1/2', '1/4', 'empty']
    if remaining not in valid_amounts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"剩餘量必須是 {valid_amounts} 之一"
        )

    wine_item = (
        db.query(WineItem)
        .join(WineCellar, WineItem.cellar_id == WineCellar.id)
        .filter(WineItem.id == id, WineCellar.user_id == user_id)
        .first()
    )

    if not wine_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒款不存在或無權限存取"
        )

    wine_item.remaining_amount = remaining
    if remaining == 'empty':
        wine_item.status = 'consumed'
        wine_item.status_changed_at = datetime.utcnow()
        wine_item.status_changed_by = user_id

    db.commit()
    db.refresh(wine_item)

    return _build_wine_item_response(wine_item)


@router.post("/wine-items/{id}/change-status", response_model=WineItemResponse)
async def change_wine_status(
    id: int,
    new_status: str,  # sold / gifted / consumed
    db: DBSession,
    user_id: CurrentUserId
):
    """
    變更酒款狀態（售出、送禮、已喝完）
    """
    valid_statuses = ['active', 'sold', 'gifted', 'consumed']
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"狀態必須是 {valid_statuses} 之一"
        )

    wine_item = (
        db.query(WineItem)
        .join(WineCellar, WineItem.cellar_id == WineCellar.id)
        .filter(WineItem.id == id, WineCellar.user_id == user_id)
        .first()
    )

    if not wine_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒款不存在或無權限存取"
        )

    wine_item.status = new_status
    wine_item.status_changed_at = datetime.utcnow()
    wine_item.status_changed_by = user_id

    db.commit()
    db.refresh(wine_item)

    logger.info(f"使用者 {user_id} 變更酒款狀態: {wine_item.name} → {new_status}")

    return _build_wine_item_response(wine_item)


@router.post("/wine-items/recognize", response_model=AIWineRecognitionResponse)
async def recognize_wine_label(
    db: DBSession,
    user_id: CurrentUserId,
    cellar_id: int = Form(...),
    image: UploadFile = File(...),
):
    """
    AI 辨識酒標圖片

    接收 multipart/form-data:
    - cellar_id: 酒窖 ID
    - image: 圖片檔案
    """
    # 驗證酒窖所有權
    cellar = db.query(WineCellar).filter(
        WineCellar.id == cellar_id, WineCellar.user_id == user_id
    ).first()

    if not cellar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="酒窖不存在或無權限存取"
        )

    # 驗證圖片格式
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="檔案必須是圖片格式"
        )

    try:
        # 讀取圖片
        image_bytes = await image.read()

        # 上傳至 Cloudinary
        upload_result = storage.upload_image(image_bytes, folder="wine_items")

        # AI 辨識酒標
        ai_result = wine_vision.recognize_wine_label(image_bytes)

        # 組裝回應
        response = AIWineRecognitionResponse(
            name=ai_result["name"],
            wine_type=ai_result.get("wine_type", "其他"),
            brand=ai_result.get("brand"),
            vintage=ai_result.get("vintage"),
            region=ai_result.get("region"),
            country=ai_result.get("country"),
            abv=ai_result.get("abv"),
            container_type=ai_result.get("container_type", "瓶"),
            suggested_storage_temp=ai_result.get("suggested_storage_temp"),
            description=ai_result.get("description"),
            image_url=upload_result["url"],
            cloudinary_public_id=upload_result["public_id"],
        )

        logger.info(f"使用者 {user_id} AI 辨識酒標成功: {response.name}")
        return response

    except Exception as e:
        logger.error(f"AI 辨識失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 辨識失敗: {str(e)}",
        ) from e


# ============ Split & History Match Schemas ============

class SplitRequest(BaseModel):
    """拆分酒款請求"""
    split_count: int



# ============ Split & History Match Routes ============

@router.post("/wine-items/{id}/split")
def split_wine_item(
    id: int,
    data: SplitRequest,
    db: DBSession,
    user_id: CurrentUserId
):
    """
    拆分酒款 - 將多瓶酒款拆分成獨立記錄
    
    例如：將 quantity=3 的酒款拆分出 2 瓶，
    原酒款變成 quantity=1，新建 2 筆各 quantity=1 的記錄。
    """
    # 驗證拆分數量
    if data.split_count < 1:
        raise HTTPException(status_code=400, detail="拆分數量必須大於 0")
    
    # 取得原酒款
    item = db.query(WineItem).filter(WineItem.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到酒款")
    
    # 驗證擁有權（透過酒窖）
    from src.models.wine_cellar import WineCellar
    cellar = db.query(WineCellar).filter(WineCellar.id == item.cellar_id).first()
    if not cellar or cellar.user_id != user_id:
        raise HTTPException(status_code=403, detail="無權限操作此酒款")
    
    # 驗證數量足夠
    if item.quantity <= data.split_count:
        raise HTTPException(
            status_code=400, 
            detail=f"拆分數量 ({data.split_count}) 必須小於原數量 ({item.quantity})"
        )
    
    # 減少原酒款數量
    item.quantity -= data.split_count
    
    # 建立新酒款記錄
    new_items = []
    for _ in range(data.split_count):
        new_item = WineItem(
            cellar_id=item.cellar_id,
            name=item.name,
            wine_type=item.wine_type,
            brand=item.brand,
            vintage=item.vintage,
            region=item.region,
            country=item.country,
            abv=item.abv,
            quantity=1,
            space_units=item.space_units / (item.quantity + data.split_count),
            container_type=item.container_type,
            bottle_status=item.bottle_status,
            preservation_type=item.preservation_type,
            remaining_amount=item.remaining_amount,
            disposition=item.disposition,
            purchase_price=item.purchase_price,
            retail_price=item.retail_price,
            purchase_date=item.purchase_date,
            optimal_drinking_start=item.optimal_drinking_start,
            optimal_drinking_end=item.optimal_drinking_end,
            storage_location=item.storage_location,
            storage_temp=item.storage_temp,
            image_url=item.image_url,
            cloudinary_public_id=item.cloudinary_public_id,
            notes=item.notes,
            tasting_notes=item.tasting_notes,
            recognized_by_ai=item.recognized_by_ai,
            split_from_id=item.id,  # 記錄來源
        )
        db.add(new_item)
        new_items.append(new_item)
    
    db.commit()
    
    # Refresh to get IDs
    for new_item in new_items:
        db.refresh(new_item)
    
    logger.info(f"使用者 {user_id} 拆分酒款 {id}，拆出 {data.split_count} 瓶")
    
    return {
        "original_remaining": item.quantity,
        "new_items": [_build_wine_item_response(ni) for ni in new_items]
    }


@router.patch("/wine-items/{id}/disposition")
def update_disposition(
    id: int,
    disposition: str,  # personal / gift / sale / collection
    db: DBSession,
    user_id: CurrentUserId
):
    """
    更新酒款用途（自飲/送禮/待售/收藏）
    """
    valid_dispositions = ['personal', 'gift', 'sale', 'collection']
    if disposition not in valid_dispositions:
        raise HTTPException(
            status_code=400,
            detail=f"無效的用途，必須是: {', '.join(valid_dispositions)}"
        )
    
    # 取得酒款
    item = db.query(WineItem).filter(WineItem.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到酒款")
    
    # 驗證擁有權
    from src.models.wine_cellar import WineCellar
    cellar = db.query(WineCellar).filter(WineCellar.id == item.cellar_id).first()
    if not cellar or cellar.user_id != user_id:
        raise HTTPException(status_code=403, detail="無權限操作此酒款")
    
    item.disposition = disposition
    db.commit()
    db.refresh(item)
    
    logger.info(f"使用者 {user_id} 更新酒款 {id} 用途為 {disposition}")
    
    return _build_wine_item_response(item)
