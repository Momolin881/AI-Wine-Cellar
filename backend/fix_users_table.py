#!/usr/bin/env python3
"""
修復 users 表缺少的欄位
"""

import psycopg2

def fix_users_table():
    """修復 users 表缺少的 picture_url 欄位"""
    
    DATABASE_URL = "postgresql://root:Sf7D9Cj3t4P61eism2KBd8hL5u0TFkoZ@tpe1.clusters.zeabur.com:25970/zeabur"
    
    try:
        print("🔧 開始修復 users 表...")
        
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
        
        # 需要新增的欄位
        missing_columns = []
        
        if 'picture_url' not in existing_columns:
            missing_columns.append(('picture_url', 'TEXT'))
        
        if 'language_code' not in existing_columns:
            missing_columns.append(('language_code', 'VARCHAR(10) DEFAULT \'zh-TW\''))
            
        if 'timezone' not in existing_columns:
            missing_columns.append(('timezone', 'VARCHAR(50) DEFAULT \'Asia/Taipei\''))
        
        # 執行修復
        if missing_columns:
            print(f"🔨 需要新增的欄位: {[col[0] for col in missing_columns]}")
            
            for col_name, col_type in missing_columns:
                try:
                    sql = f'ALTER TABLE users ADD COLUMN {col_name} {col_type}'
                    print(f"執行: {sql}")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"✅ 已新增欄位: {col_name}")
                except Exception as e:
                    print(f"⚠️ 新增欄位 {col_name} 失敗: {e}")
                    conn.rollback()
        else:
            print("✅ users 表欄位完整，無需修復")
        
        # 再次檢查結果
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND table_schema = 'public'
            ORDER BY column_name
        """)
        final_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 修復後的欄位: {final_columns}")
        
        print("✅ users 表修復完成！")
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_users_table()