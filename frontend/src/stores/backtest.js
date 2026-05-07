import { defineStore } from 'pinia'
import {
  runBacktest,
  getBacktestPresets,
  listBacktestSessions,
  getBacktestSession,
  deleteBacktestSession,
  validateExpression
} from '@/api'

export const useBacktestStore = defineStore('backtest', {
  state: () => ({
    // Configuration state
    selectedStock: null,  // { ts_code, name }
    startDate: '',
    endDate: '',
    initialCapital: 1000000,
    indicators: [],  // [{ name: '', expression: '', valid: null, error: '', fields: [] }]
    buyConditions: { type: 'group', operator: 'AND', children: [] },
    sellConditions: { type: 'group', operator: 'AND', children: [] },

    // Results state
    currentResult: null,  // full result from API
    presets: [],
    historyList: [],
    historyTotal: 0,

    // UI state
    loading: false,
    error: null,
    resultsVisible: false  // whether results panel is expanded
  }),

  getters: {
    hasStock: (state) => state.selectedStock !== null,
    hasDates: (state) => state.startDate && state.endDate,
    hasIndicators: (state) => state.indicators.length > 0 && state.indicators.every(i => i.valid && i.name),
    hasBuyConditions: (state) => state.buyConditions.children.length > 0,
    hasSellConditions: (state) => state.sellConditions.children.length > 0,
    canRun: (state) => {
      return state.selectedStock && state.startDate && state.endDate
        && state.buyConditions.children.length > 0
        && state.sellConditions.children.length > 0
    }
  },

  actions: {
    setStock(stock) {
      this.selectedStock = stock
    },

    addIndicator() {
      this.indicators.push({ name: '', expression: '', valid: null, error: '', fields: [] })
    },

    removeIndicator(index) {
      this.indicators.splice(index, 1)
    },

    updateIndicator(index, field, value) {
      this.indicators[index][field] = value
    },

    async validateIndicator(index) {
      const expr = this.indicators[index].expression
      if (!expr || !expr.trim()) {
        this.indicators[index].valid = false
        this.indicators[index].error = '表达式不能为空'
        return
      }
      try {
        const { data } = await validateExpression(expr)
        this.indicators[index].valid = data.valid
        this.indicators[index].error = data.error || ''
        this.indicators[index].fields = data.fields || []
      } catch (err) {
        this.indicators[index].valid = false
        this.indicators[index].error = '验证失败'
      }
    },

    async loadPresets() {
      try {
        const { data } = await getBacktestPresets()
        this.presets = data
      } catch (err) {
        console.error('Failed to load presets:', err)
      }
    },

    applyPreset(preset) {
      // Per D-10: preset fills in the config, user can modify
      this.indicators = preset.indicators.map(i => ({
        name: i.name, expression: i.expression, valid: null, error: '', fields: []
      }))
      this.buyConditions = JSON.parse(JSON.stringify(preset.buy_conditions))
      this.sellConditions = JSON.parse(JSON.stringify(preset.sell_conditions))
      // Validate all indicator expressions
      this.indicators.forEach((_, idx) => this.validateIndicator(idx))
    },

    async executeBacktest() {
      if (!this.canRun) return
      this.loading = true
      this.error = null
      try {
        const config = {
          ts_code: this.selectedStock.ts_code,
          stock_name: this.selectedStock.name || '',
          start_date: this.startDate,
          end_date: this.endDate,
          initial_capital: this.initialCapital,
          indicators_config: this.indicators.map(i => ({ name: i.name, expression: i.expression })),
          buy_conditions: this.buyConditions,
          sell_conditions: this.sellConditions
        }
        const { data } = await runBacktest(config)
        this.currentResult = data
        this.resultsVisible = true
        // Refresh history
        this.loadHistory()
      } catch (err) {
        this.error = err.response?.data?.detail || err.message || '回测运行失败'
      } finally {
        this.loading = false
      }
    },

    async loadHistory(params = {}) {
      try {
        const { data } = await listBacktestSessions(params)
        this.historyList = data.sessions
        this.historyTotal = data.total
      } catch (err) {
        console.error('Failed to load history:', err)
      }
    },

    async loadSession(sessionId) {
      try {
        const { data } = await getBacktestSession(sessionId)
        this.currentResult = data
        this.resultsVisible = true
      } catch (err) {
        console.error('Failed to load session:', err)
      }
    },

    async deleteSession(sessionId) {
      try {
        await deleteBacktestSession(sessionId)
        this.loadHistory()
        if (this.currentResult?.session_id === sessionId) {
          this.currentResult = null
          this.resultsVisible = false
        }
      } catch (err) {
        console.error('Failed to delete session:', err)
      }
    },

    reset() {
      this.selectedStock = null
      this.startDate = ''
      this.endDate = ''
      this.initialCapital = 1000000
      this.indicators = []
      this.buyConditions = { type: 'group', operator: 'AND', children: [] }
      this.sellConditions = { type: 'group', operator: 'AND', children: [] }
      this.currentResult = null
      this.error = null
      this.resultsVisible = false
    }
  }
})
