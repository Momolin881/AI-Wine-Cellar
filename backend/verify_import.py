#!/usr/bin/env python3
"""
驗證酒窖資料是否成功匯入
"""

import psycopg2
from datetime import datetime

# 從環境變數讀取資料庫連接
import os
NEW_DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/zeabur')

def verify_import():
    """驗證匯入結果"""
    
    try:
        print("🔍 驗證酒窖資料匯入結果...")
        conn = psycopg2.connect(NEW_DATABASE_URL)
        cursor = conn.cursor()
        
        # 1. 檢查所有資料表的資料量
        print("📊 檢查資料表資料量...")
        tables = ['users', 'wine_cellars', 'wine_items', 'invitations', 'budget_settings', 'notification_settings']
        
        total_rows = 0
        table_stats = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_rows += count
                table_stats[table] = count
                
                status = "✅" if count > 0 else "⚠️ "
                print(f"  {status} {table}: {count} 筆資料")
                
            except Exception as e:
                print(f"  ❌ {table}: 檢查失敗 - {e}")
                table_stats[table] = 0
        
        print(f"\n📈 總計: {total_rows} 筆資料")
        
        # 2. 檢查外鍵關聯是否正確
        print("\n🔗 檢查外鍵關聯...")
        
        # 檢查 wine_items -> wine_cellars
        cursor.execute("""
            SELECT COUNT(*) FROM wine_items w 
            LEFT JOIN wine_cellars c ON w.cellar_id = c.id 
            WHERE c.id IS NULL AND w.cellar_id IS NOT NULL
        """)
        orphaned_wines = cursor.fetchone()[0]
        
        if orphaned_wines == 0:
            print("  ✅ wine_items -> wine_cellars: 外鍵關聯正常")
        else:
            print(f"  ❌ wine_items -> wine_cellars: {orphaned_wines} 筆孤兒記錄")
        
        # 檢查 wine_cellars -> users (如果有 owner_id 欄位)
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'wine_cellars' AND column_name = 'owner_id'
        """)
        has_owner_id = cursor.fetchone()
        
        if has_owner_id:
            cursor.execute("""
                SELECT COUNT(*) FROM wine_cellars c 
                LEFT JOIN users u ON c.owner_id = u.id 
                WHERE u.id IS NULL AND c.owner_id IS NOT NULL
            """)
            orphaned_cellars = cursor.fetchone()[0]
            
            if orphaned_cellars == 0:
                print("  ✅ wine_cellars -> users: 外鍵關聯正常")
            else:
                print(f"  ❌ wine_cellars -> users: {orphaned_cellars} 筆孤兒記錄")
        
        # 3. 檢查資料內容樣本
        print("\n📋 檢查資料內容樣本...")
        
        # 用戶樣本
        if table_stats['users'] > 0:
            cursor.execute("SELECT id, line_user_id, display_name FROM users LIMIT 3")
            users = cursor.fetchall()
            print("  👥 用戶樣本:")
            for user in users:
                print(f"    - ID {user[0]}: {user[2]} ({user[1]})")
        
        # 酒窖樣本
        if table_stats['wine_cellars'] > 0:
            cursor.execute("SELECT id, name, description FROM wine_cellars LIMIT 3")
            cellars = cursor.fetchall()
            print("  🏛️  酒窖樣本:")
            for cellar in cellars:
                desc = cellar[2][:30] + "..." if cellar[2] and len(cellar[2]) > 30 else cellar[2]
                print(f"    - ID {cellar[0]}: {cellar[1]} ({desc})")
        
        # 酒款樣本
        if table_stats['wine_items'] > 0:
            cursor.execute("SELECT id, name, wine_type, vintage FROM wine_items LIMIT 3")
            wines = cursor.fetchall()
            print("  🍷 酒款樣本:")
            for wine in wines:
                vintage = f" ({wine[3]})" if wine[3] else ""
                wine_type = f" - {wine[2]}" if wine[2] else ""
                print(f"    - ID {wine[0]}: {wine[1]}{vintage}{wine_type}")
        
        # 4. 檢查資料日期範圍
        print("\n📅 檢查資料日期範圍...")
        for table in ['users', 'wine_cellars', 'wine_items', 'invitations']:
            if table_stats[table] > 0:
                try:
                    cursor.execute(f"SELECT MIN(created_at), MAX(created_at) FROM {table}")
                    min_date, max_date = cursor.fetchone()
                    if min_date and max_date:
                        min_str = min_date.strftime("%Y-%m-%d")
                        max_str = max_date.strftime("%Y-%m-%d")
                        print(f"  📊 {table}: {min_str} ~ {max_str}")
                except Exception as e:
                    print(f"  ⚠️  {table}: 無法檢查日期範圍")
        
        # 5. 最終評估
        print("\n🎯 最終評估:")
        
        expected_total = 171
        success_rate = (total_rows / expected_total) * 100 if expected_total > 0 else 0
        
        print(f"  📈 資料完整度: {total_rows}/{expected_total} ({success_rate:.1f}%)")
        
        if total_rows == expected_total:
            print("  🎉 完美！所有資料都已成功匯入")
        elif total_rows > expected_total * 0.9:
            print("  ✅ 良好！大部分資料已成功匯入")
        elif total_rows > 0:
            print("  ⚠️  部分成功，但有些資料可能遺失")
        else:
            print("  ❌ 匯入失敗，沒有資料")
        
        # 檢查關鍵資料表
        critical_tables = ['users', 'wine_cellars', 'wine_items']
        all_critical_ok = all(table_stats[table] > 0 for table in critical_tables)
        
        if all_critical_ok:
            print("  ✅ 所有關鍵資料表都有資料")
        else:
            missing = [table for table in critical_tables if table_stats[table] == 0]
            print(f"  ❌ 關鍵資料表缺少資料: {missing}")
        
        # 檢查外鍵完整性
        if orphaned_wines == 0:
            print("  ✅ 資料關聯完整性正常")
        else:
            print("  ⚠️  資料關聯有問題")
        
        return total_rows == expected_total and all_critical_ok and orphaned_wines == 0
        
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
    success = verify_import()
    if success:
        print("\n🎉 驗證通過！資料遷移完全成功！")
    else:
        print("\n⚠️  驗證發現問題，可能需要進一步檢查")