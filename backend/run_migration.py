#!/usr/bin/env python3
"""
執行資料庫遷移腳本
"""

import os
import psycopg2
from src.config import settings

def run_migration():
    """執行 004_fix_invitations_schema.sql 遷移"""
    
    # 讀取遷移腳本
    migration_file = "migrations/004_fix_invitations_schema.sql"
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # 連接資料庫
    try:
        # 使用 settings 中的資料庫 URL
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("開始執行資料庫遷移...")
        print(f"執行檔案: {migration_file}")
        
        # 分解 SQL 語句並逐一執行
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for i, statement in enumerate(statements):
            if statement:
                print(f"執行語句 {i+1}/{len(statements)}: {statement[:50]}...")
                cursor.execute(statement)
        
        # 提交變更
        conn.commit()
        print("✅ 資料庫遷移執行成功！")
        
        # 驗證結果
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'invitations'")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 invitations 表的欄位: {', '.join(columns)}")
        
        if 'attendees' in columns:
            print("✅ attendees 欄位已成功添加")
        else:
            print("❌ attendees 欄位添加失敗")
            
    except Exception as e:
        print(f"❌ 資料庫遷移失敗: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration()