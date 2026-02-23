#!/usr/bin/env python3
"""
簡化版資料匯入（會自動建立資料表）
"""

import psycopg2
import json
import os
import sys
from datetime import datetime

def create_tables(cursor):
    """建立所有必要的資料表"""
    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            line_user_id VARCHAR(255) UNIQUE,
            display_name VARCHAR(255),
            picture_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS cellars (
            id SERIAL PRIMARY KEY,
            owner_id INTEGER REFERENCES users(id),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            location VARCHAR(255),
            capacity INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS wine_items (
            id SERIAL PRIMARY KEY,
            cellar_id INTEGER REFERENCES cellars(id),
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS invitations (
            id SERIAL PRIMARY KEY,
            cellar_id INTEGER REFERENCES cellars(id),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            event_date TIMESTAMP,
            location VARCHAR(255),
            wine_ids JSONB,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS invitation_responses (
            id SERIAL PRIMARY KEY,
            invitation_id INTEGER REFERENCES invitations(id),
            user_id INTEGER REFERENCES users(id),
            status VARCHAR(50) DEFAULT 'pending',
            response_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    for sql in tables_sql:
        try:
            cursor.execute(sql)
            print(f"✅ 建立資料表成功")
        except Exception as e:
            print(f"⚠️  建立資料表時發生錯誤: {e}")

def main():
    """主要匯入流程"""
    
    if len(sys.argv) != 2:
        print("使用方式: python3 simple_import.py <匯出檔案.json>")
        sys.exit(1)
    
    export_file = sys.argv[1]
    
    if not os.path.exists(export_file):
        print(f"❌ 找不到匯出檔案: {export_file}")
        sys.exit(1)
    
    DATABASE_URL = "postgresql://root:atbw08hzus35C6iMy2NQf7914ZJegHBo@tpe1.clusters.zeabur.com:22032/zeabur"
    
    try:
        print(f"📥 讀取匯出檔案: {export_file}")
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        print(f"🔄 連接新資料庫...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("🔨 建立資料表...")
        create_tables(cursor)
        conn.commit()
        
        print("📥 開始匯入資料...")
        
        # 匯入順序很重要（外鍵依賴）
        import_order = ['alembic_version', 'users', 'cellars', 'wine_items', 'invitations', 'invitation_responses']
        
        for table_name in import_order:
            if table_name in export_data.get('tables', {}):
                table_info = export_data['tables'][table_name]
                data = table_info['data']
                
                if not data:
                    print(f"⚠️  {table_name}: 沒有資料")
                    continue
                
                print(f"📥 匯入 {table_name}...")
                
                # 取得欄位名稱
                column_names = [col['name'] for col in table_info['columns']]
                
                # 建立 INSERT 語句
                placeholders = ', '.join(['%s'] * len(column_names))
                columns_str = ', '.join(column_names)
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                
                # 批次插入
                rows_to_insert = []
                for row_dict in data:
                    row_values = [row_dict.get(col, None) for col in column_names]
                    rows_to_insert.append(row_values)
                
                cursor.executemany(insert_sql, rows_to_insert)
                print(f"✅ {table_name}: 匯入 {len(rows_to_insert)} 筆資料")
        
        conn.commit()
        print("\n✅ 資料匯入完成!")
        
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