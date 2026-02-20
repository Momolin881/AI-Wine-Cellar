#!/usr/bin/env python3
"""
測試創建 invitation
"""

import os
import sys
sys.path.append('.')

from datetime import datetime
from src.database import SessionLocal
from src.models.invitation import Invitation

def test_create_invitation():
    """測試創建 invitation"""
    
    db = SessionLocal()
    try:
        print("測試創建新的 invitation...")
        
        # 創建測試數據
        test_invitation = Invitation(
            title="測試聚會",
            event_time=datetime(2026, 2, 22, 18, 0),
            location="測試地點",
            description="測試描述",
            wine_ids=[1, 2],
            attendees=[],
            max_attendees=4,
            allow_forwarding=True,
            host_id=None
        )
        
        db.add(test_invitation)
        db.commit()
        db.refresh(test_invitation)
        
        print(f"✅ 成功創建 invitation ID: {test_invitation.id}")
        print(f"標題: {test_invitation.title}")
        print(f"時間: {test_invitation.event_time}")
        print(f"人數上限: {test_invitation.max_attendees}")
        
        return test_invitation.id
        
    except Exception as e:
        print(f"❌ 創建失敗: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    test_create_invitation()