/**
 * WineHome 頁面測試
 * 測試酒款首頁的載入、篩選、搜尋功能
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import WineHome from '../../pages/WineHome'
import * as api from '../../services/api'

// 模擬 API
vi.mock('../../services/api', () => ({
  getWineItems: vi.fn(),
  deleteWineItem: vi.fn(),
  archiveWineItem: vi.fn(),
  getUserInfo: vi.fn()
}))

// 模擬 ModeContext
vi.mock('../../contexts/ModeContext', () => ({
  useMode: () => ({
    mode: 'pro',
    setMode: vi.fn()
  })
}))

// 模擬數據
const mockWines = [
  {
    id: 1,
    name: 'Dom Pérignon 2012',
    brand: 'Dom Pérignon',
    wine_type: '香檳',
    vintage: 2012,
    price: 8000,
    quantity: 2,
    is_opened: false,
    location: 'A1',
    cellar_id: 1,
    status: 'available'
  },
  {
    id: 2,
    name: 'Château Margaux 2015',
    brand: 'Château Margaux',
    wine_type: '紅酒',
    vintage: 2015,
    price: 15000,
    quantity: 1,
    is_opened: true,
    location: 'B2',
    cellar_id: 1,
    status: 'available'
  },
  {
    id: 3,
    name: 'Sancerre 2020',
    brand: 'Henri Bourgeois',
    wine_type: '白酒',
    vintage: 2020,
    price: 1200,
    quantity: 3,
    is_opened: false,
    location: 'C1',
    cellar_id: 1,
    status: 'available'
  }
]

const mockUser = {
  id: 1,
  display_name: '測試用戶',
  line_user_id: 'test_user_123'
}

// 測試輔助函數
const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <ConfigProvider>
        {component}
      </ConfigProvider>
    </BrowserRouter>
  )
}

describe('WineHome', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.getUserInfo.mockResolvedValue(mockUser)
    api.getWineItems.mockResolvedValue(mockWines)
  })

  describe('初始載入', () => {
    it('應該顯示載入狀態', async () => {
      // 模擬 API 延遲
      api.getWineItems.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockWines), 100))
      )

      renderWithProviders(<WineHome />)

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
    })

    it('成功載入後應該顯示酒款列表', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
        expect(screen.getByText('Château Margaux 2015')).toBeInTheDocument()
        expect(screen.getByText('Sancerre 2020')).toBeInTheDocument()
      })

      expect(api.getWineItems).toHaveBeenCalledTimes(1)
    })

    it('API 錯誤時應該顯示錯誤訊息', async () => {
      api.getWineItems.mockRejectedValue(new Error('API Error'))

      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText(/載入失敗/)).toBeInTheDocument()
      })
    })

    it('沒有酒款時應該顯示空狀態', async () => {
      api.getWineItems.mockResolvedValue([])

      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText(/還沒有酒款/)).toBeInTheDocument()
        expect(screen.getByText(/開始新增您的第一瓶酒/)).toBeInTheDocument()
      })
    })
  })

  describe('搜尋功能', () => {
    it('搜尋酒款名稱應該過濾結果', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/搜尋酒款/i)
      await userEvent.type(searchInput, 'Dom Pérignon')

      expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      expect(screen.queryByText('Château Margaux 2015')).not.toBeInTheDocument()
    })

    it('搜尋品牌應該顯示匹配結果', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getAllByText(/Château/).length).toBeGreaterThan(0)
      })

      const searchInput = screen.getByPlaceholderText(/搜尋酒款/i)
      await userEvent.type(searchInput, 'Château')

      expect(screen.getByText('Château Margaux 2015')).toBeInTheDocument()
      expect(screen.queryByText('Dom Pérignon 2012')).not.toBeInTheDocument()
    })

    it('清空搜尋應該顯示所有酒款', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/搜尋酒款/i)
      await userEvent.type(searchInput, 'Dom')
      await userEvent.clear(searchInput)

      expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      expect(screen.getByText('Château Margaux 2015')).toBeInTheDocument()
      expect(screen.getByText('Sancerre 2020')).toBeInTheDocument()
    })
  })

  describe('篩選功能', () => {
    it('按酒類篩選應該只顯示對應類型', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      const filterSelect = screen.getByTestId('wine-type-filter')
      await userEvent.click(filterSelect)
      await userEvent.click(screen.getByText('紅酒'))

      expect(screen.getByText('Château Margaux 2015')).toBeInTheDocument()
      expect(screen.queryByText('Dom Pérignon 2012')).not.toBeInTheDocument()
    })

    it('按開瓶狀態篩選應該正確過濾', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      const statusFilter = screen.getByTestId('opened-status-filter')
      await userEvent.click(statusFilter)
      await userEvent.click(screen.getByText('已開瓶'))

      expect(screen.getByText('Château Margaux 2015')).toBeInTheDocument()
      expect(screen.queryByText('Dom Pérignon 2012')).not.toBeInTheDocument()
    })

    it('組合多個篩選條件應該正確工作', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      // 設置搜尋
      const searchInput = screen.getByPlaceholderText(/搜尋酒款/i)
      await userEvent.type(searchInput, 'Château')

      // 設置酒類篩選
      const filterSelect = screen.getByTestId('wine-type-filter')
      await userEvent.click(filterSelect)
      await userEvent.click(screen.getByText('紅酒'))

      expect(screen.getByText('Château Margaux 2015')).toBeInTheDocument()
      expect(screen.queryByText('Dom Pérignon 2012')).not.toBeInTheDocument()
      expect(screen.queryByText('Sancerre 2020')).not.toBeInTheDocument()
    })
  })

  describe('排序功能', () => {
    it('按名稱排序應該正確排列', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      const sortSelect = screen.getByTestId('sort-select')
      await userEvent.click(sortSelect)
      await userEvent.click(screen.getByText('名稱 A-Z'))

      const wineCards = screen.getAllByTestId('wine-card')
      expect(wineCards[0]).toHaveTextContent('Château Margaux 2015')
      expect(wineCards[1]).toHaveTextContent('Dom Pérignon 2012')
      expect(wineCards[2]).toHaveTextContent('Sancerre 2020')
    })

    it('按價格排序應該正確排列', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      const sortSelect = screen.getByTestId('sort-select')
      await userEvent.click(sortSelect)
      await userEvent.click(screen.getByText('價格由低到高'))

      const wineCards = screen.getAllByTestId('wine-card')
      expect(wineCards[0]).toHaveTextContent('Sancerre 2020') // $1,200
      expect(wineCards[1]).toHaveTextContent('Dom Pérignon 2012') // $8,000
      expect(wineCards[2]).toHaveTextContent('Château Margaux 2015') // $15,000
    })
  })

  describe('酒款操作', () => {
    it('編輯酒款應該導向編輯頁面', async () => {
      const mockNavigate = vi.fn()
      vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom')
        return {
          ...actual,
          useNavigate: () => mockNavigate
        }
      })

      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      const editButton = screen.getAllByTestId('edit-button')[0]
      fireEvent.click(editButton)

      expect(mockNavigate).toHaveBeenCalledWith('/edit/1')
    })

    it('刪除酒款應該顯示確認對話框', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      const deleteButton = screen.getAllByTestId('delete-button')[0]
      fireEvent.click(deleteButton)

      expect(screen.getByText(/確定要刪除/)).toBeInTheDocument()
    })

    it('確認刪除後應該呼叫 API 並重新載入', async () => {
      api.deleteWineItem.mockResolvedValue()

      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      const deleteButton = screen.getAllByTestId('delete-button')[0]
      fireEvent.click(deleteButton)

      const confirmButton = screen.getByRole('button', { name: /確定刪除/ })
      fireEvent.click(confirmButton)

      await waitFor(() => {
        expect(api.deleteWineItem).toHaveBeenCalledWith(1)
      })
    })
  })

  describe('批次操作', () => {
    it('選擇多個酒款應該顯示批次操作按鈕', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      // 選擇第一個酒款
      const checkboxes = screen.getAllByRole('checkbox')
      fireEvent.click(checkboxes[0])

      expect(screen.getByText(/已選擇 1 項/)).toBeInTheDocument()
      expect(screen.getByTestId('batch-delete-button')).toBeInTheDocument()
    })

    it('批次刪除應該正確處理', async () => {
      api.deleteWineItems = vi.fn().mockResolvedValue()

      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      })

      // 選擇多個酒款
      const checkboxes = screen.getAllByRole('checkbox')
      fireEvent.click(checkboxes[0])
      fireEvent.click(checkboxes[1])

      const batchDeleteButton = screen.getByTestId('batch-delete-button')
      fireEvent.click(batchDeleteButton)

      const confirmButton = screen.getByRole('button', { name: /確定刪除/ })
      fireEvent.click(confirmButton)

      await waitFor(() => {
        expect(api.deleteWineItems).toHaveBeenCalledWith([1, 2])
      })
    })
  })

  describe('響應式設計', () => {
    it('在行動裝置上應該調整佈局', () => {
      // 模擬行動裝置螢幕大小
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375
      })

      renderWithProviders(<WineHome />)

      const container = screen.getByTestId('wine-home-container')
      expect(container).toHaveClass(/mobile-layout/)
    })
  })

  describe('無障礙功能', () => {
    it('應該有正確的標題結構', async () => {
      renderWithProviders(<WineHome />)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /我的酒窖/ })).toBeInTheDocument()
      })
    })

    it('搜尋輸入框應該有正確的標籤', () => {
      renderWithProviders(<WineHome />)

      const searchInput = screen.getByLabelText(/搜尋酒款/i)
      expect(searchInput).toBeInTheDocument()
    })

    it('篩選控制應該可以用鍵盤操作', async () => {
      renderWithProviders(<WineHome />)

      const filterSelect = screen.getByTestId('wine-type-filter')
      
      // 測試鍵盤導航
      filterSelect.focus()
      fireEvent.keyDown(filterSelect, { key: 'Enter' })
      
      expect(screen.getByRole('listbox')).toBeInTheDocument()
    })
  })
})