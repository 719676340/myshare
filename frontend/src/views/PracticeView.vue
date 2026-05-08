<template>
  <div class="practice-view">
    <!-- Phase 0: History (shown when user clicks history) -->
    <PracticeHistory
      v-if="showHistory && !practiceStore.isConfigured"
      @back="showHistory = false"
      @resumed="showHistory = false"
    />

    <template v-else>
      <!-- Restoring session -->
      <div v-if="isRestoring" class="practice-restoring">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <span>正在恢复练习会话...</span>
      </div>

      <template v-else>
        <!-- Session tab bar (visible in config + active phases when sessions exist) -->
        <div
          v-if="practiceStore.activeSessions.length > 0 && !practiceStore.isFinished"
          class="session-tabs"
        >
          <div
            v-for="s in practiceStore.activeSessions"
            :key="s.id"
            class="session-tab"
            :class="{ active: s.id === practiceStore.session?.id }"
            @click="handleSwitchSession(s.id)"
          >
            <span class="tab-name">{{ s.stock_name || s.ts_code }}</span>
            <span class="tab-pnl" :class="s.total_pnl_pct > 0 ? 'pnl-up' : s.total_pnl_pct < 0 ? 'pnl-down' : ''">
              {{ s.total_pnl_pct > 0 ? '+' : '' }}{{ (s.total_pnl_pct || 0).toFixed(1) }}%
            </span>
          </div>
          <div class="session-tab session-tab-new" @click="goToNewPractice">
            +新建
          </div>
        </div>

        <!-- Phase 1: Config -->
        <div v-if="!practiceStore.isConfigured" class="practice-landing">
          <PracticeConfig />
          <div class="history-entry">
            <el-button size="large" @click="showHistory = true">
              历史记录
            </el-button>
          </div>
        </div>

        <!-- Phase 2: Active Practice -->
        <div v-else-if="!practiceStore.isFinished" class="practice-main">
          <div class="practice-chart">
            <div class="practice-toolbar">
              <el-button
                size="small"
                :type="chartStore.showMACD ? 'primary' : 'default'"
                @click="togglePracticeIndicator('showMACD')"
              >MACD</el-button>
              <el-button
                size="small"
                :type="chartStore.showRSI ? 'primary' : 'default'"
                @click="togglePracticeIndicator('showRSI')"
              >RSI</el-button>
              <el-button
                size="small"
                :type="chartStore.showKDJ ? 'primary' : 'default'"
                @click="togglePracticeIndicator('showKDJ')"
              >KDJ</el-button>
              <el-button
                size="small"
                :type="chartStore.showBOLL ? 'primary' : 'default'"
                @click="togglePracticeIndicator('showBOLL')"
              >BOLL</el-button>
              <div class="toolbar-divider"></div>
              <el-button
                v-for="(tw, idx) in TIME_WINDOWS"
                :key="tw.label"
                size="small"
                :type="activeTimeWindow === idx ? 'primary' : 'default'"
                @click="handleTimeWindow(tw.bars, idx)"
              >{{ tw.label }}</el-button>
            </div>
            <KLineChart ref="klineChartRef" :fixedData="practiceStore.dailyData" :buySellMarkers="buySellMarkers" />
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
      </template>
    </template>
  </div>
</template>

<script>
import { onMounted, onBeforeUnmount, watch, ref, computed } from 'vue'
import KLineChart from '@/components/KLineChart.vue'
import PracticeConfig from '@/components/practice/PracticeConfig.vue'
import PracticePanel from '@/components/practice/PracticePanel.vue'
import PracticeStats from '@/components/practice/PracticeStats.vue'
import PracticeHistory from '@/components/practice/PracticeHistory.vue'
import { Loading } from '@element-plus/icons-vue'
import { usePracticeStore } from '@/stores/practice'
import { useChartStore } from '@/stores/chart'

const indicatorMap = {
  showMACD: 'macd',
  showRSI: 'rsi',
  showKDJ: 'kdj',
  showBOLL: 'boll'
}

