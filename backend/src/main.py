"""
FastAPI 主應用程式

初始化 FastAPI 應用、設定 CORS、註冊路由、管理 scheduler 生命週期。
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from sqlalchemy import text, inspect

from src.config import settings
from src.database import Base, engine
from src import models  # 確保所有 models 都被導入


def run_migrations():
    """
    執行資料庫遷移 - 新增缺少的欄位

    這是一個簡易的遷移方案，在啟動時檢查並新增缺少的欄位。
    """
    try:
        inspector = inspect(engine)

        # 檢查 wine_items 表格是否存在
        if 'wine_items' not in inspector.get_table_names():
            print("⚠️ wine_items 表格尚未建立，跳過遷移")
            return

        # 取得 wine_items 表格現有欄位
        existing_columns = {col['name'] for col in inspector.get_columns('wine_items')}

        # 需要新增的欄位 (欄位名, 類型)
        new_columns = [
            ('review', 'TEXT'),
            ('acidity', 'INTEGER'),
            ('tannin', 'INTEGER'),
            ('body', 'INTEGER'),
            ('sweetness', 'INTEGER'),
            ('alcohol_feel', 'INTEGER'),
        ]

        with engine.connect() as conn:
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    try:
                        conn.execute(text(f'ALTER TABLE wine_items ADD COLUMN {col_name} {col_type}'))
                        conn.commit()
                        print(f"✅ 已新增欄位: wine_items.{col_name}")
                    except Exception as e:
                        print(f"⚠️ 新增欄位 {col_name} 失敗 (可能已存在): {e}")
    except Exception as e:
        print(f"⚠️ 資料庫遷移檢查失敗: {e}")


from src.services import scheduler
# 酒窖路由
from src.routes import wine_items, wine_cellars
# 功能路由

# 功能路由
from src.routes import line_webhook, notifications, budget, recipes, fridge_members, fridge_export, invitations


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理

    啟動時: 建立資料庫表格、啟動排程器
    關閉時: 關閉排程器
    """
    # Startup
    # 建立所有資料庫表格（如果不存在）
    Base.metadata.create_all(bind=engine)
    print("資料庫表格初始化完成")

    # 執行資料庫遷移（新增缺少的欄位）
    run_migrations()
    print("資料庫遷移檢查完成")

    # 啟動排程器
    scheduler.start_scheduler()
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    # Shutdown
    scheduler.stop_scheduler()
    print(f"{settings.APP_NAME} stopped")


# 建立 FastAPI 應用實例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Wine Cellar - 個人數位酒窖管理系統 API",
    lifespan=lifespan,
)

# 設定 CORS middleware
# 設定 CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# 全局異常處理器：記錄詳細的 422 驗證錯誤
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    捕獲並記錄詳細的請求驗證錯誤（422）
    """
    errors = exc.errors()
    logger.error(f"❌ 422 Validation Error on {request.method} {request.url.path}")
    logger.error(f"Validation errors: {errors}")

    # 返回標準的 422 錯誤回應
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


# CORS preflight 處理器
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """處理所有 OPTIONS 請求（CORS preflight）"""
    return {"status": "ok"}


# 健康檢查端點
@app.get("/health")
async def health_check():
    """健康檢查端點（用於 Zeabur 和監控）"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# 註冊酒窖路由
app.include_router(wine_cellars.router, prefix="/api/v1", tags=["Wine Cellars"])
app.include_router(wine_items.router, prefix="/api/v1", tags=["Wine Items"])

# 註冊功能路由
app.include_router(line_webhook.router, tags=["LINE"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
app.include_router(budget.router, prefix="/api/v1", tags=["Budget"])
app.include_router(recipes.router, prefix="/api/v1", tags=["Recipes"])
# app.include_router(fridge_members.router, prefix="/api/v1", tags=["Cellar Members"])  # 暫時停用
# app.include_router(fridge_export.router, prefix="/api/v1", tags=["Cellar Export"])  # 暫時停用
app.include_router(invitations.router, prefix="/api/v1", tags=["Invitations"])
