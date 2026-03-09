#!/usr/bin/env python3
"""
簡化遷移腳本 - 直接使用 pg_dump 和 psql
"""

import subprocess
import sys

# 舊資料庫連接（已洩露的）
OLD_DB_URL = "postgresql://root:8x26U597Iukp4MjGWda3RoZe1mtXTJl0@tpe1.clusters.zeabur.com:27644/zeabur"
# 新資料庫連接
NEW_DB_URL = "postgresql://root:Sf7D9Cj3t4P61eism2KBd8hL5u0TFkoZ@tpe1.clusters.zeabur.com:25970/zeabur"

def main():
    """使用 pg_dump 和 psql 進行完整遷移"""
    
    print("🔄 步驟 1: 從舊資料庫匯出完整 schema 和資料...")
    
    # 使用 pg_dump 匯出完整資料庫
    dump_cmd = [
        'pg_dump',
        '--clean',  # 清理現有資料
        '--if-exists',  # 如果存在才刪除
        '--no-owner',  # 不包含擁有者資訊
        '--no-privileges',  # 不包含權限
        '--verbose',
        OLD_DB_URL
    ]
    
    print(f"執行: {' '.join(dump_cmd)}")
    
    try:
        # 執行 dump 並直接 pipe 到新資料庫
        print("🔄 步驟 2: 直接匯入到新資料庫...")
        
        dump_process = subprocess.Popen(
            dump_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        restore_cmd = ['psql', NEW_DB_URL]
        
        restore_process = subprocess.Popen(
            restore_cmd,
            stdin=dump_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待完成
        dump_stdout, dump_stderr = dump_process.communicate()
        restore_stdout, restore_stderr = restore_process.communicate()
        
        if dump_process.returncode == 0 and restore_process.returncode == 0:
            print("✅ 資料庫遷移成功完成！")
            
            # 驗證資料
            print("🔍 驗證遷移結果...")
            verify_cmd = ['psql', NEW_DB_URL, '-c', 
                         "SELECT 'users' as table_name, COUNT(*) FROM users UNION ALL "
                         "SELECT 'wine_cellars', COUNT(*) FROM wine_cellars UNION ALL "
                         "SELECT 'wine_items', COUNT(*) FROM wine_items UNION ALL "
                         "SELECT 'invitations', COUNT(*) FROM invitations;"]
            
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
            
            if verify_result.returncode == 0:
                print("📊 遷移結果:")
                print(verify_result.stdout)
            else:
                print(f"⚠️ 驗證失敗: {verify_result.stderr}")
                
        else:
            print("❌ 遷移失敗!")
            print(f"Dump stderr: {dump_stderr}")
            print(f"Restore stderr: {restore_stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 遷移過程出錯: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)