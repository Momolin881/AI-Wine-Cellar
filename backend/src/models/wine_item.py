"""
WineItem 模型

儲存酒款資訊，包含名稱、類型、年份、產區、價格、圖片等。
匹配實際 Production 資料庫結構。
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from src.database import Base


class WineItem(Base):
    """酒款模型 — 與 Production DB 完全同步"""

    __tablename__ = "wine_items"

    id = Column(Integer, primary_key=True, index=True)
    cellar_id = Column(Integer, ForeignKey("wine_cellars.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── 酒款基本資訊 ──
    name = Column(String(255), nullable=False, index=True)       # 酒名
    wine_type = Column(String(50), nullable=True)                # 酒類型（紅酒、白酒、威士忌…）
    brand = Column(String(255), nullable=True)                   # 品牌 / 酒莊
    vintage = Column(Integer, nullable=True)                     # 年份
    region = Column(String(255), nullable=True)                  # 產區
    country = Column(String(255), nullable=True)                 # 國家
    abv = Column(Float, nullable=True)                           # 酒精濃度 %

    # ── 數量與容器 ──
    quantity = Column(Integer, default=1, nullable=True)          # 數量（瓶數）
    space_units = Column(Float, default=1.0, nullable=True)      # 佔用空間單位
    container_type = Column(String(50), default='瓶', nullable=True)  # 容器類型

    # ── 酒瓶狀態 ──
    bottle_status = Column(String(20), default='unopened', nullable=True)    # 開瓶狀態 (unopened / opened)
    preservation_type = Column(String(20), default='immediate', nullable=True)  # 保存類型 (immediate / aging)
    remaining_amount = Column(String(10), default='full', nullable=True)     # 剩餘量 (full / 3/4 / 1/2 / 1/4 / empty)
    opened_at = Column(DateTime, nullable=True)                              # 開瓶時間

    # ── 用途與來源 ──
    disposition = Column(String(20), default='personal', nullable=True)  # 用途 (personal / gift / sale / collection)
    split_from_id = Column(Integer, nullable=True)                       # 拆分來源酒款 ID
    recognized_by_ai = Column(Integer, default=0, nullable=True)         # 是否由 AI 辨識 (0: 手動, 1: AI)

    # ── 價格 ──
    purchase_price = Column(Float, nullable=True)    # 進貨價（台幣）
    retail_price = Column(Float, nullable=True)      # 建議售價

    # ── 日期 ──
    purchase_date = Column(Date, nullable=True)              # 購買日期
    optimal_drinking_start = Column(Date, nullable=True)     # 最佳飲用期開始
    optimal_drinking_end = Column(Date, nullable=True)       # 最佳飲用期結束

    # ── 儲存資訊 ──
    storage_location = Column(String(255), nullable=True)    # 儲存位置
    storage_temp = Column(String(50), nullable=True)         # 建議儲存溫度

    # ── 圖片 ──
    image_url = Column(Text, nullable=True)                  # 圖片 URL
    cloudinary_public_id = Column(String(255), nullable=True)  # Cloudinary public_id

    # ── 狀態管理 ──
    status = Column(String(20), default='active', nullable=True)  # 狀態 (active / sold / gifted / consumed)
    status_changed_at = Column(DateTime, nullable=True)           # 狀態變更時間
    status_changed_by = Column(Integer, nullable=True)            # 狀態變更者

    # ── 備註 ──
    notes = Column(Text, nullable=True)            # 一般備註
    tasting_notes = Column(Text, nullable=True)    # 品酒筆記（舊欄位）

    # ── 品評欄位 ──
    rating = Column(Integer, nullable=True)        # 評分 1-10
    review = Column(Text, nullable=True)           # 文字評論
    flavor_tags = Column(Text, nullable=True)      # 風味標籤 JSON
    aroma = Column(Text, nullable=True)            # 香氣
    palate = Column(Text, nullable=True)           # 口感
    finish = Column(Text, nullable=True)           # 餘韻
    acidity = Column(Integer, nullable=True)       # 酸度 1-5
    tannin = Column(Integer, nullable=True)        # 單寧 1-5
    body = Column(Integer, nullable=True)          # 酒體 1-5
    sweetness = Column(Integer, nullable=True)     # 甜度 1-5
    alcohol_feel = Column(Integer, nullable=True)  # 酒精感 1-5

    # ── 時間戳記 ──
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # ── 關聯 ──
    cellar = relationship("WineCellar", back_populates="wine_items")

    # ── 計算屬性 ──
    @property
    def is_optimal_now(self) -> bool:
        """是否在最佳飲用期內"""
        today = date.today()
        start = self.optimal_drinking_start
        end = self.optimal_drinking_end
        if start and end:
            return start <= today <= end
        if end:
            return today <= end
        return False

    @property
    def total_value(self) -> float:
        """該酒款的總價值（單價 × 數量）"""
        return float(self.purchase_price or 0) * (self.quantity or 1)

    def __repr__(self):
        return f"<WineItem(id={self.id}, name='{self.name}', vintage={self.vintage})>"