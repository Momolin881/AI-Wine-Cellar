"""
BudgetService 服務模組

提供預算控管和消費分析功能，專為 Wine Cellar 設計。
"""

import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from src.models.wine_item import WineItem
from src.models.wine_cellar import WineCellar
from src.models.budget_settings import BudgetSettings
from src.models.notification_settings import NotificationSettings
from src.schemas.budget import (
    SpendingStatsResponse,
    CategorySpending,
    MonthlyTrend,
    ShoppingSuggestion,
)

logger = logging.getLogger(__name__)


class BudgetService:
    """預算控管服務類別"""

    @staticmethod
    def get_spending_stats(
        db: Session,
        user_id: int,
        period: str = 'month'
    ) -> SpendingStatsResponse:
        """
        獲取消費統計

        Args:
            db: 資料庫 session
            user_id: 使用者 ID
            period: 統計期間 ('month' 或 'year')

        Returns:
            SpendingStatsResponse: 消費統計結果
        """
        # 獲取預算設定
        budget_settings = db.query(BudgetSettings).filter(
            BudgetSettings.user_id == user_id
        ).first()

        if not budget_settings:
            # 如果沒有設定預算，返回空統計
            return SpendingStatsResponse(
                total_spending=0.0,
                budget_amount=0.0,
                budget_used_percentage=0.0,
                is_over_threshold=False,
                category_breakdown=[],
                monthly_trend=[]
            )

        budget_amount = budget_settings.monthly_budget
        warning_threshold = budget_settings.warning_threshold

        # 計算統計期間
        today = date.today()
        if period == 'month':
            start_date = date(today.year, today.month, 1)
            budget_for_period = budget_amount
        else:  # year
            start_date = date(today.year, 1, 1)
            budget_for_period = budget_amount * 12

        # 查詢該期間的酒款消費
        query = db.query(WineItem).join(WineCellar).filter(
            WineCellar.owner_id == user_id,
            WineItem.purchase_date >= start_date,
            WineItem.purchase_date <= today,
            WineItem.price.isnot(None)
        )

        wine_items = query.all()

        # 計算總消費
        total_spending = sum(item.price for item in wine_items if item.price)

        # 計算預算使用百分比
        budget_used_percentage = (total_spending / budget_for_period * 100) if budget_for_period > 0 else 0

        # 檢查是否超過警告門檻
        is_over_threshold = budget_used_percentage >= warning_threshold

        # 分類統計
        category_stats = {}
        for item in wine_items:
            category = item.wine_type or '未分類'
            if category not in category_stats:
                category_stats[category] = {'amount': 0.0, 'count': 0}
            category_stats[category]['amount'] += item.price or 0.0
            category_stats[category]['count'] += 1

        category_breakdown = [
            CategorySpending(
                category=cat,
                amount=round(stats['amount'], 2),
                count=stats['count']
            )
            for cat, stats in category_stats.items()
        ]

        # 排序（金額由高到低）
        category_breakdown.sort(key=lambda x: x.amount, reverse=True)

        # 月度趨勢（最近12個月）
        monthly_trend = BudgetService._calculate_monthly_trend(db, user_id)

        return SpendingStatsResponse(
            total_spending=round(total_spending, 2),
            budget_amount=round(budget_for_period, 2),
            budget_used_percentage=round(budget_used_percentage, 2),
            is_over_threshold=is_over_threshold,
            category_breakdown=category_breakdown,
            monthly_trend=monthly_trend
        )

    @staticmethod
    def _calculate_monthly_trend(
        db: Session,
        user_id: int
    ) -> List[MonthlyTrend]:
        """計算最近12個月的消費趨勢"""
        trends = []
        today = date.today()

        for i in range(12):
            # 計算該月份的起始和結束日期
            target_month = today - relativedelta(months=i)
            start_date = date(target_month.year, target_month.month, 1)

            # 計算該月的最後一天
            if target_month.month == 12:
                end_date = date(target_month.year + 1, 1, 1) - relativedelta(days=1)
            else:
                end_date = date(target_month.year, target_month.month + 1, 1) - relativedelta(days=1)

            # 查詢該月的消費
            monthly_spending = db.query(func.sum(WineItem.price)).join(WineCellar).filter(
                WineCellar.owner_id == user_id,
                WineItem.purchase_date >= start_date,
                WineItem.purchase_date <= end_date,
                WineItem.price.isnot(None)
            ).scalar() or 0.0

            trends.append(MonthlyTrend(
                month=target_month.strftime('%Y-%m'),
                amount=round(monthly_spending, 2)
            ))

        return trends

    @staticmethod
    def get_shopping_suggestions(
        db: Session,
        user_id: int
    ) -> List[ShoppingSuggestion]:
        """
        獲取採買建議 (Wine Cellar 不提供自動採買建議)

        Args:
            db: 資料庫 session
            user_id: 使用者 ID

        Returns:
            List[ShoppingSuggestion]: 空的建議清單
        """
        logger.info(f"Shopping suggestions not applicable for wine cellar (user {user_id})")
        return []

    @staticmethod
    def check_budget_warning(
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """
        檢查預算警告

        Args:
            db: 資料庫 session
            user_id: 使用者 ID

        Returns:
            Dict: 包含 is_warning, budget_used_percentage, threshold 的字典
        """
        try:
            stats = BudgetService.get_spending_stats(db, user_id, 'month')
            
            budget_settings = db.query(BudgetSettings).filter(
                BudgetSettings.user_id == user_id
            ).first()
            
            threshold = budget_settings.warning_threshold if budget_settings else 80.0
            
            return {
                'is_warning': stats.is_over_threshold,
                'budget_used_percentage': stats.budget_used_percentage,
                'threshold': threshold,
                'total_spending': stats.total_spending,
                'budget_amount': stats.budget_amount
            }
            
        except Exception as e:
            logger.error(f"預算警告檢查失敗: {e}")
            return {
                'is_warning': False,
                'budget_used_percentage': 0.0,
                'threshold': 80.0,
                'total_spending': 0.0,
                'budget_amount': 0.0
            }