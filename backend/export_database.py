#!/usr/bin/env python3
"""
匯出舊 PostgreSQL 資料庫的所有資料
"""

import psycopg2
import json
import os
from datetime import datetime

# 舊的資料庫連線（最後一次使用）
OLD_DATABASE_URL = "postgresql://root:4Y7RhKkQ5N8m12sUyilw09MnSGcx3eL6@sjc1.clusters.zeabur.com:28948/zeabur"

def export_table_data(cursor, table_name):
    """匯出單一資料表的資料"""
    try:
        # 取得資料表結構
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        # 取得所有資料
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # 轉換為可序列化格式
        table_data = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                column_name = column_names[i]
                # 處理特殊資料類型
                if isinstance(value, datetime):
                    row_dict[column_name] = value.isoformat()
                elif value is None:
                    row_dict[column_name] = None
                else:
                    row_dict[column_name] = value
            table_data.append(row_dict)
        
        return {
            'table_name': table_name,
            'columns': [{'name': col[0], 'type': col[1]} for col in columns],
            'data': table_data,
            'row_count': len(table_data)
        }
        
    except Exception as e:
        print(f"❌ 匯出資料表 {table_name} 失敗: {e}")
        return None

def main():
    """主要匯出流程"""
    
    try:
        print("🔄 連接舊資料庫...")
        conn = psycopg2.connect(OLD_DATABASE_URL)
        cursor = conn.cursor()
        
        # 取得所有使用者資料表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 發現 {len(tables)} 個資料表: {tables}")
        
        # 匯出所有資料表
        export_data = {
            'export_date': datetime.now().isoformat(),
            'database_info': {
                'host': 'sjc1.clusters.zeabur.com',
                'port': 28948,
                'database': 'zeabur'
            },
            'tables': {}
        }
        
        for table_name in tables:
            print(f"📥 匯出資料表: {table_name}")
            table_data = export_table_data(cursor, table_name)
            if table_data:
                export_data['tables'][table_name] = table_data
                print(f"✅ {table_name}: {table_data['row_count']} 筆資料")
            else:
                print(f"⚠️  {table_name}: 匯出失敗")
        
        # 儲存匯出檔案
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"database_export_{timestamp}.json"
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 資料匯出完成: {export_file}")
        print(f"📄 總共匯出 {len(export_data['tables'])} 個資料表")
        
        # 顯示摘要
        print("\n📋 匯出摘要:")
        for table_name, table_info in export_data['tables'].items():
            print(f"  - {table_name}: {table_info['row_count']} 筆資料")
            
    except Exception as e:
        print(f"❌ 匯出失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()