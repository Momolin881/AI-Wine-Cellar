#!/usr/bin/env python3
"""
手動遷移 - 創建表格並匯入資料
"""

import psycopg2
import json
from datetime import datetime

# 舊資料庫連接（已洩露的）
OLD_DB_URL = "postgresql://root:8x26U597Iukp4MjGWda3RoZe1mtXTJl0@tpe1.clusters.zeabur.com:27644/zeabur"
# 新資料庫連接
NEW_DB_URL = "postgresql://root:Sf7D9Cj3t4P61eism2KBd8hL5u0TFkoZ@tpe1.clusters.zeabur.com:25970/zeabur"

def create_tables():
    """手動創建必要的表格"""
    print("🔄 手動創建資料庫表格...")
    
    new_conn = psycopg2.connect(NEW_DB_URL)
    new_cursor = new_conn.cursor()
    
    # 創建 users 表
    new_cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            line_user_id VARCHAR(255) UNIQUE NOT NULL,
            display_name VARCHAR(255),
            profile_picture_url TEXT,
            status_message TEXT,
            language VARCHAR(10) DEFAULT 'zh-TW',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 創建 wine_cellars 表
    new_cursor.execute("""
        CREATE TABLE IF NOT EXISTS wine_cellars (
            id SERIAL PRIMARY KEY,
            owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            location VARCHAR(255),
            capacity INTEGER,
            temperature_min NUMERIC(4,1),
            temperature_max NUMERIC(4,1),
            humidity_min NUMERIC(5,2),
            humidity_max NUMERIC(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 創建 wine_items 表
    new_cursor.execute("""
        CREATE TABLE IF NOT EXISTS wine_items (
            id SERIAL PRIMARY KEY,
            cellar_id INTEGER REFERENCES wine_cellars(id) ON DELETE CASCADE NOT NULL,
            name VARCHAR(255) NOT NULL,
            producer VARCHAR(255),
            region VARCHAR(255),
            vintage INTEGER,
            grape_variety VARCHAR(255),
            wine_type VARCHAR(50),
            alcohol_content NUMERIC(4,2),
            price NUMERIC(10,2),
            currency VARCHAR(10) DEFAULT 'TWD',
            purchase_date DATE,
            optimal_drinking_start DATE,
            optimal_drinking_end DATE,
            storage_location VARCHAR(255),
            notes TEXT,
            image_url TEXT,
            barcode VARCHAR(50),
            quantity INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rating INTEGER,
            review TEXT,
            flavor_tags TEXT,
            aroma TEXT,
            palate TEXT,
            finish TEXT,
            acidity INTEGER,
            tannin INTEGER,
            body INTEGER,
            sweetness INTEGER,
            alcohol_feel INTEGER
        )
    """)
    
    new_conn.commit()
    new_cursor.close()
    new_conn.close()
    print("✅ 資料庫表格創建完成")

def export_and_import():
    """匯出和匯入資料"""
    print("🔄 連接兩個資料庫...")
    
    old_conn = psycopg2.connect(OLD_DB_URL)
    old_cursor = old_conn.cursor()
    
    new_conn = psycopg2.connect(NEW_DB_URL)
    new_cursor = new_conn.cursor()
    
    # 匯入用戶
    print("📥 匯入用戶...")
    old_cursor.execute("SELECT * FROM users ORDER BY id")
    users = old_cursor.fetchall()
    
    for user in users:
        new_cursor.execute("""
            INSERT INTO users (id, line_user_id, display_name, profile_picture_url, status_message, language, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (line_user_id) DO NOTHING
        """, user)
    
    print(f"✅ 匯入了 {len(users)} 個用戶")
    
    # 匯入酒窖
    print("📥 匯入酒窖...")
    old_cursor.execute("SELECT * FROM wine_cellars ORDER BY id")
    cellars = old_cursor.fetchall()
    
    for cellar in cellars:
        # 舊資料庫順序: id, name, description, owner_id, location, capacity, temperature_min, temperature_max, humidity_min, humidity_max, created_at, updated_at
        new_cursor.execute("""
            INSERT INTO wine_cellars (id, name, description, owner_id, location, capacity, 
                                     temperature_min, temperature_max, humidity_min, humidity_max, 
                                     created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, cellar)
    
    print(f"✅ 匯入了 {len(cellars)} 個酒窖")
    
    # 匯入酒款
    print("📥 匯入酒款...")
    old_cursor.execute("SELECT * FROM wine_items ORDER BY id")
    wines = old_cursor.fetchall()
    
    for wine in wines:
        new_cursor.execute("""
            INSERT INTO wine_items (id, cellar_id, name, producer, region, vintage, grape_variety, 
                                   wine_type, alcohol_content, price, currency, purchase_date, 
                                   optimal_drinking_start, optimal_drinking_end, storage_location, 
                                   notes, image_url, barcode, quantity, created_by, created_at, 
                                   updated_at, rating, review, flavor_tags, aroma, palate, finish, 
                                   acidity, tannin, body, sweetness, alcohol_feel)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, wine)
    
    print(f"✅ 匯入了 {len(wines)} 個酒款")
    
    # 重設序列
    print("🔄 重設序列...")
    new_cursor.execute("SELECT setval('users_id_seq', COALESCE(MAX(id), 1)) FROM users")
    new_cursor.execute("SELECT setval('wine_cellars_id_seq', COALESCE(MAX(id), 1)) FROM wine_cellars") 
    new_cursor.execute("SELECT setval('wine_items_id_seq', COALESCE(MAX(id), 1)) FROM wine_items")
    
    new_conn.commit()
    old_cursor.close()
    old_conn.close()
    new_cursor.close()
    new_conn.close()

def verify_migration():
    """驗證遷移結果"""
    print("🔍 驗證遷移結果...")
    
    new_conn = psycopg2.connect(NEW_DB_URL)
    new_cursor = new_conn.cursor()
    
    # 檢查資料數量
    tables = ['users', 'wine_cellars', 'wine_items']
    for table in tables:
        new_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = new_cursor.fetchone()[0]
        print(f"  📊 {table}: {count} 筆資料")
    
    # 檢查 Linmomo 的資料
    new_cursor.execute("""
        SELECT u.display_name, COUNT(c.id) as cellar_count, COUNT(w.id) as wine_count
        FROM users u
        LEFT JOIN wine_cellars c ON u.id = c.owner_id
        LEFT JOIN wine_items w ON c.id = w.cellar_id
        WHERE u.line_user_id = 'U1cec7d5d0c7cf770fbe8113e5a729a26'
        GROUP BY u.id, u.display_name
    """)
    result = new_cursor.fetchone()
    
    if result:
        print(f"  🎯 {result[0]}: {result[1]} 個酒窖, {result[2]} 個酒款")
    else:
        print("  ⚠️ 找不到 Linmomo 的資料")
    
    new_cursor.close()
    new_conn.close()

def main():
    """主要遷移流程"""
    try:
        create_tables()
        export_and_import()
        verify_migration()
        print("\n🎉 資料庫遷移完成！")
        
    except Exception as e:
        print(f"❌ 遷移失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()