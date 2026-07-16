<template>
  <aside class="sidebar-root">
    <div class="brand">
      <span class="brand-emoji">🎓</span>
      <span class="brand-text">辅导员工作平台</span>
      <span class="brand-ver">V3-A</span>
    </div>

    <el-menu
      class="side-menu"
      :default-active="$route.path"
      router
      background-color="transparent"
      text-color="#EAF3F7"
      active-text-color="#F5F7F9"
    >
      <el-menu-item index="/dashboard"><el-icon><DataBoard /></el-icon><span>驾驶舱</span></el-menu-item>
      <el-menu-item index="/students"><el-icon><User /></el-icon><span>学生管理</span></el-menu-item>
      <el-menu-item index="/classes"><el-icon><OfficeBuilding /></el-icon><span>班级管理</span></el-menu-item>
      <el-menu-item index="/org"><el-icon><Grid /></el-icon><span>三级架构</span></el-menu-item>
      <el-menu-item index="/smart-import"><el-icon><Upload /></el-icon><span>智能导入</span></el-menu-item>

      <el-sub-menu index="modules">
        <template #title><el-icon><Menu /></el-icon><span>业务模块</span></template>
        <el-menu-item index="/module/grades">📊 成绩</el-menu-item>
        <el-menu-item index="/module/warnings">🚦 学业预警</el-menu-item>
        <el-menu-item index="/module/party">🎯 党团</el-menu-item>
        <el-menu-item index="/module/psychology">💚 心理</el-menu-item>
        <el-menu-item index="/module/family">🏠 家庭</el-menu-item>
        <el-menu-item index="/module/cadres">👥 干部</el-menu-item>
        <el-menu-item index="/module/activities">🎨 活动</el-menu-item>
        <el-menu-item index="/module/employment">💼 就业</el-menu-item>
        <el-menu-item index="/module/meetings">📋 班会</el-menu-item>
        <el-menu-item index="/module/teachers">🧑‍🏫 班主任</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/system"><el-icon><Setting /></el-icon><span>系统设置</span></el-menu-item>
    </el-menu>

    <div class="footer-hint">
      <div>V3-A 地基版</div>
      <div class="text-muted">Ctrl+K 全局搜索</div>
    </div>
  </aside>
</template>

<script setup>
// 只做导航，无逻辑
</script>

<style scoped>
.sidebar-root {
  width: 220px;
  height: 100vh;
  background: var(--color-sidebar);
  color: var(--color-text-inverse);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.brand {
  padding: 20px 20px 12px;
  border-bottom: 1px solid rgba(255,255,255,.12);
  display: flex;
  align-items: center;
  gap: 6px;
}
.brand-emoji { font-size: 22px; }
.brand-text { font-weight: 600; font-size: 15px; }
.brand-ver {
  background: rgba(255,255,255,.18);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 11px;
  margin-left: auto;
}
.side-menu {
  flex: 1;
  border-right: none !important;
  padding: 6px 0;
}
:deep(.el-menu-item), :deep(.el-sub-menu__title) {
  border-radius: 8px !important;
  margin: 2px 8px !important;
  transition: background .18s;
}
:deep(.el-menu-item.is-active) {
  background: rgba(255,255,255,.16) !important;
  font-weight: 600;
}
:deep(.el-menu-item:hover), :deep(.el-sub-menu__title:hover) {
  background: rgba(255,255,255,.10) !important;
}
:deep(.el-sub-menu .el-menu-item) {
  min-width: unset !important;
  padding-left: 40px !important;
}
.footer-hint {
  padding: 12px 20px;
  font-size: 12px;
  color: rgba(255,255,255,.65);
  border-top: 1px solid rgba(255,255,255,.12);
}
.footer-hint .text-muted { color: rgba(255,255,255,.5); }
</style>
