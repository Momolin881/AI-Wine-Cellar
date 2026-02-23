#!/usr/bin/env python3
"""
檢查 Zeabur 舊資料庫
"""

import psycopg2

def check_zeabur_database():
    """檢查 Zeabur 舊資料庫"""
    
    # 你提供的舊 Zeabur 連線
    OLD_ZEABUR_URL = "postgresql://root:J6HQI5zKwdbmr4i7L2o1sRSNvhZ30j98@tpe1.clusters.zeabur.com:27118/zeabur"
    
    try:
        print("🔍 檢查 Zeabur 舊資料庫...")
        print("🔗 連線: tpe1.clusters.zeabur.com:27118")
        
        conn = psycopg2.connect(OLD_ZEABUR_URL)
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
        for table_name in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                total_rows += row_count
                print(f"  - {table_name}: {row_count} 筆資料")
            except Exception as e:
                print(f"  - {table_name}: 無法取得資料數量 ({e})")
        
        print(f"\n📈 總計: {total_rows} 筆資料")
        
        # 檢查是否有酒窖相關資料
        wine_tables = [t for t in tables if 'wine' in t.lower() or 'cellar' in t.lower()]
        fridge_tables = [t for t in tables if 'fridge' in t.lower() or 'food' in t.lower()]
        
        if wine_tables:
            print(f"🍷 酒窖相關資料表: {wine_tables}")
        if fridge_tables:
            print(f"🧊 冰箱相關資料表: {fridge_tables}")
            
        return tables, total_rows > 0, wine_tables
        
    except Exception as e:
        print(f"❌ 檢查 Zeabur 資料庫失敗: {e}")
        return [], False, []
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_zeabur_database()