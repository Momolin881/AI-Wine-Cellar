# 🍷 AI Wine Cellar - LINE Bot 設定指南

## 📌 概述

只需要建立 **一個 LINE Bot Channel**，包含：
- Messaging API（聊天功能）
- LIFF App（網頁應用）

---

## Step 1: 建立 Provider（如果還沒有）

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 登入你的 LINE 帳號
3. 點擊 **Create New Provider**
4. 輸入 Provider 名稱（例如：`My Apps` 或你的公司名稱）

---

## Step 2: 建立 Messaging API Channel

1. 在 Provider 頁面，點擊 **Create a new channel**
2. 選擇 **Messaging API**
3. 填寫資訊：

| 欄位 | 建議值 |
|------|--------|
| Channel name | `酒窖管家` 或 `AI Wine Cellar` |
| Channel description | `個人酒窖管理系統 - AI 辨識酒標、追蹤庫存` |
| Category | `Food & Beverage` |
| Subcategory | `Drink` |
| Email | 你的 Email |

4. 勾選同意條款，點擊 **Create**

---

## Step 3: 取得 Channel 金鑰

### 3.1 Channel Secret
1. 進入剛建立的 Channel
2. 在 **Basic settings** 頁籤
3. 找到 **Channel secret** → 點擊複製

```
📋 記下來：LINE_CHANNEL_SECRET=xxxxxxxx
```

### 3.2 Channel Access Token
1. 切換到 **Messaging API** 頁籤
2. 捲到最下方找到 **Channel access token**
3. 點擊 **Issue** 生成 Token（選擇 0 hours 不過期）
4. 複製生成的 Token

```
📋 記下來：LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxx
```

---

## Step 4: 設定 Webhook

在 **Messaging API** 頁籤：

1. **Webhook URL**: 
   - 開發中先留空
   - 部署後填入：`https://your-domain.zeabur.app/webhook/line`

2. **Use webhook**: 開啟 ✅

3. **Auto-reply messages**: 關閉 ❌（我們用程式回覆）

4. **Greeting messages**: 可自訂或關閉

---

## Step 5: 建立 LIFF App

1. 在同一個 Channel 頁面，點擊 **LIFF** 頁籤
2. 點擊 **Add**
3. 填寫：

| 欄位 | 值 |
|------|-----|
| LIFF app name | `Wine Cellar App` |
| Size | `Full`（全螢幕） |
| Endpoint URL | `https://your-frontend.zeabur.app`（先填假的，部署後改） |
| Scope | ✅ `profile` ✅ `openid` |
| Bot link feature | `On (Aggressive)` |

4. 點擊 **Add** 建立
5. 複製生成的 **LIFF ID**

```
📋 記下來：LIFF_ID=xxxx-xxxxxxxx
```

---

## Step 6: 更新 .env 檔案

將取得的金鑰填入 `backend/.env`：

```env
# LINE Bot - 酒窖管家
LINE_CHANNEL_SECRET=你的_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=你的_access_token
LIFF_ID=你的_liff_id
```

---

## Step 7: 加入好友測試

1. 在 **Messaging API** 頁籤找到 **QR code**
2. 用手機 LINE 掃描加入好友
3. 你的 Bot 就建立完成了！

---

## ✅ 完成檢查清單

- [ ] 建立 Provider
- [ ] 建立 Messaging API Channel
- [ ] 取得 Channel Secret
- [ ] 取得 Channel Access Token
- [ ] 關閉 Auto-reply
- [ ] 建立 LIFF App
- [ ] 取得 LIFF ID
- [ ] 更新 .env 檔案
- [ ] 掃碼加入好友

---

## 📝 備註

### 開發 vs 正式環境
這份設定同時用於開發和正式環境，只需要：
- Webhook URL 部署後填入正式網址
- LIFF Endpoint URL 部署後更新

### 費用
LINE Messaging API **免費版**每月可發送 500 則推播訊息，一般個人使用綽綽有餘。

---

## 🔗 相關連結

- [LINE Developers Console](https://developers.line.biz/console/)
- [LIFF 文件](https://developers.line.biz/en/docs/liff/)
- [Messaging API 文件](https://developers.line.biz/en/docs/messaging-api/)
