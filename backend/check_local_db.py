#!/usr/bin/env python3
"""
檢查本地 SQLite 資料庫
"""

import sqlite3
import os

def check_local_database():
    """檢查本地資料庫"""
    
    db_path = "/Users/momo/Desktop/AI-Wine-Cellar/backend/data/wine_cellar.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 本地資料庫不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查本地 SQLite 資料庫...")
        print(f"📁 資料庫位置: {db_path}")
        
        # 取得所有資料表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 發現 {len(tables)} 個資料表:")
        
        total_rows = 0
        for table_name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            total_rows += row_count
            print(f"  - {table_name}: {row_count} 筆資料")
        
        print(f"\n📈 總計: {total_rows} 筆資料")
        
        # 檢查是否有酒窖相關資料
        wine_tables = [t for t in tables if 'wine' in t.lower() or 'cellar' in t.lower()]
        if wine_tables:
            print(f"🍷 酒窖相關資料表: {wine_tables}")
        
        return tables, total_rows > 0
        
    except Exception as e:
        print(f"❌ 檢查本地資料庫失敗: {e}")
        return [], False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_local_database()