"""
管理員 API 端點 - Wine Cellar 管理後台
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from src.database import get_db
from src.models.user import User
from src.models.wine_cellar import WineCellar
from src.models.wine_item import WineItem
from src.models.invitation import Invitation
from src.models.budget_settings import BudgetSettings
from src.config import settings
import jwt

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()

# 管理員認證配置
ADMIN_TOKEN_SECRET = settings.SECRET_KEY + "_admin"
ADMIN_CREDENTIALS = {
    "admin": "wine_cellar_admin_2024"  # 實際部署時應使用環境變數
}

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """驗證管理員 JWT Token"""
    try:
        payload = jwt.decode(credentials.credentials, ADMIN_TOKEN_SECRET, algorithms=["HS256"])
        username = payload.get("username")
        if username not in ADMIN_CREDENTIALS:
            raise HTTPException(status_code=401, detail="Invalid admin token")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid admin token")

from pydantic import BaseModel

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def admin_login(request: AdminLoginRequest):
    """管理員登入"""
    if request.username not in ADMIN_CREDENTIALS or ADMIN_CREDENTIALS[request.username] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 生成 JWT Token
    payload = {
        "username": request.username,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, ADMIN_TOKEN_SECRET, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400  # 24 hours
    }

@router.get("/dashboard/stats")
def get_dashboard_stats(
    admin: dict = Depends(verify_admin_token), 
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """獲取 Dashboard 總覽統計"""
    
    # 基本統計
    total_users = db.query(User).count()
    total_cellars = db.query(WineCellar).count()
    total_wines = db.query(WineItem).count()
    total_invitations = db.query(Invitation).count()
    
    # 今日新增
    today = date.today()
    today_users = db.query(User).filter(func.date(User.created_at) == today).count()
    today_wines = db.query(WineItem).filter(func.date(WineItem.created_at) == today).count()
    today_invitations = db.query(Invitation).filter(func.date(Invitation.created_at) == today).count()
    
    # 本週活躍用戶（有新增酒款或邀請）
    week_ago = datetime.now() - timedelta(days=7)
    active_users_week = db.query(func.count(func.distinct(WineItem.created_by)))\
        .filter(WineItem.created_at >= week_ago).scalar() or 0
    
    # 熱門酒類統計
    wine_types = db.query(
        WineItem.wine_type,
        func.count(WineItem.id).label('count')
    ).filter(WineItem.wine_type.isnot(None))\
     .group_by(WineItem.wine_type)\
     .order_by(desc('count'))\
     .limit(5)\
     .all()
    
    # 價格區間分析
    price_ranges = db.query(
        func.case(
            (WineItem.price == None, "未設定"),
            (WineItem.price < 1000, "< $1,000"),
            (WineItem.price < 3000, "$1,000 - $3,000"),
            (WineItem.price < 5000, "$3,000 - $5,000"),
            (WineItem.price >= 5000, "> $5,000")
        ).label('price_range'),
        func.count(WineItem.id).label('count')
    ).group_by('price_range').all()
    
    # 最近 7 天的用戶增長趨勢
    user_growth = []
    for i in range(7):
        day = today - timedelta(days=i)
        count = db.query(User).filter(func.date(User.created_at) == day).count()
        user_growth.append({
            "date": day.strftime("%m-%d"),
            "count": count
        })
    user_growth.reverse()
    
    return {
        "overview": {
            "total_users": total_users,
            "total_cellars": total_cellars,
            "total_wines": total_wines,
            "total_invitations": total_invitations,
            "today_new_users": today_users,
            "today_new_wines": today_wines,
            "today_new_invitations": today_invitations,
            "active_users_week": active_users_week
        },
        "wine_types": [{"type": wt[0], "count": wt[1]} for wt in wine_types],
        "price_ranges": [{"range": pr[0], "count": pr[1]} for pr in price_ranges],
        "user_growth": user_growth,
        "system_info": {
            "app_version": settings.APP_VERSION,
            "database_status": "healthy",
            "last_updated": datetime.now().isoformat()
        }
    }

@router.get("/users")
def get_users_list(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """獲取用戶列表"""
    
    query = db.query(User)
    
    # 搜尋功能
    if search:
        query = query.filter(
            User.display_name.contains(search) |
            User.line_user_id.contains(search)
        )
    
    # 分頁
    offset = (page - 1) * limit
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
    
    # 為每個用戶添加統計資訊
    user_list = []
    for user in users:
        cellar_count = db.query(WineCellar).filter(WineCellar.owner_id == user.id).count()
        wine_count = db.query(WineItem).filter(WineItem.created_by == user.id).count()
        invitation_count = db.query(Invitation).filter(Invitation.created_by == user.id).count()
        
        user_list.append({
            "id": user.id,
            "line_user_id": user.line_user_id,
            "display_name": user.display_name,
            "picture_url": user.picture_url,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "stats": {
                "cellars": cellar_count,
                "wines": wine_count,
                "invitations": invitation_count
            }
        })
    
    return {
        "users": user_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }

@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """獲取用戶詳細資訊"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 用戶的酒窖
    cellars = db.query(WineCellar).filter(WineCellar.owner_id == user_id).all()
    
    # 用戶的酒款（最近 10 個）
    wines = db.query(WineItem).filter(WineItem.created_by == user_id)\
        .order_by(desc(WineItem.created_at)).limit(10).all()
    
    # 用戶的邀請（最近 10 個）
    invitations = db.query(Invitation).filter(Invitation.created_by == user_id)\
        .order_by(desc(Invitation.created_at)).limit(10).all()
    
    # 預算設定
    budget = db.query(BudgetSettings).filter(BudgetSettings.user_id == user_id).first()
    
    return {
        "user": {
            "id": user.id,
            "line_user_id": user.line_user_id,
            "display_name": user.display_name,
            "picture_url": user.picture_url,
            "storage_mode": getattr(user, 'storage_mode', None),
            "created_at": user.created_at.isoformat() if user.created_at else None
        },
        "cellars": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "wine_count": db.query(WineItem).filter(WineItem.cellar_id == c.id).count()
            } for c in cellars
        ],
        "recent_wines": [
            {
                "id": w.id,
                "name": w.name,
                "wine_type": w.wine_type,
                "vintage": w.vintage,
                "price": float(w.price) if w.price else None,
                "created_at": w.created_at.isoformat() if w.created_at else None
            } for w in wines
        ],
        "recent_invitations": [
            {
                "id": i.id,
                "title": i.title,
                "event_date": i.event_date.isoformat() if i.event_date else None,
                "location": i.location,
                "created_at": i.created_at.isoformat() if i.created_at else None
            } for i in invitations
        ],
        "budget": {
            "monthly_budget": float(budget.monthly_budget) if budget and budget.monthly_budget else None,
            "currency": budget.currency if budget else "TWD"
        } if budget else None
    }

