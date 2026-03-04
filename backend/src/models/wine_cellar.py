"""
WineCellar 模型

儲存酒窖/酒櫃資訊。
匹配實際資料庫結構（171筆資料）
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from src.database import Base


class WineCellar(Base):
    """酒窖模型 - 匹配實際資料庫結構"""

    __tablename__ = "wine_cellars"

    id = Column(Integer, primary_key=True, index=True)
    # 注意：資料庫中是 owner_id，不是 user_id
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    # 酒窖資訊（匹配資料庫）
    name = Column(String(255), nullable=False)  # 酒窖名稱
    description = Column(Text, nullable=True)  # 描述
    location = Column(String(255), nullable=True)  # 位置
    capacity = Column(Integer, nullable=True)  # 容量

    # 溫濕度控制
    temperature_min = Column(Numeric(4,1), nullable=True)  # 最低溫度
    temperature_max = Column(Numeric(4,1), nullable=True)  # 最高溫度
    humidity_min = Column(Numeric(5,2), nullable=True)  # 最低濕度
    humidity_max = Column(Numeric(5,2), nullable=True)  # 最高濕度

    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # 關係（為了向後兼容，提供 user_id 屬性）
    @property
    def user_id(self):
        """向後兼容的 user_id 屬性"""
        return self.owner_id
    
    @user_id.setter
    def user_id(self, value):
        """向後兼容的 user_id setter"""
        self.owner_id = value

    # 關聯
    wine_items = relationship("WineItem", back_populates="cellar")
    owner = relationship("User", foreign_keys=[owner_id])

    def __repr__(self):
        return f"<WineCellar(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"