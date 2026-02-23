#!/usr/bin/env python3
"""
智能資料匯入（會自動調整欄位差異）
"""

import psycopg2
import json
import os
import sys
from datetime import datetime

DATABASE_URL = "postgresql://root:atbw08hzus35C6iMy2NQf7914ZJegHBo@tpe1.clusters.zeabur.com:22032/zeabur"

def get_table_columns(cursor, table_name):
    """取得資料表現有欄位"""
    try:
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            ORDER BY ordinal_position
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}
    except:
        return {}

def create_dynamic_tables(cursor, export_data):
    """根據匯出資料動態建立資料表"""
    
    # 建立基本資料表（如果不存在）
    base_tables = {
        'users': """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                line_user_id VARCHAR(255) UNIQUE,
                display_name VARCHAR(255),
                picture_url TEXT,
                storage_mode VARCHAR(50),
                notification_enabled BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'fridges': """
            CREATE TABLE IF NOT EXISTS fridges (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                owner_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'fridge_members': """
            CREATE TABLE IF NOT EXISTS fridge_members (
                id SERIAL PRIMARY KEY,
                fridge_id INTEGER,
                user_id INTEGER,
                role VARCHAR(50) DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'fridge_compartments': """
            CREATE TABLE IF NOT EXISTS fridge_compartments (
                id SERIAL PRIMARY KEY,
                fridge_id INTEGER,
                name VARCHAR(255),
                temperature DECIMAL(4,1),
                humidity DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'food_items': """
            CREATE TABLE IF NOT EXISTS food_items (
                id SERIAL PRIMARY KEY,
                fridge_id INTEGER,
                compartment_id INTEGER,
                name VARCHAR(255) NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit VARCHAR(50),
                expiry_date DATE,
                purchase_date DATE,
                category VARCHAR(100),
                barcode VARCHAR(50),
                notes TEXT,
                image_url TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'fridge_invites': """
            CREATE TABLE IF NOT EXISTS fridge_invites (
                id SERIAL PRIMARY KEY,
                fridge_id INTEGER,
                invited_by INTEGER,
                invitee_line_id VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'invitations': """
            CREATE TABLE IF NOT EXISTS invitations (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255),
                description TEXT,
                event_date TIMESTAMP,
                location VARCHAR(255),
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'recipes': """
            CREATE TABLE IF NOT EXISTS recipes (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                ingredients JSONB,
                instructions TEXT,
                prep_time INTEGER,
                cook_time INTEGER,
                servings INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'user_recipes': """
            CREATE TABLE IF NOT EXISTS user_recipes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                recipe_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'budget_settings': """
            CREATE TABLE IF NOT EXISTS budget_settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                monthly_budget DECIMAL(10,2),
                currency VARCHAR(10) DEFAULT 'TWD',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'notification_settings': """
            CREATE TABLE IF NOT EXISTS notification_settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                expiry_reminder BOOLEAN DEFAULT true,
                budget_alert BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    }
    
    for table_name, create_sql in base_tables.items():
        try:
            cursor.execute(create_sql)
            print(f"✅ 建立/檢查資料表: {table_name}")
        except Exception as e:
            print(f"⚠️  建立資料表 {table_name} 失敗: {e}")

def smart_import_table(cursor, table_name, table_info):
    """智能匯入資料表（只匯入存在的欄位）"""
    
    data = table_info['data']
    if not data:
        print(f"⚠️  {table_name}: 沒有資料")
        return True
    
    # 取得目標資料表的現有欄位
    existing_columns = get_table_columns(cursor, table_name)
    
    if not existing_columns:
        print(f"⚠️  {table_name}: 資料表不存在，跳過")
        return True
    
    # 找出可匯入的欄位（來源和目標都有的）
    source_columns = [col['name'] for col in table_info['columns']]
    valid_columns = [col for col in source_columns if col in existing_columns]
    
    if not valid_columns:
        print(f"⚠️  {table_name}: 沒有匹配的欄位，跳過")
        return True
    
    print(f"📥 匯入 {table_name} ({len(valid_columns)}/{len(source_columns)} 個欄位)...")
    print(f"   可匯入欄位: {valid_columns}")
    
    try:
        # 建立 INSERT 語句（只包含有效欄位）
        placeholders = ', '.join(['%s'] * len(valid_columns))
        columns_str = ', '.join(valid_columns)
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        # 準備資料（只取有效欄位）
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
        print("使用方式: python3 smart_import.py <匯出檔案.json>")
        sys.exit(1)
    
    export_file = sys.argv[1]
    
    try:
        print(f"📥 讀取匯出檔案: {export_file}")
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        print(f"🔄 連接新資料庫...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("🔨 建立資料表...")
        create_dynamic_tables(cursor, export_data)
        conn.commit()
        
        print("📥 開始智能匯入資料...")
        
        # 按依賴關係順序匯入
        import_order = [
            'users', 'fridges', 'fridge_members', 'fridge_compartments',
            'food_items', 'fridge_invites', 'invitations', 'recipes',
            'user_recipes', 'budget_settings', 'notification_settings'
        ]
        
        successful_imports = 0
        total_tables = 0
        
        for table_name in import_order:
            if table_name in export_data.get('tables', {}):
                table_info = export_data['tables'][table_name]
                if smart_import_table(cursor, table_name, table_info):
                    successful_imports += 1
                total_tables += 1
        
        conn.commit()
        
        print(f"\n✅ 智能匯入完成!")
        print(f"📊 成功匯入: {successful_imports}/{total_tables} 個資料表")
        
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