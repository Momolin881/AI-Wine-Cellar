"""
WineCellar 模型

儲存酒窖/酒櫃資訊。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base


class WineCellar(Base):
    """酒窖模型"""

    __tablename__ = "wine_cellars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 酒窖資訊
    name = Column(String(255), default="我的酒窖", nullable=False)  # 酒窖名稱
    description = Column(String(500), nullable=True)  # 描述
    total_capacity = Column(Integer, default=50, nullable=False)  # 總容量（瓶位數）

    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 關聯
    owner = relationship("User", back_populates="wine_cellars")
    wine_items = relationship("WineItem", back_populates="cellar", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WineCellar(id={self.id}, name='{self.name}', user_id={self.user_id})>"

    @property
    def used_capacity(self) -> float:
        """計算已使用容量"""
        return sum(item.space_units * item.quantity for item in self.wine_items if item.status == 'active')

    @property
    def available_capacity(self) -> float:
        """計算剩餘容量"""
        return self.total_capacity - self.used_capacity

    @property
    def total_value(self) -> float:
        """計算酒窖總價值"""
        return sum(item.total_value for item in self.wine_items if item.status == 'active')
