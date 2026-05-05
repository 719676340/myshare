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

export default apiClient
