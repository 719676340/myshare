<template>
  <div class="stock-search">
    <el-autocomplete
      v-model="searchText"
      :fetch-suggestions="handleSearch"
      placeholder="搜索股票代码或名称"
      :trigger-on-focus="false"
      :debounce="300"
      clearable
      size="default"
      @select="handleSelect"
    >
      <template #default="{ item }">
        <div class="suggestion-item">
          <span class="stock-code">{{ item.ts_code }}</span>
          <span class="stock-name">{{ item.name }}</span>
        </div>
      </template>
      <template #prefix>
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-4.35-4.35" />
        </svg>
      </template>
    </el-autocomplete>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useStockStore } from '@/stores/stock'

export default {
  name: 'StockSearch',
  emits: ['select'],
  setup(props, { emit }) {
    const stockStore = useStockStore()
    const searchText = ref('')

    let searchTimer = null

    async function handleSearch(query, cb) {
      if (!query || query.trim().length === 0) {
        cb([])
        return
      }

      // Additional debounce beyond el-autocomplete's built-in debounce
      clearTimeout(searchTimer)
      searchTimer = setTimeout(async () => {
        try {
          const results = await stockStore.searchStocks(query)
          const suggestions = results.map((item) => ({
            value: item.ts_code,
            ts_code: item.ts_code,
            name: item.name
          }))
          cb(suggestions)
        } catch (err) {
          cb([])
        }
      }, 300)
    }

    function handleSelect(item) {
      stockStore.selectStock(item.ts_code, item.name)
      emit('select', { ts_code: item.ts_code, name: item.name })
      searchText.value = ''
    }

    return {
      searchText,
      handleSearch,
      handleSelect
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.stock-search {
  width: 300px;

  :deep(.el-input__wrapper) {
    background-color: $bg-secondary;
    border-radius: 4px;
  }

  :deep(.el-input__inner) {
    color: $text-primary;
    font-size: 13px;

    &::placeholder {
      color: $text-secondary;
    }
  }

  :deep(.el-input__prefix) {
    color: $text-secondary;
  }

  :deep(.el-input__clear) {
    color: $text-secondary;
  }
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;

  .stock-code {
    color: $text-primary;
    font-size: 13px;
    font-family: 'SF Mono', 'Menlo', monospace;
    min-width: 90px;
  }

  .stock-name {
    color: $text-secondary;
    font-size: 13px;
  }
}
</style>
