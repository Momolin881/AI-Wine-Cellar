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
    
    # 新手用戶 (7天內註冊)
    newcomers = db.query(User).filter(User.created_at >= week_ago).count()
    
    # 新手完成度分析
    newcomer_users = db.query(User).filter(User.created_at >= week_ago).all()
    newcomer_progress = []
    
    for user in newcomer_users:
        # 檢查新手三部曲進度
        has_cellar = db.query(WineCellar).filter(WineCellar.owner_id == user.id).count() > 0
        has_wine = db.query(WineItem).filter(WineItem.created_by == user.id).count() > 0
        has_invitation = db.query(Invitation).filter(Invitation.host_id == user.id).count() > 0
        
        progress_score = sum([has_cellar, has_wine, has_invitation])
        days_since_join = (datetime.now() - user.created_at).days if user.created_at else 0
        
        newcomer_progress.append({
            "user_id": user.id,
            "display_name": user.display_name,
            "picture_url": user.picture_url,
            "days_since_join": days_since_join,
            "progress": {
                "has_cellar": has_cellar,
                "has_wine": has_wine,
                "has_invitation": has_invitation,
                "score": progress_score,
                "completion_rate": (progress_score / 3) * 100
            },
            "needs_reminder": progress_score < 3 and days_since_join <= 7
        })
    
    # 用戶活躍度分類
    user_activity_stats = {
        "highly_active": 0,  # 5+ 酒款或邀請
        "moderate": 0,       # 2-4 酒款或邀請  
        "light": 0,          # 1 酒款或邀請
        "inactive": 0        # 0 活動
    }
    
    for user in db.query(User).all():
        wine_count = db.query(WineItem).filter(WineItem.created_by == user.id).count()
        invitation_count = db.query(Invitation).filter(Invitation.created_by == user.id).count()
        total_activity = wine_count + invitation_count
        
        if total_activity >= 5:
            user_activity_stats["highly_active"] += 1
        elif total_activity >= 2:
            user_activity_stats["moderate"] += 1
        elif total_activity >= 1:
            user_activity_stats["light"] += 1
        else:
            user_activity_stats["inactive"] += 1
    
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
    
    # PRO 用戶統計
    pro_users_count = db.query(User).filter(User.storage_mode == 'pro').count() if hasattr(User, 'storage_mode') else 0
    pro_percentage = round((pro_users_count / total_users) * 100, 1) if total_users > 0 else 0
    
    # 整體酒款偏好分析
    overall_wine_types = db.query(
        WineItem.wine_type,
        func.count(WineItem.id).label('count')
    ).filter(WineItem.wine_type.isnot(None))\
     .group_by(WineItem.wine_type)\
     .order_by(desc('count'))\
     .all()
    
    total_wines_with_type = sum([wt[1] for wt in overall_wine_types])
    wine_distribution = [
        {
            "type": wt[0], 
            "count": wt[1], 
            "percentage": round((wt[1] / total_wines_with_type) * 100, 1) if total_wines_with_type > 0 else 0
        } for wt in overall_wine_types
    ]
    
    # 整體價格區間分析
    overall_price_ranges = db.query(
        func.case(
            (WineItem.price == None, "未設定"),
            (WineItem.price < 1000, "< $1K"),
            (WineItem.price < 3000, "$1K - $3K"),
            (WineItem.price < 5000, "$3K - $5K"),
            (WineItem.price >= 5000, "> $5K")
        ).label('price_range'),
        func.count(WineItem.id).label('count')
    ).group_by('price_range').all()
    
    total_wines_analyzed = sum([pr[1] for pr in overall_price_ranges])
    price_distribution = [
        {
            "range": pr[0],
            "count": pr[1],
            "percentage": round((pr[1] / total_wines_analyzed) * 100, 1) if total_wines_analyzed > 0 else 0
        } for pr in overall_price_ranges
    ]
    
    return {
        "overview": {
            "total_users": total_users,
            "total_cellars": total_cellars,
            "total_wines": total_wines,
            "total_invitations": total_invitations,
            "today_new_users": today_users,
            "today_new_wines": today_wines,
            "today_new_invitations": today_invitations,
            "active_users_week": active_users_week,
            "newcomers_7days": newcomers,
            "pro_users": {
                "count": pro_users_count,
                "percentage": pro_percentage
            }
        },
        "overall_wine_analysis": {
            "wine_distribution": wine_distribution,
            "price_distribution": price_distribution
        },
        "newcomer_analysis": {
            "total_newcomers": len(newcomer_progress),
            "need_reminders": len([u for u in newcomer_progress if u["needs_reminder"]]),
            "avg_completion_rate": sum([u["progress"]["completion_rate"] for u in newcomer_progress]) / len(newcomer_progress) if newcomer_progress else 0,
            "users": newcomer_progress
        },
        "user_activity": user_activity_stats,
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
        
        # 檢查是否為 PRO 用戶
        is_pro = getattr(user, 'storage_mode', 'cellar') == 'pro'
        
        # 計算品飲筆記使用率 (PRO 用戶才有)
        tasting_notes_usage = 0
        if is_pro:
            wines_with_notes = db.query(WineItem).filter(
                WineItem.created_by == user.id,
                WineItem.notes.isnot(None),
                WineItem.notes != ''
            ).count()
            tasting_notes_usage = round((wines_with_notes / wine_count) * 100, 1) if wine_count > 0 else 0
        
        # 檢查新手進度
        days_since_join = (datetime.now() - user.created_at).days if user.created_at else 999
        has_cellar = cellar_count > 0
        has_wine = wine_count > 0
        has_invitation = invitation_count > 0
        onboarding_progress = sum([has_cellar, has_wine, has_invitation])
        
        user_list.append({
            "id": user.id,
            "line_user_id": user.line_user_id,
            "display_name": user.display_name,
            "picture_url": user.picture_url,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_pro": is_pro,
            "days_since_join": days_since_join,
            "is_newcomer": days_since_join <= 7,
            "onboarding_progress": {
                "score": onboarding_progress,
                "total": 3,
                "percentage": round((onboarding_progress / 3) * 100, 1)
            },
            "tasting_notes_usage": tasting_notes_usage if is_pro else None,
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
    invitations = db.query(Invitation).filter(Invitation.host_id == user_id)\
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
        } if budget else None,
        "wine_preferences": analyze_wine_preferences(db, user_id),
        "consumption_patterns": analyze_consumption_patterns(db, user_id),
        "onboarding_progress": get_onboarding_progress(db, user)
    }

def analyze_wine_preferences(db: Session, user_id: int) -> Dict[str, Any]:
    """分析用戶酒款偏好"""
    
    user_wines = db.query(WineItem).filter(WineItem.created_by == user_id).all()
    
    if not user_wines:
        return {"total_wines": 0, "preferences": {}}
    
    # 酒類偏好
    wine_types = {}
    regions = {}
    price_ranges = {"under_1k": 0, "1k_3k": 0, "3k_5k": 0, "over_5k": 0, "unset": 0}
    vintages = {}
    
    total_value = 0
    wines_with_price = 0
    
    for wine in user_wines:
        # 酒類統計
        wine_type = wine.wine_type or "未分類"
        wine_types[wine_type] = wine_types.get(wine_type, 0) + 1
        
        # 產區統計
        region = wine.region or "未知產區"
        regions[region] = regions.get(region, 0) + 1
        
        # 價格分析
        if wine.price:
            wines_with_price += 1
            total_value += float(wine.price)
            
            if wine.price < 1000:
                price_ranges["under_1k"] += 1
            elif wine.price < 3000:
                price_ranges["1k_3k"] += 1
            elif wine.price < 5000:
                price_ranges["3k_5k"] += 1
            else:
                price_ranges["over_5k"] += 1
        else:
            price_ranges["unset"] += 1
        
        # 年份統計
        if wine.vintage:
            decade = f"{wine.vintage // 10 * 10}年代"
            vintages[decade] = vintages.get(decade, 0) + 1
    
    # 排序並取前5
    top_wine_types = sorted(wine_types.items(), key=lambda x: x[1], reverse=True)[:5]
    top_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_wines": len(user_wines),
        "avg_price": round(total_value / wines_with_price, 2) if wines_with_price > 0 else None,
        "collection_value": round(total_value, 2),
        "preferences": {
            "wine_types": [{"type": t[0], "count": t[1], "percentage": round(t[1]/len(user_wines)*100, 1)} for t in top_wine_types],
            "regions": [{"region": r[0], "count": r[1], "percentage": round(r[1]/len(user_wines)*100, 1)} for r in top_regions],
            "price_distribution": price_ranges,
            "vintage_decades": vintages
        }
    }

