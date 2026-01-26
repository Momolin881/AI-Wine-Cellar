from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel

class InvitationBase(BaseModel):
    title: str
    event_time: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    theme_image_url: Optional[str] = None
    wine_ids: List[int] = []

class InvitationCreate(InvitationBase):
    pass

class InvitationUpdate(InvitationBase):
    title: Optional[str] = None
    event_time: Optional[datetime] = None

class InvitationResponse(InvitationBase):
    id: int
    host_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # 這裡可以加入 wine_details 如果需要回傳詳細酒款資訊
    # wine_details: List[WineItemResponse] = []

    class Config:
        from_attributes = True
