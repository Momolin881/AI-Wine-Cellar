/**
 * WineItemCard 元件測試
 * 測試酒款卡片的顯示和交互功能
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import WineItemCard from '../../components/WineItemCard'

// 模擬數據
const mockWine = {
  id: 1,
  name: 'Dom Pérignon 2012',
  brand: 'Dom Pérignon',
  wine_type: '香檳',
  vintage: 2012,
  price: 8000,
  quantity: 2,
  is_opened: false,
  location: 'A1',
  image_url: 'https://example.com/wine.jpg',
  notes: '特殊場合使用',
  purchase_date: '2024-01-15',
  created_at: '2024-01-15T10:00:00Z'
}

const mockOpenedWine = {
  ...mockWine,
  id: 2,
  is_opened: true,
  opened_date: '2024-03-01',
  expiry_date: '2024-03-06',
  remaining_volume: 0.7
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

describe('WineItemCard', () => {
  let mockOnEdit, mockOnDelete, mockOnArchive

  beforeEach(() => {
    mockOnEdit = vi.fn()
    mockOnDelete = vi.fn()
    mockOnArchive = vi.fn()
  })

  describe('基本顯示功能', () => {
    it('應該顯示酒款基本資訊', () => {
      renderWithProviders(
        <WineItemCard
          wine={mockWine}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          onArchive={mockOnArchive}
        />
      )

      expect(screen.getByText('Dom Pérignon 2012')).toBeInTheDocument()
      expect(screen.getByText('Dom Pérignon')).toBeInTheDocument()
      expect(screen.getByText('香檳')).toBeInTheDocument()
      expect(screen.getByText('2012')).toBeInTheDocument()
      expect(screen.getByText('$8,000')).toBeInTheDocument()
      expect(screen.getByText('2瓶')).toBeInTheDocument()
      expect(screen.getByText('A1')).toBeInTheDocument()
    })

    it('應該顯示酒款圖片', () => {
      renderWithProviders(
        <WineItemCard wine={mockWine} />
      )

      const image = screen.getByRole('img', { name: /wine/i })
      expect(image).toBeInTheDocument()
      expect(image).toHaveAttribute('src', mockWine.image_url)
    })

    it('當沒有圖片時應該顯示預設圖片', () => {
      const wineWithoutImage = { ...mockWine, image_url: null }
      
      renderWithProviders(
        <WineItemCard wine={wineWithoutImage} />
      )

      const image = screen.getByRole('img', { name: /wine/i })
      expect(image).toBeInTheDocument()
      expect(image.src).toContain('default') // 或其他預設圖片的識別
    })

    it('應該顯示購買日期', () => {
      renderWithProviders(
        <WineItemCard wine={mockWine} />
      )

      expect(screen.getByText(/2024-01-15/)).toBeInTheDocument()
    })

    it('有備註時應該顯示備註', () => {
      renderWithProviders(
        <WineItemCard wine={mockWine} />
      )

      expect(screen.getByText('特殊場合使用')).toBeInTheDocument()
    })
  })

  describe('開瓶狀態顯示', () => {
    it('未開瓶酒款應該顯示正常狀態', () => {
      renderWithProviders(
        <WineItemCard wine={mockWine} />
      )

      expect(screen.queryByText(/已開瓶/)).not.toBeInTheDocument()
      expect(screen.queryByText(/剩餘/)).not.toBeInTheDocument()
    })

    it('已開瓶酒款應該顯示開瓶資訊', () => {
      renderWithProviders(
        <WineItemCard wine={mockOpenedWine} />
      )

      expect(screen.getByText(/已開瓶/)).toBeInTheDocument()
      expect(screen.getByText(/70%/)).toBeInTheDocument()
      expect(screen.getByText(/2024-03-06/)).toBeInTheDocument() // 到期日
    })

    it('接近過期的酒款應該有警告樣式', () => {
      const nearExpiryWine = {
        ...mockOpenedWine,
        expiry_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 明天到期
      }

      renderWithProviders(
        <WineItemCard wine={nearExpiryWine} />
      )

      const card = screen.getByTestId('wine-card')
      expect(card).toHaveClass(/warning/) // 假設有警告樣式
    })
  })

  describe('操作按鈕', () => {
    it('點擊編輯按鈕應該觸發 onEdit', () => {
      renderWithProviders(
        <WineItemCard
          wine={mockWine}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          onArchive={mockOnArchive}
        />
      )

      const editButton = screen.getByRole('button', { name: /編輯/i })
      fireEvent.click(editButton)

      expect(mockOnEdit).toHaveBeenCalledWith(mockWine)
      expect(mockOnEdit).toHaveBeenCalledTimes(1)
    })

    it('點擊刪除按鈕應該觸發 onDelete', () => {
      renderWithProviders(
        <WineItemCard
          wine={mockWine}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          onArchive={mockOnArchive}
        />
      )

      const deleteButton = screen.getByRole('button', { name: /刪除/i })
      fireEvent.click(deleteButton)

      expect(mockOnDelete).toHaveBeenCalledWith(mockWine)
      expect(mockOnDelete).toHaveBeenCalledTimes(1)
    })

    it('點擊歸檔按鈕應該觸發 onArchive', () => {
      renderWithProviders(
        <WineItemCard
          wine={mockWine}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          onArchive={mockOnArchive}
        />
      )

      const archiveButton = screen.getByRole('button', { name: /歸檔/i })
      fireEvent.click(archiveButton)

      expect(mockOnArchive).toHaveBeenCalledWith(mockWine)
      expect(mockOnArchive).toHaveBeenCalledTimes(1)
    })

    it('當沒有提供操作函數時不應該顯示按鈕', () => {
      renderWithProviders(
        <WineItemCard wine={mockWine} />
      )

      expect(screen.queryByRole('button', { name: /編輯/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /刪除/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /歸檔/i })).not.toBeInTheDocument()
    })
  })

  describe('響應式顯示', () => {
    it('在小螢幕上應該調整佈局', () => {
      // 模擬小螢幕
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375
      })

      renderWithProviders(
        <WineItemCard wine={mockWine} />
      )

      const card = screen.getByTestId('wine-card')
      expect(card).toHaveClass(/mobile/) // 假設有行動版樣式
    })
  })

  describe('無障礙功能', () => {
    it('應該有正確的 ARIA 標籤', () => {
      renderWithProviders(
        <WineItemCard wine={mockWine} />
      )

      const card = screen.getByRole('article')
      expect(card).toHaveAttribute('aria-label', expect.stringContaining(mockWine.name))
    })

    it('圖片應該有替代文字', () => {
      renderWithProviders(
        <WineItemCard wine={mockWine} />
      )

      const image = screen.getByRole('img')
      expect(image).toHaveAttribute('alt', expect.stringContaining(mockWine.name))
    })

    it('按鈕應該有正確的標籤', () => {
      renderWithProviders(
        <WineItemCard
          wine={mockWine}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByRole('button', { name: /編輯.*Dom Pérignon/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /刪除.*Dom Pérignon/i })).toBeInTheDocument()
    })
  })

  describe('邊界情況', () => {
    it('處理缺失資料的酒款', () => {
      const incompleteWine = {
        id: 3,
        name: '不完整酒款',
        wine_type: '紅酒'
        // 缺少其他欄位
      }

      renderWithProviders(
        <WineItemCard wine={incompleteWine} />
      )

      expect(screen.getByText('不完整酒款')).toBeInTheDocument()
      expect(screen.getByText('紅酒')).toBeInTheDocument()
      // 應該優雅處理缺失的欄位
    })

    it('處理極長的酒款名稱', () => {
      const longNameWine = {
        ...mockWine,
        name: 'A'.repeat(100) // 100個字元的長名稱
      }

      renderWithProviders(
        <WineItemCard wine={longNameWine} />
      )

      // 名稱應該被適當截斷或換行
      expect(screen.getByText(longNameWine.name)).toBeInTheDocument()
    })

    it('處理零價格和零數量', () => {
      const zeroValueWine = {
        ...mockWine,
        price: 0,
        quantity: 0
      }

      renderWithProviders(
        <WineItemCard wine={zeroValueWine} />
      )

      expect(screen.getByText('$0')).toBeInTheDocument()
      expect(screen.getByText('0瓶')).toBeInTheDocument()
    })
  })
})