@router.post("/migrate-database")
def run_database_migration(db: Session = Depends(get_db)):
    """
    執行資料庫遷移
    修復 invitations 表的 schema 問題
    """
    try:
        # 檢查 attendees 欄位是否存在
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'invitations' AND column_name = 'attendees'
        """)
        result = db.execute(check_query).fetchone()
        
        if result:
            return {"status": "success", "message": "attendees 欄位已存在，無需遷移"}
        
        # 執行遷移
        migration_queries = [
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS attendees TEXT DEFAULT '[]'",
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS latitude VARCHAR(50)",  
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS longitude VARCHAR(50)",
            "UPDATE invitations SET attendees = '[]' WHERE attendees IS NULL",
            "UPDATE invitations SET wine_ids = '[]' WHERE wine_ids IS NULL"
        ]
        
        for query in migration_queries:
            db.execute(text(query))
        
        db.commit()
        
        # 驗證結果
        verify_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'invitations'
            ORDER BY column_name
        """)
        columns = [row[0] for row in db.execute(verify_query).fetchall()]
        
        return {
            "status": "success", 
            "message": "資料庫遷移完成",
            "columns": columns
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"資料庫遷移失敗: {str(e)}"
        )

@router.post("/create-test-invitation")
def create_test_invitation(db: Session = Depends(get_db)):
    """
    創建測試邀請用於功能驗證
    """
    try:
        from datetime import datetime, timezone
        import json
        
        # 創建測試邀請
        insert_query = text("""
            INSERT INTO invitations 
            (title, description, event_time, location, theme_image_url, wine_ids, attendees, host_id, created_at, updated_at)
            VALUES (:title, :description, :event_time, :location, :theme_image_url, :wine_ids, :attendees, :host_id, :created_at, :updated_at)
            RETURNING id;
        """)
        
        now = datetime.now(timezone.utc)
        result = db.execute(insert_query, {
            'title': '功能測試邀請 - 三大功能驗證',
            'description': '測試 Google Maps 地點導航、Google Calendar 行事曆、RSVP 報名功能',
            'event_time': datetime(2026, 2, 14, 19, 30, tzinfo=timezone.utc),
            'location': '台北101觀景台',
            'theme_image_url': 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'wine_ids': '[]',
            'attendees': '[]',
            'host_id': None,
            'created_at': now,
            'updated_at': now
        })
        
        invitation_id = result.fetchone()[0]
        db.commit()
        
        return {
            "status": "success",
            "message": "測試邀請創建成功",
            "invitation_id": invitation_id,
            "detail_url": f"https://ai-wine-cellar.zeabur.app/invitation/{invitation_id}",
            "liff_url": f"https://liff.line.me/2008946239-5U8c7ry2/invitation/{invitation_id}"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"創建測試邀請失敗: {str(e)}"
        )

@router.post("/fix-invitation-forwarding")
def fix_invitation_forwarding(db: Session = Depends(get_db)):
    """
    修復舊邀請記錄的 allow_forwarding 欄位
    """
    try:
        # 先嘗試添加欄位（如果不存在）
        try:
            db.execute(text("""
                ALTER TABLE invitations 
                ADD COLUMN allow_forwarding BOOLEAN DEFAULT TRUE
            """))
            db.commit()
        except Exception:
            # 欄位可能已經存在，忽略錯誤
            pass
        
        # 為 NULL 值設定預設值
        result = db.execute(text("""
            UPDATE invitations 
            SET allow_forwarding = TRUE 
            WHERE allow_forwarding IS NULL
        """))
        
        db.commit()
        
        return {
            "status": "success", 
            "message": f"Fixed {result.rowcount} invitation records with missing allow_forwarding field",
            "updated_count": result.rowcount
        }
        
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}