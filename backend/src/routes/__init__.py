"""
API 路由模組

包含所有 FastAPI 路由定義。
AI Wine Cellar - 個人數位酒窖
"""

# 酒窖路由
from src.routes import wine_items, wine_cellars, line_webhook, notifications, budget, recipes

__all__ = [
    "wine_items",
    "wine_cellars",
    "line_webhook",
    "notifications",
    "budget",
    "recipes",
]
