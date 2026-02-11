from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from src.database import Base

class Invitation(Base):
    """
    品飲聚會邀請函模型
    """
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    # 假設目前系統尚無完整登入或是 User ID 為 Integer，先保留欄位但設為 nullable
    # 暫時移除外鍵約束，避免users表不存在導致錯誤
    host_id = Column(Integer, nullable=True)
    
    title = Column(String(100), nullable=False, comment="聚會標題")
    description = Column(Text, nullable=True, comment="聚會描述")
    event_time = Column(DateTime, nullable=False, comment="聚會時間")
    location = Column(String(200), nullable=True, comment="地點名稱")
    
    # 地點座標 (選填，用於地圖導航)
    latitude = Column(String(50), nullable=True) # 使用 String 以免 float 精度問題，或者單純 float
    longitude = Column(String(50), nullable=True)
    
    theme_image_url = Column(String(500), nullable=True, comment="主題圖片 URL")
    
    # 儲存與此邀請相關的酒款 ID 列表
    # 使用 generic JSON type，SQLAlchemy 會自動處理 SQLite (as Text) 和 PG (as JSON)
    wine_ids = Column(JSON, default=list, comment="酒款 ID 列表")
    
    # 報名者列表 [{line_user_id, name, avatar_url}]
    attendees = Column(JSON, default=list, comment="報名者列表")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # host = relationship("User", back_populates="invitations")

    def __repr__(self):
        return f"<Invitation {self.title}>"
