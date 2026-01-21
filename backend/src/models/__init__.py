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

# 保留舊模型（之後遷移時刪除）
from src.models.fridge import Fridge, FridgeCompartment
from src.models.fridge_member import FridgeMember, FridgeInvite
from src.models.food_item import FoodItem
from src.models.budget_settings import BudgetSettings

__all__ = [
    # 新酒窖模型
    "User",
    "WineCellar",
    "WineItem",
    "NotificationSettings",
    "Recipe",
    "UserRecipe",
    # 舊模型（遷移後移除）
    "Fridge",
    "FridgeCompartment",
    "FridgeMember",
    "FridgeInvite",
    "FoodItem",
    "BudgetSettings",
]
