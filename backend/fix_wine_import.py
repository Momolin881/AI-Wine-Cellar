#!/usr/bin/env python3
"""
修復酒窖資料匯入問題
"""

import psycopg2
import json

# 新 PostgreSQL 連線
NEW_DATABASE_URL = "postgresql://root:atbw08hzus35C6iMy2NQf7914ZJegHBo@tpe1.clusters.zeabur.com:22032/zeabur"

def fix_database():
    """修復資料庫問題"""
    
    try:
        print("🔧 修復資料庫問題...")
        conn = psycopg2.connect(NEW_DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # 1. 修復外鍵引用 - 將 wine_items 的 cellar_id 指向正確的表
        print("🔧 修復外鍵引用...")
        try:
            cursor.execute("ALTER TABLE wine_items DROP CONSTRAINT IF EXISTS wine_items_cellar_id_fkey")
            cursor.execute("ALTER TABLE wine_items ADD CONSTRAINT wine_items_cellar_id_fkey FOREIGN KEY (cellar_id) REFERENCES wine_cellars(id)")
            print("✅ 修復 wine_items 外鍵引用")
        except Exception as e:
            print(f"⚠️  修復外鍵時發生錯誤: {e}")
        
        # 2. 重新建立缺少的資料表
        print("🔨 重新建立缺少的資料表...")
        
        missing_tables = {
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
        
        for table_name, create_sql in missing_tables.items():
            try:
                cursor.execute(create_sql)
                print(f"✅ 重新建立資料表: {table_name}")
            except Exception as e:
                print(f"⚠️  建立 {table_name} 失敗: {e}")
        
        conn.commit()
        
        # 3. 重新匯入失敗的資料
        print("📥 重新匯入資料...")
        
        # 讀取匯出檔案
        with open('wine_cellar_export_20260223_160517.json', 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        # 重新匯入 wine_items（現在外鍵應該正確了）
        if 'wine_items' in export_data['tables']:
            print("📥 重新匯入 wine_items...")
            table_info = export_data['tables']['wine_items']
            
            # 清空可能的錯誤資料
            cursor.execute("DELETE FROM wine_items")
            
            # 重新匯入
            valid_columns = ['id', 'cellar_id', 'name', 'wine_type', 'vintage', 'region', 
                           'purchase_date', 'optimal_drinking_start', 'optimal_drinking_end', 
                           'storage_location', 'image_url', 'notes', 'created_at', 'updated_at']
            
            placeholders = ', '.join(['%s'] * len(valid_columns))
            columns_str = ', '.join(valid_columns)
            insert_sql = f"INSERT INTO wine_items ({columns_str}) VALUES ({placeholders})"
            
            rows_to_insert = []
            for row_dict in table_info['data']:
                row_values = [row_dict.get(col, None) for col in valid_columns]
                rows_to_insert.append(row_values)
            
            cursor.executemany(insert_sql, rows_to_insert)
            print(f"✅ wine_items: 重新匯入 {len(rows_to_insert)} 筆資料")
        
        # 匯入其他資料表
        for table_name in ['invitations', 'budget_settings', 'notification_settings']:
            if table_name in export_data['tables']:
                print(f"📥 匯入 {table_name}...")
                table_info = export_data['tables'][table_name]
                
                if table_info['data']:
                    # 取得欄位
                    cursor.execute(f"""
                        SELECT column_name
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        ORDER BY ordinal_position
                    """)
                    target_columns = [row[0] for row in cursor.fetchall()]
                    source_columns = [col['name'] for col in table_info['columns']]
                    valid_columns = [col for col in source_columns if col in target_columns]
                    
                    if valid_columns:
                        placeholders = ', '.join(['%s'] * len(valid_columns))
                        columns_str = ', '.join(valid_columns)
                        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                        
                        rows_to_insert = []
                        for row_dict in table_info['data']:
                            row_values = [row_dict.get(col, None) for col in valid_columns]
                            rows_to_insert.append(row_values)
                        
                        cursor.executemany(insert_sql, rows_to_insert)
                        print(f"✅ {table_name}: 匯入 {len(rows_to_insert)} 筆資料")
                else:
                    print(f"⚠️  {table_name}: 沒有資料")
        
        conn.commit()
        
        # 4. 最終驗證
        print("\n🔍 驗證匯入結果...")
        tables = ['users', 'wine_cellars', 'wine_items', 'invitations', 'budget_settings', 'notification_settings']
        total_rows = 0
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_rows += count
            print(f"  ✅ {table}: {count} 筆資料")
        
        print(f"\n✅ 修復完成！總計 {total_rows} 筆酒窖資料")
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
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
    fix_database()