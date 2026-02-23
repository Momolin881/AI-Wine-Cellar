#!/usr/bin/env python3
"""
匯出正確的酒窖資料
"""

import psycopg2
import json
import os
from datetime import datetime, date
from decimal import Decimal

# 正確的舊 Zeabur 資料庫
OLD_ZEABUR_URL = "postgresql://root:J6HQI5zKwdbmr4i7L2o1sRSNvhZ30j98@tpe1.clusters.zeabur.com:27118/zeabur"

def serialize_value(value):
    """安全地序列化各種資料類型"""
    if value is None:
        return None
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, date):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, (dict, list)):
        return json.dumps(value)
    else:
        return str(value)

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
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
        rows = cursor.fetchall()
        
        # 轉換為可序列化格式
        table_data = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                column_name = column_names[i]
                row_dict[column_name] = serialize_value(value)
            table_data.append(row_dict)
        
        # 顯示最新資料時間
        if table_data and 'created_at' in table_data[0]:
            latest_date = max([row.get('created_at', '') for row in table_data if row.get('created_at')])
            print(f"  📅 最新資料: {latest_date[:10]}")
        
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
        print("🍷 匯出正確的酒窖資料...")
        print("🔗 連線到正確的 Zeabur 舊資料庫")
        
        conn = psycopg2.connect(OLD_ZEABUR_URL)
        cursor = conn.cursor()
        
        # 只匯出酒窖相關的核心資料表
        wine_tables = [
            'users',
            'wine_cellars', 
            'wine_items',
            'invitations',
            'budget_settings',
            'notification_settings'
        ]
        
        print(f"📊 匯出 {len(wine_tables)} 個核心酒窖資料表")
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'source': 'zeabur_old_wine_cellar',
            'database_info': {
                'host': 'tpe1.clusters.zeabur.com',
                'port': 27118,
                'database': 'zeabur'
            },
            'tables': {}
        }
        
        total_rows = 0
        for table_name in wine_tables:
            print(f"📥 匯出資料表: {table_name}")
            table_data = export_table_data(cursor, table_name)
            if table_data:
                export_data['tables'][table_name] = table_data
                total_rows += table_data['row_count']
                print(f"✅ {table_name}: {table_data['row_count']} 筆資料")
        
        # 儲存匯出檔案
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"wine_cellar_export_{timestamp}.json"
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n✅ 酒窖資料匯出完成: {export_file}")
        print(f"📄 總共匯出 {len(export_data['tables'])} 個資料表，{total_rows} 筆資料")
        
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