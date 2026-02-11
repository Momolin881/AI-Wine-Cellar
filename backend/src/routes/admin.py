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