# AI Wine Cellar 數位酒窖管理系統

🍷 智慧酒窖管理系統 - 透過 LINE Bot + AI 幫你管理酒款、追蹤適飲期、推薦酒食搭配！

## 功能特色

### 🎯 P1 - 酒款入庫與管理（MVP）
- 📸 **拍照辨識**：使用 GPT-4 Vision API 自動辨識酒標資訊
- 📝 **快速登錄**：自動識別酒名、年份、產區、酒莊、價格
- 🗂️ **智慧分類**：支援紅酒、白酒、氣泡酒、威士忌等多種酒類
- 📊 **清單管理**：LIFF 頁面查看、編輯、刪除所有酒款

### ⏰ P2 - 適飲期與庫存提醒
- 🔔 **適飲期提醒**：酒款即將到達最佳飲用期自動 LINE 通知
- 📉 **庫存警報**：安全存量不足時提醒補貨
- 📦 **空間提醒**：酒窖使用率超過 80% 時提醒整理

### 🍳 P3 - 酒食搭配建議
- 🤖 **智慧推薦**：根據現有酒款推薦適合的料理搭配
- 📚 **個人搭配庫**：建立自己的「常用」和「專業級」搭配清單

### 💰 P4 - 採購預算控管
- 📈 **消費分析**：支出趨勢圖表、分類統計
- 💳 **預算追蹤**：每月預算控管、超支提醒
- 📋 **採買建議**：根據歷史和庫存生成採買清單

## 技術架構

### 後端
- **語言**: Python 3.11+
- **框架**: FastAPI 0.104+
- **套件管理**: uv（超快速 Python 套件管理工具）
- **資料庫**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **排程**: APScheduler
- **AI**: OpenAI GPT-4 Vision API
- **檔案儲存**: Cloudinary

### 前端
- **框架**: React + Vite
- **UI 元件**: Ant Design
- **主題**: Neumorphism 深色主題
- **LIFF SDK**: @line/liff

### 部署
- **平台**: Zeabur
- **成本**: $65/月（100 人 MVP）

## 快速開始

### 環境需求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- uv (Python 套件管理工具)

### 安裝 uv
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### 本地開發

1. **Clone 專案**
```bash
git clone <repository-url>
cd ai-wine-cellar
```

2. **設定環境變數**
```bash
cp .env.example .env
# 編輯 .env 填入你的 API keys
```

3. **啟動後端**
```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --reload
```

4. **啟動前端**
```bash
cd frontend
npm install
npm run dev
```

5. **訪問應用**
- API 文件: http://localhost:8000/docs
- LIFF 前端: http://localhost:5174

## 開發者資訊

### 專案結構
```
ai-wine-cellar/
├── backend/          # FastAPI 後端
│   ├── src/          # 原始碼
│   └── migrations/   # 資料庫遷移
├── frontend/         # React LIFF 前端
│   ├── src/          # 原始碼
│   └── public/       # 靜態資源
└── docs/             # 文件
```

### LINE Bot 設定

需要在 [LINE Developers Console](https://developers.line.biz/console/) 設定：

1. **Messaging API Channel**: 取得 Channel Secret 和 Access Token
2. **LIFF App**: 建立 LIFF 應用並取得 LIFF ID
3. **Webhook URL**: 設定為你的後端網域 + `/webhook/line`

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

---

**Built with ❤️ using FastAPI, React, and LINE Bot**

---

## 🍷 AI Wine Cellar 開發維護與排錯手冊 (2026 版)
這份文件紀錄了專案開發中關於 LINE LIFF 權限與前端 UI 優化的關鍵紀錄。

### 🛠 一、LINE LIFF shareTargetPicker 功能解鎖
當應用程式點擊分享跳出權限錯誤時，請依序檢查後台：

1. **基礎設定 (Basic Settings)**：確保已填寫 Privacy policy URL 與 Terms of use URL。
2. **頻道層級授權 (LINE Login)**：
   - 於 OpenID Connect 區塊點擊 Apply 以刷出隱藏的 Scopes 表格。
   - 於 Scopes 中找到 `share_target_picker` 並點擊 Apply。
3. **LIFF 實例開啟**：
   - 於 LIFF 設定中勾選 `share_target_picker` 權限。
   - 於最下方 Options 將 Share Target Picker 切換為 ON (綠色)。

### 🎨 二、前端 UI 優化：Ant Design (antd) v5 語法
修正 Deprecated 警告，提升效能與相容性：

- **Card / Modal**：將 `bodyStyle` 替換為 `styles={{ body: { ... } }}`。
- **DatePicker**：將 `popupStyle` 替換為 `styles={{ popup: { root: { ... } } }}`。
- **靜態方法**：應改用 `App` 元件包裹，以解決 `message.success` 無法消費動態主題的問題。

### ⚡ 三、重要修復與環境變數
- **前端初始化**：`liff.init()` 必須確保 `liffId` 不為空。目前 ID 為 `2008946239-5U8c7ry2`。
- **後端 API 修復**：在 `app/src/routes/invitations.py` 中，必須正確導入 `File`。
  - 修正：`from fastapi import File, UploadFile`。
- **部署網址**：https://ai-wine-cellar.zeabur.app