export default {
  name: 'PracticeView',
  components: {
    KLineChart,
    PracticeConfig,
    PracticePanel,
    PracticeStats,
    PracticeHistory,
    Loading
  },
  setup() {
    const practiceStore = usePracticeStore()
    const chartStore = useChartStore()
    const showHistory = ref(false)
    const klineChartRef = ref(null)
    const activeTimeWindow = ref(null)
    const isRestoring = ref(false)

    const TIME_WINDOWS = [
      { label: '1月', bars: 22 },
      { label: '3月', bars: 66 },
      { label: '6月', bars: 132 },
      { label: '1年', bars: 250 },
      { label: '全部', bars: Infinity }
    ]

    // Convert practice trades to buy/sell markers for KLineChart
    const buySellMarkers = computed(() => {
      return practiceStore.trades.map((t) => ({
        date: t.trade_date,
        type: t.trade_type, // 'buy' or 'sell'
        price: t.price
      }))
    })

    function handleTimeWindow(bars, index) {
      activeTimeWindow.value = index
      klineChartRef.value?.zoomToRange(bars)
    }

    function handleKeydown(event) {
      if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.isContentEditable) {
        return
      }
      if (event.code === 'Space' && practiceStore.isConfigured && !practiceStore.isFinished && !practiceStore.isAdvancing) {
        event.preventDefault()
        practiceStore.advanceDay()
      }
    }

    function goToNewPractice() {
      // Navigate to config without removing session from active list
      // Setting session to null makes isConfigured false -> shows PracticeConfig
      // activeSessions is preserved so tab bar still shows existing sessions
      practiceStore.session = null
      practiceStore.stats = null
    }

    function handleNewPractice() {
      practiceStore.resetPractice()
      practiceStore.fetchActiveSessions()
    }

    async function handleSwitchSession(sessionId) {
      try {
        await practiceStore.switchSession(sessionId)
        practiceStore.fetchAllEnabledIndicators(chartStore)
      } catch (err) {
        console.error('Failed to switch session:', err)
      }
    }

    function togglePracticeIndicator(name) {
      chartStore.toggleIndicator(name)
      if (chartStore[name]) {
        const indicator = indicatorMap[name]
        if (indicator) {
          practiceStore.fetchIndicatorDataForPractice(indicator, chartStore.indicatorParams[indicator])
        }
      }
    }

    // When practice session starts, fetch all enabled indicators
    watch(() => practiceStore.isConfigured, (configured) => {
      if (configured && !practiceStore.isFinished) {
        practiceStore.fetchAllEnabledIndicators(chartStore)
        practiceStore.fetchActiveSessions()
      }
    })

    // Auto-switch to another active session when current one is finished
    watch(() => practiceStore.isFinished, (finished) => {
      if (finished && practiceStore.activeSessions.length > 0) {
        practiceStore.switchSession(practiceStore.activeSessions[0].id)
        practiceStore.fetchAllEnabledIndicators(chartStore)
      }
    })

    onMounted(async () => {
      // Try to restore any active practice session
      if (!practiceStore.isConfigured) {
        isRestoring.value = true
        try {
          await practiceStore.tryRestoreSession()
        } catch (e) {
          console.error('Failed to restore practice session:', e)
        } finally {
          isRestoring.value = false
        }
      }
      // Fetch active sessions list for the switcher
      practiceStore.fetchActiveSessions()
      window.addEventListener('keydown', handleKeydown)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('keydown', handleKeydown)
    })

    return {
      practiceStore,
      chartStore,
      showHistory,
      isRestoring,
      goToNewPractice,
      handleNewPractice,
      handleSwitchSession,
      togglePracticeIndicator,
      klineChartRef,
      activeTimeWindow,
      TIME_WINDOWS,
      handleTimeWindow,
      buySellMarkers
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

.practice-landing {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.history-entry {
  margin-top: 8px;
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
  display: flex;
  flex-direction: column;
}

.practice-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background-color: $bg-secondary;
  border-bottom: 1px solid $border-color;
  flex-shrink: 0;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background-color: $border-color;
  margin: 0 4px;
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

.practice-restoring {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: $text-secondary;
}

.session-tabs {
  display: flex;
  align-items: center;
  padding: 0 10px;
  background-color: $bg-toolbar;
  border-bottom: 1px solid $border-color;
  flex-shrink: 0;
  overflow-x: auto;
  gap: 2px;

  .session-tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    font-size: 13px;
    color: $text-secondary;
    transition: color 0.2s, border-color 0.2s;

    &:hover {
      color: $text-primary;
    }

    &.active {
      color: $text-primary;
      border-bottom-color: $accent-blue;
    }

    .tab-name {
      font-weight: 500;
    }

    .tab-pnl {
      font-size: 11px;
      font-family: 'SF Mono', 'Menlo', monospace;
    }

    .pnl-up { color: $color-up; }
    .pnl-down { color: $color-down; }
  }

  .session-tab-new {
    color: $text-secondary;
    font-size: 12px;
    padding: 6px 12px;
    cursor: pointer;
    border-left: 1px solid $border-color;
    margin-left: 4px;

    &:hover {
      color: $accent-blue;
    }
  }
}
</style>
