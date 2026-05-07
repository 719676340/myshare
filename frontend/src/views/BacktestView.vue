<template>
  <div class="backtest-view">
    <!-- Config Area -->
    <div class="config-area" :class="{ 'config-compact': backtestStore.resultsVisible }">
      <BacktestConfig />
    </div>

    <!-- Error Message -->
    <el-alert
      v-if="backtestStore.error"
      :title="backtestStore.error"
      type="error"
      show-icon
      closable
      @close="backtestStore.error = null"
      style="margin: 0 32px 16px"
    />

    <!-- Results Area -->
    <div v-if="backtestStore.currentResult && backtestStore.resultsVisible" class="results-area">
      <BacktestResults />
    </div>

    <!-- History Section -->
    <div class="history-section" v-if="backtestStore.historyList.length > 0">
      <h3>历史回测</h3>
      <el-table :data="backtestStore.historyList" size="small" @row-click="handleHistoryClick">
        <el-table-column prop="ts_code" label="股票" width="100" />
        <el-table-column prop="start_date" label="起始" width="100" />
        <el-table-column prop="end_date" label="结束" width="100" />
        <el-table-column label="收益率" width="100">
          <template #default="{ row }">
            <span :class="row.statistics?.total_return_pct > 0 ? 'text-red' : 'text-green'">
              {{ row.statistics?.total_return_pct?.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button type="danger" size="small" text @click.stop="backtestStore.deleteSession(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script>
import { onMounted, watch } from 'vue'
import BacktestConfig from '@/components/backtest/BacktestConfig.vue'
import BacktestResults from '@/components/backtest/BacktestResults.vue'
import { useBacktestStore } from '@/stores/backtest'
import { useStockStore } from '@/stores/stock'

export default {
  name: 'BacktestView',
  components: {
    BacktestConfig,
    BacktestResults
  },
  setup() {
    const backtestStore = useBacktestStore()
    const stockStore = useStockStore()

    onMounted(() => {
      backtestStore.loadPresets()
      backtestStore.loadHistory()
    })

    // When stock changes, fetch daily data so KLineChart has data
    watch(() => backtestStore.selectedStock, (stock) => {
      if (stock) {
        stockStore.selectStock(stock.ts_code, stock.name)
      }
    })

    function handleHistoryClick(row) {
      backtestStore.loadSession(row.id)
    }

    return {
      backtestStore,
      handleHistoryClick
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.backtest-view {
  height: 100%;
  overflow-y: auto;
  background-color: $bg-primary;
  padding: 24px 32px;
}

.config-area {
  margin-bottom: 24px;
  transition: margin-bottom 0.3s;
}

.config-area.config-compact {
  margin-bottom: 16px;
}

.results-area {
  margin-bottom: 24px;
}

.history-section {
  margin-top: 16px;

  h3 {
    color: $text-secondary;
    font-size: 15px;
    margin-bottom: 12px;
  }
}

.text-red { color: #ef5350; }
.text-green { color: #26a69a; }
</style>
