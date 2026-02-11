"""
管理員 API 端點
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import get_db

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
)

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