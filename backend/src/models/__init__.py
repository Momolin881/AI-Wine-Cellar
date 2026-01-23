"""
資料庫模型模組

包含所有 SQLAlchemy ORM models。
AI Wine Cellar - 個人數位酒窖
"""

from src.models.user import User
from src.models.wine_cellar import WineCellar
from src.models.wine_item import WineItem
from src.models.notification_settings import NotificationSettings
from src.models.recipe import Recipe
from src.models.user_recipe import UserRecipe
from src.models.budget_settings import BudgetSettings

# 注意：舊的 Fridge 模型已移除，避免與新 WineCellar 模型衝突

__all__ = [
    "User",
    "WineCellar",
    "WineItem",
    "NotificationSettings",
    "Recipe",
    "UserRecipe",
    "BudgetSettings",
]
