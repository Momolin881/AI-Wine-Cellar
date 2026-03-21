"""
管理員 API 端點 - 簡化安全版本（無 JWT 依賴）
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from datetime import datetime
from src.database import get_db
from src.models.user import User
from src.models.wine_cellar import WineCellar
from src.models.wine_item import WineItem
from src.models.invitation import Invitation

router = APIRouter()

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """獲取管理後台統計資料"""
    try:
        # 基本統計
        total_users = db.query(func.count(User.id)).scalar()
        total_cellars = db.query(func.count(WineCellar.id)).scalar()
        total_wines = db.query(func.count(WineItem.id)).scalar()
        total_invitations = db.query(func.count(Invitation.id)).scalar()
        
        # 酒類分佈統計（從 DB 查詢）
        wine_type_rows = db.query(
            WineItem.wine_type, func.count(WineItem.id)
        ).group_by(WineItem.wine_type).all()

        wine_types = [
            {"type": wt or "未分類", "count": cnt}
            for wt, cnt in wine_type_rows
        ]

        return {
            "status": "success",
            "overview": {
                "total_users": total_users or 0,
                "total_cellars": total_cellars or 0,
                "total_wines": total_wines or 0,
                "total_invitations": total_invitations or 0
            },
            "wine_types": wine_types,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "overview": {
                "total_users": 0,
                "total_cellars": 0,
                "total_wines": 0,
                "total_invitations": 0
            }
        }

@router.get("/health")
async def admin_health():
    """管理後台健康檢查"""
    return {
        "status": "healthy",
        "service": "admin",
        "timestamp": datetime.now().isoformat()
    }