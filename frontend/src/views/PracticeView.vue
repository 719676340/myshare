<template>
  <div class="placeholder-view">
    <div class="placeholder-content">
      <h2>交易练习模块开发中</h2>
      <p>选股后逐日推进K线，模拟买入卖出操作，练习量价分析技巧</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PracticeView'
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.placeholder-view {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: $bg-primary;
}

.placeholder-content {
  text-align: center;

  h2 {
    color: $text-secondary;
    font-size: 20px;
    font-weight: 500;
    margin-bottom: 12px;
  }

  p {
    color: $text-secondary;
    font-size: 14px;
    opacity: 0.7;
  }
}
</style>
