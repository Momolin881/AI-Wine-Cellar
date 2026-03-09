#!/usr/bin/env python3
"""
資料庫遷移腳本 - 從舊資料庫匯出到新資料庫
"""

import psycopg2
import json
from datetime import datetime

# 舊資料庫連接（已洩露的）
OLD_DB_URL = "postgresql://root:8x26U597Iukp4MjGWda3RoZe1mtXTJl0@tpe1.clusters.zeabur.com:27644/zeabur"
# 新資料庫連接
NEW_DB_URL = "postgresql://root:Sf7D9Cj3t4P61eism2KBd8hL5u0TFkoZ@tpe1.clusters.zeabur.com:25970/zeabur"

def export_from_old_db():
    """從舊資料庫匯出所有資料"""
    print("🔄 連接舊資料庫...")
    old_conn = psycopg2.connect(OLD_DB_URL)
    old_cursor = old_conn.cursor()
    
    data = {}
    
    # 匯出用戶
    print("📊 匯出用戶資料...")
    old_cursor.execute("SELECT * FROM users ORDER BY id")
    columns = [desc[0] for desc in old_cursor.description]
    data['users'] = [dict(zip(columns, row)) for row in old_cursor.fetchall()]
    print(f"✅ 匯出 {len(data['users'])} 個用戶")
    
    # 匯出酒窖
    print("📊 匯出酒窖資料...")
    old_cursor.execute("SELECT * FROM wine_cellars ORDER BY id")
    columns = [desc[0] for desc in old_cursor.description]
    data['wine_cellars'] = [dict(zip(columns, row)) for row in old_cursor.fetchall()]
    print(f"✅ 匯出 {len(data['wine_cellars'])} 個酒窖")
    
    # 匯出酒款
    print("📊 匯出酒款資料...")
    old_cursor.execute("SELECT * FROM wine_items ORDER BY id")
    columns = [desc[0] for desc in old_cursor.description]
    data['wine_items'] = [dict(zip(columns, row)) for row in old_cursor.fetchall()]
    print(f"✅ 匯出 {len(data['wine_items'])} 個酒款")
    
    # 匯出邀請
    print("📊 匯出邀請資料...")
    old_cursor.execute("SELECT * FROM invitations ORDER BY id")
    columns = [desc[0] for desc in old_cursor.description]
    data['invitations'] = [dict(zip(columns, row)) for row in old_cursor.fetchall()]
    print(f"✅ 匯出 {len(data['invitations'])} 個邀請")
    
    # 匯出預算設定
    print("📊 匯出預算設定...")
    old_cursor.execute("SELECT * FROM budget_settings ORDER BY id")
    columns = [desc[0] for desc in old_cursor.description]
    data['budget_settings'] = [dict(zip(columns, row)) for row in old_cursor.fetchall()]
    print(f"✅ 匯出 {len(data['budget_settings'])} 個預算設定")
    
    # 匯出通知設定
    print("📊 匯出通知設定...")
    old_cursor.execute("SELECT * FROM notification_settings ORDER BY id")
    columns = [desc[0] for desc in old_cursor.description]
    data['notification_settings'] = [dict(zip(columns, row)) for row in old_cursor.fetchall()]
    print(f"✅ 匯出 {len(data['notification_settings'])} 個通知設定")
    
    old_cursor.close()
    old_conn.close()
    
    return data

def create_new_db_schema():
    """建立新資料庫結構"""
    print("🔄 建立資料庫表格...")
    
    # 更新環境變數以使用新資料庫
    import os
    os.environ['DATABASE_URL'] = NEW_DB_URL
    
    # 重新載入 database 模組使用新連接
    import importlib
    from src import database
    importlib.reload(database)
    from src.database import Base, engine
    
    # 確保所有 models 都被載入
    from src import models
    
    Base.metadata.create_all(bind=engine)
    print("✅ 資料庫表格建立完成")

def import_to_new_db(data):
    """匯入資料到新資料庫"""
    print("🔄 連接新資料庫...")
    new_conn = psycopg2.connect(NEW_DB_URL)
    new_cursor = new_conn.cursor()
    
    def convert_value(value):
        """轉換 Python 值到 SQL 格式"""
        if value is None:
            return 'NULL'
        elif isinstance(value, str):
            return f"'{value.replace(chr(39), chr(39)+chr(39))}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime):
            return f"'{value.isoformat()}'"
        elif hasattr(value, 'isoformat'):  # date
            return f"'{value.isoformat()}'"
        elif isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        else:
            return f"'{str(value).replace(chr(39), chr(39)+chr(39))}'"
    
    # 匯入順序很重要（外鍵依賴）
    tables = ['users', 'wine_cellars', 'wine_items', 'invitations', 'budget_settings', 'notification_settings']
    
    for table in tables:
        if table in data and data[table]:
            print(f"📥 匯入 {table}...")
            
            # 清空現有資料
            new_cursor.execute(f"DELETE FROM {table}")
            
            for row in data[table]:
                columns = list(row.keys())
                values = [convert_value(row[col]) for col in columns]
                
                query = f"""
                    INSERT INTO {table} ({', '.join(columns)}) 
                    VALUES ({', '.join(values)})
                """
                
                try:
                    new_cursor.execute(query)
                except Exception as e:
                    print(f"⚠️ 插入失敗: {e}")
                    print(f"   SQL: {query[:100]}...")
                    continue
            
            # 重設序列
            if table != 'notification_settings':  # 這個表可能沒有序列
                try:
                    new_cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}")
                except:
                    pass
            
            new_conn.commit()
            print(f"✅ {table} 匯入完成")
    
    new_cursor.close()
    new_conn.close()

def main():
    """主要遷移流程"""
    try:
        # 步驟 1: 匯出舊資料
        print("=" * 50)
        print("📦 步驟 1: 匯出舊資料庫資料")
        print("=" * 50)
        data = export_from_old_db()
        
        # 步驟 2: 建立新資料庫結構
        print("\n" + "=" * 50)
        print("🏗️  步驟 2: 建立新資料庫結構")
        print("=" * 50)
        create_new_db_schema()
        
        # 步驟 3: 匯入資料
        print("\n" + "=" * 50)
        print("📥 步驟 3: 匯入資料到新資料庫")
        print("=" * 50)
        import_to_new_db(data)
        
        print("\n🎉 資料庫遷移完成！")
        print(f"總計遷移: {len(data['users'])} 用戶, {len(data['wine_cellars'])} 酒窖, {len(data['wine_items'])} 酒款")
        
    except Exception as e:
        print(f"❌ 遷移失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()