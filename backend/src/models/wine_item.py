"""
WineItem 模型

儲存酒款資訊，包含名稱、類型、年份、產區、價格、圖片等。
匹配實際資料庫結構（171筆資料）
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship

from src.database import Base


class WineItem(Base):
    """酒款模型 - 匹配實際資料庫結構"""

    __tablename__ = "wine_items"

    id = Column(Integer, primary_key=True, index=True)
    cellar_id = Column(Integer, ForeignKey("wine_cellars.id", ondelete="CASCADE"), nullable=False, index=True)

    # 酒款基本資訊（匹配資料庫）
    name = Column(String(255), nullable=False, index=True)  # 酒名
    producer = Column(String(255), nullable=True)  # 生產商/酒莊
    region = Column(String(255), nullable=True)  # 產區
    vintage = Column(Integer, nullable=True)  # 年份
    grape_variety = Column(String(255), nullable=True)  # 葡萄品種
    wine_type = Column(String(50), nullable=True)  # 酒類型
    alcohol_content = Column(Numeric(4,2), nullable=True)  # 酒精含量
    
    # 價格和貨幣
    price = Column(Numeric(10,2), nullable=True)  # 價格
    currency = Column(String(10), default='TWD', nullable=True)  # 貨幣
    
    # 日期
    purchase_date = Column(Date, nullable=True)  # 購買日期
    optimal_drinking_start = Column(Date, nullable=True)  # 最佳飲用期開始
    optimal_drinking_end = Column(Date, nullable=True)  # 最佳飲用期結束
    
    # 儲存和其他資訊
    storage_location = Column(String(255), nullable=True)  # 儲存位置
    notes = Column(Text, nullable=True)  # 備註
    image_url = Column(Text, nullable=True)  # 圖片URL
    barcode = Column(String(50), nullable=True)  # 條碼
    quantity = Column(Integer, default=1, nullable=True)  # 數量
    
    # 用戶關聯
    created_by = Column(Integer, nullable=True)  # 創建者
    
    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # 品評相關欄位（新增的）
    rating = Column(Integer, nullable=True)  # 評分
    review = Column(Text, nullable=True)  # 評論
    flavor_tags = Column(Text, nullable=True)  # 風味標籤
    aroma = Column(Text, nullable=True)  # 香氣
    palate = Column(Text, nullable=True)  # 口感
    finish = Column(Text, nullable=True)  # 餘韻
    acidity = Column(Integer, nullable=True)  # 酸度
    tannin = Column(Integer, nullable=True)  # 單寧
    body = Column(Integer, nullable=True)  # 酒體
    sweetness = Column(Integer, nullable=True)  # 甜度
    alcohol_feel = Column(Integer, nullable=True)  # 酒精感

    # 關係
    cellar = relationship("WineCellar", back_populates="wine_items")

    def __repr__(self):
        return f"<WineItem(id={self.id}, name='{self.name}', vintage={self.vintage})>"