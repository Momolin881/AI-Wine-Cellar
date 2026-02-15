/**
 * LIFF SDK 初始化模組
 *
 * 提供 LIFF SDK 的初始化和常用方法封裝。
 * 處理 LINE Login 和使用者資訊獲取。
 */

import liff from '@line/liff';


// Use hardcoded ID as fallback to ensure it works in production
const LIFF_ID = import.meta.env.VITE_LIFF_ID || '2008946239-5U8c7ry2';
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

/**
 * 初始化 LIFF SDK

 * @returns {Promise<boolean>} 初始化成功返回 true，失敗返回 false
 */
export const initializeLiff = async () => {
  // 開發模式：跳過 LIFF 初始化
  if (DEV_MODE) {
    console.log('Development mode: Skipping LIFF initialization');
    return true;
  }

  try {
    await liff.init({ liffId: LIFF_ID });

    // 檢查登入狀態
    if (!liff.isLoggedIn()) {
      // 儲存當前路徑，登入後恢復
      const currentPath = window.location.pathname + window.location.search;
      if (currentPath !== '/') {
        localStorage.setItem('liff_redirect_path', currentPath);
        console.log('Saving redirect path:', currentPath);
      }
      
      liff.login();
      return false;
    }

    // 已登入，檢查是否需要跳轉到之前的頁面
    const redirectPath = localStorage.getItem('liff_redirect_path');
    if (redirectPath && redirectPath !== window.location.pathname) {
      console.log('Redirecting to saved path:', redirectPath);
      localStorage.removeItem('liff_redirect_path');
      // 使用 pushState 來更新 URL，讓 React Router 處理
      setTimeout(() => {
        window.history.pushState({}, '', redirectPath);
        window.location.reload();
      }, 100);
    }

    return true;
  } catch (error) {
    console.error('LIFF initialization failed:', error);
    throw error;
  }
};

/**
 * 獲取 LIFF Access Token
 * @returns {string|null} Access Token 或 null
 */
export const getLiffAccessToken = () => {
  // 開發模式：返回測試 token
  if (DEV_MODE) {
    return 'dev-test-token';
  }
  if (liff.isLoggedIn()) {
    return liff.getAccessToken();
  }
  return null;
};

/**
 * 獲取使用者資訊
 * @returns {Promise<Object>} 使用者資訊物件
 */
export const getUserProfile = async () => {
  try {
    const profile = await liff.getProfile();
    return {
      userId: profile.userId,
      displayName: profile.displayName,
      pictureUrl: profile.pictureUrl,
      statusMessage: profile.statusMessage,
    };
  } catch (error) {
    console.error('Failed to get user profile:', error);
    throw error;
  }
};

/**
 * 登出
 */
export const logout = () => {
  liff.logout();
  window.location.reload();
};

/**
 * 關閉 LIFF 視窗
 */
export const closeLiff = () => {
  liff.closeWindow();
};

/**
 * 檢查是否在 LINE 應用內
 * @returns {boolean}
 */
export const isInClient = () => {
  return liff.isInClient();
};

/**
 * 傳送訊息給使用者（僅限 LINE 內部）
 * @param {string} message - 要傳送的訊息
 */
export const sendMessage = (message) => {
  if (liff.isInClient()) {
    liff.sendMessages([
      {
        type: 'text',
        text: message,
      }
    ]);
  }
};

export default liff;
