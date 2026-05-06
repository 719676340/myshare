import { defineStore } from 'pinia'

export const useChartStore = defineStore('chart', {
  state: () => ({
    showMA: {
      ma5: true,
      ma10: true,
      ma20: true,
      ma60: true
    },
    dateRange: null, // { start, end }

    // Indicator sub-chart toggles (default OFF)
    showMACD: false,
    showRSI: false,
    showKDJ: false,
    showBOLL: false,

    // Signal/pattern display toggles (default ON)
    showSignals: true,
    showPatterns: true,

    // Indicator parameters (defaults)
    indicatorParams: {
      macd: { fastperiod: 12, slowperiod: 26, signalperiod: 9 },
      rsi: { window: 14 },
      kdj: { n: 9, m1: 3, m2: 3 },
      boll: { window: 20, window_dev: 2 }
    }
  }),

  actions: {
    toggleMA(maKey) {
      if (maKey in this.showMA) {
        this.showMA[maKey] = !this.showMA[maKey]
      }
    },

    toggleIndicator(name) {
      // name: 'showMACD' | 'showRSI' | 'showKDJ' | 'showBOLL' | 'showSignals' | 'showPatterns'
      if (name in this.$state) {
        this[name] = !this[name]
      }
    },

    updateIndicatorParams(indicator, newParams) {
      // indicator: 'macd' | 'rsi' | 'kdj' | 'boll'
      if (indicator in this.indicatorParams) {
        this.indicatorParams[indicator] = { ...this.indicatorParams[indicator], ...newParams }
      }
    },

    setDateRange(start, end) {
      this.dateRange = { start, end }
    },

    resetDateRange() {
      this.dateRange = null
    }
  }
})
