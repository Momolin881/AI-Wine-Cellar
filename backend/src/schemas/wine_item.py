"""
WineItem Pydantic Schemas

酒款相關的請求和回應驗證 schemas — 唯一權威來源。
路由檔案應 import 此模組，而非自行定義。
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── 建立酒款 ──

class WineItemCreate(BaseModel):
    """新增酒款的請求資料"""
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
    preservation_type: str = "immediate"   # immediate / aging
    remaining_amount: str = "full"
    disposition: str = "personal"          # personal / gift / sale / collection
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


# ── 更新酒款 ──

class WineItemUpdate(BaseModel):
    """更新酒款的請求資料（所有欄位可選）"""
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


# ── 酒款回應 ──

class WineItemResponse(BaseModel):
    """酒款 API 回應"""
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

    model_config = {"from_attributes": True}


# ── AI 辨識回應 ──

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


# ── 拆分相關 ──

class SplitRequest(BaseModel):
    """拆分酒款請求"""
    split_count: int = Field(..., ge=1, le=100, description="要拆分的數量")


class SplitResponse(BaseModel):
    """拆分結果"""
    original_remaining: int = Field(..., description="原酒款剩餘數量")
    new_items: List[WineItemResponse] = Field(..., description="新建的酒款列表")


# ── 歷史比對相關 ──

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
    matched: bool = Field(..., description="是否找到相符記錄")
    history: List[HistoryMatch] = Field(default_factory=list, description="歷史記錄列表")
