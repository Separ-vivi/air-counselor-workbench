<template>
  <el-row :gutter="16" style="margin-bottom: 16px">
    <el-col :span="6" v-for="stat in statCards" :key="stat.label">
      <el-card shadow="hover" class="stat-card" :body-style="{ padding: '20px' }"
        :style="{ '--stat-accent': stat.color, '--stat-color': stat.color }">
        <div class="stat-icon" :style="{ background: stat.bg, color: stat.color }"><el-icon :size="28"><component :is="stat.icon" /></el-icon></div>
        <div class="stat-body">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ stat.value }}</div>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
defineProps({
  statCards: { type: Array, required: true }
})
</script>

<style scoped>
.dashboard-stat :deep(.el-row) { display: flex; flex-wrap: wrap; }
.dashboard-stat :deep(.el-col) { display: flex; }
.dashboard-stat :deep(.el-col > .el-card) {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg) !important;
  background: linear-gradient(180deg, #FFFFFF 0%, #F3F8FE 100%) !important;
  border: 1px solid rgba(200, 215, 235, 0.55) !important;
  box-shadow:
    0 2px 10px rgba(90, 130, 180, 0.06),
    0 6px 22px rgba(90, 130, 180, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}
.dashboard-stat :deep(.el-col > .el-card:hover) {
  transform: translateY(-2px);
  box-shadow:
    0 4px 14px rgba(90, 130, 180, 0.12),
    0 12px 28px rgba(90, 130, 180, 0.10);
  border-color: rgba(160, 195, 225, 0.75) !important;
}
.dashboard-stat :deep(.el-col > .el-card > .el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.stat-card {
  border-radius: var(--radius-lg);
  border: none;
  position: relative;
  overflow: hidden;
}
.stat-card::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 12%;
  right: 12%;
  height: 4px;
  border-radius: 4px 4px 0 0;
  background: var(--stat-accent, var(--color-primary));
  opacity: 0.7;
  transition: opacity 0.2s;
}
.stat-card:hover::after { opacity: 1; }
.stat-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
  padding: 20px 12px 24px !important;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .25s cubic-bezier(.4,0,.2,1), box-shadow .25s;
  box-shadow: 0 2px 8px var(--color-primary-light);
}
.stat-card:hover .stat-icon {
  transform: scale(1.08);
  box-shadow: var(--shadow-md);
}
.stat-body { text-align: center; width: 100%; }
.stat-body .stat-label {
  color: #7B8B9C;
  font-size: 13px;
  text-align: center;
  font-weight: 500;
  letter-spacing: 0.3px;
}
.stat-body .stat-value {
  font-size: 28px;
  font-weight: 800;
  margin-top: 4px;
  text-align: center;
  letter-spacing: 0.5px;
  font-family: -apple-system, 'SF Pro Display', 'PingFang SC', sans-serif;
  color: var(--stat-color, #1E3A56);
}
</style>
