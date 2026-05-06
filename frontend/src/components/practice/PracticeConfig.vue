<template>
  <div class="practice-config">
    <div class="config-card">
      <h2>交易练习设置</h2>
      <p class="config-desc">选择股票和时间范围，开始逐日模拟交易练习</p>

      <!-- Step 1: Stock Selection -->
      <div class="config-section">
        <div class="section-label">1. 选择股票</div>
        <StockSearch />
        <div v-if="stockStore.currentStock" class="selected-stock">
          <el-tag type="info" size="large">{{ stockStore.currentStockCode }} {{ stockStore.currentStockName }}</el-tag>
        </div>
      </div>

      <!-- Step 2: Date Range -->
      <div class="config-section">
        <div class="section-label">2. 选择练习时间范围</div>
        <div class="date-range">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="起始日期"
            end-placeholder="结束日期"
            format="YYYYMMDD"
            value-format="YYYYMMDD"
            :disabled-date="disabledDate"
          />
        </div>
      </div>

      <!-- Step 3: Initial Capital -->
      <div class="config-section">
        <div class="section-label">3. 初始资金</div>
        <el-input-number
          v-model="initialCapital"
          :min="10000"
          :max="100000000"
          :step="10000"
          :precision="0"
          :controls="true"
          style="width: 280px"
        />
        <span class="capital-hint">{{ formattedCapital }}</span>
      </div>

      <!-- Start Button -->
      <div class="config-actions">
        <el-button
          type="primary"
          size="large"
          :disabled="!canStart"
          :loading="practiceStore.isLoading"
          @click="startPractice"
        >
          开始练习
        </el-button>
        <div v-if="!canStart && stockStore.currentStock" class="start-hint">
          请选择练习时间范围
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import StockSearch from '@/components/StockSearch.vue'
import { useStockStore } from '@/stores/stock'
import { usePracticeStore } from '@/stores/practice'

export default {
  name: 'PracticeConfig',
  components: { StockSearch },
  setup() {
    const router = useRouter()
    const stockStore = useStockStore()
    const practiceStore = usePracticeStore()

    const dateRange = ref(null)
    const initialCapital = ref(1000000)

    const formattedCapital = computed(() => {
      if (initialCapital.value >= 10000) {
        return (initialCapital.value / 10000).toFixed(0) + '万'
      }
      return initialCapital.value.toLocaleString() + '元'
    })

    const canStart = computed(() => {
      return stockStore.currentStock && dateRange.value && dateRange.value.length === 2
    })

    const disabledDate = (time) => {
      // Disable future dates and dates before 2000
      return time.getTime() > Date.now() || time.getTime() < new Date('2000-01-01').getTime()
    }

    async function startPractice() {
      if (!canStart.value) return
      const [startDate, endDate] = dateRange.value
      try {
        await practiceStore.createSession(
          stockStore.currentStockCode,
          startDate,
          endDate,
          initialCapital.value
        )
        ElMessage.success('练习会话已创建')
      } catch (err) {
        ElMessage.error(err.message || '创建练习失败')
      }
    }

    return {
      dateRange,
      initialCapital,
      formattedCapital,
      canStart,
      disabledDate,
      startPractice,
      stockStore,
      practiceStore
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.practice-config {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: $bg-primary;
}

.config-card {
  width: 520px;
  padding: 40px;
  background-color: $bg-secondary;
  border-radius: 8px;
  border: 1px solid $border-color;

  h2 {
    color: $text-primary;
    font-size: 22px;
    margin-bottom: 8px;
  }

  .config-desc {
    color: $text-secondary;
    font-size: 14px;
    margin-bottom: 32px;
  }
}

.config-section {
  margin-bottom: 24px;

  .section-label {
    color: $text-secondary;
    font-size: 13px;
    margin-bottom: 10px;
    font-weight: 500;
  }
}

.selected-stock {
  margin-top: 10px;
}

.date-range {
  :deep(.el-date-editor) {
    width: 100%;
  }
}

.capital-hint {
  margin-left: 12px;
  color: $text-secondary;
  font-size: 13px;
}

.config-actions {
  margin-top: 32px;
  text-align: center;

  .start-hint {
    margin-top: 10px;
    color: $text-secondary;
    font-size: 12px;
  }
}
</style>
