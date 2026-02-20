#!/usr/bin/env python3
"""
直接在生產環境資料庫新增 max_attendees 欄位
"""

import psycopg2
import os

# 嘗試多種可能的資料庫 URL 環境變數
possible_db_urls = [
    os.getenv('POSTGRES_URL'),
    os.getenv('DATABASE_URL'),  
    os.getenv('ZEABUR_POSTGRES_URL'),
    "postgresql://root:4Y7RhKkQ5N8m12sUyilw09MnSGcx3eL6@sjc1.clusters.zeabur.com:28948/zeabur"  # fallback
]

DATABASE_URL = next((url for url in possible_db_urls if url), None)

if not DATABASE_URL:
    print("❌ 找不到資料庫 URL")
    exit(1)

def add_max_attendees_column():
    """新增 max_attendees 欄位到 invitations 表"""
    
    try:
        print(f"連接資料庫: {DATABASE_URL[:50]}...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("檢查現有的 invitations 表結構...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'invitations'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]
        print(f"現有欄位: {columns}")
        
        if 'max_attendees' not in columns:
            print("新增 max_attendees 欄位...")
            cursor.execute("ALTER TABLE invitations ADD COLUMN max_attendees INTEGER")
            print("✅ max_attendees 欄位新增成功")
        else:
            print("✅ max_attendees 欄位已存在")
        
        # 驗證結果
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'invitations'
            ORDER BY ordinal_position
        """)
        columns_after = [row[0] for row in cursor.fetchall()]
        print(f"更新後欄位: {columns_after}")
        
        if 'max_attendees' in columns_after:
            print("✅ 欄位驗證成功")
        else:
            print("❌ 欄位驗證失敗")
            
    except Exception as e:
        print(f"❌ 操作失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_max_attendees_column()