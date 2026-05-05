<template>
  <div class="placeholder-view">
    <div class="placeholder-content">
      <h2>自动回测模块开发中</h2>
      <p>选择策略模板，设置参数，自动运行回测并输出收益分析报告</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BacktestView'
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
