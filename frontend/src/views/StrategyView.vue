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
        <div v-if="stockStore.hasData" class="indicator-toggles">
          <!-- MACD button with Popover -->
          <el-popover placement="bottom" :width="240" trigger="click">
            <template #reference>
              <el-button
                :type="chartStore.showMACD ? 'primary' : 'default'"
                size="small"
                @click="toggleIndicator('showMACD')"
              >MACD</el-button>
            </template>
            <div class="param-panel">
              <div class="param-row">
                <label>快线周期</label>
                <el-input-number v-model="macdParams.fastperiod" :min="2" :max="100" size="small" />
              </div>
              <div class="param-row">
                <label>慢线周期</label>
                <el-input-number v-model="macdParams.slowperiod" :min="2" :max="200" size="small" />
              </div>
              <div class="param-row">
                <label>信号线周期</label>
                <el-input-number v-model="macdParams.signalperiod" :min="2" :max="100" size="small" />
              </div>
              <el-button type="primary" size="small" @click="applyParams('macd')" style="width:100%;margin-top:8px">应用</el-button>
            </div>
          </el-popover>

          <!-- RSI button with Popover -->
          <el-popover placement="bottom" :width="200" trigger="click">
            <template #reference>
              <el-button
                :type="chartStore.showRSI ? 'primary' : 'default'"
                size="small"
                @click="toggleIndicator('showRSI')"
              >RSI</el-button>
            </template>
            <div class="param-panel">
              <div class="param-row">
                <label>周期</label>
                <el-input-number v-model="rsiParams.window" :min="2" :max="100" size="small" />
              </div>
              <el-button type="primary" size="small" @click="applyParams('rsi')" style="width:100%;margin-top:8px">应用</el-button>
            </div>
          </el-popover>

          <!-- KDJ button with Popover -->
          <el-popover placement="bottom" :width="240" trigger="click">
            <template #reference>
              <el-button
                :type="chartStore.showKDJ ? 'primary' : 'default'"
                size="small"
                @click="toggleIndicator('showKDJ')"
              >KDJ</el-button>
            </template>
            <div class="param-panel">
              <div class="param-row">
                <label>N 周期</label>
                <el-input-number v-model="kdjParams.n" :min="2" :max="100" size="small" />
              </div>
              <div class="param-row">
                <label>M1</label>
                <el-input-number v-model="kdjParams.m1" :min="1" :max="50" size="small" />
              </div>
              <div class="param-row">
                <label>M2</label>
                <el-input-number v-model="kdjParams.m2" :min="1" :max="50" size="small" />
              </div>
              <el-button type="primary" size="small" @click="applyParams('kdj')" style="width:100%;margin-top:8px">应用</el-button>
            </div>
          </el-popover>

          <!-- BOLL button with Popover -->
          <el-popover placement="bottom" :width="240" trigger="click">
            <template #reference>
              <el-button
                :type="chartStore.showBOLL ? 'primary' : 'default'"
                size="small"
                @click="toggleIndicator('showBOLL')"
              >BOLL</el-button>
            </template>
            <div class="param-panel">
              <div class="param-row">
                <label>周期</label>
                <el-input-number v-model="bollParams.window" :min="2" :max="200" size="small" />
              </div>
              <div class="param-row">
                <label>标准差倍数</label>
                <el-input-number v-model="bollParams.window_dev" :min="0.5" :max="5" :step="0.5" :precision="1" size="small" />
              </div>
              <el-button type="primary" size="small" @click="applyParams('boll')" style="width:100%;margin-top:8px">应用</el-button>
            </div>
          </el-popover>

          <div class="toggle-divider"></div>

          <!-- Signal toggle -->
          <el-button
            :type="chartStore.showSignals ? 'primary' : 'default'"
            size="small"
            @click="toggleIndicator('showSignals')"
          >量价信号</el-button>

          <!-- Pattern toggle -->
          <el-button
            :type="chartStore.showPatterns ? 'primary' : 'default'"
            size="small"
            @click="toggleIndicator('showPatterns')"
          >K线形态</el-button>
        </div>
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
import { reactive, watch } from 'vue'
import { useStockStore } from '@/stores/stock'
import { useChartStore } from '@/stores/chart'
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
    const chartStore = useChartStore()

    // Local reactive copies of indicator params for Popover editing
    const macdParams = reactive({ ...chartStore.indicatorParams.macd })
    const rsiParams = reactive({ ...chartStore.indicatorParams.rsi })
    const kdjParams = reactive({ ...chartStore.indicatorParams.kdj })
    const bollParams = reactive({ ...chartStore.indicatorParams.boll })

    // Map toggle names to indicator keys
    const indicatorMap = {
      showMACD: 'macd',
      showRSI: 'rsi',
      showKDJ: 'kdj',
      showBOLL: 'boll'
    }

    function toggleIndicator(name) {
      chartStore.toggleIndicator(name)
      // When toggling an indicator on, fetch its data
      if (chartStore[name] && stockStore.currentStock) {
        const indicator = indicatorMap[name]
        if (indicator) {
          stockStore.fetchIndicatorData(indicator, chartStore.indicatorParams[indicator])
        }
        if (name === 'showSignals' || name === 'showPatterns') {
          stockStore.fetchVPAData()
        }
      }
    }

    function applyParams(indicator) {
      const paramsMap = { macd: macdParams, rsi: rsiParams, kdj: kdjParams, boll: bollParams }
      const params = paramsMap[indicator]
      chartStore.updateIndicatorParams(indicator, { ...params })
      stockStore.fetchIndicatorData(indicator, params)
    }

    // Fetch all enabled data when daily data loads for a stock
    watch(
      () => stockStore.hasData,
      (hasData) => {
        if (hasData && stockStore.currentStock) {
          stockStore.fetchAllEnabledData(chartStore)
        }
      }
    )

    return {
      stockStore,
      chartStore,
      macdParams,
      rsiParams,
      kdjParams,
      bollParams,
      toggleIndicator,
      applyParams
    }
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
  gap: 12px;
}

.stock-info {
  color: $text-secondary;
  font-size: 13px;
}

.indicator-toggles {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toggle-divider {
  width: 1px;
  height: 20px;
  background-color: $border-color;
  margin: 0 4px;
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

<style lang="scss">
/* Global styles for popover content (scoped styles don't apply to popovers) */
.param-panel {
  .param-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;

    label {
      font-size: 12px;
      color: #787b86;
      min-width: 70px;
    }

    .el-input-number {
      width: 120px;
    }
  }
}
</style>
