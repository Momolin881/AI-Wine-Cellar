#!/usr/bin/env python3
"""
檢查當前 Zeabur 資料庫
"""

import psycopg2

def check_current_database():
    """檢查當前 Zeabur 資料庫"""
    
    # 新的 Zeabur 連線
    NEW_ZEABUR_URL = "postgresql://root:Sf7D9Cj3t4P61eism2KBd8hL5u0TFkoZ@tpe1.clusters.zeabur.com:25970/zeabur"
    
    try:
        print("🔍 檢查當前 Zeabur 資料庫...")
        print("🔗 連線: tpe1.clusters.zeabur.com:25970")
        
        conn = psycopg2.connect(NEW_ZEABUR_URL)
        cursor = conn.cursor()
        
        # 取得所有資料表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 發現 {len(tables)} 個資料表:")
        
        total_rows = 0
        wine_data_count = 0
        
        for table_name in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                total_rows += row_count
                
                # 特別統計酒款相關資料
                if 'wine' in table_name.lower():
                    wine_data_count += row_count
                
                print(f"  - {table_name}: {row_count} 筆資料")
                
                # 如果是重要資料表，顯示一些範例資料
                if table_name in ['wine_items', 'wine_cellars'] and row_count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    print(f"    📝 範例資料 (前3筆):")
                    for i, row in enumerate(sample_data, 1):
                        print(f"      {i}. {row[:3]}...")  # 只顯示前3個欄位避免太長
                        
            except Exception as e:
                print(f"  - {table_name}: 無法取得資料數量 ({e})")
        
        print(f"\n📈 總計: {total_rows} 筆資料")
        print(f"🍷 酒款相關資料: {wine_data_count} 筆")
        
        # 檢查是否有酒窖相關資料
        wine_tables = [t for t in tables if 'wine' in t.lower() or 'cellar' in t.lower()]
        fridge_tables = [t for t in tables if 'fridge' in t.lower() or 'food' in t.lower()]
        
        if wine_tables:
            print(f"🍷 酒窖相關資料表: {wine_tables}")
        if fridge_tables:
            print(f"🧊 冰箱相關資料表: {fridge_tables}")
            
        return tables, total_rows, wine_data_count
        
    except Exception as e:
        print(f"❌ 檢查資料庫失敗: {e}")
        return [], 0, 0
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    tables, total, wine_count = check_current_database()
    if total > 0:
        print(f"\n✅ 資料庫連線成功，共有 {total} 筆資料")
        if wine_count >= 171:
            print(f"✅ 酒款資料充足 ({wine_count} 筆)")
        else:
            print(f"⚠️ 酒款資料可能不足 ({wine_count} 筆，預期 171 筆)")
    else:
        print("\n❌ 資料庫無資料或連線失敗")