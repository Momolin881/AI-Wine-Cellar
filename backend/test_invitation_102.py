#!/usr/bin/env python3
"""
直接測試 invitation 102 的資料
"""

import psycopg2
import json

DATABASE_URL = "postgresql://root:4Y7RhKkQ5N8m12sUyilw09MnSGcx3eL6@sjc1.clusters.zeabur.com:28948/zeabur"

def test_invitation_102():
    """測試 invitation 102"""
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("查詢 invitation 102...")
        cursor.execute("SELECT * FROM invitations WHERE id = 102")
        row = cursor.fetchone()
        
        if row:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'invitations' ORDER BY ordinal_position")
            columns = [col[0] for col in cursor.fetchall()]
            
            print("✅ Invitation 102 存在")
            print(f"欄位: {columns}")
            print("資料:")
            for i, col in enumerate(columns):
                value = row[i] if i < len(row) else "N/A"
                print(f"  {col}: {value}")
                
            # 檢查 wine_ids
            wine_ids_index = columns.index('wine_ids') if 'wine_ids' in columns else -1
            if wine_ids_index >= 0 and row[wine_ids_index]:
                wine_ids = row[wine_ids_index]
                print(f"\nwine_ids: {wine_ids} (type: {type(wine_ids)})")
                
                if wine_ids:
                    print("\n查詢關聯的酒款...")
                    if isinstance(wine_ids, str):
                        wine_ids_list = json.loads(wine_ids)
                    else:
                        wine_ids_list = wine_ids
                    
                    cursor.execute("SELECT id, name FROM wine_items WHERE id = ANY(%s)", (wine_ids_list,))
                    wines = cursor.fetchall()
                    print(f"找到酒款: {wines}")
                
        else:
            print("❌ Invitation 102 不存在")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_invitation_102()