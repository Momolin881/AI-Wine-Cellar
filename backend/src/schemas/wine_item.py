"""
WineItem Pydantic schemas

包含酒款相關的請求和回應驗證 schemas。
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WineItemBase(BaseModel):
    """酒款基礎欄位"""
    name: str = Field(..., min_length=1, max_length=255, description="酒名")
    wine_type: str = Field(..., description="酒類（紅酒、白酒、威士忌等）")
    brand: Optional[str] = Field(None, max_length=255, description="品牌 / 酒莊")
    vintage: Optional[int] = Field(None, description="年份")
    region: Optional[str] = Field(None, max_length=255, description="產區")
    country: Optional[str] = Field(None, max_length=100, description="國家")
    abv: Optional[float] = Field(None, description="酒精濃度 %")
    quantity: int = Field(1, ge=1, description="數量（瓶數）")
    purchase_price: Optional[float] = Field(None, ge=0, description="進貨價（台幣）")
    purchase_date: date = Field(default_factory=date.today, description="購買日期")
    disposition: str = Field('personal', description="用途：personal/gift/sale/collection")


class WineItemCreate(WineItemBase):
    """新增酒款請求"""
    cellar_id: int = Field(..., description="酒窖 ID")
    image_url: Optional[str] = Field(None, description="圖片 URL")
    cloudinary_public_id: Optional[str] = Field(None, description="Cloudinary public_id")
    recognized_by_ai: int = Field(0, description="是否由 AI 辨識（0: 手動, 1: AI）")
    notes: Optional[str] = Field(None, max_length=1000, description="備註")
    tasting_notes: Optional[str] = Field(None, max_length=1000, description="品酒筆記")


class WineItemUpdate(BaseModel):
    """更新酒款請求（所有欄位可選）"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    wine_type: Optional[str] = None
    brand: Optional[str] = None
    vintage: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    abv: Optional[float] = None
    quantity: Optional[int] = Field(None, ge=1)
    purchase_price: Optional[float] = Field(None, ge=0)
    purchase_date: Optional[date] = None
    disposition: Optional[str] = None
    bottle_status: Optional[str] = None
    remaining_amount: Optional[str] = None
    notes: Optional[str] = None
    tasting_notes: Optional[str] = None


class WineItemResponse(WineItemBase):
    """酒款回應"""
    id: int
    cellar_id: int
    image_url: Optional[str] = None
    cloudinary_public_id: Optional[str] = None
    bottle_status: str = 'unopened'
    preservation_type: str = 'immediate'
    remaining_amount: str = 'full'
    opened_at: Optional[datetime] = None
    status: str = 'active'
    split_from_id: Optional[int] = None
    notes: Optional[str] = None
    tasting_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- 拆分相關 ---

class SplitRequest(BaseModel):
    """拆分酒款請求"""
    split_count: int = Field(..., ge=1, le=100, description="要拆分的數量")


class SplitResponse(BaseModel):
    """拆分結果"""
    original_remaining: int = Field(..., description="原酒款剩餘數量")
    new_items: List[WineItemResponse] = Field(..., description="新建的酒款列表")


# --- 歷史比對相關 ---

class HistoryMatch(BaseModel):
    """歷史比對結果"""
    id: int
    name: str
    brand: Optional[str] = None
    vintage: Optional[int] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[date] = None
    tasting_notes: Optional[str] = None
    image_url: Optional[str] = None


class HistoryMatchResponse(BaseModel):
    """歷史比對 API 回應"""
    matched: bool = Field(..., description="是否找到相符記錄")
    history: List[HistoryMatch] = Field(default_factory=list, description="歷史記錄列表")
