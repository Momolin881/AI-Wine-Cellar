#!/usr/bin/env python3
"""
修復所有表格的缺失欄位問題
"""

import psycopg2

def fix_all_tables():
    """修復所有表格的缺失欄位"""
    
    DATABASE_URL = "postgresql://root:Sf7D9Cj3t4P61eism2KBd8hL5u0TFkoZ@tpe1.clusters.zeabur.com:25970/zeabur"
    
    try:
        print("🔧 開始修復所有表格...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 修復 invitations 表
        print("\n📋 修復 invitations 表...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'invitations' 
            AND table_schema = 'public'
            ORDER BY column_name
        """)
        invitations_columns = [row[0] for row in cursor.fetchall()]
        print(f"現有欄位: {invitations_columns}")
        
        invitations_fixes = [
            ('latitude', 'DECIMAL(10, 8)'),
            ('longitude', 'DECIMAL(11, 8)'),
            ('max_attendees', 'INTEGER DEFAULT 10'),
        ]
        
        for col_name, col_definition in invitations_fixes:
            if col_name not in invitations_columns:
                try:
                    sql = f'ALTER TABLE invitations ADD COLUMN {col_name} {col_definition}'
                    print(f"執行: {sql}")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"✅ 已新增欄位: invitations.{col_name}")
                except Exception as e:
                    print(f"⚠️ 新增欄位 {col_name} 失敗: {e}")
                    conn.rollback()
        
        # 檢查 wine_items 表是否需要額外欄位
        print("\n📋 檢查 wine_items 表...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'wine_items' 
            AND table_schema = 'public'
            ORDER BY column_name
        """)
        wine_items_columns = [row[0] for row in cursor.fetchall()]
        print(f"wine_items 欄位: {wine_items_columns}")
        
        # 檢查 wine_cellars 表
        print("\n📋 檢查 wine_cellars 表...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'wine_cellars' 
            AND table_schema = 'public'
            ORDER BY column_name
        """)
        wine_cellars_columns = [row[0] for row in cursor.fetchall()]
        print(f"wine_cellars 欄位: {wine_cellars_columns}")
        
        # 最終檢查
        print("\n🔍 檢查所有重要表格...")
        important_tables = ['users', 'wine_items', 'wine_cellars', 'invitations']
        
        for table in important_tables:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND table_schema = 'public'
            """)
            col_count = cursor.fetchone()[0]
            print(f"✓ {table}: {col_count} 個欄位")
        
        print("\n✅ 所有表格修復完成！")
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_all_tables()