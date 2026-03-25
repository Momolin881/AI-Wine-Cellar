"""
pytest 配置文件
提供測試用的 fixtures 和配置
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import Base, get_db
from src.models.user import User
from src.models.wine_cellar import WineCellar
from src.routes.dependencies import get_current_user_id


# 測試用的 SQLite 記憶體資料庫
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """測試用的資料庫 session"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user_id():
    """測試用的使用者 ID - 模擬已登入使用者"""
    return 1


@pytest.fixture(scope="session")
def event_loop():
    """提供事件循環給整個測試會話"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """為每個測試提供乾淨的資料庫 session"""
    Base.metadata.create_all(bind=engine)
    
    # 創建測試用戶和酒窖
    db = TestingSessionLocal()
    try:
        # 創建測試用戶
        test_user = User(
            id=1,
            line_user_id="test_user_123",
            display_name="測試用戶",
            picture_url="https://example.com/avatar.jpg"
        )
        db.add(test_user)
        
        # 創建測試酒窖
        test_cellar = WineCellar(
            id=1,
            name="測試酒窖",
            description="用於測試的酒窖",
            owner_id=1
        )
        db.add(test_cellar)
        
        db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """
    測試用的 FastAPI client
    使用測試資料庫和模擬的認證
    """
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    非同步測試 client
    用於測試需要非同步操作的 API
    """
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_wine_data():
    """範例酒款資料"""
    return {
        "name": "Dom Pérignon 2012",
        "brand": "Dom Pérignon", 
        "wine_type": "香檳",
        "vintage": 2012,
        "price": 8000,
        "quantity": 2,
        "cellar_id": 1,
        "location": "A1",
        "purchase_date": "2024-01-15",
        "notes": "特殊場合用"
    }


@pytest.fixture
def auth_headers():
    """模擬認證 headers"""
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }