from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.models.invitation import Invitation
from src.schemas.invitation import InvitationCreate, InvitationResponse, InvitationUpdate
# from src.services.invitation_service import generate_invitation_flex_message

router = APIRouter(
    prefix="/invitations",
    tags=["Invitations"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(invitation: InvitationCreate, db: Session = Depends(get_db)):
    """建立新的邀請函"""
    db_invitation = Invitation(**invitation.model_dump())
    db.add(db_invitation)
    db.commit()
    db.refresh(db_invitation)
    return db_invitation

@router.get("/{invitation_id}", response_model=InvitationResponse)
def get_invitation(invitation_id: int, db: Session = Depends(get_db)):
    """取得邀請函詳情"""
    db_invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not db_invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return db_invitation

@router.get("/{invitation_id}/flex")
def get_invitation_flex(invitation_id: int, db: Session = Depends(get_db)):
    """取得邀請函的 Flex Message JSON (供前端 LIFF 發送)"""
    db_invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not db_invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # TODO: 這裡應該呼叫 Service 產生真正的 Flex Message
    # 暫時回傳一個簡單的範例
    flex_message = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": db_invitation.theme_image_url or "https://example.com/wine_party.jpg",
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": db_invitation.title,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "時間",
                                    "color": "#aaaaaa",
                                    "size": "sm",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": db_invitation.event_time.strftime("%Y-%m-%d %H:%M"),
                                    "wrap": True,
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 5
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "查看詳情",
                        "uri": f"https://liff.line.me/YOUR_LIFF_ID/invitation/{invitation_id}"
                    }
                }
            ],
            "flex": 0
        }
    }
    
    return flex_message
