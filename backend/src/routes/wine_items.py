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
from pydantic import BaseModel

from src.models.wine_item import WineItem
from src.models.wine_cellar import WineCellar
from src.routes.dependencies import DBSession, CurrentUserId
from src.services import wine_vision, storage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Wine Items"])


# ============ Schemas ============

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
    recognized_by_ai: int = 0


class WineItemUpdate(BaseModel):
    """更新酒款的請求資料"""
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
    purchase_price: Optional[float] = None
    retail_price: Optional[float] = None
    storage_location: Optional[str] = None
    storage_temp: Optional[str] = None
    notes: Optional[str] = None
    tasting_notes: Optional[str] = None


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

    wine_items = query.all()
    return [_build_wine_item_response(item) for item in wine_items]


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

        # 建立酒款
        wine_item = WineItem(**item_data)
        db.add(wine_item)
        db.commit()
        db.refresh(wine_item)

        logger.info(f"使用者 {user_id} 新增酒款: {wine_item.name} (ID: {wine_item.id})")
        return _build_wine_item_response(wine_item)
        
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
async def update_wine_item(id: int, data: WineItemUpdate, db: DBSession, user_id: CurrentUserId):
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
