"""
排程器服務模組

使用 APScheduler 管理定時任務，包含效期提醒和空間警告。
"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func

from src.database import SessionLocal
from src.models.notification_settings import NotificationSettings
from src.models.food_item import FoodItem
from src.models.fridge import Fridge, FridgeCompartment
from src.services.line_bot import send_expiry_notification, send_space_warning

logger = logging.getLogger(__name__)

# 台灣時區
TAIWAN_TZ = ZoneInfo("Asia/Taipei")

# 建立背景排程器（使用台灣時區）
scheduler = BackgroundScheduler(timezone=TAIWAN_TZ)


def start_scheduler():
    """
    啟動排程器並註冊所有定時任務
    """
    if scheduler.running:
        logger.warning("排程器已經在運行中")
        return

    try:
        # 註冊每週任務：檢查適飲期提醒（每週五 18:00 執行）
        scheduler.add_job(
            check_drinking_period,
            trigger=CronTrigger(day_of_week='fri', hour=18, minute=0),
            id="check_drinking_period",
            name="每週五適飲期提醒",
            replace_existing=True
        )

        # 註冊每日任務：檢查空間使用率（每天早上 9:00 執行）
        scheduler.add_job(
            check_space_usage,
            trigger=CronTrigger(hour=9, minute=0),
            id="check_space_usage",
            name="檢查酒窖空間使用率",
            replace_existing=True
        )

        scheduler.start()
        logger.info("排程器已啟動，已註冊定時任務")

    except Exception as e:
        logger.error(f"啟動排程器失敗: {e}")
        raise


def stop_scheduler():
    """
    停止排程器
    """
    if not scheduler.running:
        logger.warning("排程器未運行")
        return

    try:
        scheduler.shutdown(wait=True)
        logger.info("排程器已停止")

    except Exception as e:
        logger.error(f"停止排程器失敗: {e}")
        raise


def check_drinking_period():
    """
    檢查所有使用者的適飲期提醒並發送通知
    
    對象：已開瓶 (opened) 且接近最佳飲用期結束 (optimal_drinking_end) 的酒款
    時間：每週五 18:00
    """
    logger.info("開始執行：每週五適飲期提醒")
    db = SessionLocal()

    try:
        # 查詢所有啟用適飲期提醒的通知設定
        settings_list = db.query(NotificationSettings).filter(
            NotificationSettings.expiry_warning_enabled == True
        ).all()

        logger.info(f"找到 {len(settings_list)} 位使用者啟用適飲期提醒")

        for settings in settings_list:
            try:
                today = datetime.now(TAIWAN_TZ).date()
                
                # 查詢該使用者的所有酒款
                # 條件 1: 已開瓶 (bottle_status == 'opened')
                # 條件 2: active 狀態
                # 條件 3: 有設定 optimal_drinking_end
                
                from src.models.wine_item import WineItem
                from src.models.wine_cellar import WineCellar
                
                items = db.query(WineItem).join(
                    WineCellar, WineItem.cellar_id == WineCellar.id
                ).filter(
                    WineCellar.user_id == settings.user_id,
                    WineItem.status == 'active',
                    WineItem.bottle_status == 'opened',
                    WineItem.optimal_drinking_end.isnot(None)
                ).all()

                # 篩選邏輯：
                # 1. 已經過期 (optimal_drinking_end < today)
                # 2. 即將過期 (within 7 days)
                
                notify_items = []
                for item in items:
                    days_remaining = (item.optimal_drinking_end - today).days
                    
                    if days_remaining <= 7: # 剩餘 7 天內或已過期
                        notify_items.append({
                            "name": item.name,
                            "expiry_date": item.optimal_drinking_end.isoformat(),
                            "days_remaining": days_remaining,
                            "type": item.preservation_type
                        })

                if notify_items:
                    # 發送通知
                    logger.info(f"使用者 {settings.user_id} 有 {len(notify_items)} 瓶酒款需要注意")
                    send_expiry_notification(settings.user.line_user_id, notify_items)

            except Exception as e:
                logger.error(f"處理使用者 {settings.user_id} 的提醒時發生錯誤: {e}")
                continue

        logger.info("完成：每週五適飲期提醒")

    except Exception as e:
        logger.error(f"檢查適飲期時發生錯誤: {e}")

    finally:
        db.close()


def check_space_usage():
    """
    檢查所有使用者的酒窖空間使用率並發送警告

    遍歷所有啟用空間提醒的使用者，檢查其酒窖空間使用率。
    """
    logger.info("開始執行：檢查酒窖空間使用率")
    db = SessionLocal()

    try:
        # 查詢所有啟用空間提醒的通知設定
        settings_list = db.query(NotificationSettings).filter(
            NotificationSettings.space_warning_enabled == True
        ).all()

        logger.info(f"找到 {len(settings_list)} 位使用者啟用空間提醒")

        for settings in settings_list:
            try:
                # 查詢該使用者的所有酒窖
                fridges = db.query(Fridge).filter(
                    Fridge.user_id == settings.user_id
                ).all()

                for fridge in fridges:
                    # 計算總容量和已使用容量
                    compartments = db.query(FridgeCompartment).filter(
                        FridgeCompartment.fridge_id == fridge.id
                    ).all()

                    total_capacity = sum(c.total_slots for c in compartments)
                    if total_capacity == 0:
                        continue

                    # 計算已使用的格子數
                    used_slots = db.query(func.count(FoodItem.id)).filter(
                        FoodItem.fridge_id == fridge.id
                    ).scalar()

                    # 計算使用率
                    usage_percentage = (used_slots / total_capacity) * 100

                    # 如果超過門檻，發送警告
                    if usage_percentage >= settings.space_warning_threshold:
                        logger.info(
                            f"酒窖 {fridge.id} 空間使用率 {usage_percentage:.1f}% "
                            f"超過門檻 {settings.space_warning_threshold}%"
                        )
                        send_space_warning(settings.user.line_user_id, usage_percentage)

            except Exception as e:
                logger.error(f"處理使用者 {settings.user_id} 的空間提醒時發生錯誤: {e}")
                continue

        logger.info("完成：檢查酒窖空間使用率")

    except Exception as e:
        logger.error(f"檢查酒窖空間使用率時發生錯誤: {e}")

    finally:
        db.close()
