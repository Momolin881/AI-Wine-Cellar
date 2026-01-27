/**
 * API 客戶端模組
 *
 * 使用 Axios 提供與後端 API 的通信介面。
 * 自動處理認證 token 和錯誤處理。
 */

import axios from 'axios';
import { getLiffAccessToken } from '../liff';

// API 基礎 URL
// 優先使用 VITE_API_URL（完整 URL），否則使用相對路徑（開發環境靠 proxy）
const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : (import.meta.env.VITE_API_BASE_URL || '/api/v1');

// 建立 Axios 實例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// 請求攔截器：自動設置 Content-Type（FormData 除外）
apiClient.interceptors.request.use(
  (config) => {
    if (config.data instanceof FormData) {
      // FormData：刪除預設的 Content-Type，讓瀏覽器自動設置（包含 boundary）
      delete config.headers['Content-Type'];
      // 增加上傳超時時間
      config.timeout = 60000;
      console.log('📤 FormData request:', config.url);
    } else {
      config.headers['Content-Type'] = 'application/json';
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 請求攔截器：自動添加 Authorization header
apiClient.interceptors.request.use(
  (config) => {
    const token = getLiffAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 回應攔截器：統一錯誤處理
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      // 伺服器回應錯誤
      console.error('API Error:', error.response.status, error.response.data);

      // 401 未授權 - 重新登入
      if (error.response.status === 401) {
        window.location.href = '/';
      }
    } else if (error.request) {
      // 請求已發送但無回應
      console.error('Network Error:', error.request);
      console.error('Error details:', error.message, error.code);
    } else {
      // 其他錯誤
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ========== API 方法 ==========

// ---------- 使用者相關 ----------

/**
 * 獲取使用者資訊
 * @returns {Promise<Object>} 使用者資訊
 */
export const getUserInfo = () => {
  return apiClient.get('/users/me');
};

/**
 * 更新使用者設定
 * @param {Object} settings - 設定物件
 * @returns {Promise<Object>} 更新後的設定
 */
export const updateUserSettings = (settings) => {
  return apiClient.put('/users/me/settings', settings);
};

// ---------- 酒款相關 ----------

/**
 * 獲取所有酒款
 * @param {Object} params - 查詢參數 (compartment, status, etc.)
 * @returns {Promise<Array>} 酒款清單
 */
export const getFoodItems = (params = {}) => {
  return apiClient.get('/wine-items', { params });
};

/**
 * 獲取單一酒款詳情
 * @param {number} itemId - 酒款 ID
 * @returns {Promise<Object>} 酒款詳情
 */
export const getFoodItem = (itemId) => {
  return apiClient.get(`/wine-items/${itemId}`);
};

/**
 * 上傳圖片並辨識酒標
 * @param {File} imageFile - 圖片檔案
 * @param {number} fridgeId - 酒窖 ID
 * @param {string} storageType - 儲存類型
 * @param {number} compartmentId - 分區 ID（可選）
 * @returns {Promise<Object>} 辨識結果
 */
export const recognizeFoodImage = (imageFile, cellarId, storageType, compartmentId = null) => {
  // 嚴格驗證 cellarId 必須是有效數字
  const validCellarId = Number(cellarId);
  if (!cellarId || isNaN(validCellarId) || validCellarId <= 0) {
    console.error('❌ Invalid cellar_id in recognizeFoodImage:', { cellarId, validCellarId });
    return Promise.reject(new Error('cellar_id 必須是有效的數字'));
  }

  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('cellar_id', validCellarId);  // 使用驗證過的數字
  if (compartmentId) {
    formData.append('compartment_id', compartmentId);
  }

  // Debug logging
  console.log('🔍 recognizeFoodImage called with:', {
    imageFile: imageFile ? { name: imageFile.name, size: imageFile.size, type: imageFile.type } : null,
    cellarId: validCellarId,
    compartmentId,
  });

  // 不要手動設置 Content-Type，讓瀏覽器自動處理 FormData（會自動加上 boundary）
  return apiClient.post('/wine-items/recognize', formData);
};

/**
 * 新增酒款
 * @param {Object} foodData - 酒款資料
 * @returns {Promise<Object>} 新增的酒款
 */
export const createFoodItem = (foodData) => {
  return apiClient.post('/wine-items', foodData);
};

/**
 * 更新酒款
 * @param {number} itemId - 酒款 ID
 * @param {Object} foodData - 更新的資料
 * @returns {Promise<Object>} 更新後的酒款
 */
export const updateFoodItem = (itemId, foodData) => {
  return apiClient.put(`/wine-items/${itemId}`, foodData);
};

/**
 * 刪除酒款
 * @param {number} itemId - 酒款 ID
 * @returns {Promise<void>}
 */
export const deleteFoodItem = (itemId) => {
  return apiClient.delete(`/wine-items/${itemId}`);
};

/**
 * 標記酒款狀態（已售出/已送禮/已喝完）
 * @param {number} itemId - 酒款 ID
 * @returns {Promise<Object>} 更新後的酒款
 */
export const archiveFoodItem = (itemId) => {
  return apiClient.post(`/wine-items/${itemId}/change-status?new_status=consumed`);
};

/**
 * 批次刪除酒款
 * @param {Array<number>} itemIds - 酒款 ID 陣列
 * @returns {Promise<void>}
 */
export const deleteFoodItems = (itemIds) => {
  return apiClient.post('/wine-items/batch-delete', { item_ids: itemIds });
};

// ---------- 酒窖相關 ----------

/**
 * 獲取使用者的所有酒窖
 * @returns {Promise<Array>} 酒窖清單
 */
export const getFridges = () => {
  return apiClient.get('/fridges');
};

/**
 * 獲取單一酒窖詳情（含分區）
 * @param {number} fridgeId - 酒窖 ID
 * @returns {Promise<Object>} 酒窖詳情
 */
export const getFridge = (fridgeId) => {
  return apiClient.get(`/fridges/${fridgeId}`);
};

/**
 * 新增酒窖
 * @param {Object} fridgeData - 酒窖資料
 * @returns {Promise<Object>} 新增的酒窖
 */
export const createFridge = (fridgeData) => {
  return apiClient.post('/fridges', fridgeData);
};

/**
 * 更新酒窖
 * @param {number} fridgeId - 酒窖 ID
 * @param {Object} fridgeData - 更新的資料
 * @returns {Promise<Object>} 更新後的酒窖
 */
export const updateFridge = (fridgeId, fridgeData) => {
  return apiClient.put(`/fridges/${fridgeId}`, fridgeData);
};

/**
 * 新增酒窖分區
 * @param {number} fridgeId - 酒窖 ID
 * @param {Object} compartmentData - 分區資料
 * @returns {Promise<Object>} 新增的分區
 */
export const createCompartment = (fridgeId, compartmentData) => {
  return apiClient.post(`/fridges/${fridgeId}/compartments`, compartmentData);
};

// ---------- 通知相關 ----------

/**
 * 獲取通知設定
 * @returns {Promise<Object>} 通知設定
 */
export const getNotificationSettings = () => {
  return apiClient.get('/notifications/settings');
};

/**
 * 更新通知設定
 * @param {Object} settings - 通知設定
 * @returns {Promise<Object>} 更新後的設定
 */
export const updateNotificationSettings = (settings) => {
  return apiClient.put('/notifications/settings', settings);
};

/**
 * 測試適飲期提醒通知（手動觸發）
 * @returns {Promise<Object>} 執行結果
 */
export const testExpiryNotification = () => {
  return apiClient.post('/notifications/test-expiry-check');
};

// ---------- 酒食搭配相關 ----------

/**
 * 根據現有酒款推薦酒食搭配
 * @param {Array<number>} itemIds - 酒款 ID 陣列（可選）
 * @returns {Promise<Array>} 推薦搭配清單
 */
export const getRecipeRecommendations = (itemIds = []) => {
  return apiClient.post('/recipes/recommendations', { item_ids: itemIds });
};

/**
 * 獲取使用者酒食搭配
 * @param {string} category - 類別 (favorites, pro)
 * @returns {Promise<Array>} 搭配清單
 */
export const getUserRecipes = (category = null) => {
  return apiClient.get('/recipes', { params: { category } });
};

/**
 * 新增使用者酒食搭配
 * @param {Object} recipeData - 搭配資料
 * @param {string} category - 分類 (favorites, pro, 常用)
 * @returns {Promise<Object>} 新增的搭配
 */
export const createUserRecipe = (recipeData, category = 'favorites') => {
  return apiClient.post('/recipes', recipeData, { params: { category } });
};

/**
 * 刪除使用者酒食搭配
 * @param {number} userRecipeId - 使用者搭配 ID
 * @returns {Promise<void>}
 */
export const deleteUserRecipe = (userRecipeId) => {
  return apiClient.delete(`/recipes/${userRecipeId}`);
};

// ---------- 預算相關 ----------

/**
 * 獲取消費統計
 * @param {string} period - 期間 (month, year)
 * @returns {Promise<Object>} 消費統計
 */
export const getSpendingStats = (period = 'month') => {
  return apiClient.get('/budget/stats', { params: { period } });
};

/**
 * 獲取預算設定
 * @returns {Promise<Object>} 預算設定
 */
export const getBudgetSettings = () => {
  return apiClient.get('/budget/settings');
};

/**
 * 更新預算設定
 * @param {Object} settings - 預算設定
 * @returns {Promise<Object>} 更新後的設定
 */
export const updateBudgetSettings = (settings) => {
  return apiClient.put('/budget/settings', settings);
};

/**
 * 獲取採買建議
 * @returns {Promise<Array>} 建議採買清單
 */
export const getShoppingSuggestions = () => {
  return apiClient.get('/budget/shopping-suggestions');
};

// ---------- 酒窖成員相關 ----------

/**
 * 獲取酒窖成員清單
 * @param {number} fridgeId - 酒窖 ID
 * @returns {Promise<Array>} 成員清單
 */
export const getFridgeMembers = (fridgeId) => {
  return apiClient.get(`/fridges/${fridgeId}/members`);
};

/**
 * 產生酒窖邀請碼
 * @param {number} fridgeId - 酒窖 ID
 * @param {Object} options - 邀請選項 { default_role, expires_days }
 * @returns {Promise<Object>} 邀請碼資料
 */
export const createFridgeInvite = (fridgeId, options = {}) => {
  return apiClient.post(`/fridges/${fridgeId}/invites`, options);
};

/**
 * 透過邀請碼加入酒窖
 * @param {string} inviteCode - 邀請碼
 * @returns {Promise<Object>} 加入結果
 */
export const joinFridgeByCode = (inviteCode) => {
  return apiClient.post(`/fridges/join/${inviteCode}`);
};

/**
 * 更新成員權限
 * @param {number} fridgeId - 酒窖 ID
 * @param {number} memberId - 成員 ID
 * @param {Object} data - { role: 'editor' | 'viewer' }
 * @returns {Promise<Object>} 更新後的成員資料
 */
export const updateMemberRole = (fridgeId, memberId, data) => {
  return apiClient.put(`/fridges/${fridgeId}/members/${memberId}`, data);
};

/**
 * 移除酒窖成員
 * @param {number} fridgeId - 酒窖 ID
 * @param {number} memberId - 成員 ID
 * @returns {Promise<void>}
 */
export const removeMember = (fridgeId, memberId) => {
  return apiClient.delete(`/fridges/${fridgeId}/members/${memberId}`);
};

// ---------- 酒窖匯出匯入 ----------

/**
 * 匯出酒窖資料
 * @param {number} fridgeId - 酒窖 ID
 * @returns {Promise<Object>} 匯出的 JSON 資料
 */
export const exportFridge = (fridgeId) => {
  return apiClient.get(`/fridges/${fridgeId}/export`);
};

/**
 * 匯入酒窖資料
 * @param {number} fridgeId - 酒窖 ID
 * @param {Object} data - 匯入的 JSON 資料
 * @param {boolean} clearExisting - 是否清除現有酒款
 * @returns {Promise<Object>} 匯入結果
 */
export const importFridge = (fridgeId, data, clearExisting = false) => {
  return apiClient.post(`/fridges/${fridgeId}/import?clear_existing=${clearExisting}`, data);
};

// ---------- 邀請函相關 ----------

/**
 * 建立邀請函
 * @param {Object} data - 邀請函資料
 * @returns {Promise<Object>} 建立的邀請函
 */
export const createInvitation = (data) => {
  return apiClient.post('/invitations', data);
};

/**
 * 取得邀請函 Flex Message
 * @param {number} id - 邀請函 ID
 * @returns {Promise<Object>} Flex Message JSON
 */
export const getInvitationFlex = (id) => {
  return apiClient.get(`/invitations/${id}/flex`);
};

/**
 * 取得邀請函詳情
 * @param {number} id - 邀請函 ID
 * @returns {Promise<Object>} 邀請函詳情
 */
export const getInvitation = async (id) => {
  return apiClient.get(`/invitations/${id}`);
};

/**
 * 上傳邀請函主題圖片
 * @param {File} file - 圖片檔案
 * @returns {Promise<{url: string}>}
 */
export const uploadInvitationImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  // apiClient 的 response interceptor 已經回傳 response.data
  return await apiClient.post('/invitations/upload-image', formData);
};

export default apiClient;
