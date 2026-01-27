
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
    """

    # 格式化時間（轉換為台灣時間）
    event_time = invitation.event_time
    if event_time.tzinfo is None:
        # 假設資料庫存的是 UTC，轉換為台灣時間
        event_time = event_time.replace(tzinfo=timezone.utc).astimezone(TAIWAN_TZ)
    time_str = event_time.strftime("%Y/%m/%d %H:%M")
    
    # 建構酒款清單元件
    wine_components = []
    for wine in wines[:3]: # 最多顯示 3 款，避免太長
        wine_components.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "image",
                    "url": wine.image_url or "https://via.placeholder.com/150", # 預設圖片
                    "size": "xs",
                    "aspectMode": "cover",
                    "flex": 1,
                    "cornerRadius": "sm"
                },
                {
                    "type": "text",
                    "text": wine.name,
                    "size": "sm",
                    "color": "#eeeeee",
                    "flex": 4,
                    "wrap": True,
                    "gravity": "center",
                    "margin": "sm"
                }
            ],
            "margin": "md"
        })
    
    if len(wines) > 3:
        wine_components.append({
            "type": "text",
            "text": f"...還有其他 {len(wines)-3} 款好酒",
            "size": "xs",
            "color": "#aaaaaa",
            "margin": "md",
            "align": "end"
        })

    # 主題圖片
    hero_image = invitation.theme_image_url or "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"

    # LIFF URL for viewing details
    # 假設前端路由為 /invitation/{id}
    # 需透過 LIFF URL 開啟: https://liff.line.me/{LIFF_ID}/invitation/{id}
    detail_url = f"https://liff.line.me/{settings.LIFF_ID}/invitation/{invitation.id}"

    return {
        "type": "flex",
        "altText": f"🍷 收到新的品酒邀請：{invitation.title}",
        "contents": {
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
                "backgroundColor": "#2d2d2d", # 深色背景
                "contents": [
                    {
                        "type": "text",
                        "text": invitation.title,
                        "weight": "bold",
                        "size": "xl",
                        "color": "#c9a227", # 金色
                        "wrap": True
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
                                        "color": "#aaaaaa",
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
                                        "color": "#aaaaaa",
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
                    },
                    {
                        "type": "separator",
                        "margin": "lg",
                        "color": "#444444"
                    },
                    {
                        "type": "text",
                        "text": "即將品飲",
                        "weight": "bold",
                        "size": "sm",
                        "color": "#c9a227",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": wine_components,
                        "margin": "sm"
                    }
                ]
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
                            "label": "查看詳情 / 加入",
                            "uri": detail_url
                        },
                        "color": "#c9a227"
                    }
                ],
                "flex": 0
            }
        }
    }
