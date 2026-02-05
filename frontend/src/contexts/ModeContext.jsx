/**
 * Mode Context
 *
 * 管理 App 模式：Chill Mode vs Pro Mode
 * - Chill: 簡潔版，無品飲筆記，Cyberpunk 配色
 * - Pro: 完整版，有品飲筆記，經典金色調
 */

import { createContext, useContext, useState, useEffect } from 'react';

const ModeContext = createContext();

// Cyberpunk 配色 (Chill Mode)
export const CHILL_THEME = {
    primary: '#00f0ff',      // 霓虹青
    accent: '#ff00ff',       // 霓虹粉
    secondary: '#b967ff',    // 電紫
    background: '#1A1A2E',   // 暗紫黑（與 ModeSelect 一致）
    card: '#252538',         // 卡片深紫
    cardHover: '#2d2d45',    // 卡片 hover
    success: '#00ff88',      // 霓虹綠
    text: '#e0e0e0',
    textSecondary: '#888',
    border: '#2a2a4a',
    glow: '0 0 20px rgba(0, 240, 255, 0.3)',
};

// 經典金色調 (Pro Mode)
export const PRO_THEME = {
    primary: '#c9a227',      // 金色
    accent: '#ffd700',       // 亮金
    secondary: '#8b7355',    // 棕金
    background: '#1a1a1a',   // 深灰黑
    card: '#2d2d2d',         // 卡片灰
    cardHover: '#3d3d3d',    // 卡片 hover
    success: '#52c41a',      // 綠色
    text: '#f5f5f5',
    textSecondary: '#888',
    border: '#555',
    glow: 'none',
};

export function ModeProvider({ children }) {
    const [mode, setMode] = useState(() => {
        // 從 localStorage 讀取，預設為 null（未選擇）
        return localStorage.getItem('wineMode') || null;
    });

    const [isFirstTime, setIsFirstTime] = useState(() => {
        return !localStorage.getItem('wineMode');
    });

    // 取得當前主題
    const theme = mode === 'pro' ? PRO_THEME : CHILL_THEME;
    const isPro = mode === 'pro';
    const isChill = mode === 'chill';

    // 切換模式
    const setModeAndSave = (newMode) => {
        setMode(newMode);
        localStorage.setItem('wineMode', newMode);
        setIsFirstTime(false);
    };

    // 應用 CSS 變數到 root 並設定 body class
    useEffect(() => {
        if (!mode) return;

        const root = document.documentElement;
        Object.entries(theme).forEach(([key, value]) => {
            root.style.setProperty(`--theme-${key}`, value);
        });

        // 設定 body class 和背景
        document.body.classList.remove('chill-mode', 'pro-mode');
        document.body.classList.add(mode === 'chill' ? 'chill-mode' : 'pro-mode');
        document.body.style.background = theme.background;
    }, [mode, theme]);

    return (
        <ModeContext.Provider value={{
            mode,
            setMode: setModeAndSave,
            theme,
            isPro,
            isChill,
            isFirstTime,
            CHILL_THEME,
            PRO_THEME,
        }}>
            {children}
        </ModeContext.Provider>
    );
}

export function useMode() {
    const context = useContext(ModeContext);
    if (!context) {
        throw new Error('useMode must be used within a ModeProvider');
    }
    return context;
}

export default ModeContext;
