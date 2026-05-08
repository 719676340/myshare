import { defineStore } from 'pinia'
import {
  createPracticeSession,
  getPracticeSession,
  advancePracticeDay,
  placeBuyOrder,
  placeSellOrder,
  endPracticeSession,
  getPracticeStats,
  getIndicatorData,
  listPracticeSessions,
  deletePracticeSession,
  updateSessionNotes
} from '@/api'
import { useStockStore } from '@/stores/stock'

const ACTIVE_SESSIONS_KEY = 'practice_active_session_ids'
const CURRENT_SESSION_KEY = 'practice_current_session_id'
// Old key for backward compat cleanup
const OLD_ACTIVE_SESSION_KEY = 'practice_active_session_id'

// --- localStorage helper functions ---

function getActiveSessionIds() {
  try {
    return JSON.parse(localStorage.getItem(ACTIVE_SESSIONS_KEY) || '[]')
  } catch {
    return []
  }
}

function addActiveSession(id) {
  const ids = getActiveSessionIds()
  const numId = Number(id)
  if (!ids.includes(numId)) {
    ids.push(numId)
  }
  localStorage.setItem(ACTIVE_SESSIONS_KEY, JSON.stringify(ids))
}

function removeActiveSession(id) {
  const ids = getActiveSessionIds()
  const numId = Number(id)
  const filtered = ids.filter(i => i !== numId)
  localStorage.setItem(ACTIVE_SESSIONS_KEY, JSON.stringify(filtered))
}

function getCurrentSessionId() {
  const val = localStorage.getItem(CURRENT_SESSION_KEY)
  return val ? Number(val) : null
}