def analyze_consumption_patterns(db: Session, user_id: int) -> Dict[str, Any]:
    """分析用戶消費模式（暫時返回基本統計，未來可擴展）"""
    
    # 這裡可以根據未來的 wine_consumption 表或酒款狀態來分析
    # 目前先返回基本的邀請和社交活動統計
    
    invitations = db.query(Invitation).filter(Invitation.created_by == user_id).all()
    
    return {
        "social_activity": {
            "total_invitations": len(invitations),
            "avg_invitations_per_month": round(len(invitations) / max(1, (datetime.now() - db.query(User).filter(User.id == user_id).first().created_at).days / 30), 2) if invitations else 0
        },
        # 未來可以增加：
        # "tasting_frequency": {...},
        # "opening_patterns": {...},
        # "consumption_rate": {...}
    }

def get_onboarding_progress(db: Session, user: User) -> Dict[str, Any]:
    """獲取用戶新手進度"""
    
    days_since_join = (datetime.now() - user.created_at).days if user.created_at else 999
    
    # 新手三部曲檢查
    has_cellar = db.query(WineCellar).filter(WineCellar.owner_id == user.id).count() > 0
    has_wine = db.query(WineItem).filter(WineItem.created_by == user.id).count() > 0
    has_invitation = db.query(Invitation).filter(Invitation.host_id == user.id).count() > 0
    
    progress_steps = [
        {"step": "建立酒窖", "completed": has_cellar, "description": "設定個人酒窖空間"},
        {"step": "新增酒款", "completed": has_wine, "description": "添加第一款酒到酒窖"},
        {"step": "發送邀請", "completed": has_invitation, "description": "邀請朋友品酒聚會"}
    ]
    
    completed_steps = sum([step["completed"] for step in progress_steps])
    
    return {
        "is_newcomer": days_since_join <= 7,
        "days_since_join": days_since_join,
        "progress": {
            "steps": progress_steps,
            "completed_count": completed_steps,
            "total_count": 3,
            "completion_rate": round((completed_steps / 3) * 100, 1)
        },
        "needs_guidance": completed_steps < 3 and days_since_join <= 7,
        "next_suggestion": get_next_suggestion(progress_steps)
    }

