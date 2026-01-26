
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

class WineSimple(BaseModel):
    id: int
    name: str
    wine_type: str
    image_url: Optional[str] = None
    vintage: Optional[int] = None

class InvitationResponse(InvitationBase):
    id: int
    host_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # 加入 wine_details 用於回傳詳細酒款資訊 (公開資訊)
    wine_details: List[WineSimple] = []

    class Config:
        from_attributes = True
