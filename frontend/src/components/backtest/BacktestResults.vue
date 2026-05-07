<template>
  <div class="backtest-results">
    <!-- Header -->
    <div class="results-header">
      <div class="results-title-row">
        <h2>回测结果</h2>
        <div class="results-summary">
          <span v-if="backtestStore.currentResult">
            {{ backtestStore.selectedStock?.name }}（{{ backtestStore.selectedStock?.ts_code }}）
            {{ backtestStore.startDate }} — {{ backtestStore.endDate }}
          </span>
        </div>
        <el-button text size="small" @click="collapsed = !collapsed">
          {{ collapsed ? '展开' : '收起' }}
          <svg
            viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"
            :style="{ transform: collapsed ? 'rotate(0deg)' : 'rotate(180deg)', transition: 'transform 0.2s' }"
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </el-button>
      </div>
    </div>

    <template v-if="!collapsed">
      <!-- Metrics Cards Row (8 cards) -->
      <div class="metrics-row">
        <div class="metric-card">
          <div class="metric-value" :class="returnClass">{{ formatPct(statistics?.total_return_pct) }}</div>
          <div class="metric-label">总收益率</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ formatPct(statistics?.annualized_return_pct) }}</div>
          <div class="metric-label">年化收益率</div>
        </div>
        <div class="metric-card">
          <div class="metric-value text-green">{{ formatPct(statistics?.max_drawdown_pct) }}</div>
          <div class="metric-label">最大回撤</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ statistics?.trade_count || 0 }}</div>
          <div class="metric-label">交易次数</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ formatPct(statistics?.win_rate_pct) }}</div>
          <div class="metric-label">胜率</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ statistics?.profit_factor?.toFixed(2) || '--' }}</div>
          <div class="metric-label">盈亏比</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ statistics?.sharpe_ratio?.toFixed(2) || '--' }}</div>
          <div class="metric-label">夏普比率</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ statistics?.avg_holding_days?.toFixed(1) || '--' }}</div>
          <div class="metric-label">平均持仓天数</div>
        </div>
      </div>

      <!-- Equity Curve (dual-line) -->
      <div class="chart-section">
        <h3>资金曲线</h3>
        <v-chart :option="equityCurveOption" autoresize style="height: 300px" />
      </div>

      <!-- K-line with Buy/Sell Markers -->
      <div class="chart-section">
        <h3>交易点位</h3>
        <KLineChart
          :buySellMarkers="buySellMarkers"
          :fixedData="dailyData"
        />
      </div>

      <!-- Trade Detail Table -->
      <div class="table-section">
        <h3>交易明细</h3>
        <el-table :data="tradePairs" style="width: 100%" size="small">
          <el-table-column prop="buy_date" label="买入日期" width="110" />
          <el-table-column label="买入价" width="80">
            <template #default="{ row }">{{ row.buy_price?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="sell_date" label="卖出日期" width="110" />
          <el-table-column label="卖出价" width="80">
            <template #default="{ row }">{{ row.sell_price?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="sell_shares" label="股数" width="80" />
          <el-table-column prop="holding_days" label="持仓天数" width="80" />
          <el-table-column label="盈亏金额" width="100">
            <template #default="{ row }">
              <span :class="row.profit_amount > 0 ? 'text-red' : 'text-green'">
                {{ formatMoney(row.profit_amount) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="盈亏%">
            <template #default="{ row }">
              <span :class="row.profit_pct > 0 ? 'text-red' : 'text-green'">
                {{ row.profit_pct?.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="tradePairs.length === 0" class="empty-text">
          无完整交易记录
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import KLineChart from '@/components/KLineChart.vue'
import { useBacktestStore } from '@/stores/backtest'
import { useStockStore } from '@/stores/stock'

use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

export default {
  name: 'BacktestResults',
  components: { VChart, KLineChart },
  setup() {
    const backtestStore = useBacktestStore()
    const stockStore = useStockStore()
    const collapsed = ref(false)

    const statistics = computed(() => backtestStore.currentResult?.statistics || null)
    const tradePairs = computed(() => statistics.value?.trade_pairs || [])

    const equityCurveOption = computed(() => {
      const curve = backtestStore.currentResult?.equity_curve || []
      const baseline = backtestStore.currentResult?.baseline_curve || []
      if (curve.length === 0) return {}

      const dates = curve.map(d => d.date)
      const strategyData = curve.map(d => d.net_worth)
      const baselineData = baseline.map(d => d.net_worth)

      // If baseline has different length or is empty, fill with empty array
      const baselineValues = baseline.length === curve.length ? baselineData : []

      return {
        backgroundColor: '#131722',
        grid: { left: 65, right: 20, top: 40, bottom: 30 },
        legend: {
          data: ['策略净值', '买入持有'],
          top: 5,
          textStyle: { color: '#787b86', fontSize: 11 }
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLabel: { color: '#787b86', fontSize: 11 }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            color: '#787b86',
            fontSize: 11,
            formatter: v => (v / 10000).toFixed(0) + '万'
          },
          splitLine: { lineStyle: { color: '#2a2e39' } }
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#1e222d',
          borderColor: '#2a2e39',
          textStyle: { color: '#d1d4dc' }
        },
        series: [
          {
            name: '策略净值',
            type: 'line',
            data: strategyData,
            lineStyle: { color: '#2962ff', width: 2 },
            symbol: 'none',
            areaStyle: {
              color: {
                type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(41,98,255,0.3)' },
                  { offset: 1, color: 'rgba(41,98,255,0.02)' }
                ]
              }
            }
          },
          {
            name: '买入持有',
            type: 'line',
            data: baselineValues,
            lineStyle: { color: '#787b86', width: 1, type: 'dashed' },
            symbol: 'none'
          }
        ]
      }
    })

    const buySellMarkers = computed(() => {
      const trades = backtestStore.currentResult?.trades || []
      return trades.map(t => ({
        date: t.trade_date,
        type: t.trade_type,
        price: t.price
      }))
    })

    // Use stock store daily data (loaded when stock selected in BacktestView)
    const dailyData = computed(() => stockStore.dailyData)

    const returnClass = computed(() => {
      const pct = statistics.value?.total_return_pct
      if (pct == null) return ''
      return pct > 0 ? 'text-red' : pct < 0 ? 'text-green' : ''
    })

    function formatMoney(n) {
      if (n == null) return '--'
      const abs = Math.abs(n)
      if (abs >= 10000) return (n / 10000).toFixed(2) + '万'
      return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    function formatPct(v) {
      if (v == null) return '--'
      return (v > 0 ? '+' : '') + v.toFixed(2) + '%'
    }

    return {
      backtestStore,
      collapsed,
      statistics,
      tradePairs,
      equityCurveOption,
      buySellMarkers,
      dailyData,
      returnClass,
      formatMoney,
      formatPct
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.backtest-results {
  background-color: $bg-primary;
}

.results-header {
  margin-bottom: 24px;
}

.results-title-row {
  display: flex;
  align-items: center;
  gap: 12px;

  h2 {
    color: $text-primary;
    font-size: 22px;
    margin: 0;
  }

  .results-summary {
    color: $text-secondary;
    font-size: 13px;
  }
}

.metrics-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.metric-card {
  flex: 1;
  min-width: 140px;
  padding: 16px 20px;
  background-color: $bg-secondary;
  border-radius: 6px;
  border: 1px solid $border-color;
  text-align: center;

  .metric-value {
    font-size: 24px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 6px;
  }

  .metric-label {
    font-size: 12px;
    color: $text-secondary;
  }
}

.text-red { color: #ef5350; }
.text-green { color: #26a69a; }

.chart-section {
  margin-bottom: 24px;
  background-color: $bg-secondary;
  border-radius: 6px;
  border: 1px solid $border-color;
  padding: 16px;

  h3 { color: $text-secondary; font-size: 15px; margin-bottom: 12px; }
}

.table-section {
  margin-bottom: 24px;

  h3 { color: $text-secondary; font-size: 15px; margin-bottom: 12px; }
  .empty-text { text-align: center; color: $text-secondary; padding: 32px 0; }
}
</style>
