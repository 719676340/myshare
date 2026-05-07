<template>
  <div class="backtest-config">
    <!-- Step 1: Stock and Date Range -->
    <div class="config-step">
      <div class="step-header">
        <span class="step-badge">1</span>
        <span class="step-title">选股与时间范围</span>
      </div>
      <div class="step-body">
        <div class="step-row">
          <StockSearch @select="handleStockSelect" />
          <div v-if="backtestStore.selectedStock" class="selected-stock">
            <el-tag type="info" size="small">
              {{ backtestStore.selectedStock.ts_code }}
              {{ backtestStore.selectedStock.name }}
            </el-tag>
          </div>
        </div>
        <div class="step-row">
          <el-date-picker
            v-model="startDate"
            type="date"
            placeholder="起始日期"
            format="YYYY-MM-DD"
            value-format="YYYYMMDD"
            size="small"
            style="width: 180px"
          />
          <span class="date-sep">至</span>
          <el-date-picker
            v-model="endDate"
            type="date"
            placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYYMMDD"
            size="small"
            style="width: 180px"
          />
        </div>
        <div class="step-row">
          <span class="field-label">初始资金</span>
          <el-input-number
            v-model="backtestStore.initialCapital"
            :min="100000"
            :step="100000"
            :precision="0"
            :controls="true"
            size="small"
            style="width: 200px"
          />
          <span class="capital-hint">{{ formattedCapital }}</span>
        </div>
      </div>
    </div>

    <!-- Step 2: Custom Indicators -->
    <div class="config-step">
      <div class="step-header">
        <span class="step-badge">2</span>
        <span class="step-title">自定义指标</span>
      </div>
      <div class="step-body">
        <PresetSelector />
        <div v-if="backtestStore.indicators.length > 0" class="indicator-list">
          <IndicatorBuilder
            v-for="(_, idx) in backtestStore.indicators"
            :key="idx"
            :index="idx"
          />
        </div>
        <div v-else class="hint-text">
          点击上方预设策略快速开始，或手动添加指标
        </div>
        <el-button type="primary" plain size="small" @click="backtestStore.addIndicator()">
          添加指标
        </el-button>
      </div>
    </div>

    <!-- Step 3: Buy/Sell Conditions -->
    <div class="config-step">
      <div class="step-header">
        <span class="step-badge">3</span>
        <span class="step-title">买卖条件组</span>
      </div>
      <div class="step-body">
        <div class="conditions-section">
          <div class="conditions-label">买入条件</div>
          <ConditionGroup
            v-if="backtestStore.buyConditions.children.length > 0"
            :group="backtestStore.buyConditions"
            @update:group="backtestStore.buyConditions = $event"
          />
          <div v-else class="hint-text">
            点击添加条件按钮创建买卖规则
          </div>
        </div>

        <div class="conditions-section">
          <div class="conditions-label">卖出条件</div>
          <ConditionGroup
            v-if="backtestStore.sellConditions.children.length > 0"
            :group="backtestStore.sellConditions"
            @update:group="backtestStore.sellConditions = $event"
          />
          <div v-else class="hint-text">
            点击添加条件按钮创建买卖规则
          </div>
        </div>
      </div>
    </div>

    <!-- Run Button -->
    <div class="config-actions">
      <el-button
        type="primary"
        size="large"
        :loading="backtestStore.loading"
        :disabled="!backtestStore.canRun"
        @click="backtestStore.executeBacktest()"
      >
        运行回测
      </el-button>
      <el-button
        size="large"
        @click="backtestStore.reset()"
      >
        重置
      </el-button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import StockSearch from '@/components/StockSearch.vue'
import PresetSelector from './PresetSelector.vue'
import IndicatorBuilder from './IndicatorBuilder.vue'
import ConditionGroup from './ConditionGroup.vue'
import { useBacktestStore } from '@/stores/backtest'

export default {
  name: 'BacktestConfig',
  components: {
    StockSearch,
    PresetSelector,
    IndicatorBuilder,
    ConditionGroup
  },
  setup() {
    const backtestStore = useBacktestStore()

    const startDate = computed({
      get: () => backtestStore.startDate,
      set: (val) => { backtestStore.startDate = val }
    })

    const endDate = computed({
      get: () => backtestStore.endDate,
      set: (val) => { backtestStore.endDate = val }
    })

    const formattedCapital = computed(() => {
      const val = backtestStore.initialCapital
      if (val >= 10000) {
        return (val / 10000).toFixed(0) + '万'
      }
      return val.toLocaleString() + '元'
    })

    function handleStockSelect(stock) {
      backtestStore.setStock(stock)
    }

    return {
      backtestStore,
      startDate,
      endDate,
      formattedCapital,
      handleStockSelect
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.backtest-config {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-step {
  background-color: $bg-secondary;
  border: 1px solid $border-color;
  border-radius: 6px;
  padding: 20px;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.step-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: $accent-blue;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-title {
  color: $text-primary;
  font-size: 16px;
  font-weight: 500;
}

.step-body {
  padding-left: 34px;
}

.step-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.date-sep {
  color: $text-secondary;
  font-size: 13px;
}

.field-label {
  color: $text-secondary;
  font-size: 13px;
  min-width: 60px;
}

.capital-hint {
  color: $text-secondary;
  font-size: 13px;
}

.selected-stock {
  margin-left: 8px;
}

.indicator-list {
  margin-bottom: 12px;
}

.hint-text {
  color: $text-secondary;
  font-size: 13px;
  padding: 12px 0;
}

.conditions-section {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }
}

.conditions-label {
  color: $text-secondary;
  font-size: 13px;
  margin-bottom: 8px;
  font-weight: 500;
}

.config-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 8px 0;
}
</style>
