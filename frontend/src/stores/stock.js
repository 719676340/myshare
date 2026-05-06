import { defineStore } from 'pinia'
import { searchStocks as searchStocksApi, getDailyData, refreshData as refreshDataApi, getIndicatorData, getVPAData } from '@/api'

export const useStockStore = defineStore('stock', {
  state: () => ({
    currentStock: null, // { ts_code, name }
    dailyData: [],
    loading: false,
    error: null,
    cacheInfo: null, // { last_date, total_bars }
    indicatorData: {},       // { macd: {data: [...]}, rsi: {data: [...]}, ... }
    vpaData: { signals: [], patterns: [] }
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
      this.indicatorData = {}
      this.vpaData = { signals: [], patterns: [] }
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
      this.indicatorData = {}
      this.vpaData = { signals: [], patterns: [] }
    },

    /**
     * Fetch indicator data for a specific indicator
     */
    async fetchIndicatorData(indicator, params = {}) {
      if (!this.currentStock) return
      try {
        const result = await getIndicatorData(this.currentStock.ts_code, indicator, params)
        // Store as { [indicator]: { params, params_hash, data } }
        this.indicatorData = { ...this.indicatorData, [indicator]: result }
      } catch (err) {
        console.error(`Failed to fetch ${indicator} data:`, err)
      }
    },

    /**
     * Fetch volume-price analysis data (signals + patterns)
     */
    async fetchVPAData() {
      if (!this.currentStock) return
      try {
        const result = await getVPAData(this.currentStock.ts_code)
        this.vpaData = { signals: result.signals || [], patterns: result.patterns || [] }
      } catch (err) {
        console.error('Failed to fetch VPA data:', err)
      }
    },

    /**
     * Fetch indicator data for all enabled indicators
     */
    async fetchAllEnabledData(chartStore) {
      const promises = []
      if (chartStore.showMACD) {
        promises.push(this.fetchIndicatorData('macd', chartStore.indicatorParams.macd))
      }
      if (chartStore.showRSI) {
        promises.push(this.fetchIndicatorData('rsi', chartStore.indicatorParams.rsi))
      }
      if (chartStore.showKDJ) {
        promises.push(this.fetchIndicatorData('kdj', chartStore.indicatorParams.kdj))
      }
      if (chartStore.showBOLL) {
        promises.push(this.fetchIndicatorData('boll', chartStore.indicatorParams.boll))
      }
      if (chartStore.showSignals || chartStore.showPatterns) {
        promises.push(this.fetchVPAData())
      }
      await Promise.all(promises)
    }
  }
})