def get_next_suggestion(steps: List[Dict[str, Any]]) -> str:
    """根據進度給出下一步建議"""
    
    for step in steps:
        if not step["completed"]:
            return f"建議完成：{step['step']} - {step['description']}"
    
    return "恭喜完成新手三部曲！開始享受Wine Cellar的完整功能吧！"

@router.post("/users/{user_id}/toggle-pro")
def toggle_user_pro_mode(
    user_id: int,
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """切換用戶的 PRO 模式狀態"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 切換 storage_mode
    current_mode = getattr(user, 'storage_mode', 'cellar')
    new_mode = 'pro' if current_mode != 'pro' else 'cellar'
    
    # 如果 User model 沒有 storage_mode 欄位，需要先檢查是否存在
    try:
        user.storage_mode = new_mode
        db.commit()
        
        return {
            "status": "success",
            "user_id": user_id,
            "old_mode": current_mode,
            "new_mode": new_mode,
            "is_pro": new_mode == 'pro',
            "message": f"用戶 {user.display_name} 已{'升級為' if new_mode == 'pro' else '降級為'} {'PRO' if new_mode == 'pro' else '一般'} 用戶"
        }
        
    except Exception as e:
        db.rollback()
        # 如果沒有 storage_mode 欄位，先添加
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN storage_mode VARCHAR(50) DEFAULT 'cellar'"))
            db.commit()
            # 重新嘗試
            user = db.query(User).filter(User.id == user_id).first()
            user.storage_mode = new_mode
            db.commit()
            
            return {
                "status": "success", 
                "user_id": user_id,
                "new_mode": new_mode,
                "is_pro": new_mode == 'pro',
                "message": f"已為用戶添加 PRO 模式功能並設定為 {'PRO' if new_mode == 'pro' else '一般'} 用戶"
            }
        except Exception as e2:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"更新用戶模式失敗: {str(e2)}"
            )

@router.post("/migrate-database")
def run_database_migration(db: Session = Depends(get_db)):
    """
    執行資料庫遷移
    修復 invitations 表的 schema 問題
    """
    try:
        # 檢查 attendees 欄位是否存在
        # 獲取當前所有欄位
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'invitations'
        """)
        result = db.execute(check_query).fetchall()
        existing_columns = [row[0] for row in result]
        
        # 執行遷移
        migration_queries = [
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS attendees TEXT DEFAULT '[]'",
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS latitude VARCHAR(50)",  
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS longitude VARCHAR(50)",
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS host_id INTEGER",
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS theme_image_url VARCHAR(500)",
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
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
            (title, description, event_date, location, theme_image_url, wine_ids, attendees, host_id, created_at, updated_at)
            VALUES (:title, :description, :event_date, :location, :theme_image_url, :wine_ids, :attendees, :host_id, :created_at, :updated_at)
            RETURNING id;
        """)
        
        now = datetime.now(timezone.utc)
        result = db.execute(insert_query, {
            'title': '功能測試邀請 - 三大功能驗證',
            'description': '測試 Google Maps 地點導航、Google Calendar 行事曆、RSVP 報名功能',
            'event_date': datetime(2026, 2, 14, 19, 30, tzinfo=timezone.utc),
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