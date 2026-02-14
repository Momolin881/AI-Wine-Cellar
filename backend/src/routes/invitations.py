from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.models.invitation import Invitation
from src.schemas.invitation import InvitationCreate, InvitationResponse, InvitationUpdate, AttendeeJoinRequest, AttendeeInfo
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
    
    # 確保 attendees 是 list 格式，避免序列化錯誤
    if isinstance(db_invitation.attendees, str):
        import json
        try:
            db_invitation.attendees = json.loads(db_invitation.attendees)
        except:
            db_invitation.attendees = []
    elif db_invitation.attendees is None:
        db_invitation.attendees = []
        
    # 確保 wine_details 存在
    db_invitation.wine_details = []
    
    return db_invitation

@router.get("/create-via-get", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation_via_get(
    title: str,
    event_time: str,
    location: str = "",
    description: str = "",
    wine_ids: str = "[]",  # JSON 字符串
    theme_image_url: str = "",
    db: Session = Depends(get_db)
):
    """
    透過 GET 請求建立邀請函 (解決 LINE App POST 請求限制)
    wine_ids 格式: "[1,2,3]" (JSON 字符串)
    """
    import json
    from datetime import datetime
    
    try:
        # 解析 wine_ids JSON 字符串
        wine_ids_list = json.loads(wine_ids) if wine_ids else []
        
        # 解析 event_time
        event_datetime = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
        
        db_invitation = Invitation(
            title=title,
            event_time=event_datetime,
            location=location,
            description=description,
            wine_ids=wine_ids_list,
            theme_image_url=theme_image_url or "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            host_id=None  # 明確設為 None，因為沒有用戶認證
        )
        db.add(db_invitation)
        db.commit()
        db.refresh(db_invitation)
        
        # 確保 attendees 是 list 格式，避免序列化錯誤
        if isinstance(db_invitation.attendees, str):
            import json
            try:
                db_invitation.attendees = json.loads(db_invitation.attendees)
            except:
                db_invitation.attendees = []
        elif db_invitation.attendees is None:
            db_invitation.attendees = []
            
        # 確保 wine_details 存在
        db_invitation.wine_details = []
        
        return db_invitation
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="wine_ids 必須是有效的 JSON 陣列字符串"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"日期格式錯誤: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立邀請失敗: {str(e)}"
        )


from src.models.wine_item import WineItem

# ... (Previous imports)

@router.get("/{invitation_id}", response_model=InvitationResponse)
def get_invitation(invitation_id: int, db: Session = Depends(get_db)):
    """取得邀請函詳情"""
    try:
        db_invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
        if not db_invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        # 查詢關聯的酒款詳情
        wine_details = []
        if db_invitation.wine_ids:
            try:
                wines = db.query(WineItem).filter(WineItem.id.in_(db_invitation.wine_ids)).all()
                wine_details = [
                    {
                        "id": wine.id,
                        "name": wine.name,
                        "vintage": wine.vintage,
                        "region": wine.region,
                        "wine_type": wine.wine_type,
                        "image_url": wine.image_url
                    }
                    for wine in wines
                ]
            except Exception as e:
                print(f"Error fetching wine details: {e}")
                wine_details = []
        
        db_invitation.wine_details = wine_details
        
        # 確保 attendees 是 list 格式，避免 JSON 轉換問題
        if isinstance(db_invitation.attendees, str):
            import json
            try:
                db_invitation.attendees = json.loads(db_invitation.attendees)
            except:
                db_invitation.attendees = []
        elif db_invitation.attendees is None:
            db_invitation.attendees = []
        
        # 構建回應資料，確保所有欄位都存在  
        response_data = {
            "id": db_invitation.id,
            "title": db_invitation.title,
            "event_time": db_invitation.event_time,
            "location": db_invitation.location or "",
            "description": db_invitation.description or "",
            "latitude": db_invitation.latitude,
            "longitude": db_invitation.longitude,
            "theme_image_url": db_invitation.theme_image_url,
            "wine_ids": db_invitation.wine_ids or [],
            "allow_forwarding": getattr(db_invitation, 'allow_forwarding', True),  # 安全取得，預設 True
            "host_id": db_invitation.host_id,
            "created_at": db_invitation.created_at,
            "updated_at": db_invitation.updated_at,
            "wine_details": db_invitation.wine_details,
            "attendees": db_invitation.attendees
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得邀請詳情失敗: {str(e)}")

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


@router.post("/{invitation_id}/join", response_model=AttendeeInfo)
def join_invitation(
    invitation_id: int,
    attendee: AttendeeJoinRequest,
    db: Session = Depends(get_db)
):
    """報名參加邀請函"""
    db_invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not db_invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # 取得現有的 attendees 列表
    current_attendees = db_invitation.attendees or []
    
    # 檢查是否已經報名 (避免重複)
    for att in current_attendees:
        if att.get("line_user_id") == attendee.line_user_id:
            # 已報名，直接返回
            return AttendeeInfo(**att)
    
    # 新增報名者
    new_attendee = attendee.model_dump()
    current_attendees.append(new_attendee)
    
    # 更新資料庫 (SQLAlchemy JSON 需要重新賦值才能偵測變更)
    db_invitation.attendees = current_attendees
    db.commit()
    db.refresh(db_invitation)
    
    return AttendeeInfo(**new_attendee)


@router.get("/{invitation_id}/attendees", response_model=List[AttendeeInfo])
def get_invitation_attendees(invitation_id: int, db: Session = Depends(get_db)):
    """取得邀請函的報名者列表"""
    db_invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not db_invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    return [AttendeeInfo(**att) for att in (db_invitation.attendees or [])]
