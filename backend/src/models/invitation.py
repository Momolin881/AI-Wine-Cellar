
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from src.database import Base

class Invitation(Base):
    """
    品飲聚會邀請函模型
    """
    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id = Column(String, ForeignKey("users.id"), nullable=True) # 暫時允許 Null，如果還沒實作使用者系統
    
    title = Column(String, nullable=False, comment="聚會標題")
    description = Column(Text, nullable=True, comment="聚會描述")
    event_time = Column(DateTime, nullable=False, comment="聚會時間")
    location = Column(String, nullable=True, comment="地點名稱")
    
    # 地點座標 (選填，用於地圖導航)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    theme_image_url = Column(String, nullable=True, comment="主題圖片 URL")
    
    # 儲存與此邀請相關的酒款 ID 列表
    # 使用 JSONB 儲存 list of strings/integers
    wine_ids = Column(JSONB, default=list, comment="酒款 ID 列表")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯 (如果有 User model)
    # host = relationship("User", back_populates="invitations")

    def __repr__(self):
        return f"<Invitation {self.title}>"
