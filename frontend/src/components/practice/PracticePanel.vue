<template>
  <div class="practice-panel">
    <!-- Zone 1: Account Info -->
    <div class="panel-section account-info">
      <h3 class="section-title">账户信息</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">可用资金</span>
          <span class="info-value">{{ formatMoney(practiceStore.availableCash) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">持仓市值</span>
          <span class="info-value">{{ formatMoney(practiceStore.totalMarketValue) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">总资产</span>
          <span class="info-value total">{{ formatMoney(practiceStore.totalAssets) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">浮动盈亏</span>
          <span class="info-value" :class="pnlClass">{{ formatPnl(practiceStore.totalPnl) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">盈亏比例</span>
          <span class="info-value" :class="pnlClass">{{ formatPct(practiceStore.totalPnlPct) }}</span>
        </div>
      </div>

      <!-- Progress -->
      <div class="progress-section">
        <div class="progress-text">
          进度：{{ practiceStore.session?.current_date }}（第{{ practiceStore.progress.current }}/{{ practiceStore.progress.total }}天）
        </div>
        <el-progress
          :percentage="practiceStore.progress.pct"
          :stroke-width="6"
          :show-text="false"
        />
      </div>
    </div>

    <!-- Zone 2: Trading Operations -->
    <div class="panel-section trading-ops">
      <h3 class="section-title">交易操作</h3>

      <!-- Day advancement -->
      <div class="advance-section">
        <el-button
          type="primary"
          size="large"
          :disabled="practiceStore.isFinished || practiceStore.isAdvancing"
          :loading="practiceStore.isAdvancing"
          @click="handleAdvance"
          style="width: 100%"
        >
          下一日 →
        </el-button>
        <div class="shortcut-hint">快捷键：空格键</div>
      </div>

      <!-- Buy/Sell tabs -->
      <el-tabs v-model="activeTab" class="trade-tabs">
        <el-tab-pane label="买入" name="buy">
          <div class="trade-form">
            <div class="position-presets">
              <div class="preset-label">仓位选择</div>
              <el-radio-group v-model="buyPreset" size="small" @change="onBuyPresetChange">
                <el-radio-button value="quarter">1/4仓</el-radio-button>
                <el-radio-button value="third">1/3仓</el-radio-button>
                <el-radio-button value="half">半仓</el-radio-button>
                <el-radio-button value="full">全仓</el-radio-button>
                <el-radio-button value="custom">自定义</el-radio-button>
              </el-radio-group>
            </div>
            <div class="trade-inputs">
              <div class="input-row">
                <label>收盘价</label>
                <span class="price-display">{{ getCurrentPrice().toFixed(2) }}</span>
              </div>
              <div class="input-row">
                <label>股数</label>
                <el-input-number
                  v-model="buyShares"
                  :min="100"
                  :step="100"
                  :max="99999900"
                  :disabled="buyPreset !== 'custom'"
                  style="width: 100%"
                />
              </div>
            </div>
            <div v-if="buyPreview" class="order-preview">
              <div>预估金额：{{ formatMoney(buyPreview.amount) }}</div>
              <div>佣金：{{ formatMoney(buyPreview.commission) }}（万2.5）</div>
              <div>合计：{{ formatMoney(buyPreview.total) }}</div>
            </div>
            <el-button
              type="success"
              :disabled="!canBuy || practiceStore.isTrading"
              :loading="practiceStore.isTrading"
              @click="handleBuy"
              style="width: 100%; margin-top: 12px"
            >
              确认买入
            </el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="卖出" name="sell">
          <div class="trade-form">
            <!-- Holdings list -->
            <div v-if="practiceStore.positions.length === 0" class="empty-positions">
              暂无持仓
            </div>
            <div v-else class="positions-list">
              <div
                v-for="pos in practiceStore.positions"
                :key="pos.id"
                class="position-item"
                :class="{ selected: selectedPosition?.id === pos.id }"
                @click="selectPosition(pos)"
              >
                <div class="pos-header">
                  <span>{{ pos.buy_date }} 买入</span>
                  <span>{{ pos.remaining_shares }} 股可卖</span>
                </div>
                <div class="pos-detail">
                  <span>成本 {{ pos.buy_price.toFixed(2) }}</span>
                  <span>现价 {{ getCurrentPrice().toFixed(2) }}</span>
                </div>
                <div class="pos-pnl" :class="getPositionPnlClass(pos)">
                  {{ formatPnl(pos.floating_pnl) }}（{{ formatPct(pos.floating_pnl_pct) }}）
                </div>
              </div>
            </div>
            <div v-if="selectedPosition" class="trade-inputs" style="margin-top: 12px">
              <div class="input-row">
                <label>收盘价</label>
                <span class="price-display">{{ getCurrentPrice().toFixed(2) }}</span>
              </div>
              <div class="input-row">
                <label>卖出股数</label>
                <el-input-number
                  v-model="sellShares"
                  :min="100"
                  :step="100"
                  :max="selectedPosition.remaining_shares"
                  style="width: 100%"
                />
              </div>
            </div>
            <div v-if="sellPreview" class="order-preview">
              <div>预估金额：{{ formatMoney(sellPreview.amount) }}</div>
              <div>佣金：{{ formatMoney(sellPreview.commission) }}（万2.5）</div>
              <div>印花税：{{ formatMoney(sellPreview.stampTax) }}（千1）</div>
              <div>到账：{{ formatMoney(sellPreview.net) }}</div>
            </div>
            <el-button
              type="danger"
              :disabled="!canSell || practiceStore.isTrading"
              :loading="practiceStore.isTrading"
              @click="handleSell"
              style="width: 100%; margin-top: 12px"
            >
              确认卖出
            </el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Zone 3: Trade History -->
    <div class="panel-section trade-history">
      <h3 class="section-title">交易记录</h3>
      <div class="trade-list">
        <div v-if="practiceStore.trades.length === 0" class="empty-text">
          暂无交易
        </div>
        <div
          v-for="trade in practiceStore.trades.slice().reverse()"
          :key="trade.id"
          class="trade-item"
          :class="trade.trade_type"
        >
          <span class="trade-date">{{ trade.trade_date }}</span>
          <span class="trade-type">{{ trade.trade_type === 'buy' ? '买入' : '卖出' }}</span>
          <span class="trade-shares">{{ trade.shares }}股</span>
          <span class="trade-price">{{ trade.price.toFixed(2) }}</span>
          <span class="trade-amount">{{ formatMoney(trade.amount) }}</span>
        </div>
      </div>
    </div>

    <!-- End Practice Button -->
    <div v-if="practiceStore.isConfigured && !practiceStore.isFinished" class="end-section">
      <div class="end-buttons">
        <el-button
          type="primary"
          size="small"
          @click="handleNewPractice"
        >
          新建练习
        </el-button>
        <el-button
          type="warning"
          size="small"
          @click="handleEndPractice"
        >
          结束练习
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePracticeStore } from '@/stores/practice'

export default {
  name: 'PracticePanel',
  setup() {
    const practiceStore = usePracticeStore()

    const activeTab = ref('buy')
    const buyPreset = ref('half')
    const buyShares = ref(0)
    const sellShares = ref(100)
    const selectedPosition = ref(null)

    // Get current price from last visible bar (close price)
    function getCurrentPrice() {
      const data = practiceStore.dailyData
      if (data.length === 0) return 0
      return data[data.length - 1].close
    }

    // Format money: >= 10000 show "X.XX万", else locale string
    function formatMoney(n) {
      if (n == null || isNaN(n)) return '--'
      const abs = Math.abs(n)
      if (abs >= 10000) {
        return (n < 0 ? '-' : '') + (abs / 10000).toFixed(2) + '万'
      }
      return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    // Format P&L with +/- prefix
    function formatPnl(n) {
      if (n == null || isNaN(n)) return '--'
      const prefix = n > 0 ? '+' : ''
      const abs = Math.abs(n)
      if (abs >= 10000) {
        return prefix + (n / 10000).toFixed(2) + '万'
      }
      return prefix + n.toFixed(2)
    }

    // Format percentage
    function formatPct(n) {
      if (n == null || isNaN(n)) return '--'
      const prefix = n > 0 ? '+' : ''
      return prefix + n.toFixed(2) + '%'
    }

    // P&L CSS class (A-share: red=up, green=down)
    const pnlClass = computed(() => {
      const pnl = practiceStore.totalPnl
      if (pnl > 0) return 'pnl-up'
      if (pnl < 0) return 'pnl-down'
      return ''
    })

    // Buy position presets
    function onBuyPresetChange(val) {
      if (val === 'custom') return
      const currentPrice = getCurrentPrice()
      if (!currentPrice) return

      const fractions = {
        quarter: 0.25,
        third: 1 / 3,
        half: 0.5,
        full: 1
      }
      const fraction = fractions[val] || 1
      const availableCash = practiceStore.availableCash
      // Round down to lot size 100
      buyShares.value = Math.floor(availableCash * fraction / currentPrice / 100) * 100
    }

    // Buy preview computation (uses current close price)
    const buyPreview = computed(() => {
      const price = getCurrentPrice()
      if (!buyShares.value || !price) return null
      const amount = buyShares.value * price
      const commission = Math.round(amount * 0.00025 * 100) / 100
      const total = amount + commission
      return { amount, commission, total }
    })

    // Sell preview computation (uses current close price)
    const sellPreview = computed(() => {
      const price = getCurrentPrice()
      if (!sellShares.value || !price) return null
      const amount = sellShares.value * price
      const commission = Math.round(amount * 0.00025 * 100) / 100
      const stampTax = Math.round(amount * 0.001 * 100) / 100
      const net = amount - commission - stampTax
      return { amount, commission, stampTax, net }
    })

    // Buy validation
    const canBuy = computed(() => {
      return buyShares.value > 0 && getCurrentPrice() > 0
    })

    // Sell validation
    const canSell = computed(() => {
      return selectedPosition.value && sellShares.value > 0 && getCurrentPrice() > 0
    })

    // Position P&L class
    function getPositionPnlClass(pos) {
      if (pos.floating_pnl > 0) return 'pnl-up'
      if (pos.floating_pnl < 0) return 'pnl-down'
      return ''
    }

    // Select position for selling
    function selectPosition(pos) {
      selectedPosition.value = pos
      sellShares.value = pos.remaining_shares
    }

    // Handle advance day
    async function handleAdvance() {
      try {
        await practiceStore.advanceDay()
        // Recalculate preset shares with new close price
        if (buyPreset.value !== 'custom') {
          onBuyPresetChange(buyPreset.value)
        }
      } catch (err) {
        ElMessage.error(err.message || '推进日期失败')
      }
    }

    // Handle buy
    async function handleBuy() {
      try {
        const result = await practiceStore.buyOrder(buyShares.value)
        ElMessage.success(result.message || '买入成功')
        // Recalculate preset after cash change
        if (buyPreset.value !== 'custom') {
          onBuyPresetChange(buyPreset.value)
        }
      } catch (err) {
        ElMessage.error(err.message || '买入失败')
      }
    }

    // Handle sell
    async function handleSell() {
      if (!selectedPosition.value) return
      try {
        const result = await practiceStore.sellOrder(
          selectedPosition.value.id,
          sellShares.value
        )
        ElMessage.success(result.message || '卖出成功')
        selectedPosition.value = null
      } catch (err) {
        ElMessage.error(err.message || '卖出失败')
      }
    }

    // Handle new practice (keep session in activeSessions, just clear display state)
    function handleNewPractice() {
      practiceStore.session = null
      practiceStore.stats = null
    }

    // Handle end practice
    async function handleEndPractice() {
      try {
        await ElMessageBox.confirm(
          '确定结束练习？结束后将无法继续操作。',
          '结束练习',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await practiceStore.endSession()
        ElMessage.success('练习已结束，查看统计结果')
      } catch (err) {
        // User cancelled or error
        if (err !== 'cancel') {
          ElMessage.error(err.message || '结束练习失败')
        }
      }
    }

    // Spacebar shortcut for advancing day
    function handleKeydown(e) {
      if (e.code === 'Space' && !e.target.matches('input, textarea, select, .el-input__inner')) {
        e.preventDefault()
        if (!practiceStore.isFinished && !practiceStore.isAdvancing) {
          handleAdvance()
        }
      }
    }

    onMounted(() => {
      window.addEventListener('keydown', handleKeydown)
      // Initialize shares from preset
      onBuyPresetChange(buyPreset.value)
    })

    onUnmounted(() => {
      window.removeEventListener('keydown', handleKeydown)
    })

    return {
      practiceStore,
      activeTab,
      buyPreset,
      buyShares,
      sellShares,
      selectedPosition,
      pnlClass,
      buyPreview,
      sellPreview,
      canBuy,
      canSell,
      getCurrentPrice,
      formatMoney,
      formatPnl,
      formatPct,
      getPositionPnlClass,
      selectPosition,
      onBuyPresetChange,
      handleAdvance,
      handleBuy,
      handleSell,
      handleNewPractice,
      handleEndPractice
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.practice-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: $bg-secondary;
  border-left: 1px solid $border-color;
  overflow-y: auto;
}

.panel-section {
  padding: 12px 16px;
  border-bottom: 1px solid $border-color;

  .section-title {
    color: $text-secondary;
    font-size: 12px;
    font-weight: 500;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
}

// Zone 1: Account Info
.account-info {
  .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 12px;
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: 2px;

    .info-label {
      color: $text-secondary;
      font-size: 11px;
    }

    .info-value {
      color: $text-primary;
      font-size: 14px;
      font-family: 'SF Mono', 'Menlo', monospace;

      &.total {
        color: $accent-blue;
        font-weight: 600;
      }
    }
  }

  .pnl-up {
    color: $color-up !important; // A-share red = profit
  }

  .pnl-down {
    color: $color-down !important; // A-share green = loss
  }

  .progress-section {
    margin-top: 10px;

    .progress-text {
      color: $text-secondary;
      font-size: 12px;
      margin-bottom: 6px;
    }
  }
}

// Zone 2: Trading Operations
.trading-ops {
  .advance-section {
    margin-bottom: 12px;

    .shortcut-hint {
      color: $text-secondary;
      font-size: 11px;
      margin-top: 6px;
      text-align: center;
      opacity: 0.7;
    }
  }

  .position-presets {
    margin-bottom: 12px;

    .preset-label {
      color: $text-secondary;
      font-size: 12px;
      margin-bottom: 6px;
    }

    :deep(.el-radio-group) {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
  }

  .trade-inputs {
    .input-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;

      label {
        color: $text-secondary;
        font-size: 12px;
        min-width: 60px;
        flex-shrink: 0;
      }

      .price-display {
        color: $text-primary;
        font-family: 'SF Mono', 'Menlo', monospace;
        font-size: 14px;
        font-weight: 600;
      }
    }
  }

  .order-preview {
    background-color: $bg-primary;
    border-radius: 4px;
    padding: 8px 12px;
    margin-top: 8px;
    font-size: 12px;
    color: $text-secondary;
    line-height: 1.8;
  }

  .empty-positions {
    color: $text-secondary;
    font-size: 13px;
    text-align: center;
    padding: 16px 0;
    opacity: 0.7;
  }

  .positions-list {
    max-height: 180px;
    overflow-y: auto;
  }

  .position-item {
    background-color: $bg-primary;
    border-radius: 4px;
    padding: 8px 12px;
    margin-bottom: 4px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: border-color 0.2s;

    &:hover {
      border-color: $border-color;
    }

    &.selected {
      border-color: $accent-blue;
    }

    .pos-header {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: $text-primary;
      margin-bottom: 4px;
    }

    .pos-detail {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: $text-secondary;
      margin-bottom: 2px;
    }

    .pos-pnl {
      font-size: 12px;
      font-family: 'SF Mono', 'Menlo', monospace;

      &.pnl-up {
        color: $color-up;
      }

      &.pnl-down {
        color: $color-down;
      }
    }
  }
}

// Zone 3: Trade History
.trade-history {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  .trade-list {
    flex: 1;
    overflow-y: auto;
    max-height: 200px;
  }

  .empty-text {
    color: $text-secondary;
    font-size: 13px;
    text-align: center;
    padding: 16px 0;
    opacity: 0.7;
  }

  .trade-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    font-size: 12px;
    border-bottom: 1px solid rgba($border-color, 0.3);

    &.buy .trade-type {
      color: $color-up;
    }

    &.sell .trade-type {
      color: $color-down;
    }

    .trade-date {
      color: $text-secondary;
      min-width: 70px;
    }

    .trade-type {
      min-width: 28px;
      font-weight: 500;
    }

    .trade-shares {
      color: $text-primary;
      min-width: 50px;
    }

    .trade-price {
      color: $text-primary;
      font-family: 'SF Mono', 'Menlo', monospace;
      min-width: 55px;
    }

    .trade-amount {
      color: $text-secondary;
      margin-left: auto;
      font-size: 11px;
    }
  }
}

// End Practice
.end-section {
  padding: 8px 16px 12px;

  .end-buttons {
    display: flex;
    gap: 8px;

    .el-button {
      flex: 1;
    }
  }
}

// Tabs styling
.trade-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 12px;
  }

  :deep(.el-tabs__item) {
    color: $text-secondary;
    font-size: 13px;

    &.is-active {
      color: $text-primary;
    }
  }
}
</style>
