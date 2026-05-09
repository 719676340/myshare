<template>
  <div class="practice-history">
    <div class="history-header">
      <h2>练习记录</h2>
      <el-button size="small" @click="$emit('back')">← 返回新练习</el-button>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <el-input
        v-model="filterTsCode"
        placeholder="搜索股票代码"
        clearable
        style="width: 180px"
        @clear="loadHistory"
        @keyup.enter="loadHistory"
      />
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px" @change="loadHistory">
        <el-option label="已结束" value="finished" />
        <el-option label="进行中" value="active" />
      </el-select>
      <el-button type="primary" size="small" @click="loadHistory">搜索</el-button>
    </div>

    <!-- Table -->
    <el-table
      :data="practiceStore.historyList"
      v-loading="practiceStore.historyLoading"
      stripe
      style="width: 100%"
      @row-click="handleRowClick"
      class="history-table"
    >
      <el-table-column prop="stock_name" label="股票" min-width="100" />
      <el-table-column label="日期范围" min-width="160">
        <template #default="{ row }">
          {{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}
        </template>
      </el-table-column>
      <el-table-column label="收益率" width="100" align="right">
        <template #default="{ row }">
          <span :class="row.return_pct > 0 ? 'pnl-up' : row.return_pct < 0 ? 'pnl-down' : ''">
            {{ row.return_pct > 0 ? '+' : '' }}{{ row.return_pct.toFixed(2) }}%
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="trade_count" label="交易次数" width="90" align="center" />
      <el-table-column prop="status" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'finished' ? 'info' : 'success'" size="small">
            {{ row.status === 'finished' ? '已结束' : '进行中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="备注" min-width="140">
        <template #default="{ row }">
          <span class="notes-text">{{ row.notes || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="110">
        <template #default="{ row }">
          {{ row.created_at?.slice(0, 10) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'active'" link type="success" size="small" @click.stop="resumePractice(row)">
            继续练习
          </el-button>
          <el-button v-if="row.status === 'finished'" link type="primary" size="small" @click.stop="viewDetail(row)">
            复盘
          </el-button>
          <el-button link type="primary" size="small" @click.stop="editNotes(row)">
            备注
          </el-button>
          <el-button link type="danger" size="small" @click.stop="confirmDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-bar" v-if="practiceStore.historyTotal > pageSize">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="practiceStore.historyTotal"
        layout="prev, pager, next"
        @current-change="onPageChange"
      />
    </div>

    <!-- Notes dialog -->
    <el-dialog v-model="notesDialogVisible" title="编辑备注" width="460px">
      <el-input
        v-model="editingNotes"
        type="textarea"
        :rows="4"
        placeholder="写下你的交易心得..."
        maxlength="500"
        show-word-limit
      />
      <template #footer>
        <el-button @click="notesDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNotes">保存</el-button>
      </template>
    </el-dialog>

    <!-- Detail dialog -->
    <el-dialog v-model="detailVisible" :title="detailTitle" width="90%" top="3vh" class="detail-dialog" @close="onDetailClose">
      <div v-loading="detailLoading">
        <div v-if="detailStats" class="detail-content">
          <!-- K-line chart with buy/sell markers -->
          <div class="detail-chart" v-if="detailDailyData.length">
            <KLineChart :fixedData="detailDailyData" :buySellMarkers="detailMarkers" />
          </div>

          <!-- Metric cards -->
          <div class="detail-metrics">
            <div class="metric-card">
              <span class="metric-label">总收益率</span>
              <span class="metric-value" :class="detailStats.total_return_pct > 0 ? 'pnl-up' : 'pnl-down'">
                {{ detailStats.total_return_pct > 0 ? '+' : '' }}{{ detailStats.total_return_pct?.toFixed(2) }}%
              </span>
            </div>
            <div class="metric-card">
              <span class="metric-label">最终权益</span>
              <span class="metric-value">{{ formatMoney(detailStats.final_capital) }}</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">交易次数</span>
              <span class="metric-value">{{ detailStats.trade_count }}</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">胜率</span>
              <span class="metric-value">{{ detailStats.win_rate?.toFixed(1) }}%</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">总手续费</span>
              <span class="metric-value">{{ formatMoney(detailStats.total_fees) }}</span>
            </div>
          </div>

          <!-- Trade pairs table -->
          <div v-if="detailStats.trade_pairs?.length" class="detail-section">
            <h4>交易配对</h4>
            <el-table :data="detailStats.trade_pairs" size="small" stripe max-height="300">
              <el-table-column label="买入日期" prop="buy_date" width="100" />
              <el-table-column label="买入价" width="80" align="right">
                <template #default="{ row }">{{ row.buy_price?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column label="卖出日期" prop="sell_date" width="100" />
              <el-table-column label="卖出价" width="80" align="right">
                <template #default="{ row }">{{ row.sell_price?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column label="股数" prop="shares" width="70" align="right" />
              <el-table-column label="盈亏" width="100" align="right">
                <template #default="{ row }">
                  <span :class="row.profit > 0 ? 'pnl-up' : 'pnl-down'">
                    {{ row.profit > 0 ? '+' : '' }}{{ row.profit?.toFixed(2) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="持仓天数" prop="holding_days" width="80" align="center" />
            </el-table>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePracticeStore } from '@/stores/practice'
import { useChartStore } from '@/stores/chart'
import { getPracticeStats, getPracticeSession } from '@/api'
import KLineChart from '@/components/KLineChart.vue'

export default {
  name: 'PracticeHistory',
  emits: ['back', 'resumed'],
  components: { KLineChart },
  setup(props, { emit }) {
    const practiceStore = usePracticeStore()
    const chartStore = useChartStore()

    const filterTsCode = ref('')
    const filterStatus = ref('')
    const currentPage = ref(1)
    const pageSize = 20

    const notesDialogVisible = ref(false)
    const editingNotes = ref('')
    const editingSessionId = ref(null)

    const detailVisible = ref(false)
    const detailTitle = ref('')
    const detailStats = ref(null)
    const detailLoading = ref(false)
    const detailDailyData = ref([])
    const detailMarkers = computed(() => {
      if (!detailStats.value?.trade_pairs) return []
      const markers = []
      for (const pair of detailStats.value.trade_pairs) {
        markers.push({ date: pair.buy_date, type: 'buy', price: pair.buy_price })
        if (pair.sell_date) {
          markers.push({ date: pair.sell_date, type: 'sell', price: pair.sell_price })
        }
      }
      return markers
    })

    function formatDate(dateStr) {
      if (!dateStr || dateStr.length !== 8) return dateStr
      return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`
    }

    function formatMoney(n) {
      if (n == null || isNaN(n)) return '--'
      const abs = Math.abs(n)
      if (abs >= 10000) {
        return (n < 0 ? '-' : '') + (abs / 10000).toFixed(2) + '万'
      }
      return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    function loadHistory() {
      const params = { limit: pageSize, offset: (currentPage.value - 1) * pageSize }
      if (filterTsCode.value) params.ts_code = filterTsCode.value
      if (filterStatus.value) params.status = filterStatus.value
      practiceStore.fetchHistory(params)
    }

    function onPageChange(page) {
      currentPage.value = page
      loadHistory()
    }

    function editNotes(row) {
      editingSessionId.value = row.id
      editingNotes.value = row.notes || ''
      notesDialogVisible.value = true
    }

    async function saveNotes() {
      await practiceStore.updateNotes(editingSessionId.value, editingNotes.value)
      notesDialogVisible.value = false
      ElMessage.success('备注已保存')
    }

    function confirmDelete(row) {
      ElMessageBox.confirm(
        `确定删除 ${row.stock_name}（${formatDate(row.start_date)}）的练习记录？`,
        '删除确认',
        { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
      ).then(async () => {
        await practiceStore.deleteHistory(row.id)
        ElMessage.success('已删除')
      }).catch(() => {})
    }

    async function viewDetail(row) {
      detailTitle.value = `${row.stock_name} ${formatDate(row.start_date)} ~ ${formatDate(row.end_date)}`
      detailVisible.value = true
      detailLoading.value = true
      detailStats.value = null
      detailDailyData.value = []
      try {
        const [stats, sessionData] = await Promise.all([
          getPracticeStats(row.id),
          getPracticeSession(row.id)
        ])
        detailStats.value = stats
        detailDailyData.value = sessionData.daily_data || []
      } catch (err) {
        ElMessage.error('加载详情失败')
      } finally {
        detailLoading.value = false
      }
    }

    function onDetailClose() {
      detailDailyData.value = []
      detailStats.value = null
    }

    async function resumePractice(row) {
      try {
        await practiceStore.resumeSession(row.id)
        emit('resumed')
      } catch (err) {
        ElMessage.error('恢复练习失败: ' + (err.message || '未知错误'))
      }
    }

    function handleRowClick(row) {
      if (row.status === 'finished') {
        viewDetail(row)
      } else if (row.status === 'active') {
        resumePractice(row)
      }
    }

    onMounted(() => {
      loadHistory()
    })

    return {
      practiceStore,
      filterTsCode,
      filterStatus,
      currentPage,
      pageSize,
      notesDialogVisible,
      editingNotes,
      detailVisible,
      detailTitle,
      detailStats,
      detailLoading,
      detailDailyData,
      detailMarkers,
      formatDate,
      formatMoney,
      loadHistory,
      onPageChange,
      editNotes,
      saveNotes,
      confirmDelete,
      viewDetail,
      onDetailClose,
      handleRowClick,
      resumePractice
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.practice-history {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px 24px;
  background-color: $bg-primary;
  color: $text-primary;
  overflow-y: auto;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h2 {
    font-size: 18px;
    font-weight: 500;
    color: $text-primary;
  }
}

.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  align-items: center;
}

.history-table {
  flex: 1;

  :deep(.el-table) {
    background-color: $bg-secondary;
    color: $text-primary;
  }

  :deep(th.el-table__cell) {
    background-color: $bg-toolbar;
    color: $text-secondary;
  }

  :deep(tr) {
    background-color: $bg-secondary;
    cursor: pointer;

    &:hover > td.el-table__cell {
      background-color: $bg-toolbar;
    }
  }

  :deep(.el-table__empty-block) {
    background-color: $bg-secondary;
  }
}

.notes-text {
  color: $text-secondary;
  font-size: 12px;
}

.pnl-up {
  color: $color-up !important;
}

.pnl-down {
  color: $color-down !important;
}

.pagination-bar {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.detail-content {
  color: $text-primary;
}

.detail-chart {
  height: 400px;
  margin-bottom: 16px;
  border-radius: 6px;
  overflow: hidden;
}

.detail-metrics {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.metric-card {
  background-color: $bg-secondary;
  border-radius: 6px;
  padding: 12px 16px;
  min-width: 120px;
  display: flex;
  flex-direction: column;
  gap: 4px;

  .metric-label {
    color: $text-secondary;
    font-size: 12px;
  }

  .metric-value {
    font-size: 16px;
    font-weight: 600;
    font-family: 'SF Mono', 'Menlo', monospace;
  }
}

.detail-section {
  h4 {
    color: $text-secondary;
    font-size: 13px;
    margin-bottom: 10px;
  }
}
</style>
