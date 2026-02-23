#!/usr/bin/env python3
"""
匯入資料到新 PostgreSQL 資料庫
"""

import psycopg2
import json
import os
from datetime import datetime

def import_table_data(cursor, table_info):
    """匯入單一資料表的資料"""
    table_name = table_info['table_name']
    data = table_info['data']
    
    if not data:
        print(f"⚠️  {table_name}: 沒有資料需要匯入")
        return True
    
    try:
        # 取得欄位名稱
        column_names = [col['name'] for col in table_info['columns']]
        
        # 建立 INSERT 語句
        placeholders = ', '.join(['%s'] * len(column_names))
        columns_str = ', '.join(column_names)
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # 批次插入資料
        rows_to_insert = []
        for row_dict in data:
            row_values = [row_dict.get(col, None) for col in column_names]
            rows_to_insert.append(row_values)
        
        cursor.executemany(insert_sql, rows_to_insert)
        print(f"✅ {table_name}: 匯入 {len(rows_to_insert)} 筆資料")
        return True
        
    except Exception as e:
        print(f"❌ 匯入資料表 {table_name} 失敗: {e}")
        return False

def main():
    """主要匯入流程"""
    
    import sys
    if len(sys.argv) != 2:
        print("使用方式: python import_database.py <匯出檔案.json>")
        sys.exit(1)
    
    export_file = sys.argv[1]
    
    if not os.path.exists(export_file):
        print(f"❌ 找不到匯出檔案: {export_file}")
        sys.exit(1)
    
    # 從環境變數取得新資料庫連線
    NEW_DATABASE_URL = os.getenv('DATABASE_URL')
    if not NEW_DATABASE_URL:
        print("❌ 請設定 DATABASE_URL 環境變數")
        sys.exit(1)
    
    try:
        print(f"📥 讀取匯出檔案: {export_file}")
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        print(f"🔄 連接新資料庫...")
        conn = psycopg2.connect(NEW_DATABASE_URL)
        conn.autocommit = False  # 使用事務
        cursor = conn.cursor()
        
        # 檢查資料表是否存在
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        print(f"📊 新資料庫現有資料表: {existing_tables}")
        
        # 按順序匯入資料表（考慮外鍵依賴）
        import_order = [
            'users',
            'cellars', 
            'wine_items',
            'invitations',
            'invitation_responses',
            'alembic_version'
        ]
        
        successful_imports = 0
        total_imports = 0
        
        # 開始事務
        cursor.execute("BEGIN")
        
        for table_name in import_order:
            if table_name in export_data['tables']:
                if table_name not in existing_tables:
                    print(f"⚠️  資料表 {table_name} 不存在，跳過匯入")
                    continue
                    
                print(f"📥 匯入資料表: {table_name}")
                table_info = export_data['tables'][table_name]
                
                if import_table_data(cursor, table_info):
                    successful_imports += 1
                total_imports += 1
        
        # 匯入其他未列在順序中的資料表
        for table_name, table_info in export_data['tables'].items():
            if table_name not in import_order:
                if table_name not in existing_tables:
                    print(f"⚠️  資料表 {table_name} 不存在，跳過匯入")
                    continue
                    
                print(f"📥 匯入資料表: {table_name}")
                if import_table_data(cursor, table_info):
                    successful_imports += 1
                total_imports += 1
        
        # 提交事務
        conn.commit()
        
        print(f"\n✅ 資料匯入完成!")
        print(f"📊 成功匯入: {successful_imports}/{total_imports} 個資料表")
        
        # 更新序列（如果有自動遞增欄位）
        print("🔄 更新序列...")
        for table_name in existing_tables:
            try:
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND column_default LIKE 'nextval%'
                """)
                auto_columns = cursor.fetchall()
                
                for col in auto_columns:
                    column_name = col[0]
                    cursor.execute(f"""
                        SELECT setval(
                            pg_get_serial_sequence('{table_name}', '{column_name}'),
                            COALESCE((SELECT MAX({column_name}) FROM {table_name}), 1),
                            true
                        )
                    """)
                    print(f"  ✅ 更新 {table_name}.{column_name} 序列")
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