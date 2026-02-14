# Debug Summary - 系統問題修復記錄

## 🐛 Bug #1: 邀請傳送失敗問題 (2026-02-14)

### 問題描述
- **症狀**: 已創建的邀請 97-103 無法開啟，返回 500 錯誤
- **影響範圍**: 所有已發送的邀請連結失效，用戶無法訪問
- **緊急程度**: 🔴 Critical - 影響核心功能

### 根因分析
```
邀請功能新增 `allow_forwarding` 欄位 → 前端/後端不同步 → 500 錯誤
```

1. **Schema 不一致**：
   - 新增功能時添加了 `allow_forwarding` 欄位
   - 現有邀請記錄缺少此欄位
   - Backend 嘗試訪問不存在的欄位 → NULL 值錯誤

2. **向後相容性缺失**：
   - 沒有資料庫遷移腳本
   - 沒有預設值處理
   - 沒有安全存取機制

### 修復方案

#### 1. 熱修復 - 手動響應構建 (commit: ebff399)
```python
# 使用手動響應構建，安全取得欄位值
response_data = {
    "allow_forwarding": getattr(db_invitation, 'allow_forwarding', True),
    # ... 其他欄位
}
```

#### 2. 自動遷移 - 啟動時修復 (commit: b965888)
```python
def run_migrations():
    # 檢查 invitations 表格的 allow_forwarding 欄位
    if 'allow_forwarding' not in invitation_columns:
        conn.execute(text('ALTER TABLE invitations ADD COLUMN allow_forwarding BOOLEAN DEFAULT TRUE'))
        conn.execute(text('UPDATE invitations SET allow_forwarding = TRUE WHERE allow_forwarding IS NULL'))
```

#### 3. 手動修復 API - 應急方案 (commit: b256acf)
```python
@router.post("/admin/fix-invitation-forwarding")
def fix_invitation_forwarding(db: Session = Depends(get_db)):
    # 為現有邀請添加缺失欄位
```

### 部署流程
1. **即時修復**: 手動響應構建 → 立即恢復服務
2. **結構修復**: 自動遷移腳本 → 重啟時執行
3. **驗證**: 測試邀請 97-103 可正常訪問

### 受影響的邀請
- **邀請 ID**: 97, 98, 99, 100, 101, 102, 103
- **修復狀態**: ✅ 已修復，所有邀請可正常訪問

### 學到的教訓
1. **Schema 變更必須包含遷移腳本**
2. **新欄位需要預設值和向後相容性**
3. **關鍵功能需要即時監控**
4. **分段部署：熱修復 → 結構修復 → 驗證**

---

## 🐛 Bug #2: 時區時差通知問題 (2026-02-14)

### 問題描述
- **症狀 1**: 開瓶 5 天後才收到通知（延遲問題）
- **症狀 2**: 凌晨 2:00 收到通知（時區問題）
- **期望**: 開瓶後按酒款類型計算，在用戶設定時間通知

### 根因分析
```
週五統一檢查邏輯 + 固定18:00發送 + 時區轉換問題 = 延遲+錯誤時間
```

1. **邏輯設計錯誤**：
   ```python
   # ❌ 錯誤：每週五統一檢查
   trigger=CronTrigger(day_of_week='fri', hour=18, minute=0)
   ```
   - 如果週日開瓶，要等到週五 = 5天延遲

2. **時區處理錯誤**：
   - 固定 18:00 發送，但用戶設定可能是 9:00
   - 台灣時間 vs UTC 時間轉換問題
   - 18:00 (台灣) → 10:00 (UTC) → 2:00 (其他計算錯誤)

### 修復方案

#### 1. 即時排程系統 (commit: 1d54de7)
```python
def schedule_bottle_opened_reminder(wine_item, user_id):
    # 開瓶時立即設置個人提醒任務
    reminder_date = wine_item.optimal_drinking_end - timedelta(days=3)
    reminder_datetime = datetime.combine(reminder_date, user_time, tzinfo=TAIWAN_TZ)
    
    scheduler.add_job(
        send_bottle_opened_reminder,
        trigger=DateTrigger(run_date=reminder_datetime),
        id=f"bottle_reminder_{wine_item.id}_{user_id}"
    )
```

#### 2. 用戶時間尊重
```python
# 檢查是否為該用戶的通知時間（允許 ±15 分鐘誤差）
user_notification_time = settings.notification_time
time_diff = abs((current_time.hour * 60 + current_time.minute) - 
              (user_notification_time.hour * 60 + user_notification_time.minute))

if time_diff > 15:  # 不在用戶設定時間範圍內，跳過
    continue
```

#### 3. 台灣時區統一
```python
TAIWAN_TZ = ZoneInfo("Asia/Taipei")
scheduler = BackgroundScheduler(timezone=TAIWAN_TZ)
```

### 新的通知流程
```
開瓶動作 → 計算最佳飲用期 → 設置提醒(期限前3天,用戶設定時間) → 準時發送
```

**實例**：
- 週日開瓶 Purple Reign (5天最佳期)
- 計算提醒時間：週二 + 用戶設定時間 (9:00)
- 結果：週二早上 9:00 準時收到通知

### 學到的教訓
1. **避免批次處理延遲，改用事件驅動**
2. **時區處理要統一，避免多重轉換**
3. **尊重用戶設定，不要硬編碼時間**
4. **通知系統要考慮用戶體驗，不是系統方便**

---

## 🐛 Bug #3: 時區處理邀請時間差 (2026-02-14)

### 問題描述
- **症狀**: 送方創建邀請的時間與收方看到的時間有時差
- **原因**: dayjs 時區處理和 backend UTC 時間序列化問題

### 修復方案 (commit: 749e561, 2c54506)
1. **Backend**: 時間回傳加上 'Z' UTC 標示
2. **Frontend**: 使用 `dayjs.utc().local()` 正確轉換
3. **Plugin**: 添加 dayjs UTC 插件支援

---

## 📋 系統改進建議

### 立即行動項目
1. **監控告警**：設置邀請訪問失敗告警
2. **測試覆蓋**：增加 schema 變更的自動化測試
3. **部署檢查**：Schema 變更前的相容性檢查清單

### 中期優化
1. **資料庫版本控制**：引入 Alembic 遷移管理
2. **藍綠部署**：減少停機時間
3. **用戶通知**：系統維護期間的用戶提醒機制

### 長期規劃
1. **微服務拆分**：通知系統獨立化
2. **事件驅動架構**：減少批次處理依賴
3. **多時區支援**：國際化準備

---

## 🔧 Debug 工具與技巧

### 快速診斷命令
```bash
# 檢查邀請狀態
curl "https://ai-wine-cellar.zeabur.app/api/v1/invitations/99"

# 檢查資料庫遷移
curl -X POST "https://ai-wine-cellar.zeabur.app/api/v1/admin/migrate-database"

# 測試通知設定
curl "https://ai-wine-cellar.zeabur.app/api/v1/notifications/settings"
```

### 日志追蹤重點
1. **API 錯誤**: 關注 500 錯誤的堆棧追蹤
2. **時區轉換**: 記錄 UTC → 本地時間的轉換過程
3. **排程任務**: 任務創建和執行時間的日志

### 測試驗證清單
- [ ] 新邀請創建和訪問
- [ ] 舊邀請依然可訪問
- [ ] 轉發功能正常
- [ ] 時間顯示正確
- [ ] 通知按用戶設定時間發送

---

*最後更新: 2026-02-14*
*維護者: Claude Code Assistant*