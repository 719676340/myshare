<template>
  <div class="practice-stats">
    <div class="stats-header">
      <h2>练习统计</h2>
      <div class="stats-summary">
        <span>{{ practiceStore.stock?.name }}（{{ practiceStore.stock?.ts_code }}）</span>
        <span>{{ practiceStore.session?.start_date }} — {{ practiceStore.session?.end_date }}</span>
      </div>
    </div>

    <!-- Tier 1: Primary metrics (large cards) -->
    <div class="metrics-row tier-1">
      <div class="metric-card primary">
        <div class="metric-value" :class="returnClass">{{ formatPct(practiceStore.stats?.total_return_pct) }}</div>
        <div class="metric-label">总收益率</div>
      </div>
      <div class="metric-card primary">
        <div class="metric-value" :class="drawdownClass">{{ formatPct(practiceStore.stats?.max_drawdown_pct) }}</div>
        <div class="metric-label">最大回撤</div>
      </div>
      <div class="metric-card primary">
        <div class="metric-value">{{ formatPct(practiceStore.stats?.win_rate) }}</div>
        <div class="metric-label">胜率</div>
      </div>
      <div class="metric-card primary">
        <div class="metric-value">{{ formatProfitFactor(practiceStore.stats?.profit_factor) }}</div>
        <div class="metric-label">盈亏比</div>
      </div>
    </div>

    <!-- Tier 2: Secondary metrics (smaller cards) -->
    <div class="metrics-row tier-2">
      <div class="metric-card secondary">
        <div class="metric-value">{{ formatMoney(practiceStore.stats?.final_capital) }}</div>
        <div class="metric-label">最终资金</div>
      </div>
      <div class="metric-card secondary">
        <div class="metric-value">{{ practiceStore.stats?.total_trades || 0 }}</div>
        <div class="metric-label">交易次数</div>
      </div>
      <div class="metric-card secondary">
        <div class="metric-value">{{ practiceStore.stats?.avg_holding_days || 0 }}天</div>
        <div class="metric-label">平均持仓</div>
      </div>
      <div class="metric-card secondary">
        <div class="metric-value text-red">{{ formatMoney(practiceStore.stats?.avg_win_amount) }}</div>
        <div class="metric-label">平均盈利</div>
      </div>
      <div class="metric-card secondary">
        <div class="metric-value text-green">{{ formatMoney(practiceStore.stats?.avg_loss_amount) }}</div>
        <div class="metric-label">平均亏损</div>
      </div>
      <div class="metric-card secondary">
        <div class="metric-value">{{ formatMoney((practiceStore.stats?.total_commission || 0) + (practiceStore.stats?.total_stamp_tax || 0)) }}</div>
        <div class="metric-label">总费用</div>
      </div>
      <div class="metric-card secondary">
        <div class="metric-value text-red">{{ formatMoney(practiceStore.stats?.max_win_amount) }}</div>
        <div class="metric-label">最大单笔盈利</div>
      </div>
      <div class="metric-card secondary">
        <div class="metric-value text-green">{{ formatMoney(practiceStore.stats?.max_loss_amount) }}</div>
        <div class="metric-label">最大单笔亏损</div>
      </div>
    </div>

    <!-- Equity Curve -->
    <div class="chart-section">
      <h3>资金曲线</h3>
      <v-chart :option="equityCurveOption" autoresize style="height: 300px" />
      <div v-if="practiceStore.stats?.trade_pairs?.length" class="drawdown-info">
        最大回撤: {{ practiceStore.stats?.max_drawdown_pct }}% （{{ practiceStore.stats?.max_drawdown_start }} ~ {{ practiceStore.stats?.max_drawdown_end }}）
      </div>
    </div>

    <!-- K-line with Buy/Sell Markers -->
    <div class="chart-section">
      <h3>交易点位</h3>
      <KLineChart
        :buySellMarkers="buySellMarkers"
        :fixedData="practiceStore.dailyData"
      />
    </div>

    <!-- Trade Table -->
    <div class="table-section">
      <h3>交易明细</h3>
      <el-table :data="practiceStore.stats?.trade_pairs || []" style="width: 100%" size="small">
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
        <el-table-column label="盈亏%" width="80">
          <template #default="{ row }">
            <span :class="row.profit_pct > 0 ? 'text-red' : 'text-green'">
              {{ row.profit_pct?.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="累计盈亏" width="110">
          <template #default="{ row }">
            <span :class="row.cumulative_pnl > 0 ? 'text-red' : row.cumulative_pnl < 0 ? 'text-green' : ''">
              {{ formatMoney(row.cumulative_pnl) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!practiceStore.stats?.trade_pairs?.length" class="empty-text">
        无完整交易记录
      </div>
    </div>

    <div class="stats-actions">
      <el-button type="primary" size="large" @click="$emit('newPractice')">
        开始新的练习
      </el-button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import KLineChart from '@/components/KLineChart.vue'
import { usePracticeStore } from '@/stores/practice'

use([LineChart, GridComponent, MarkLineComponent, CanvasRenderer])

export default {
  name: 'PracticeStats',
  components: { VChart, KLineChart },
  emits: ['newPractice'],
  setup() {
    const practiceStore = usePracticeStore()

    const equityCurveOption = computed(() => {
      const curve = practiceStore.stats?.equity_curve || []
      const initialCapital = practiceStore.stats?.initial_capital || 0
      return {
        backgroundColor: '#131722',
        grid: { left: 65, right: 20, top: 20, bottom: 30 },
        xAxis: {
          type: 'category',
          data: curve.map(d => d.date),
          axisLabel: { color: '#787b86', fontSize: 11 }
        },
        yAxis: {
          type: 'value',
          axisLabel: { color: '#787b86', fontSize: 11, formatter: v => (v / 10000).toFixed(0) + '万' },
          splitLine: { lineStyle: { color: '#2a2e39' } }
        },
        series: [{
          type: 'line',
          data: curve.map(d => d.net_worth),
          lineStyle: { color: '#5b9bd5', width: 2 },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(91,155,213,0.3)' },
                { offset: 1, color: 'rgba(91,155,213,0.02)' }
              ]
            }
          },
          symbol: 'none',
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { color: '#787b86', type: 'dashed', width: 1 },
            label: {
              show: true,
              position: 'insideEndTop',
              formatter: '初始资金',
              color: '#787b86',
              fontSize: 11
            },
            data: [{ yAxis: initialCapital }]
          }
        }]
      }
    })

    const buySellMarkers = computed(() => {
      const trades = practiceStore.stats?.all_trades || []
      return trades.map(t => ({
        date: t.trade_date,
        type: t.trade_type,
        price: t.price
      }))
    })

    const returnClass = computed(() => {
      const pct = practiceStore.stats?.total_return_pct
      if (pct == null) return ''
      return pct > 0 ? 'text-red' : pct < 0 ? 'text-green' : ''
    })

    const drawdownClass = computed(() => {
      const dd = practiceStore.stats?.max_drawdown_pct
      if (dd == null || dd === 0) return ''
      return 'text-green' // drawdown is negative, show in loss color
    })

    function formatMoney(n) {
      if (n == null) return '--'
      const abs = Math.abs(n)
      if (abs >= 10000) return (n < 0 ? '-' : '') + (abs / 10000).toFixed(2) + '万'
      return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    function formatPct(v) {
      if (v == null) return '--'
      return (v > 0 ? '+' : '') + v.toFixed(2) + '%'
    }

    function formatProfitFactor(v) {
      if (v == null) return '--'
      if (!isFinite(v)) return '∞'
      return v.toFixed(2)
    }

    return {
      practiceStore,
      equityCurveOption,
      buySellMarkers,
      returnClass,
      drawdownClass,
      formatMoney,
      formatPct,
      formatProfitFactor
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.practice-stats {
  height: 100%;
  overflow-y: auto;
  padding: 24px 32px;
  background-color: $bg-primary;
}

.stats-header {
  margin-bottom: 24px;
  h2 { color: $text-primary; font-size: 22px; margin-bottom: 6px; }
  .stats-summary { color: $text-secondary; font-size: 13px; }
}

.metrics-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;

  &.tier-1 {
    margin-bottom: 12px;
  }
}

.metric-card {
  flex: 1;
  min-width: 140px;
  padding: 16px 20px;
  background-color: $bg-secondary;
  border-radius: 6px;
  border: 1px solid $border-color;
  text-align: center;

  &.primary {
    min-width: 160px;
    .metric-value {
      font-size: 24px;
      font-weight: 600;
    }
  }

  &.secondary {
    min-width: 120px;
    padding: 12px 16px;
    .metric-value {
      font-size: 18px;
      font-weight: 600;
    }
  }

  .metric-value {
    color: $text-primary;
    margin-bottom: 4px;
  }

  .metric-label {
    font-size: 12px;
    color: $text-secondary;
  }
}

.text-red { color: #ef5350; }
.text-green { color: #26a69a; }

.drawdown-info {
  color: $color-down;
  font-size: 12px;
  margin-top: 8px;
  text-align: right;
}

.chart-section {
  margin-bottom: 24px;
  h3 { color: $text-secondary; font-size: 15px; margin-bottom: 12px; }
  background-color: $bg-secondary;
  border-radius: 6px;
  border: 1px solid $border-color;
  padding: 16px;
}

.table-section {
  margin-bottom: 24px;
  h3 { color: $text-secondary; font-size: 15px; margin-bottom: 12px; }
  .empty-text { text-align: center; color: $text-secondary; padding: 32px 0; }
}

.stats-actions {
  text-align: center;
  padding: 16px 0 32px;
}
</style>
