#!/usr/bin/env python3
"""
直接在資料庫中創建測試邀請
"""

import os
import psycopg2
from datetime import datetime, timezone
import json
from src.config import settings

def create_test_invitation():
    """直接在資料庫中創建測試邀請"""
    
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        # 創建測試邀請
        insert_sql = """
        INSERT INTO invitations 
        (title, description, event_time, location, theme_image_url, wine_ids, attendees, host_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        test_data = (
            "功能測試邀請 - 三大功能驗證",
            "測試 Google Maps 地點導航、Google Calendar 行事曆、RSVP 報名功能",
            datetime(2026, 2, 14, 19, 30, tzinfo=timezone.utc),
            "台北101觀景台",
            "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            json.dumps([]),
            json.dumps([]),
            None,
            datetime.now(timezone.utc),
            datetime.now(timezone.utc)
        )
        
        cursor.execute(insert_sql, test_data)
        invitation_id = cursor.fetchone()[0]
        
        conn.commit()
        print(f"✅ 成功創建測試邀請，ID: {invitation_id}")
        print(f"📱 邀請詳情頁面: https://ai-wine-cellar.zeabur.app/invitation/{invitation_id}")
        print(f"🔗 LIFF 頁面: https://liff.line.me/{settings.LIFF_ID}/invitation/{invitation_id}")
        
        return invitation_id
        
    except Exception as e:
        print(f"❌ 創建測試邀請失敗: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_test_invitation()