/**
 * App 主元件 - AI Wine Cellar
 *
 * 應用程式的根元件，負責路由設定和 LIFF 初始化。
 * 支援 Chill Mode (Cyberpunk) 和 Pro Mode (經典金色)
 */

import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ConfigProvider, Spin, App as AntApp } from 'antd';
import zhTW from 'antd/locale/zh_TW';
import { initializeLiff } from './liff';
import { ModeProvider, useMode } from './contexts/ModeContext';
import {
  WineHome,
  AddWineItem,
  EditWineItem,
  CellarSettings,
  NotificationSettings,
  CreateInvitation,
  InvitationDetail,
  ModeSelect,
} from './pages';
import WineGroupDetail from './components/WineGroupDetail';
import './styles/CyberpunkTheme.css';

// 根據 Mode 動態生成主題
const createTheme = (mode) => {
  const isPro = mode === 'pro';

  return {
    token: {
      colorPrimary: isPro ? '#c9a227' : '#00f0ff',
      colorBgContainer: isPro ? '#2d2d2d' : '#1a1a2e',
      colorBgElevated: isPro ? '#353535' : '#252542',
      colorText: '#f5f5f5',
      colorTextSecondary: '#b0b0b0',
      colorBorder: isPro ? '#404040' : '#2a2a4a',
      borderRadius: 12,
    },
    components: {
      Card: {
        colorBgContainer: isPro ? '#2d2d2d' : '#1a1a2e',
      },
      Button: {
        colorPrimary: isPro ? '#c9a227' : '#00f0ff',
        algorithm: true,
      },
      Input: {
        colorBgContainer: isPro ? '#2d2d2d' : '#1a1a2e',
      },
      Select: {
        colorBgContainer: isPro ? '#2d2d2d' : '#1a1a2e',
      },
    },
  };
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

  useEffect(() => {
    // 初始化 LIFF SDK
    const init = async () => {
      try {
        const isReady = await initializeLiff();

        if (isReady) {
          setLiffReady(true);
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

  // 初始化中
  if (!liffReady) {
    return <LoadingPage />;
  }

  // LIFF 已就緒，顯示應用
  return (
    <ModeProvider>
      <AppWithMode />
    </ModeProvider>
  );
}

// 根據 Mode 渲染的內部元件
function AppWithMode() {
  const { mode, isFirstTime } = useMode();
  const theme = createTheme(mode);

  return (
    <ConfigProvider locale={zhTW} theme={theme}>
      <AntApp>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <AppRoutes isFirstTime={isFirstTime} />
        </Router>
      </AntApp>
    </ConfigProvider>
  );
}

// 路由元件（處理首次使用者導向）
function AppRoutes({ isFirstTime }) {
  const location = useLocation();

  // 首次使用者導向選擇頁面
  if (isFirstTime && location.pathname !== '/mode-select') {
    return <Navigate to="/mode-select" replace />;
  }

  return (
    <Routes>
      {/* Mode 選擇頁 */}
      <Route path="/mode-select" element={<ModeSelect />} />

      {/* 首頁 - 酒款清單 */}
      <Route path="/" element={<WineHome />} />

      {/* 新增酒款 */}
      <Route path="/add" element={<AddWineItem />} />

      {/* 編輯酒款 */}
      <Route path="/edit/:id" element={<EditWineItem />} />

      {/* 酒款群組詳情 */}
      <Route path="/wine-group/:brand/:name/:vintage?" element={<WineGroupDetail />} />

      {/* 酒窖設定 */}
      <Route path="/settings" element={<CellarSettings />} />
      <Route path="/settings/cellar" element={<CellarSettings />} />

      {/* 通知設定 */}
      <Route path="/settings/notifications" element={<NotificationSettings />} />

      {/* 聚會邀請 */}
      <Route path="/invitation/create" element={<CreateInvitation />} />
      <Route path="/invitation/:id" element={<InvitationDetail />} />

      {/* 404 重新導向到首頁 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