function setCurrentSessionId(id) {
  localStorage.setItem(CURRENT_SESSION_KEY, String(id))
}

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

    // Multi-session support
    activeSessions: [],         // Array of lightweight session summaries for the switcher UI
    activeSessionsLoading: false,

    // UI state
    isLoading: false,
    isAdvancing: false,
    isTrading: false,
    error: null,
    lastMessage: null,      // Latest trade confirmation message to show user

    // History management
    historyList: [],
    historyTotal: 0,
    historyLoading: false,
  }),

  getters: {
    isConfigured: (state) => state.session !== null,
    isFinished: (state) => state.session?.status === 'finished',
    availableCash: (state) => state.session?.cash || 0,
    hasOpenPositions: (state) => state.positions.length > 0,
    currentDate: (state) => state.session?.current_date || '',
    hasOtherActiveSessions: (state) => state.activeSessions.length > 1,
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
        addActiveSession(result.session_id)
        setCurrentSessionId(result.session_id)
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
     * Place a buy order at current day's close price.
     */
    async buyOrder(shares) {
      if (!this.session?.id) return
      this.isTrading = true
      this.error = null
      try {
        const result = await placeBuyOrder(this.session.id, shares)
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
     * Place a sell order at current day's close price.
     */
    async sellOrder(positionId, shares) {
      if (!this.session?.id) return
      this.isTrading = true
      this.error = null
      try {
        const result = await placeSellOrder(this.session.id, positionId, shares)
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
        const endedId = this.session.id
        this.session = { ...this.session, status: 'finished' }
        removeActiveSession(endedId)
        // Clear current session key if it matches the ended one
        if (getCurrentSessionId() === endedId) {
          localStorage.removeItem(CURRENT_SESSION_KEY)
        }
        // Load statistics
        const stats = await getPracticeStats(this.session.id)
        this.stats = stats
        // Refresh active sessions list
        await this.fetchActiveSessions()
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
      // Clear indicator data to avoid stale data affecting strategy mode
      const stockStore = useStockStore()
      stockStore.indicatorData = {}

      // Remove current session from active list if present
      if (this.session?.id) {
        removeActiveSession(this.session.id)
      }
      localStorage.removeItem(CURRENT_SESSION_KEY)

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

      // Refresh active sessions list
      this.fetchActiveSessions()
    },

    /**
     * Resume an active practice session by sessionId.
     * Called from PracticeHistory when user clicks "继续练习".
     * Throws on non-active status so the caller can show an error.
     */
    async resumeSession(sessionId) {
      this.isLoading = true
      this.error = null
      try {
        await this.fetchSession(sessionId)
        if (this.session.status !== 'active') {
          throw new Error('该练习已结束')
        }
        this.isActive = true
        addActiveSession(sessionId)
        setCurrentSessionId(sessionId)
        this.stats = null
        return true
      } catch (err) {
        this.error = err.message || '恢复练习失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Try to restore a previously active practice session from localStorage.
     * Returns true if a session was successfully restored, false otherwise.
     */
    async tryRestoreSession() {
      // Backward compat: clean up old single key if present
      const oldKey = localStorage.getItem(OLD_ACTIVE_SESSION_KEY)
      if (oldKey) {
        addActiveSession(Number(oldKey))
        setCurrentSessionId(Number(oldKey))
        localStorage.removeItem(OLD_ACTIVE_SESSION_KEY)
      }

      const currentId = getCurrentSessionId()
      if (currentId) {
        try {
          await this.fetchSession(currentId)
          if (this.session && this.session.status === 'active') {
            this.isActive = true
            return true
          }
          // Current session is not active — remove it
          removeActiveSession(currentId)
          localStorage.removeItem(CURRENT_SESSION_KEY)
        } catch (e) {
          // API call failed — remove stale reference
          removeActiveSession(currentId)
          localStorage.removeItem(CURRENT_SESSION_KEY)
        }
      }

      // Try remaining active sessions in localStorage
      const remainingIds = getActiveSessionIds()
      for (const id of remainingIds) {
        try {
          await this.fetchSession(id)
          if (this.session && this.session.status === 'active') {
            this.isActive = true
            setCurrentSessionId(id)
            return true
          }
          // Not active — remove from list
          removeActiveSession(id)
        } catch (e) {
          // Failed — remove from list
          removeActiveSession(id)
        }
      }

      // No valid sessions found — clear all
      localStorage.removeItem(ACTIVE_SESSIONS_KEY)
      localStorage.removeItem(CURRENT_SESSION_KEY)
      return false
    },

    /**
     * Fetch indicator data for the practice stock.
     * Stores results into stockStore.indicatorData so KLineChart can read them.
     */
    async fetchIndicatorDataForPractice(indicator, params = {}) {
      if (!this.stock?.ts_code) return
      try {
        const result = await getIndicatorData(this.stock.ts_code, indicator, params)
        const stockStore = useStockStore()
        stockStore.indicatorData = { ...stockStore.indicatorData, [indicator]: result }
      } catch (err) {
        console.error(`Failed to fetch ${indicator} data for practice:`, err)
      }
    },

    /**
     * Fetch all enabled indicator data for the practice stock.
     */
    async fetchAllEnabledIndicators(chartStore) {
      if (!this.stock?.ts_code) return
      // Clear stale indicator data first
      const stockStore = useStockStore()
      stockStore.indicatorData = {}

      const promises = []
      if (chartStore.showMACD) {
        promises.push(this.fetchIndicatorDataForPractice('macd', chartStore.indicatorParams.macd))
      }
      if (chartStore.showRSI) {
        promises.push(this.fetchIndicatorDataForPractice('rsi', chartStore.indicatorParams.rsi))
      }
      if (chartStore.showKDJ) {
        promises.push(this.fetchIndicatorDataForPractice('kdj', chartStore.indicatorParams.kdj))
      }
      if (chartStore.showBOLL) {
        promises.push(this.fetchIndicatorDataForPractice('boll', chartStore.indicatorParams.boll))
      }
      await Promise.all(promises)
    },

    /**
     * Fetch practice history list with optional filtering.
     */
    async fetchHistory(params = {}) {
      this.historyLoading = true
      try {
        const result = await listPracticeSessions(params)
        this.historyList = result.items
        this.historyTotal = result.total
      } catch (err) {
        console.error('Failed to fetch history:', err)
      } finally {
        this.historyLoading = false
      }
    },

    /**
     * Delete a practice session record.
     */
    async deleteHistory(sessionId) {
      await deletePracticeSession(sessionId)
      this.historyList = this.historyList.filter(s => s.id !== sessionId)
      this.historyTotal--
    },

    /**
     * Update notes for a practice session.
     */
    async updateNotes(sessionId, notes) {
      await updateSessionNotes(sessionId, notes)
      const item = this.historyList.find(s => s.id === sessionId)
      if (item) item.notes = notes
    },

    /**
     * Switch to a different active session.
     * Loads the session data and sets it as current.
     */
    async switchSession(sessionId) {
      this.isLoading = true
      this.error = null
      try {
        await this.fetchSession(sessionId)
        setCurrentSessionId(sessionId)
        this.isActive = true
        this.stats = null
      } catch (err) {
        this.error = err.message || '切换练习会话失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Fetch all active sessions for the switcher UI.
     * Syncs localStorage with backend state.
     */
    async fetchActiveSessions() {
      this.activeSessionsLoading = true
      try {
        const result = await listPracticeSessions({ status: 'active', limit: 50 })
        this.activeSessions = result.items
        // Sync localStorage: ensure all returned sessions are in the array
        const backendIds = result.items.map(s => s.id)
        for (const id of backendIds) {
          addActiveSession(id)
        }
        // Remove any localStorage IDs not returned by backend (deleted or finished)
        const storedIds = getActiveSessionIds()
        for (const id of storedIds) {
          if (!backendIds.includes(id)) {
            removeActiveSession(id)
          }
        }
      } catch (err) {
        console.error('Failed to fetch active sessions:', err)
      } finally {
        this.activeSessionsLoading = false
      }
    }
  }
})
