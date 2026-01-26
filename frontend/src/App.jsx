/**
 * App 主元件 - AI Wine Cellar
 *
 * 應用程式的根元件，負責路由設定和 LIFF 初始化。
 * Neumorphism 深色主題
 */

import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Spin, App as AntApp } from 'antd';
import zhTW from 'antd/locale/zh_TW';
import { initializeLiff } from './liff';
import {
  WineHome,
  AddWineItem,
  EditWineItem,
  CellarSettings,

  NotificationSettings,
  CreateInvitation,
  InvitationDetail,
} from './pages';

// 深色主題配置
const darkTheme = {
  token: {
    colorPrimary: '#c9a227',
    colorBgContainer: '#2d2d2d',
    colorBgElevated: '#353535',
    colorText: '#f5f5f5',
    colorTextSecondary: '#b0b0b0',
    colorBorder: '#404040',
    borderRadius: 12,
  },
  components: {
    Card: {
      colorBgContainer: '#2d2d2d',
    },
    Button: {
      colorPrimary: '#c9a227',
      algorithm: true,
    },
    Input: {
      colorBgContainer: '#2d2d2d',
    },
    Select: {
      colorBgContainer: '#2d2d2d',
    },
  },
};

// 載入元件
const LoadingPage = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    flexDirection: 'column',
    gap: '20px',
    background: '#2d2d2d',
    color: '#f5f5f5',
  }}>
    <Spin size="large" />
    <p>🍷 載入酒窖中...</p>
  </div>
);

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [liffReady, setLiffReady] = useState(false);
  const [liffError, setLiffError] = useState(null);
  const [hasCellar, setHasCellar] = useState(true);
  const [checkingCellar, setCheckingCellar] = useState(true);

  useEffect(() => {
    // 初始化 LIFF SDK
    const init = async () => {
      try {
        const isReady = await initializeLiff();

        if (isReady) {
          setLiffReady(true);
          // 檢查是否已設定酒窖
          checkCellarSetup();
        } else {
          console.log('Redirecting to LINE login...');
        }
      } catch (error) {
        console.error('LIFF init error:', error);
        setLiffError(error.message || 'LIFF 初始化失敗');
      }
    };

    init();
  }, []);

  const checkCellarSetup = async () => {
    try {
      // 使用 API client（會自動加入 Authorization header）
      const { default: apiClient } = await import('./services/api.js');
      const cellars = await apiClient.get('/wine-cellars');

      setHasCellar(cellars.length > 0);

      // 如果沒有酒窖，自動建立一個
      if (cellars.length === 0) {
        await apiClient.post('/wine-cellars', {
          name: '我的酒窖',
          total_capacity: 100,
        });
        setHasCellar(true);
      }
    } catch (error) {
      console.error('檢查酒窖設定失敗:', error);
      setHasCellar(true); // 出錯時假設有酒窖，讓用戶可以操作
    } finally {
      setCheckingCellar(false);
    }
  };

  // 顯示錯誤訊息
  if (liffError) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '10px',
        padding: '20px',
        textAlign: 'center',
        background: '#2d2d2d',
        color: '#f5f5f5',
      }}>
        <h2>😔 發生錯誤</h2>
        <p>{liffError}</p>
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: '10px 20px',
            background: '#c9a227',
            border: 'none',
            borderRadius: '8px',
            color: '#1a1a1a',
            cursor: 'pointer',
          }}
        >
          重新載入
        </button>
      </div>
    );
  }

  // 初始化中或檢查酒窖設定中
  if (!liffReady || checkingCellar) {
    return <LoadingPage />;
  }

  // LIFF 已就緒，顯示應用
  return (
    <ConfigProvider locale={zhTW} theme={darkTheme}>
      <AntApp>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            {/* 首頁 - 酒款清單 */}
            <Route path="/" element={<WineHome />} />

            {/* 新增酒款 */}
            <Route path="/add" element={<AddWineItem />} />

            {/* 編輯酒款 */}
            <Route path="/edit/:id" element={<EditWineItem />} />

            {/* 酒窖設定 */}
            <Route path="/settings" element={<CellarSettings />} />

            {/* 通知設定 */}
            <Route path="/settings/notifications" element={<NotificationSettings />} />

            {/* 聚會邀請 */}
            <Route path="/invitation/create" element={<CreateInvitation />} />
            <Route path="/invitation/:id" element={<InvitationDetail />} />

            {/* 404 重新導向到首頁 */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AntApp>
    </ConfigProvider>
  );
}

export default App;
