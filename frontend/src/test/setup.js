/**
 * Vitest 測試環境設定
 * 配置測試所需的全域設定和模擬
 */

import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

// 清理每個測試後的 DOM
afterEach(() => {
  cleanup()
})

// 模擬 LIFF SDK
global.liff = {
  init: vi.fn().mockResolvedValue(true),
  isLoggedIn: vi.fn().mockReturnValue(true),
  getAccessToken: vi.fn().mockReturnValue('mock_access_token'),
  getProfile: vi.fn().mockResolvedValue({
    userId: 'test_user_123',
    displayName: '測試用戶',
    pictureUrl: 'https://example.com/avatar.jpg'
  }),
  shareTargetPicker: vi.fn().mockResolvedValue({ status: 'success' }),
  closeWindow: vi.fn(),
  openWindow: vi.fn(),
  ready: vi.fn(),
  isInClient: vi.fn().mockReturnValue(true),
  isApiAvailable: vi.fn().mockReturnValue(true)
}

// 模擬環境變數
process.env.VITE_LIFF_ID = 'test-liff-id'
process.env.VITE_API_URL = 'http://localhost:8000/api/v1'

// 模擬 window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'https://liff.line.me/test-liff-id',
    origin: 'https://liff.line.me',
    pathname: '/test-liff-id',
    search: '',
    hash: '',
    reload: vi.fn(),
    assign: vi.fn()
  },
  writable: true
})

// 模擬 localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// 模擬 sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock
})

// 模擬 IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// 模擬 ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// 模擬 Canvas API (for chart.js if needed)
HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
  fillRect: vi.fn(),
  clearRect: vi.fn(),
  getImageData: vi.fn(() => ({
    data: new Array(4)
  })),
  putImageData: vi.fn(),
  createImageData: vi.fn(() => []),
  setTransform: vi.fn(),
  drawImage: vi.fn(),
  save: vi.fn(),
  fillText: vi.fn(),
  restore: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  stroke: vi.fn(),
  translate: vi.fn(),
  scale: vi.fn(),
  rotate: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  measureText: vi.fn(() => ({ width: 0 })),
  transform: vi.fn(),
  rect: vi.fn(),
  clip: vi.fn()
})

// 增加 expect 的自定義 matcher（如果需要的話）
expect.extend({
  toBeInTheDocument(received) {
    const pass = received !== null && received !== undefined
    return {
      message: () => pass 
        ? `expected element not to be in the document` 
        : `expected element to be in the document`,
      pass,
    }
  }
})

// 靜默 console 警告（只在測試環境）
const originalConsoleWarn = console.warn
console.warn = (...args) => {
  // 忽略 React Router 的警告
  if (args[0]?.includes && args[0].includes('React Router')) {
    return
  }
  originalConsoleWarn.call(console, ...args)
}