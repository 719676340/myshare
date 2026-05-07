<template>
  <div class="indicator-builder">
    <div class="indicator-row">
      <el-input
        :model-value="indicator.name"
        @update:model-value="updateField('name', $event)"
        placeholder="指标名称"
        class="name-input"
        size="small"
      />
      <el-input
        :model-value="indicator.expression"
        @update:model-value="updateField('expression', $event)"
        @blur="validate"
        placeholder="如 VOL/MA(VOL,20)"
        class="expr-input"
        size="small"
      />
      <el-icon
        v-if="indicator.valid === true"
        class="valid-icon valid-success"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M20 6L9 17l-5-5" />
        </svg>
      </el-icon>
      <el-icon
        v-else-if="indicator.valid === false"
        class="valid-icon valid-error"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M12 2a10 10 0 100 20 10 10 0 000-20zM15 9l-6 6M9 9l6 6" />
        </svg>
      </el-icon>
      <el-button
        type="danger"
        text
        size="small"
        @click="backtestStore.removeIndicator(index)"
      >
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </el-button>
    </div>
    <div v-if="indicator.valid === false && indicator.error" class="error-text">
      {{ indicator.error }}
    </div>
  </div>
</template>

<script>
import { useBacktestStore } from '@/stores/backtest'

export default {
  name: 'IndicatorBuilder',
  props: {
    index: {
      type: Number,
      required: true
    }
  },
  setup(props) {
    const backtestStore = useBacktestStore()

    const indicator = computed(() => backtestStore.indicators[props.index])

    function updateField(field, value) {
      backtestStore.updateIndicator(props.index, field, value)
    }

    function validate() {
      backtestStore.validateIndicator(props.index)
    }

    return {
      backtestStore,
      indicator,
      updateField,
      validate
    }
  }
}

import { computed } from 'vue'
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.indicator-builder {
  margin-bottom: 10px;
}

.indicator-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-input {
  width: 120px;
  flex-shrink: 0;

  :deep(.el-input__wrapper) {
    background-color: $bg-secondary;
    border-color: $border-color;
  }

  :deep(.el-input__inner) {
    color: $text-primary;
    font-size: 13px;

    &::placeholder {
      color: $text-secondary;
    }
  }
}

.expr-input {
  flex: 1;

  :deep(.el-input__wrapper) {
    background-color: $bg-secondary;
    border-color: $border-color;
  }

  :deep(.el-input__inner) {
    color: $text-primary;
    font-size: 13px;
    font-family: 'SF Mono', 'Menlo', monospace;

    &::placeholder {
      color: $text-secondary;
    }
  }
}

.valid-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.valid-success {
  color: #26a69a;
}

.valid-error {
  color: #ef5350;
}

.error-text {
  margin-top: 4px;
  padding-left: 128px;
  color: #ef5350;
  font-size: 12px;
}
</style>
