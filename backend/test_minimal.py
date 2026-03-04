#!/usr/bin/env python3
"""
最小化測試 - 檢查是否有語法錯誤
"""

try:
    print("🔄 測試導入...")
    
    # 逐步導入測試
    from src.config import settings
    print("✅ config imported")
    
    from src.database import engine
    print("✅ database imported") 
    
    from src.main import app
    print("✅ main imported")
    
    print(f"✅ App loaded: {app.title}")
    print("🎉 所有模組載入成功！")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()