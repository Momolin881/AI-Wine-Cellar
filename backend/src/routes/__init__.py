"""
API 路由模組

包含所有 FastAPI 路由定義。
AI Wine Cellar - 個人數位酒窖
"""

# 新酒窖路由
from src.routes import wine_items, wine_cellars

# 保留舊路由（向下相容）
from src.routes import food_items, fridges, line_webhook, notifications, budget, recipes

__all__ = [
    # 新路由
    "wine_items",
    "wine_cellars",
    # 舊路由（向下相容）
    "food_items",
    "fridges",
    "line_webhook",
    "notifications",
    "budget",
    "recipes",
]
