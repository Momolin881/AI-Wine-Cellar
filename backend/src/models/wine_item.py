"""
WineItem 模型

儲存酒款資訊，包含名稱、類型、年份、產區、價格、圖片等。
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base


class WineItem(Base):
    """酒款模型"""

    __tablename__ = "wine_items"

    id = Column(Integer, primary_key=True, index=True)
    cellar_id = Column(Integer, ForeignKey("wine_cellars.id", ondelete="CASCADE"), nullable=False, index=True)

    # 酒款基本資訊
    name = Column(String(255), nullable=False, index=True)  # 酒名
    wine_type = Column(String(100), nullable=False)  # 酒類（紅酒、白酒、氣泡酒、威士忌等）
    brand = Column(String(255), nullable=True)  # 品牌 / 酒莊
    vintage = Column(Integer, nullable=True)  # 年份
    region = Column(String(255), nullable=True)  # 產區（如：波爾多、勃根地、蘇格蘭）
    country = Column(String(100), nullable=True)  # 國家
    abv = Column(Float, nullable=True)  # 酒精濃度 ABV (Alcohol by Volume) %

    # 數量與空間
    quantity = Column(Integer, default=1, nullable=False)  # 數量（瓶數）
    space_units = Column(Float, default=1.0, nullable=False)  # 占用空間單位（瓶位數）
    container_type = Column(String(50), default="瓶", nullable=False)  # 容器類型（瓶、箱、桶）

    # 開瓶狀態與剩餘量
    bottle_status = Column(String(20), default='unopened', nullable=False)  # unopened / opened
    preservation_type = Column(String(50), default='immediate', nullable=False)  # immediate (即飲) / aging (陳年)
    remaining_amount = Column(String(20), default='full', nullable=False)  # full / 3/4 / 1/2 / 1/4 / empty
    opened_at = Column(DateTime, nullable=True)  # 開瓶時間

    # 價格
    purchase_price = Column(Float, nullable=True)  # 進貨價（台幣）
    retail_price = Column(Float, nullable=True)  # 零售價（台幣）

    # 日期
    purchase_date = Column(Date, default=date.today, nullable=False)  # 購買日期
    optimal_drinking_start = Column(Date, nullable=True)  # 最佳飲用期開始
    optimal_drinking_end = Column(Date, nullable=True)  # 最佳飲用期結束

    # 儲存位置
    storage_location = Column(String(255), nullable=True)  # 存放位置（如：A架第2層）
    storage_temp = Column(String(50), nullable=True)  # 建議儲存溫度（如：12-14°C）

    # 圖片
    image_url = Column(String(512), nullable=True)  # Cloudinary URL
    cloudinary_public_id = Column(String(255), nullable=True)  # Cloudinary public_id（用於刪除）

    # AI 辨識相關
    recognized_by_ai = Column(Integer, default=0, nullable=False)  # 是否由 AI 辨識（0: 手動, 1: AI）

    # 狀態
    status = Column(String(20), default='active', nullable=False, index=True)  # active / sold / gifted / consumed
    status_changed_at = Column(DateTime, nullable=True)  # 狀態變更時間
    status_changed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # 用途/去向 (personal: 自飲, gift: 送禮, sale: 售出, collection: 收藏)
    disposition = Column(String(20), default='personal', nullable=False)
    
    # 拆分來源 (如果這瓶酒是從另一筆拆分出來的，記錄原始 ID)
    split_from_id = Column(Integer, ForeignKey("wine_items.id", ondelete="SET NULL"), nullable=True)

    # 備註
    notes = Column(String(1000), nullable=True)  # 備註（AI辨識結果、其他說明）

    # 品飲筆記（喝完時填寫）
    tasting_notes = Column(String(1000), nullable=True)  # 舊欄位，保留相容
    rating = Column(Integer, nullable=True)  # 評分 1-10
    flavor_tags = Column(String(500), nullable=True)  # 風味標籤 JSON array
    aroma = Column(String(500), nullable=True)  # 香氣
    palate = Column(String(500), nullable=True)  # 口感
    finish = Column(String(500), nullable=True)  # 餘韻

    # 風味分析 (1-5分)
    acidity = Column(Integer, nullable=True)  # 酸度
    tannin = Column(Integer, nullable=True)  # 單寧
    body = Column(Integer, nullable=True)  # 酒體
    sweetness = Column(Integer, nullable=True)  # 甜度
    alcohol_feel = Column(Integer, nullable=True)  # 酒感 (不同於 ABV，是主觀感受)

    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 關聯
    cellar = relationship("WineCellar", back_populates="wine_items")

    def __repr__(self):
        return f"<WineItem(id={self.id}, name='{self.name}', type='{self.wine_type}', vintage={self.vintage})>"

    @property
    def is_optimal_now(self) -> bool:
        """檢查是否在最佳飲用期"""
        today = date.today()
        if self.optimal_drinking_start and today < self.optimal_drinking_start:
            return False
        if self.optimal_drinking_end and today > self.optimal_drinking_end:
            return False
        return True

    @property
    def total_value(self) -> float:
        """計算總價值（進貨價 * 數量）"""
        if self.purchase_price:
            return self.purchase_price * self.quantity
        return 0.0
