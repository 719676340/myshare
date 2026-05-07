<template>
  <div class="condition-rule">
    <el-select
      :model-value="rule.indicator"
      @update:model-value="updateRule('indicator', $event)"
      placeholder="指标"
      size="small"
      class="rule-select"
    >
      <el-option
        v-for="opt in indicatorOptions"
        :key="opt.value"
        :label="opt.label"
        :value="opt.value"
      />
    </el-select>

    <el-select
      :model-value="rule.operator"
      @update:model-value="updateRule('operator', $event)"
      placeholder="运算符"
      size="small"
      class="operator-select"
    >
      <el-option
        v-for="op in operatorOptions"
        :key="op.value"
        :label="op.label"
        :value="op.value"
      />
    </el-select>

    <!-- Threshold value for numeric comparison operators -->
    <el-input-number
      v-if="showThresholdValue"
      :model-value="rule.threshold"
      @update:model-value="updateRule('threshold', $event)"
      placeholder="阈值"
      size="small"
      :controls="false"
      class="threshold-input"
    />

    <!-- Threshold indicator for cross/break operators -->
    <el-select
      v-if="showThresholdIndicator"
      :model-value="rule.threshold_indicator"
      @update:model-value="updateRule('threshold_indicator', $event)"
      placeholder="参考指标"
      size="small"
      class="rule-select"
    >
      <el-option
        v-for="opt in indicatorOptions"
        :key="opt.value"
        :label="opt.label"
        :value="opt.value"
      />
    </el-select>

    <el-button
      type="danger"
      text
      size="small"
      circle
      @click="$emit('remove')"
    >
      <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 6L6 18M6 6l12 12" />
      </svg>
    </el-button>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useBacktestStore } from '@/stores/backtest'

// Base fields always available for conditions
const BASE_FIELDS = [
  { value: 'OPEN', label: '开盘价' },
  { value: 'HIGH', label: '最高价' },
  { value: 'LOW', label: '最低价' },
  { value: 'CLOSE', label: '收盘价' },
  { value: 'VOL', label: '成交量' },
  { value: 'AMOUNT', label: '成交额' },
  { value: 'PRE_CLOSE', label: '前收盘价' },
  { value: 'CHANGE_PCT', label: '涨跌幅' }
]

// Operators per D-07
const OPERATOR_OPTIONS = [
  { value: '>', label: '大于' },
  { value: '<', label: '小于' },
  { value: '>=', label: '大于等于' },
  { value: '<=', label: '小于等于' },
  { value: '==', label: '等于' },
  { value: 'golden_cross', label: '上穿' },
  { value: 'death_cross', label: '下穿' },
  { value: 'break_below', label: '从上跌破' },
  { value: 'break_above', label: '从下突破' },
  { value: 'enter_overbought', label: '进入超买区' },
  { value: 'enter_oversold', label: '进入超卖区' }
]

// Operators that require a numeric threshold
const THRESHOLD_VALUE_OPERATORS = ['>', '<', '>=', '<=', '==', 'enter_overbought', 'enter_oversold']

// Operators that require another indicator reference
const THRESHOLD_INDICATOR_OPERATORS = ['golden_cross', 'death_cross', 'break_above', 'break_below']

export default {
  name: 'ConditionRule',
  props: {
    rule: {
      type: Object,
      required: true
    }
  },
  emits: ['update:rule', 'remove'],
  setup(props, { emit }) {
    const backtestStore = useBacktestStore()

    const indicatorOptions = computed(() => {
      const customIndicators = backtestStore.indicators
        .filter(i => i.name)
        .map(i => ({ value: i.name, label: i.name }))
      return [...customIndicators, ...BASE_FIELDS]
    })

    const operatorOptions = OPERATOR_OPTIONS

    const showThresholdValue = computed(() => {
      return THRESHOLD_VALUE_OPERATORS.includes(props.rule.operator)
    })

    const showThresholdIndicator = computed(() => {
      return THRESHOLD_INDICATOR_OPERATORS.includes(props.rule.operator)
    })

    function updateRule(field, value) {
      const updated = { ...props.rule, [field]: value }
      // Clear irrelevant threshold when switching operator type
      if (field === 'operator') {
        if (THRESHOLD_VALUE_OPERATORS.includes(value)) {
          updated.threshold_indicator = null
        } else if (THRESHOLD_INDICATOR_OPERATORS.includes(value)) {
          updated.threshold = null
        }
      }
      emit('update:rule', updated)
    }

    return {
      indicatorOptions,
      operatorOptions,
      showThresholdValue,
      showThresholdIndicator,
      updateRule
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.condition-rule {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}

.rule-select {
  width: 130px;

  :deep(.el-input__wrapper) {
    background-color: $bg-primary;
    border-color: $border-color;
  }

  :deep(.el-input__inner) {
    color: $text-primary;
    font-size: 13px;
  }
}

.operator-select {
  width: 110px;

  :deep(.el-input__wrapper) {
    background-color: $bg-primary;
    border-color: $border-color;
  }

  :deep(.el-input__inner) {
    color: $text-primary;
    font-size: 13px;
  }
}

.threshold-input {
  width: 100px;

  :deep(.el-input__wrapper) {
    background-color: $bg-primary;
    border-color: $border-color;
  }

  :deep(.el-input__inner) {
    color: $text-primary;
    font-size: 13px;
  }
}
</style>
