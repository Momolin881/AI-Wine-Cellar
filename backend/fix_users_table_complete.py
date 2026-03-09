#!/usr/bin/env python3
"""
完整修復 users 表的所有缺失欄位
"""

import psycopg2

def fix_users_table_complete():
    """完整修復 users 表的所有缺失欄位"""
    
    DATABASE_URL = "postgresql://root:Sf7D9Cj3t4P61eism2KBd8hL5u0TFkoZ@tpe1.clusters.zeabur.com:25970/zeabur"
    
    try:
        print("🔧 開始完整修復 users 表...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 檢查 users 表現有欄位
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND table_schema = 'public'
            ORDER BY column_name
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 users 表現有欄位: {existing_columns}")
        
        # 完整的必需欄位列表（基於錯誤訊息）
        required_columns = [
            ('storage_mode', 'VARCHAR(20) DEFAULT \'wine_cellar\''),
            ('picture_url', 'TEXT'),  # 可能還沒完全生效
            ('language_code', 'VARCHAR(10) DEFAULT \'zh-TW\''),
            ('timezone', 'VARCHAR(50) DEFAULT \'Asia/Taipei\''),
        ]
        
        # 檢查並新增缺失欄位
        for col_name, col_definition in required_columns:
            if col_name not in existing_columns:
                try:
                    sql = f'ALTER TABLE users ADD COLUMN {col_name} {col_definition}'
                    print(f"執行: {sql}")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"✅ 已新增欄位: {col_name}")
                except Exception as e:
                    print(f"⚠️ 新增欄位 {col_name} 失敗: {e}")
                    conn.rollback()
            else:
                print(f"✓ 欄位 {col_name} 已存在")
        
        # 檢查最終結果
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND table_schema = 'public'
            ORDER BY column_name
        """)
        final_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 修復後的完整欄位: {final_columns}")
        
        # 驗證關鍵欄位是否都存在
        critical_fields = ['storage_mode', 'picture_url', 'line_user_id', 'display_name']
        missing_critical = [field for field in critical_fields if field not in final_columns]
        
        if missing_critical:
            print(f"❌ 仍有關鍵欄位缺失: {missing_critical}")
        else:
            print("✅ 所有關鍵欄位都已具備！")
        
        print("✅ users 表完整修復完成！")
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_users_table_complete()