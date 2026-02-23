#!/usr/bin/env python3
"""
診斷資料問題
"""

import psycopg2
import json

NEW_DATABASE_URL = "postgresql://root:atbw08hzus35C6iMy2NQf7914ZJegHBo@tpe1.clusters.zeabur.com:22032/zeabur"

def diagnose_data():
    """診斷資料問題"""
    
    try:
        conn = psycopg2.connect(NEW_DATABASE_URL)
        cursor = conn.cursor()
        
        # 檢查新資料庫中的 wine_cellars
        print("🔍 檢查新資料庫中的 wine_cellars...")
        cursor.execute("SELECT id, name FROM wine_cellars ORDER BY id LIMIT 10")
        cellars = cursor.fetchall()
        print(f"wine_cellars 中的 ID: {[c[0] for c in cellars]}")
        for cellar in cellars:
            print(f"  ID {cellar[0]}: {cellar[1]}")
        
        # 檢查匯出檔案中的資料
        print("\n🔍 檢查匯出檔案中的資料...")
        with open('wine_cellar_export_20260223_160517.json', 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        # 檢查 wine_items 中使用的 cellar_id
        wine_items = export_data['tables']['wine_items']['data']
        cellar_ids_used = set()
        for item in wine_items[:5]:  # 只檢查前5筆
            cellar_id = item.get('cellar_id')
            cellar_ids_used.add(cellar_id)
            print(f"wine_item '{item.get('name')}' 使用 cellar_id: {cellar_id}")
        
        print(f"\nwine_items 使用的 cellar_id: {sorted(cellar_ids_used)}")
        
        # 檢查 wine_cellars 資料中的 ID
        cellars_data = export_data['tables']['wine_cellars']['data']
        cellar_ids_available = []
        for cellar in cellars_data[:5]:
            cellar_id = cellar.get('id')
            cellar_ids_available.append(cellar_id)
            print(f"wine_cellar '{cellar.get('name')}' ID: {cellar_id}")
        
        print(f"\nwine_cellars 可用的 ID: {sorted(cellar_ids_available)}")
        
        # 找出缺少的 ID
        missing_ids = cellar_ids_used - set(cellar_ids_available)
        if missing_ids:
            print(f"\n❌ 缺少的 cellar_id: {missing_ids}")
        else:
            print(f"\n✅ 所有 cellar_id 都有對應")
            
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    diagnose_data()