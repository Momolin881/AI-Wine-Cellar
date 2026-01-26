
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import uuid

from src.database import get_db
from src.models.invitation import Invitation
from src.models.wine_item import WineItem
from src.services.flex_message import create_invitation_flex_message

router = APIRouter()

# Pydantic Models
class InvitationCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_time: datetime
    location: Optional[str] = None
    wine_ids: List[int] # WineTable uses Integer ID by default? Let's check WineItem model.
    theme_image_url: Optional[str] = None

class InvitationResponse(BaseModel):
    id: uuid.UUID
    title: str
    event_time: datetime
    location: Optional[str]
    flex_message: dict # 回傳給前端用的 Flex Message JSON

    class Config:
        from_attributes = True

@router.post("/invitations", response_model=InvitationResponse)
async def create_invitation(
    invitation_in: InvitationCreate,
    db: Session = Depends(get_db)
):
    """
    建立新的品飲聚會邀請
    """
    # 1. 驗證酒款是否存在
    # WineItem use Integer ID? Let's verify. Assuming yes for now.
    wines = db.query(WineItem).filter(WineItem.id.in_(invitation_in.wine_ids)).all()
    if len(wines) != len(invitation_in.wine_ids):
        raise HTTPException(status_code=400, detail="部分酒款 ID 無效")

    # 2. 建立邀請函記錄
    db_invitation = Invitation(
        title=invitation_in.title,
        description=invitation_in.description,
        event_time=invitation_in.event_time,
        location=invitation_in.location,
        theme_image_url=invitation_in.theme_image_url,
        wine_ids=invitation_in.wine_ids
        # host_id=current_user.id # 暫時省略
    )
    db.add(db_invitation)
    db.commit()
    db.refresh(db_invitation)

    # 3. 產生 Flex Message
    flex_message = create_invitation_flex_message(db_invitation, wines)

    return InvitationResponse(
        id=db_invitation.id,
        title=db_invitation.title,
        event_time=db_invitation.event_time,
        location=db_invitation.location,
        flex_message=flex_message
    )

@router.get("/invitations/{invitation_id}")
async def get_invitation(
    invitation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    取得邀請函詳情
    """
    invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="邀請函不存在")
    
    # 查詢酒款詳情
    wines = db.query(WineItem).filter(WineItem.id.in_(invitation.wine_ids)).all()
    
    return {
        "invitation": invitation,
        "wines": wines
    }
