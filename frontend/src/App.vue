<template>
  <div class="app-container">
    <nav class="nav-bar">
      <div class="nav-left">
        <span class="app-title">量价交易学习</span>
      </div>
      <div class="nav-right">
        <router-link to="/strategy" class="nav-link" active-class="active">
          策略分析
        </router-link>
        <router-link to="/practice" class="nav-link" active-class="active">
          交易练习
        </router-link>
        <router-link to="/backtest" class="nav-link" active-class="active">
          自动回测
        </router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style lang="scss">
@use './styles/variables' as *;

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.nav-bar {
  height: $nav-height;
  background-color: $bg-toolbar;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid $border-color;
  flex-shrink: 0;
}

.nav-left {
  display: flex;
  align-items: center;
}

.app-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
  letter-spacing: 1px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link {
  color: $text-secondary;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  transition: color 0.2s, background-color 0.2s;

  &:hover {
    color: $text-primary;
    background-color: rgba(255, 255, 255, 0.05);
  }

  &.active {
    color: $accent-blue;
    background-color: rgba($accent-blue, 0.1);
  }
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style>
