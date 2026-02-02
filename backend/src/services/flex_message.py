
from typing import Dict, Any, List
from datetime import timezone, timedelta
from src.models.invitation import Invitation
from src.models.wine_item import WineItem
from src.config import settings

# 台灣時區 (UTC+8)
TAIWAN_TZ = timezone(timedelta(hours=8))

def create_invitation_flex_message(invitation: Invitation, wines: List[WineItem]) -> Dict[str, Any]:
    """
    產生邀請函的 Flex Message JSON

    Hero 圖片保留（單張圖片經測試可正常送達）。
    酒款僅使用純文字，不含 image 元件（多張圖片會導致 LINE 靜默丟棄訊息）。
    """

    # 格式化時間（轉換為台灣時間）
    event_time = invitation.event_time
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc).astimezone(TAIWAN_TZ)
    time_str = event_time.strftime("%Y/%m/%d %H:%M")

    # 建構酒款清單（純文字）
    wine_components = []
    for wine in wines[:3]:
        wine_components.append({
            "type": "text",
            "text": f"🍷 {wine.name}",
            "size": "sm",
            "color": "#eeeeee",
            "wrap": True,
            "margin": "sm"
        })

    if len(wines) > 3:
        wine_components.append({
            "type": "text",
            "text": f"...還有其他 {len(wines) - 3} 款好酒",
            "size": "xs",
            "color": "#aaaaaa",
            "margin": "sm",
            "align": "end"
        })

    # 主題圖片
    hero_image = invitation.theme_image_url or "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"

    # LIFF URL
    detail_url = f"https://liff.line.me/{settings.LIFF_ID}/invitation/{invitation.id}"

    # Body contents
    body_contents = [
        {
            "type": "text",
            "text": "🍷 品酒邀請",
            "size": "xs",
            "color": "#aaaaaa"
        },
        {
            "type": "text",
            "text": invitation.title,
            "weight": "bold",
            "size": "xl",
            "color": "#c9a227",
            "wrap": True,
            "margin": "md"
        },
        {
            "type": "separator",
            "margin": "lg",
            "color": "#444444"
        },
        {
            "type": "box",
            "layout": "vertical",
            "margin": "lg",
            "spacing": "sm",
            "contents": [
                {
                    "type": "box",
                    "layout": "baseline",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📅",
                            "size": "sm",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": time_str,
                            "wrap": True,
                            "color": "#eeeeee",
                            "size": "sm",
                            "flex": 5
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📍",
                            "size": "sm",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": invitation.location or "待定",
                            "wrap": True,
                            "color": "#eeeeee",
                            "size": "sm",
                            "flex": 5
                        }
                    ]
                }
            ]
        }
    ]

    # 酒款區塊（僅在有酒款時加入）
    if wine_components:
        body_contents.append({
            "type": "separator",
            "margin": "lg",
            "color": "#444444"
        })
        body_contents.append({
            "type": "text",
            "text": "即將品飲",
            "weight": "bold",
            "size": "sm",
            "color": "#c9a227",
            "margin": "lg"
        })
        body_contents.extend(wine_components)

    bubble = {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": hero_image,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
            "action": {
                "type": "uri",
                "uri": detail_url
            }
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#2d2d2d",
            "paddingAll": "20px",
            "contents": body_contents
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "backgroundColor": "#2d2d2d",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "查看詳情 / 我要參加",
                        "uri": detail_url
                    },
                    "color": "#c9a227"
                }
            ],
            "flex": 0
        }
    }

    return {
        "type": "flex",
        "altText": f"🥂 {invitation.title} — 品酒邀請",
        "contents": bubble
    }
