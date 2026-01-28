/**
 * 應用程式入口點
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

// 移動端調試工具：URL 加上 ?debug=1 即可啟用
if (window.location.search.includes('debug=1')) {
  import('vconsole').then(({ default: VConsole }) => {
    new VConsole();
    console.log('vConsole 已啟用');
  });
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
// Force rebuild Wed Jan 21 00:29:11 CST 2026
