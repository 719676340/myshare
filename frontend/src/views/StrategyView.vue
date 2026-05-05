<template>
  <div class="strategy-view">
    <div class="toolbar">
      <div class="toolbar-left">
        <StockSearch />
      </div>
      <div class="toolbar-right">
        <span v-if="stockStore.currentStock" class="stock-info">
          {{ stockStore.currentStockCode }} {{ stockStore.currentStockName }}
        </span>
      </div>
    </div>
    <div class="chart-area">
      <!-- Loading state -->
      <div v-if="stockStore.isLoading" class="loading-state">
        <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
        <p>正在加载数据...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="stockStore.error" class="error-state">
        <p class="error-text">{{ stockStore.error }}</p>
        <el-button type="default" @click="stockStore.fetchDailyData()">
          重新加载
        </el-button>
      </div>

      <!-- Chart -->
      <KLineChart v-else-if="stockStore.hasData" />

      <!-- Guide page (no stock selected) -->
      <div v-else class="guide-state">
        <div class="guide-content">
          <svg class="guide-icon" viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-4.35-4.35" />
          </svg>
          <p class="guide-text">搜索股票代码或名称，开始分析</p>
          <p class="guide-hint">例如：输入 "000001" 或 "平安银行"</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useStockStore } from '@/stores/stock'
import StockSearch from '@/components/StockSearch.vue'
import KLineChart from '@/components/KLineChart.vue'
import { Loading } from '@element-plus/icons-vue'

export default {
  name: 'StrategyView',
  components: {
    StockSearch,
    KLineChart,
    Loading
  },
  setup() {
    const stockStore = useStockStore()
    return { stockStore }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.strategy-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  height: $toolbar-height;
  background-color: $bg-secondary;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid $border-color;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  width: 320px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.stock-info {
  color: $text-secondary;
  font-size: 13px;
}

.chart-area {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.loading-state,
.error-state,
.guide-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $text-secondary;
}

.loading-icon {
  animation: spin 1s linear infinite;
  color: $accent-blue;
  margin-bottom: 12px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-text {
  color: $color-up;
  margin-bottom: 12px;
}

.guide-content {
  text-align: center;
}

.guide-icon {
  color: $text-secondary;
  margin-bottom: 16px;
  opacity: 0.5;
}

.guide-text {
  font-size: 16px;
  color: $text-secondary;
  margin-bottom: 8px;
}

.guide-hint {
  font-size: 13px;
  color: $text-secondary;
  opacity: 0.6;
}
</style>
