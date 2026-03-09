"""
Pydantic schemas 模組

包含所有 API 請求和回應的資料驗證 schemas。
"""

from src.schemas.notification import (
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
)
from src.schemas.budget import (
    BudgetSettingsResponse,
    BudgetSettingsUpdate,
    SpendingStatsResponse,
    ShoppingSuggestion,
    CategorySpending,
    MonthlyTrend,
)
from src.schemas.recipe import (
    RecipeCreate,
    RecipeResponse,
    UserRecipeCreate,
    UserRecipeResponse,
    RecipeRecommendationRequest,
    RecipeRecommendationResponse,
)

__all__ = [
    "NotificationSettingsResponse",
    "NotificationSettingsUpdate",
    "BudgetSettingsResponse", 
    "BudgetSettingsUpdate",
    "SpendingStatsResponse",
    "ShoppingSuggestion",
    "CategorySpending",
    "MonthlyTrend",
    "RecipeCreate",
    "RecipeResponse",
    "UserRecipeCreate",
    "UserRecipeResponse",
    "RecipeRecommendationRequest",
    "RecipeRecommendationResponse",
]