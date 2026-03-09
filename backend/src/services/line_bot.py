"""
LINE Bot 服務模組

提供 LINE Bot 訊息發送功能，包含文字訊息和 Flex Message。
使用 LINE Bot SDK v3 API（延遲初始化，避免啟動時 crash）。
"""

import logging
from typing import Optional

from src.config import settings

logger = logging.getLogger(__name__)

# 延遲初始化 LINE Bot v3 API 客戶端（避免 import 時 crash 導致整個 app 無法啟動）
_messaging_api = None


def get_messaging_api():
    """取得 MessagingApi 實例（延遲初始化）"""
    global _messaging_api
    if _messaging_api is None:
        try:
            from linebot.v3.messaging import MessagingApi, ApiClient, Configuration
            _configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
            _api_client = ApiClient(_configuration)
            _messaging_api = MessagingApi(_api_client)
            logger.info("LINE Messaging API v3 初始化成功")
        except Exception as e:
            logger.error(f"LINE Messaging API v3 初始化失敗: {e}")
            return None
    return _messaging_api


def send_text_message(user_id: str, text: str) -> bool:
    """
    發送文字訊息給指定使用者

    Args:
        user_id: LINE User ID
        text: 要發送的文字訊息

    Returns:
        bool: 發送成功返回 True，失敗返回 False

    Examples:
        >>> success = send_text_message("U1234567890abcdef", "您好！")
        >>> print(success)
        True
    """
    try:
        from linebot.v3.messaging import ApiException
        from linebot.v3.messaging.models import TextMessage, PushMessageRequest

        api = get_messaging_api()
        if api is None:
            logger.error("LINE Messaging API 未初始化，無法發送訊息")
            return False

        api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=text)]
            )
        )
        logger.info(f"文字訊息發送成功: user_id={user_id}")
        return True

    except Exception as e:
        logger.error(f"發送文字訊息失敗: {e}")
        return False


def send_flex_message(user_id: str, alt_text: str, contents: dict) -> bool:
    """
    發送 Flex Message 給指定使用者

    Args:
        user_id: LINE User ID
        alt_text: 替代文字（在通知中顯示）
        contents: Flex Message 內容（JSON dict 格式）

    Returns:
        bool: 發送成功返回 True，失敗返回 False

    Examples:
        >>> contents = {
        ...     "type": "bubble",
        ...     "body": {
        ...         "type": "box",
        ...         "layout": "vertical",
        ...         "contents": [
        ...             {"type": "text", "text": "效期提醒", "weight": "bold"}
        ...         ]
        ...     }
        ... }
        >>> success = send_flex_message("U1234567890abcdef", "效期提醒", contents)
        >>> print(success)
        True
    """
    try:
        from linebot.v3.messaging.models import FlexMessage, FlexContainer, PushMessageRequest

        api = get_messaging_api()
        if api is None:
            logger.error("LINE Messaging API 未初始化，無法發送 Flex Message")
            return False

        # v3 SDK 需要用 FlexContainer.from_dict() 將 dict 轉為物件
        flex_container = FlexContainer.from_dict(contents)

        api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[
                    FlexMessage(alt_text=alt_text, contents=flex_container)
                ]
            )
        )
        logger.info(f"Flex Message 發送成功: user_id={user_id}, alt_text={alt_text}")
        return True

    except Exception as e:
        logger.error(f"發送 Flex Message 失敗: {e}")
        return False


def send_expiry_notification(user_id: str, items: list[dict]) -> bool:
    """
    發送適飲期提醒通知

    Args:
        user_id: LINE User ID
        items: 即將到達適飲期的酒款清單，每個 item 包含 name, expiry_date, days_remaining

    Returns:
        bool: 發送成功返回 True，失敗返回 False

    Examples:
        >>> items = [
        ...     {"name": "牛奶", "expiry_date": "2026-01-05", "days_remaining": 2},
        ...     {"name": "蘋果", "expiry_date": "2026-01-04", "days_remaining": 1}
        ... ]
        >>> success = send_expiry_notification("U1234567890abcdef", items)
    """
    if not items:
        logger.warning("沒有即將到達適飲期的酒款，不發送通知")
        return False

    # 建立 Flex Message 內容
    item_contents = []
    for item in items[:5]:  # 最多顯示 5 個
        days = item.get("days_remaining", 0)
        
        # 根據天數決定顯示文字和顏色
        if days < 0:
            days_text = f"已過期 {abs(days)} 天"
            color = "#ff4d4f"  # 紅色
        elif days == 0:
            days_text = "建議今天飲用"
            color = "#ff4d4f"  # 紅色
        else:
            days_text = f"剩餘 {days} 天"
            color = "#faad14"  # 金黃色

        item_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": item["name"],
                    "size": "sm",
                    "color": "#e0e0e0", # 深色模式文字
                    "flex": 2,
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": days_text,
                    "size": "sm",
                    "color": color,
                    "align": "end",
                    "flex": 1
                }
            ],
            "margin": "md"
        })

    contents = {
        "type": "bubble",
        "styles": {
            "body": {
                "backgroundColor": "#2d2d2d" # 深色背景
            },
            "footer": {
                "backgroundColor": "#2d2d2d"
            }
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🍷 適飲期提醒",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#c9a227" # 金色標題
                },
                {
                    "type": "text",
                    "text": f"您有 {len(items)} 瓶已開瓶的酒款要注意適飲期限喔！",
                    "size": "sm",
                    "color": "#b0b0b0",
                    "margin": "md",
                    "wrap": True
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": "#444444"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": item_contents,
                    "margin": "lg"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "打開酒窖",
                        "uri": f"https://liff.line.me/{settings.LIFF_ID}"
                    },
                    "style": "primary",
                    "color": "#c9a227" # 金色按鈕
                }
            ]
        }
    }

    return send_flex_message(user_id, f"🍷 適飲提醒：有 {len(items)} 瓶酒建議飲用", contents)


def send_low_stock_notification(user_id: str, items: list[dict]) -> bool:
    """
    發送庫存不足提醒

    Args:
        user_id: LINE User ID
        items: 庫存不足的酒款清單

    Returns:
        bool: 發送成功返回 True，失敗返回 False
    """
    if not items:
        return False

    item_names = ", ".join([item["name"] for item in items[:5]])
    text = f"📦 庫存提醒\n\n以下酒款數量不足：\n{item_names}"

    if len(items) > 5:
        text += f"\n...等共 {len(items)} 項"

    return send_text_message(user_id, text)


def send_space_warning(user_id: str, usage_percentage: float) -> bool:
    """
    發送空間占用警告

    Args:
        user_id: LINE User ID
        usage_percentage: 空間使用率（0-100）

    Returns:
        bool: 發送成功返回 True，失敗返回 False
    """
    text = f"🍷 空間提醒\n\n酒窖空間使用率已達 {usage_percentage:.1f}%，建議整理酒窖或享用部分酒款。"
    return send_text_message(user_id, text)
