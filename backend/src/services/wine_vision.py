"""
OpenAI Vision API 服務模組 - 酒標辨識

使用 GPT-4 Vision 辨識酒標圖片，返回酒名、類型、年份、產區、ABV 等資訊。
"""

import logging
import json
import base64
from typing import Optional

from openai import OpenAI

from src.config import settings

logger = logging.getLogger(__name__)

# 初始化 OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def recognize_wine_label(image_bytes: bytes) -> dict:
    """
    使用 OpenAI Vision API 辨識酒標圖片

    Args:
        image_bytes: 圖片位元組資料

    Returns:
        包含辨識結果的字典:
        {
            "name": str,              # 酒名
            "wine_type": str,         # 酒類（紅酒、白酒、威士忌等）
            "brand": str,             # 品牌/酒莊
            "vintage": int,           # 年份
            "region": str,            # 產區
            "country": str,           # 國家
            "abv": float,             # 酒精濃度
        }

    Raises:
        Exception: AI 辨識失敗時拋出
    """
    try:
        # 將圖片轉為 base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # 建立 prompt
        prompt = """
請辨識圖片中的酒類標籤，並以 JSON 格式返回以下資訊（使用繁體中文）：

{
  "name": "酒名（完整酒名，如：Château Margaux 2018）",
  "wine_type": "酒類（紅酒、白酒、粉紅酒、氣泡酒、香檳、威士忌、白蘭地、伏特加、清酒、啤酒、其他）",
  "brand": "品牌或酒莊名稱",
  "vintage": 年份（整數，如 2018，如果無法辨識則為 null）,
  "region": "產區（如：波爾多、勃根地、納帕谷、蘇格蘭高地，如果無法辨識則為 null）",
  "country": "國家（如：法國、義大利、美國、日本）",
  "abv": 酒精濃度百分比（數字，如 13.5，如果無法辨識則為 null）,
  "container_type": "容器類型（瓶、箱、桶，預設為瓶）",
  "suggested_storage_temp": "建議儲存溫度（如：12-14°C，如果不確定則為 null）",
  "description": "簡短描述（1-2句話，關於這款酒的特色或風味）"
}

注意事項：
1. 仔細閱讀酒標上的所有文字，包括小字
2. 如果是威士忌或烈酒，年份可能是陳年年數（如 12年），這時 vintage 設為 null
3. ABV 通常標示為 "XX% vol" 或 "XX% alc/vol"
4. 只返回 JSON，不要包含其他說明文字
5. 如果無法辨識酒類，name 設為「未知酒款」，wine_type 設為「其他」
"""

        # 呼叫 OpenAI Vision API
        response = client.chat.completions.create(
            model=settings.AI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high",  # 使用高解析度以辨識酒標細節
                            },
                        },
                    ],
                }
            ],
            max_tokens=settings.AI_VISION_MAX_TOKENS,
            temperature=settings.AI_VISION_TEMPERATURE,
        )

        # 解析回應
        content = response.choices[0].message.content.strip()
        logger.info(f"OpenAI Vision API 回應: {content[:200]}...")

        # 解析 JSON（移除可能的 markdown 代碼區塊標記）
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)

        # 驗證必要欄位
        required_fields = ["name", "wine_type"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"AI 回應缺少必要欄位: {field}")

        # 確保欄位類型正確
        if result.get("vintage") and not isinstance(result["vintage"], int):
            try:
                result["vintage"] = int(result["vintage"])
            except (ValueError, TypeError):
                result["vintage"] = None

        if result.get("abv") and not isinstance(result["abv"], (int, float)):
            try:
                result["abv"] = float(result["abv"])
            except (ValueError, TypeError):
                result["abv"] = None

        logger.info(f"酒標辨識成功: {result['name']}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"AI 回應 JSON 解析失敗: {e}, content: {content}")
        raise Exception("AI 辨識結果格式錯誤") from e

    except Exception as e:
        logger.error(f"AI 辨識失敗: {e}")
        raise Exception(f"AI 辨識失敗: {str(e)}") from e


# 保留舊函式以維持向下相容（之後可刪除）
def recognize_food_item(image_bytes: bytes) -> dict:
    """
    向下相容：呼叫 recognize_wine_label
    """
    return recognize_wine_label(image_bytes)
