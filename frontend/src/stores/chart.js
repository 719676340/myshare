import { defineStore } from 'pinia'

export const useChartStore = defineStore('chart', {
  state: () => ({
    showMA: {
      ma5: true,
      ma10: true,
      ma20: true,
      ma60: true
    },
    dateRange: null // { start, end }
  }),

  actions: {
    toggleMA(maKey) {
      if (maKey in this.showMA) {
        this.showMA[maKey] = !this.showMA[maKey]
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
