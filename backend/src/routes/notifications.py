"""
通知設定 API 路由

提供通知設定的查詢和更新功能。
"""

import logging
from datetime import time
from fastapi import APIRouter, HTTPException, status

from src.models.notification_settings import NotificationSettings
from src.schemas.notification import NotificationSettingsResponse, NotificationSettingsUpdate
from src.routes.dependencies import DBSession, CurrentUserId
from src.services.scheduler import check_drinking_period

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Notifications"])


@router.get("/notifications/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    db: DBSession,
    user_id: CurrentUserId
):
    """
    取得使用者的通知設定

    如果使用者尚未設定，則自動建立預設設定。

    Args:
        db: 資料庫 session
        user_id: 使用者 ID（從 token 解析）

    Returns:
        NotificationSettingsResponse: 通知設定

    Raises:
        HTTPException 404: 使用者不存在
        HTTPException 500: 伺服器內部錯誤
    """
    try:
        # 查詢通知設定
        settings = db.query(NotificationSettings).filter(
            NotificationSettings.user_id == user_id
        ).first()

        # 如果不存在，建立預設設定
        if not settings:
            logger.info(f"為使用者 {user_id} 建立預設通知設定")
            settings = NotificationSettings(
                user_id=user_id,
                expiry_warning_enabled=True,
                expiry_warning_days=3,
                low_stock_enabled=False,
                low_stock_threshold=1,
                space_warning_enabled=True,
                space_warning_threshold=80,
                budget_warning_enabled=False,
                budget_warning_amount=5000,
                notification_time=time(9, 0)
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return settings

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取得通知設定失敗: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得通知設定失敗"
        )


@router.put("/notifications/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_update: NotificationSettingsUpdate,
    db: DBSession,
    user_id: CurrentUserId
):
    """
    更新使用者的通知設定

    支援部分更新，只更新提供的欄位。

    Args:
        settings_update: 要更新的設定
        db: 資料庫 session
        user_id: 使用者 ID（從 token 解析）

    Returns:
        NotificationSettingsResponse: 更新後的通知設定

    Raises:
        HTTPException 404: 使用者或設定不存在
        HTTPException 500: 伺服器內部錯誤
    """
    try:
        # 查詢通知設定
        settings = db.query(NotificationSettings).filter(
            NotificationSettings.user_id == user_id
        ).first()

        # 如果不存在，建立預設設定
        if not settings:
            logger.info(f"為使用者 {user_id} 建立預設通知設定")
            settings = NotificationSettings(
                user_id=user_id,
                expiry_warning_enabled=True,
                expiry_warning_days=3,
                low_stock_enabled=False,
                low_stock_threshold=1,
                space_warning_enabled=True,
                space_warning_threshold=80,
                budget_warning_enabled=False,
                budget_warning_amount=5000,
                notification_time=time(9, 0)
            )
            db.add(settings)

        # 更新欄位（只更新非 None 的欄位）
        update_data = settings_update.model_dump(exclude_unset=True)

        # 特殊處理 notification_time（轉換為 time 物件）
        if "notification_time" in update_data and update_data["notification_time"] is not None:
            update_data["notification_time"] = time.fromisoformat(update_data["notification_time"])

        for field, value in update_data.items():
            setattr(settings, field, value)

        db.commit()
        db.refresh(settings)

        logger.info(f"使用者 {user_id} 的通知設定已更新")
        return settings

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"更新通知設定失敗（驗證錯誤）: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新通知設定失敗: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新通知設定失敗"
        )


@router.post("/notifications/test-expiry-check")
async def test_expiry_check(
    db: DBSession,
    user_id: CurrentUserId
):
    """
    發送測試通知到用戶的 LINE

    直接發送一條測試訊息，確認通知功能正常運作。
    """
    from src.models.user import User
    from src.services.line_bot import send_text_message

    try:
        # 取得用戶的 LINE User ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.line_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="找不到用戶的 LINE ID"
            )

        logger.info(f"發送測試通知給用戶 {user_id} (LINE: {user.line_user_id})")

        # 發送測試訊息
        success = send_text_message(
            user.line_user_id,
            "🍷 測試通知\n\n恭喜！您的通知功能運作正常。\n\n當有酒款即將到達最佳飲用期限時，我們會透過 LINE 通知您。"
        )

        if success:
            return {"message": "測試通知已發送，請查看 LINE 訊息"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="發送通知失敗，請稍後再試"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"發送測試通知失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
