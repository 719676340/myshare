<template>
  <div class="practice-view">
    <!-- Phase 1: Config -->
    <PracticeConfig v-if="!practiceStore.isConfigured" />

    <!-- Phase 2: Active Practice -->
    <div v-else-if="!practiceStore.isFinished" class="practice-main">
      <div class="practice-chart">
        <KLineChart :fixedData="practiceStore.dailyData" />
      </div>
      <div class="practice-sidebar">
        <PracticePanel />
      </div>
    </div>

    <!-- Phase 3: Statistics -->
    <PracticeStats
      v-else
      @newPractice="handleNewPractice"
    />
  </div>
</template>

<script>
import { onMounted, onBeforeUnmount } from 'vue'
import KLineChart from '@/components/KLineChart.vue'
import PracticeConfig from '@/components/practice/PracticeConfig.vue'
import PracticePanel from '@/components/practice/PracticePanel.vue'
import PracticeStats from '@/components/practice/PracticeStats.vue'
import { usePracticeStore } from '@/stores/practice'

export default {
  name: 'PracticeView',
  components: {
    KLineChart,
    PracticeConfig,
    PracticePanel,
    PracticeStats
  },
  setup() {
    const practiceStore = usePracticeStore()

    function handleKeydown(event) {
      if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.isContentEditable) {
        return
      }
      if (event.code === 'Space' && practiceStore.isConfigured && !practiceStore.isFinished && !practiceStore.isAdvancing) {
        event.preventDefault()
        practiceStore.advanceDay()
      }
    }

    function handleNewPractice() {
      practiceStore.resetPractice()
    }

    onMounted(() => {
      window.addEventListener('keydown', handleKeydown)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('keydown', handleKeydown)
    })

    return {
      practiceStore,
      handleNewPractice
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.practice-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: $bg-primary;
}

.practice-main {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.practice-chart {
  flex: 7;
  min-width: 0;
  height: 100%;
  overflow: hidden;
}

.practice-sidebar {
  flex: 3;
  min-width: 340px;
  max-width: 420px;
  height: 100%;
  overflow-y: auto;
  border-left: 1px solid $border-color;
  background-color: $bg-secondary;
}
</style>
