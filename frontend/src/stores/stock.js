import { defineStore } from 'pinia'
import { searchStocks as searchStocksApi, getDailyData, refreshData as refreshDataApi } from '@/api'

export const useStockStore = defineStore('stock', {
  state: () => ({
    currentStock: null, // { ts_code, name }
    dailyData: [],
    loading: false,
    error: null,
    cacheInfo: null // { last_date, total_bars }
  }),

  getters: {
    hasData: (state) => state.dailyData.length > 0,
    isLoading: (state) => state.loading,
    currentStockName: (state) => state.currentStock?.name || '',
    currentStockCode: (state) => state.currentStock?.ts_code || ''
  },

  actions: {
    /**
     * Search stocks by keyword (does not set state, returns results)
     */
    async searchStocks(keyword) {
      if (!keyword || !keyword.trim()) {
        return []
      }
      try {
        const results = await searchStocksApi(keyword.trim())
        return results || []
      } catch (err) {
        return []
      }
    },

    /**
     * Select a stock and fetch its daily data
     */
    async selectStock(tsCode, tsName) {
      this.currentStock = { ts_code: tsCode, name: tsName || tsCode }
      this.dailyData = []
      this.error = null
      this.cacheInfo = null
      await this.fetchDailyData()
    },

    /**
     * Fetch daily data for the current stock
     */
    async fetchDailyData() {
      if (!this.currentStock) return

      this.loading = true
      this.error = null

      try {
        const response = await getDailyData(this.currentStock.ts_code)
        this.dailyData = response.data || []
        this.cacheInfo = response.cache_info || null
        // Update stock name from response if available
        if (response.name) {
          this.currentStock.name = response.name
        }
      } catch (err) {
        this.error = err.message || '获取数据失败'
        this.dailyData = []
      } finally {
        this.loading = false
      }
    },

    /**
     * Force refresh data from tushare
     */
    async refreshData() {
      if (!this.currentStock) return

      this.loading = true
      this.error = null

      try {
        await refreshDataApi(this.currentStock.ts_code)
        await this.fetchDailyData()
      } catch (err) {
        this.error = err.message || '刷新数据失败'
      } finally {
        this.loading = false
      }
    },

    /**
     * Clear current stock and data
     */
    clearStock() {
      this.currentStock = null
      this.dailyData = []
      this.error = null
      this.cacheInfo = null
    }
  }
})
