"""
WineCellar 模型

儲存酒窖/酒櫃資訊。
匹配實際 Production 資料庫結構。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from src.database import Base


class WineCellar(Base):
    """酒窖模型 — 與 Production DB 完全同步"""

    __tablename__ = "wine_cellars"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    # 酒窖資訊
    name = Column(String(255), nullable=False)       # 酒窖名稱
    description = Column(Text, nullable=True)        # 描述
    location = Column(String(255), nullable=True)    # 位置
    capacity = Column(Integer, nullable=True)        # 容量

    # 溫濕度控制
    temperature_min = Column(Numeric(4,1), nullable=True)
    temperature_max = Column(Numeric(4,1), nullable=True)
    humidity_min = Column(Numeric(5,2), nullable=True)
    humidity_max = Column(Numeric(5,2), nullable=True)

    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # 關聯
    wine_items = relationship("WineItem", back_populates="cellar")
    owner = relationship("User", foreign_keys=[owner_id])

    def __repr__(self):
        return f"<WineCellar(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"