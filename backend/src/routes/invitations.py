from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.models.invitation import Invitation
from src.schemas.invitation import InvitationCreate, InvitationResponse, InvitationUpdate
from src.services import storage

router = APIRouter(
    prefix="/invitations",
    tags=["Invitations"],
    responses={404: {"description": "Not found"}},
)

@router.post("/upload-image", status_code=status.HTTP_201_CREATED)
async def upload_invitation_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上傳邀請函主題圖片
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="檔案必須是圖片格式"
        )
    
    try:
        content = await file.read()
        upload_result = storage.upload_image(content, folder="invitations")
        return {"url": upload_result["url"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"圖片上傳失敗: {str(e)}"
        )

@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(invitation: InvitationCreate, db: Session = Depends(get_db)):
    """建立新的邀請函"""
    db_invitation = Invitation(**invitation.model_dump())
    db.add(db_invitation)
    db.commit()
    db.refresh(db_invitation)
    return db_invitation


from src.models.wine_item import WineItem

# ... (Previous imports)

@router.get("/{invitation_id}", response_model=InvitationResponse)
def get_invitation(invitation_id: int, db: Session = Depends(get_db)):
    """取得邀請函詳情 (包含酒款公開資訊)"""
    db_invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not db_invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # 手動撈取酒款資訊 (因為 Invitation.wine_ids 是 JSON list，無關聯)
    if db_invitation.wine_ids:
        # 確保 wine_ids 是 list
        wids = db_invitation.wine_ids if isinstance(db_invitation.wine_ids, list) else []
        if wids:
            wines = db.query(WineItem).filter(WineItem.id.in_(wids)).all()
            # 轉換為 WineSimple 格式 (或讓 Pydantic 自動轉換)
            db_invitation.wine_details = wines
        else:
            db_invitation.wine_details = []
    else:
        db_invitation.wine_details = []

    return db_invitation

@router.get("/{invitation_id}/flex")
def get_invitation_flex(invitation_id: int, db: Session = Depends(get_db)):
    """取得邀請函的 Flex Message JSON (供前端 LIFF 發送)"""
    from src.services.flex_message import create_invitation_flex_message

    db_invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not db_invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # 取得關聯的酒款
    wines = []
    if db_invitation.wine_ids:
        wines = db.query(WineItem).filter(WineItem.id.in_(db_invitation.wine_ids)).all()

    # 使用完整版 Flex Message（包含地點和酒名）
    return create_invitation_flex_message(db_invitation, wines)
