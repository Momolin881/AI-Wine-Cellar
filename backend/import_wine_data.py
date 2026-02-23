#!/usr/bin/env python3
"""
匯入酒窖資料到新 PostgreSQL 資料庫
"""

import psycopg2
import json
import os
import sys
from datetime import datetime

# 新 PostgreSQL 連線
NEW_DATABASE_URL = "postgresql://root:atbw08hzus35C6iMy2NQf7914ZJegHBo@tpe1.clusters.zeabur.com:22032/zeabur"

def create_wine_tables(cursor):
    """建立酒窖資料表"""
    
    wine_tables = {
        'users': """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                line_user_id VARCHAR(255) UNIQUE,
                display_name VARCHAR(255),
                picture_url TEXT,
                storage_mode VARCHAR(50) DEFAULT 'cellar',
                notification_enabled BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'wine_cellars': """
            CREATE TABLE IF NOT EXISTS wine_cellars (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                owner_id INTEGER REFERENCES users(id),
                location VARCHAR(255),
                capacity INTEGER,
                temperature_min DECIMAL(4,1),
                temperature_max DECIMAL(4,1),
                humidity_min DECIMAL(5,2),
                humidity_max DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'wine_items': """
            CREATE TABLE IF NOT EXISTS wine_items (
                id SERIAL PRIMARY KEY,
                cellar_id INTEGER REFERENCES wine_cellars(id),
                name VARCHAR(255) NOT NULL,
                producer VARCHAR(255),
                region VARCHAR(255),
                vintage INTEGER,
                grape_variety VARCHAR(255),
                wine_type VARCHAR(50),
                alcohol_content DECIMAL(4,2),
                price DECIMAL(10,2),
                currency VARCHAR(10) DEFAULT 'TWD',
                purchase_date DATE,
                optimal_drinking_start DATE,
                optimal_drinking_end DATE,
                storage_location VARCHAR(255),
                notes TEXT,
                image_url TEXT,
                barcode VARCHAR(50),
                quantity INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'invitations': """
            CREATE TABLE IF NOT EXISTS invitations (
                id SERIAL PRIMARY KEY,
                cellar_id INTEGER REFERENCES wine_cellars(id),
                title VARCHAR(255) NOT NULL,
                description TEXT,
                event_date TIMESTAMP,
                location VARCHAR(255),
                wine_ids JSONB,
                max_attendees INTEGER,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'budget_settings': """
            CREATE TABLE IF NOT EXISTS budget_settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                monthly_budget DECIMAL(10,2),
                currency VARCHAR(10) DEFAULT 'TWD',
                alert_threshold DECIMAL(5,2) DEFAULT 80.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'notification_settings': """
            CREATE TABLE IF NOT EXISTS notification_settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                expiry_reminder BOOLEAN DEFAULT true,
                budget_alert BOOLEAN DEFAULT true,
                invitation_alert BOOLEAN DEFAULT true,
                optimal_drinking_alert BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    }
    
    for table_name, create_sql in wine_tables.items():
        try:
            cursor.execute(create_sql)
            print(f"✅ 建立酒窖資料表: {table_name}")
        except Exception as e:
            print(f"⚠️  建立資料表 {table_name} 失敗: {e}")

def get_table_columns(cursor, table_name):
    """取得資料表現有欄位"""
    try:
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            ORDER BY ordinal_position
        """)
        return [row[0] for row in cursor.fetchall()]
    except:
        return []

def import_wine_table(cursor, table_name, table_info):
    """匯入酒窖資料表"""
    
    data = table_info['data']
    if not data:
        print(f"⚠️  {table_name}: 沒有資料")
        return True
    
    # 取得目標資料表欄位
    target_columns = get_table_columns(cursor, table_name)
    if not target_columns:
        print(f"❌ {table_name}: 資料表不存在")
        return False
    
    # 取得來源資料欄位
    source_columns = [col['name'] for col in table_info['columns']]
    
    # 找出可匯入的欄位
    valid_columns = [col for col in source_columns if col in target_columns]
    
    if not valid_columns:
        print(f"⚠️  {table_name}: 沒有匹配的欄位")
        return True
    
    print(f"📥 匯入 {table_name} ({len(valid_columns)}/{len(source_columns)} 個欄位)")
    print(f"   匯入欄位: {valid_columns}")
    
    try:
        # 建立 INSERT 語句
        placeholders = ', '.join(['%s'] * len(valid_columns))
        columns_str = ', '.join(valid_columns)
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        # 準備資料
        rows_to_insert = []
        for row_dict in data:
            row_values = [row_dict.get(col, None) for col in valid_columns]
            rows_to_insert.append(row_values)
        
        cursor.executemany(insert_sql, rows_to_insert)
        print(f"✅ {table_name}: 成功匯入 {len(rows_to_insert)} 筆資料")
        return True
        
    except Exception as e:
        print(f"❌ 匯入 {table_name} 失敗: {e}")
        return False

def main():
    """主要匯入流程"""
    
    if len(sys.argv) != 2:
        print("使用方式: python3 import_wine_data.py <酒窖匯出檔案.json>")
        sys.exit(1)
    
    export_file = sys.argv[1]
    
    try:
        print(f"🍷 讀取酒窖匯出檔案: {export_file}")
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        print(f"🔄 連接新 PostgreSQL 資料庫...")
        conn = psycopg2.connect(NEW_DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("🔨 建立酒窖資料表...")
        create_wine_tables(cursor)
        conn.commit()
        
        print("🍷 開始匯入酒窖資料...")
        
        # 按依賴關係順序匯入
        import_order = [
            'users',
            'wine_cellars', 
            'wine_items',
            'invitations',
            'budget_settings',
            'notification_settings'
        ]
        
        successful_imports = 0
        total_tables = 0
        
        for table_name in import_order:
            if table_name in export_data.get('tables', {}):
                table_info = export_data['tables'][table_name]
                if import_wine_table(cursor, table_name, table_info):
                    successful_imports += 1
                total_tables += 1
        
        conn.commit()
        
        print(f"\n✅ 酒窖資料匯入完成!")
        print(f"📊 成功匯入: {successful_imports}/{total_tables} 個資料表")
        
        # 更新序列
        print("🔄 更新序列...")
        for table_name in ['users', 'wine_cellars', 'wine_items', 'invitations', 'budget_settings', 'notification_settings']:
            try:
                cursor.execute(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                        true
                    )
                """)
                print(f"  ✅ 更新 {table_name} 序列")
            except Exception as e:
                print(f"  ⚠️  更新 {table_name} 序列失敗: {e}")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
        if 'conn' in locals():
            conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()