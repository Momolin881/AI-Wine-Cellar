# Claude Code 使用指引

## 🔐 安全性第一

### 金鑰與敏感資料處理
- **絕對不能 commit 任何 .env 檔案**
- 所有 API 金鑰、資料庫密碼都在 .gitignore 中
- 如果意外洩露，立即更換所有金鑰

### 環境變數檔案
```bash
# 開發環境
backend/.env          # 本地開發用（SQLite）
backend/.env.local    # 本地開發用（備用）

# 生產環境  
backend/.env.production  # 遠端資料庫（PostgreSQL）
```

### 快速切換環境
```bash
# 切換到開發模式（本地 SQLite）
cd backend
cp .env.local .env

# 切換到生產模式（遠端 PostgreSQL）
cd backend  
cp .env.production .env

# 重啟服務
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🏗️ 開發流程

### 啟動開發環境
```bash
# 後端
cd backend
uv sync
uv run uvicorn src.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### 測試執行
```bash
# 後端測試
cd backend
uv run pytest --cov=src --cov-report=html

# 前端測試
cd frontend
npm run test:coverage
```

### 資料庫操作
```bash
# 檢查資料庫表格（SQLite）
cd backend
sqlite3 wine_cellar_dev.db ".tables"

# 檢查資料庫表格（PostgreSQL）
# 使用遠端連線工具或 psql
```

## 🚨 故障排除

### 後端 404 錯誤
1. 檢查服務是否啟動：`curl http://localhost:8000/health`
2. 檢查資料庫連線是否正常
3. 確認 API 端點在 `/docs` 中存在

### 資料庫連線失敗
1. **本地開發**：使用 SQLite (`sqlite:///./wine_cellar_dev.db`)
2. **生產環境**：確認 Zeabur PostgreSQL 服務狀態
3. 檢查 `DATABASE_URL` 格式是否正確

### LINE Bot 功能測試
- 需要使用**生產模式**（遠端資料庫）
- 確認 `LINE_CHANNEL_SECRET` 和 `LINE_CHANNEL_ACCESS_TOKEN` 正確
- LIFF ID 設定正確

## 📋 常用指令

### 品質檢查
```bash
# 程式碼格式化
cd backend && uv run black src/ && uv run ruff src/
cd frontend && npm run format

# 型別檢查
cd backend && uv run mypy src/

# 測試覆蓋率
cd backend && uv run pytest --cov=src
cd frontend && npm run test:coverage
```

### 部署準備
```bash
# 建構檢查
cd frontend && npm run build
cd backend && uv run python -c "import src.main"

# 環境變數檢查
cat backend/.env | grep -v "^#" | grep "="
```

## 🔑 環境變數清單

### 必要變數
- `DATABASE_URL` - 資料庫連線字串
- `SECRET_KEY` - JWT 安全金鑰
- `OPENAI_API_KEY` - AI 功能
- `CLOUDINARY_*` - 圖片儲存
- `LINE_*` - LINE Bot 整合
- `LIFF_ID` - 前端 LIFF 應用

### 可選變數
- `DEBUG` - 開發模式開關
- `ENVIRONMENT` - 環境識別

## 📊 測試覆蓋率目標

### 目前狀態
- 後端：44% → 目標 80%
- 前端：需建置 → 目標 70%

### 重點測試區域
1. API 端點測試（CRUD 操作）
2. 認證流程測試
3. AI 辨識功能測試
4. 前端元件測試
5. 整合測試

---

**⚠️ 記住：永遠不要 commit .env 檔案！**