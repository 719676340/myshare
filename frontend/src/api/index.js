import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Error interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    const status = error.response?.status
    const retry = status === 502 || status === 503 || error.code === 'ECONNABORTED'

    return Promise.reject({
      message,
      status,
      retry,
      original: error
    })
  }
)

/**
 * Search stocks by keyword (code or name)
 * @param {string} keyword - search keyword
 * @returns {Promise<Array<{ts_code: string, name: string, symbol: string}>>}
 */
export function searchStocks(keyword) {
  return apiClient.get('/stocks/search', { params: { keyword } })
    .then((res) => res.data)
}

/**
 * Get daily K-line data for a stock
 * @param {string} tsCode - stock code (e.g. "000001.SZ")
 * @param {string} [startDate] - optional start date YYYYMMDD
 * @param {string} [endDate] - optional end date YYYYMMDD
 * @returns {Promise<{ts_code: string, name: string, data: Array, cache_info: Object}>}
 */
export function getDailyData(tsCode, startDate, endDate) {
  const params = {}
  if (startDate) params.start_date = startDate
  if (endDate) params.end_date = endDate
  return apiClient.get(`/daily/${tsCode}`, { params })
    .then((res) => res.data)
}

/**
 * Force refresh daily data from tushare
 * @param {string} tsCode - stock code
 * @returns {Promise<Object>}
 */
export function refreshData(tsCode) {
  return apiClient.post(`/daily/${tsCode}/refresh`)
    .then((res) => res.data)
}

/**
 * Get computed indicator data for a stock
 * @param {string} tsCode - stock code
 * @param {string} indicator - indicator name: macd/rsi/kdj/boll
 * @param {Object} params - indicator parameters (optional)
 * @returns {Promise<{indicator: string, params: Object, data: Array}>}
 */
export function getIndicatorData(tsCode, indicator, params = {}) {
  const searchParams = new URLSearchParams({ indicator })
  if (Object.keys(params).length > 0) {
    searchParams.set('params', JSON.stringify(params))
  }
  return apiClient.get(`/indicators/${tsCode}`, { params: Object.fromEntries(searchParams) })
    .then((res) => res.data)
}

/**
 * Get volume-price analysis data (signals + patterns) for a stock
 * @param {string} tsCode - stock code
 * @returns {Promise<{ts_code: string, signals: Array, patterns: Array}>}
 */
export function getVPAData(tsCode) {
  return apiClient.get(`/vpa/${tsCode}`)
    .then((res) => res.data)
}

export default apiClient
