"""
Fridge 和 FridgeCompartment 模型（舊版 - 待遷移）

此為舊版酒窖模型，目前由 budget_service、recipe_service、fridge_members、fridge_export 使用。
新系統請使用 WineCellar 模型。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base


class Fridge(Base):
    """酒窖模型（舊版）"""

    __tablename__ = "fridges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 酒窖資訊
    model_name = Column(String(255), nullable=True)  # 酒窖名稱（可選）
    total_capacity_liters = Column(Float, nullable=False)  # 總容量（公升）

    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 關聯
    owner = relationship("User", back_populates="fridges")
    compartments = relationship("FridgeCompartment", back_populates="fridge", cascade="all, delete-orphan")
    food_items = relationship("FoodItem", back_populates="fridge", cascade="all, delete-orphan")
    members = relationship("FridgeMember", back_populates="fridge", cascade="all, delete-orphan")
    invites = relationship("FridgeInvite", back_populates="fridge", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Fridge(id={self.id}, user_id={self.user_id}, model='{self.model_name}')>"


class FridgeCompartment(Base):
    """酒窖分區模型（舊版）"""

    __tablename__ = "fridge_compartments"

    id = Column(Integer, primary_key=True, index=True)
    fridge_id = Column(Integer, ForeignKey("fridges.id", ondelete="CASCADE"), nullable=False, index=True)

    # 分區資訊
    name = Column(String(100), nullable=False)  # 分區名稱（如「冷藏上層」、「冷凍抽屜」）
    parent_type = Column(String(50), nullable=False)  # 父類別：「冷藏」或「冷凍」
    capacity_liters = Column(Float, nullable=True)  # 分區容量（可選）

    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 關聯
    fridge = relationship("Fridge", back_populates="compartments")
    food_items = relationship("FoodItem", back_populates="compartment")

    def __repr__(self):
        return f"<FridgeCompartment(id={self.id}, name='{self.name}', parent='{self.parent_type}')>"
