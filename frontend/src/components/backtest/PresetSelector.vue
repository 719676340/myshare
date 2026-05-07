<template>
  <div class="preset-selector">
    <div class="preset-title">预设策略模板</div>
    <div class="preset-cards">
      <div
        v-for="preset in backtestStore.presets"
        :key="preset.id"
        class="preset-card"
        :class="{ selected: selectedId === preset.id }"
        @click="selectPreset(preset)"
      >
        <div class="preset-name">{{ preset.name }}</div>
        <div class="preset-desc">{{ preset.description }}</div>
      </div>
      <div v-if="backtestStore.presets.length === 0" class="preset-empty">
        暂无预设策略
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useBacktestStore } from '@/stores/backtest'

export default {
  name: 'PresetSelector',
  setup() {
    const backtestStore = useBacktestStore()
    const selectedId = ref(null)

    onMounted(() => {
      backtestStore.loadPresets()
    })

    function selectPreset(preset) {
      selectedId.value = preset.id
      backtestStore.applyPreset(preset)
    }

    return {
      backtestStore,
      selectedId,
      selectPreset
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.preset-selector {
  margin-bottom: 16px;
}

.preset-title {
  color: $text-secondary;
  font-size: 13px;
  margin-bottom: 10px;
  font-weight: 500;
}

.preset-cards {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.preset-card {
  flex: 1;
  min-width: 160px;
  padding: 14px 16px;
  background-color: $bg-secondary;
  border: 2px solid $border-color;
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.2s;

  &:hover {
    border-color: $accent-blue;
  }

  &.selected {
    border-color: $accent-blue;
  }
}

.preset-name {
  color: $text-primary;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
}

.preset-desc {
  color: $text-secondary;
  font-size: 12px;
  line-height: 1.5;
}

.preset-empty {
  color: $text-secondary;
  font-size: 13px;
  padding: 16px 0;
}
</style>
