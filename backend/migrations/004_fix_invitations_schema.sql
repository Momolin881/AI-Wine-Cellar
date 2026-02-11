-- 修復 invitations 表 schema，添加缺失的欄位
-- 執行日期: 2026-02-11

-- 檢查並添加 attendees 欄位（JSON 格式）
ALTER TABLE invitations 
ADD COLUMN IF NOT EXISTS attendees TEXT DEFAULT '[]';

-- 檢查並添加其他可能缺失的欄位
ALTER TABLE invitations 
ADD COLUMN IF NOT EXISTS latitude VARCHAR(50);

ALTER TABLE invitations 
ADD COLUMN IF NOT EXISTS longitude VARCHAR(50);

-- 確保所有欄位都有正確的預設值
UPDATE invitations 
SET attendees = '[]' 
WHERE attendees IS NULL;

UPDATE invitations 
SET wine_ids = '[]' 
WHERE wine_ids IS NULL;

-- 驗證修改結果
-- 這個查詢應該能成功執行，不會報錯
SELECT id, title, attendees, wine_ids FROM invitations LIMIT 1;