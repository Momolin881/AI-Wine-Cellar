#!/usr/bin/env python3
"""
驗證資料庫遷移是否成功
"""

import psycopg2
import json
import os

def verify_migration():
    """驗證遷移結果"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ 請設定 DATABASE_URL 環境變數")
        return False
    
    try:
        print("🔄 連接新資料庫...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 檢查資料表
        cursor.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"📊 資料表檢查 ({len(tables)} 個):")
        total_rows = 0
        
        for table_name, column_count in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            total_rows += row_count
            print(f"  ✅ {table_name}: {row_count} 筆資料, {column_count} 個欄位")
        
        print(f"\n📈 總計: {total_rows} 筆資料")
        
        # 檢查關鍵資料表
        critical_tables = ['users', 'cellars', 'wine_items', 'invitations']
        print("\n🔍 關鍵資料檢查:")
        
        for table in critical_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"  ✅ {table}: {count} 筆資料")
                else:
                    print(f"  ⚠️  {table}: 沒有資料")
            except Exception as e:
                print(f"  ❌ {table}: 資料表不存在或錯誤 - {e}")
        
        # 檢查外鍵關聯
        print("\n🔗 外鍵關聯檢查:")
        
        # 檢查 cellars -> users
        cursor.execute("""
            SELECT COUNT(*) FROM cellars c 
            LEFT JOIN users u ON c.owner_id = u.id 
            WHERE u.id IS NULL AND c.owner_id IS NOT NULL
        """)
        orphaned_cellars = cursor.fetchone()[0]
        if orphaned_cellars == 0:
            print("  ✅ cellars -> users: 外鍵關聯正常")
        else:
            print(f"  ❌ cellars -> users: {orphaned_cellars} 筆孤兒記錄")
        
        # 檢查 wine_items -> cellars
        cursor.execute("""
            SELECT COUNT(*) FROM wine_items w 
            LEFT JOIN cellars c ON w.cellar_id = c.id 
            WHERE c.id IS NULL AND w.cellar_id IS NOT NULL
        """)
        orphaned_wines = cursor.fetchone()[0]
        if orphaned_wines == 0:
            print("  ✅ wine_items -> cellars: 外鍵關聯正常")
        else:
            print(f"  ❌ wine_items -> cellars: {orphaned_wines} 筆孤兒記錄")
        
        print("\n✅ 資料庫驗證完成!")
        return True
        
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    verify_migration()