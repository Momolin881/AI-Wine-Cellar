#!/usr/bin/env python3
"""
最終修復：完全重新匯入所有資料
"""

import psycopg2
import json

NEW_DATABASE_URL = "postgresql://root:atbw08hzus35C6iMy2NQf7914ZJegHBo@tpe1.clusters.zeabur.com:22032/zeabur"

def final_fix():
    """完全重新匯入所有資料"""
    
    try:
        print("🔄 最終修復：完全重新匯入...")
        conn = psycopg2.connect(NEW_DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # 1. 清空所有資料表（保留結構）
        print("🗑️  清空現有資料...")
        tables_to_clear = ['wine_items', 'invitations', 'budget_settings', 'notification_settings', 'wine_cellars', 'users']
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  ✅ 清空 {table}")
            except Exception as e:
                print(f"  ⚠️  清空 {table} 失敗: {e}")
        
        # 2. 讀取匯出資料
        print("📥 讀取匯出資料...")
        with open('wine_cellar_export_20260223_160517.json', 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        # 3. 按正確順序重新匯入所有資料
        import_order = ['users', 'wine_cellars', 'wine_items', 'invitations', 'budget_settings', 'notification_settings']
        
        successful_imports = 0
        total_rows = 0
        
        for table_name in import_order:
            if table_name not in export_data['tables']:
                print(f"⚠️  {table_name}: 匯出檔案中沒有此資料表")
                continue
                
            table_info = export_data['tables'][table_name]
            data = table_info['data']
            
            if not data:
                print(f"⚠️  {table_name}: 沒有資料")
                continue
            
            print(f"📥 匯入 {table_name}...")
            
            # 取得目標資料表欄位
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position
            """)
            target_columns = [row[0] for row in cursor.fetchall()]
            
            # 取得來源欄位
            source_columns = [col['name'] for col in table_info['columns']]
            
            # 找出可匯入的欄位
            valid_columns = [col for col in source_columns if col in target_columns]
            
            if not valid_columns:
                print(f"❌ {table_name}: 沒有匹配的欄位")
                continue
            
            print(f"   匯入 {len(valid_columns)} 個欄位: {valid_columns[:5]}{'...' if len(valid_columns) > 5 else ''}")
            
            try:
                # 建立 INSERT 語句
                placeholders = ', '.join(['%s'] * len(valid_columns))
                columns_str = ', '.join(valid_columns)
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                # 準備資料
                rows_to_insert = []
                for row_dict in data:
                    row_values = [row_dict.get(col, None) for col in valid_columns]
                    rows_to_insert.append(row_values)
                
                # 批次插入
                cursor.executemany(insert_sql, rows_to_insert)
                
                rows_imported = len(rows_to_insert)
                total_rows += rows_imported
                successful_imports += 1
                
                print(f"✅ {table_name}: 成功匯入 {rows_imported} 筆資料")
                
            except Exception as e:
                print(f"❌ {table_name} 匯入失敗: {e}")
                # 不要 rollback，繼續嘗試其他資料表
        
        # 4. 提交所有更改
        conn.commit()
        
        # 5. 更新序列
        print("🔄 更新序列...")
        for table_name in import_order:
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
        
        # 6. 最終驗證
        print("\n🔍 最終驗證...")
        final_total = 0
        for table_name in import_order:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                final_total += count
                print(f"  ✅ {table_name}: {count} 筆資料")
            except Exception as e:
                print(f"  ❌ {table_name}: 無法檢查資料數量")
        
        print(f"\n🎉 最終修復完成！")
        print(f"📊 成功匯入 {successful_imports}/{len(import_order)} 個資料表")
        print(f"📈 總計 {final_total} 筆酒窖資料")
        
        if final_total == 171:
            print("✅ 所有 171 筆資料都已成功匯入！")
        else:
            print(f"⚠️  預期 171 筆，實際 {final_total} 筆")
        
    except Exception as e:
        print(f"❌ 最終修復失敗: {e}")
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
    final_fix()