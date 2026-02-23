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
from fastapi.staticfiles import StaticFiles
import os

from sqlalchemy import text, inspect

from src.config import settings
from src.database import Base, engine
from src import models  # 確保所有 models 都被導入


def run_migrations():
    """
    執行資料庫遷移 - 新增缺少的欄位

    這是一個簡易的遷移方案，在啟動時檢查並新增缺少的欄位。
    """
    print("🔄 開始執行資料庫遷移檢查...")
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        print(f"📋 資料庫現有表格: {table_names}")

        # 檢查 wine_items 表格是否存在
        if 'wine_items' not in table_names:
            print("⚠️ wine_items 表格尚未建立，跳過遷移")
            return

        # 取得 wine_items 表格現有欄位
        existing_columns = {col['name'] for col in inspector.get_columns('wine_items')}
        print(f"📋 wine_items 現有欄位: {sorted(existing_columns)}")

        # 需要新增的欄位 (欄位名, 類型)
        new_columns = [
            ('rating', 'INTEGER'),
            ('review', 'TEXT'),
            ('flavor_tags', 'TEXT'),
            ('aroma', 'TEXT'),
            ('palate', 'TEXT'),
            ('finish', 'TEXT'),
            ('acidity', 'INTEGER'),
            ('tannin', 'INTEGER'),
            ('body', 'INTEGER'),
            ('sweetness', 'INTEGER'),
            ('alcohol_feel', 'INTEGER'),
        ]

        missing_columns = [col for col, _ in new_columns if col not in existing_columns]
        print(f"📋 需要新增的欄位: {missing_columns}")

        # 檢查 invitations 表格的欄位
        invitation_columns = {}
        if 'invitations' in table_names:
            invitation_columns = {col['name'] for col in inspector.get_columns('invitations')}
            print(f"📋 invitations 現有欄位: {sorted(invitation_columns)}")

        with engine.connect() as conn:
            # 處理 wine_items 表格遷移
            if missing_columns:
                for col_name, col_type in new_columns:
                    if col_name not in existing_columns:
                        try:
                            conn.execute(text(f'ALTER TABLE wine_items ADD COLUMN {col_name} {col_type}'))
                            conn.commit()
                            print(f"✅ 已新增欄位: wine_items.{col_name}")
                        except Exception as e:
                            print(f"⚠️ 新增欄位 {col_name} 失敗: {e}")
            
            # 處理 invitations 表格的缺失欄位
            if 'invitations' in table_names:
                # 檢查並新增 host_id 欄位
                if 'host_id' not in invitation_columns:
                    try:
                        conn.execute(text('ALTER TABLE invitations ADD COLUMN host_id INTEGER'))
                        conn.commit()
                        print("✅ 已新增欄位: invitations.host_id")
                    except Exception as e:
                        print(f"⚠️ 新增 host_id 欄位失敗: {e}")
                
                # 檢查並新增 allow_forwarding 欄位
                if 'allow_forwarding' not in invitation_columns:
                    try:
                        conn.execute(text('ALTER TABLE invitations ADD COLUMN allow_forwarding BOOLEAN DEFAULT TRUE'))
                        conn.commit()
                        print("✅ 已新增欄位: invitations.allow_forwarding")
                    except Exception as e:
                        print(f"⚠️ 新增 allow_forwarding 欄位失敗: {e}")
                
                # 修復 NULL 值
                try:
                    result = conn.execute(text('UPDATE invitations SET allow_forwarding = TRUE WHERE allow_forwarding IS NULL'))
                    conn.commit()
                    print(f"✅ 修復了 {result.rowcount} 筆 allow_forwarding NULL 值")
                except Exception as e:
                    print(f"⚠️ 修復 allow_forwarding NULL 值失敗: {e}")

        if not missing_columns and 'allow_forwarding' in invitation_columns:
            print("✅ 所有欄位已存在，無需遷移")
            
        print("🔄 資料庫遷移完成")
    except Exception as e:
        print(f"❌ 資料庫遷移檢查失敗: {e}")
        import traceback
        traceback.print_exc()


from src.services import scheduler
# 酒窖路由
from src.routes import wine_items, wine_cellars
# 功能路由

# 功能路由
from src.routes import line_webhook, notifications, budget, recipes, fridge_members, fridge_export, invitations, admin


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
    try:
        run_migrations()
        print("資料庫遷移檢查完成")
    except Exception as e:
        print(f"⚠️ 資料庫遷移失敗，但繼續啟動: {e}")

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

# 管理後台路由 - 必須在所有其他路由之前定義
from fastapi.responses import FileResponse

@app.get("/admin-test")
async def admin_test():
    """測試 admin 路由是否正常工作"""
    return {"message": "Admin route is working!", "timestamp": "2025-01-26", "backend_url": "https://ai-wine-cellar-backend.zeabur.app"}

@app.get("/admin")
@app.get("/admin/")
async def admin_dashboard():
    """管理後台首頁 - 暫時重導向到主應用"""
    print("🚨 Admin dashboard route hit!")
    # 暫時返回簡單的管理頁面，避免文件路徑問題
    return JSONResponse(content={
        "message": "Admin dashboard temporarily redirected",
        "redirect_url": "https://ai-wine-cellar.zeabur.app",
        "admin_api": "https://ai-wine-cellar-backend.zeabur.app/api/v1/admin"
    })

# 設定 CORS middleware - 允許前端和 LINE 來源
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",  # 管理後台本地開發
        "https://ai-wine-cellar.zeabur.app",
        "https://ai-wine-cellar-backend.zeabur.app",  # 後端自己的域名
        "https://liff.line.me",
        "https://access.line.me",
        "https://line.me",
        # 移除通配符 "*" 以支持 credentials
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # OPTIONS 預檢請求緩存時間（秒）
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
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
