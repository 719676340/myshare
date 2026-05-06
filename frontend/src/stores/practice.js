import { defineStore } from 'pinia'
import {
  createPracticeSession,
  getPracticeSession,
  advancePracticeDay,
  placeBuyOrder,
  placeSellOrder,
  endPracticeSession,
  getPracticeStats
} from '@/api'

export const usePracticeStore = defineStore('practice', {
  state: () => ({
    // Practice mode flag
    isActive: false,

    // Session data (null until session created)
    session: null,          // { id, ts_code, start_date, end_date, initial_capital, current_date, cash, status, created_at }
    stock: null,            // { ts_code, name, symbol }
    dailyData: [],          // Array of visible OHLCV bars up to current_date
    positions: [],          // [{ id, buy_trade_id, ts_code, buy_date, buy_price, total_shares, remaining_shares, market_value, floating_pnl }]
    trades: [],             // [{ id, trade_type, trade_date, shares, price, amount, commission, stamp_tax }]
    totalMarketValue: 0,
    totalAssets: 0,
    totalPnl: 0,
    totalPnlPct: 0,
    progress: { current: 0, total: 0, pct: 0 },

    // Stats (populated after session ends)
    stats: null,            // Full stats object from getPracticeStats

    // UI state
    isLoading: false,
    isAdvancing: false,
    isTrading: false,
    error: null,
    lastMessage: null,      // Latest trade confirmation message to show user
  }),

  getters: {
    isConfigured: (state) => state.session !== null,
    isFinished: (state) => state.session?.status === 'finished',
    availableCash: (state) => state.session?.cash || 0,
    hasOpenPositions: (state) => state.positions.length > 0,
    currentDate: (state) => state.session?.current_date || '',
  },

  actions: {
    /**
     * Create a new practice session and load initial state.
     * Called from PracticeConfig.vue on "Start Practice" click.
     */
    async createSession(tsCode, startDate, endDate, initialCapital = 1000000) {
      this.isLoading = true
      this.error = null
      try {
        const result = await createPracticeSession(tsCode, startDate, endDate, initialCapital)
        // Load full session state
        await this.fetchSession(result.session_id)
        this.isActive = true
      } catch (err) {
        this.error = err.message || '创建练习会话失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Fetch current session state from backend.
     */
    async fetchSession(sessionId) {
      const data = await getPracticeSession(sessionId)
      this.session = data.session
      this.stock = data.stock
      this.dailyData = data.daily_data
      this.positions = data.positions
      this.trades = data.trades
      this.totalMarketValue = data.total_market_value
      this.totalAssets = data.total_assets
      this.totalPnl = data.total_pnl
      this.totalPnlPct = data.total_pnl_pct
      this.progress = data.progress
    },

    /**
     * Advance to the next trading day.
     */
    async advanceDay() {
      if (!this.session?.id) return
      this.isAdvancing = true
      this.error = null
      try {
        const result = await advancePracticeDay(this.session.id)
        // result: { current_date, bar, is_final }
        // Append the new bar to dailyData
        this.dailyData = [...this.dailyData, result.bar]
        this.session = { ...this.session, current_date: result.current_date }
        // Refresh full session to get updated progress, positions, etc.
        await this.fetchSession(this.session.id)
        if (result.is_final) {
          this.lastMessage = '已到最后一天，点击「结束练习」查看统计'
        }
        return result
      } catch (err) {
        this.error = err.message || '推进日期失败'
        throw err
      } finally {
        this.isAdvancing = false
      }
    },

    /**
     * Place a buy order and refresh session state.
     */
    async buyOrder(shares, price) {
      if (!this.session?.id) return
      this.isTrading = true
      this.error = null
      try {
        const result = await placeBuyOrder(this.session.id, shares, price)
        // Refresh session to get updated positions, cash, trades
        await this.fetchSession(this.session.id)
        this.lastMessage = result.message
        return result
      } catch (err) {
        this.error = err.message || '买入失败'
        throw err
      } finally {
        this.isTrading = false
      }
    },

    /**
     * Place a sell order and refresh session state.
     */
    async sellOrder(positionId, shares, price) {
      if (!this.session?.id) return
      this.isTrading = true
      this.error = null
      try {
        const result = await placeSellOrder(this.session.id, positionId, shares, price)
        await this.fetchSession(this.session.id)
        this.lastMessage = result.message
        return result
      } catch (err) {
        this.error = err.message || '卖出失败'
        throw err
      } finally {
        this.isTrading = false
      }
    },

    /**
     * End the current session and load stats.
     */
    async endSession() {
      if (!this.session?.id) return
      this.isLoading = true
      try {
        await endPracticeSession(this.session.id)
        this.session = { ...this.session, status: 'finished' }
        // Load statistics
        const stats = await getPracticeStats(this.session.id)
        this.stats = stats
      } catch (err) {
        this.error = err.message || '结束练习失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Reset store to initial state (for starting a new practice).
     */
    resetPractice() {
      this.isActive = false
      this.session = null
      this.stock = null
      this.dailyData = []
      this.positions = []
      this.trades = []
      this.totalMarketValue = 0
      this.totalAssets = 0
      this.totalPnl = 0
      this.totalPnlPct = 0
      this.progress = { current: 0, total: 0, pct: 0 }
      this.stats = null
      this.isLoading = false
      this.isAdvancing = false
      this.isTrading = false
      this.error = null
      this.lastMessage = null
    }
  }
})
