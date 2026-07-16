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

      <el-sub-menu index="productivity">
        <template #title><el-icon><Compass /></el-icon><span>效率中心</span></template>
        <el-menu-item index="/notes">📝 记事本</el-menu-item>
        <el-menu-item index="/calendar">📅 校历倒计时</el-menu-item>
        <el-menu-item index="/projects">📌 项目追踪</el-menu-item>
        <el-menu-item index="/summary">📊 周汇总</el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="helper">
        <template #title><el-icon><Reading /></el-icon><span>辅助工具</span></template>
        <el-menu-item index="/knowledge">📚 知识库</el-menu-item>
        <el-menu-item index="/faqs">❓ FAQ</el-menu-item>
        <el-menu-item index="/templates">📄 文档模板</el-menu-item>
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
/* V3-G 侧边栏（淡色版）：浅蓝→浅薄荷柔和过渡 + 毛玻璃 */
.sidebar-root {
  width: 220px;
  height: 100vh;
  background: linear-gradient(180deg,
    rgba(220, 235, 250, 0.72) 0%,
    rgba(225, 245, 240, 0.75) 100%);
  backdrop-filter: blur(18px) saturate(1.2);
  -webkit-backdrop-filter: blur(18px) saturate(1.2);
  color: #3A5A6E;
  border-right: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 2px 0 14px rgba(93, 143, 160, 0.06);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.brand {
  padding: 20px 20px 14px;
  border-bottom: 1px solid rgba(122, 168, 184, 0.18);
  display: flex;
  align-items: center;
  gap: 8px;
}
.brand-emoji { font-size: 22px; }
.brand-text {
  font-weight: 600;
  font-size: 15px;
  color: #2E4A5E;
  letter-spacing: 0.3px;
}
.brand-ver {
  background: rgba(122, 168, 184, 0.18);
  color: #3B6A7C;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  margin-left: auto;
}
.side-menu {
  flex: 1;
  border-right: none !important;
  padding: 8px 0;
  background: transparent !important;
}
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: #3A5A6E !important;
  border-radius: 10px !important;
  margin: 3px 10px !important;
  transition: all .2s ease;
  font-weight: 500;
}
:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(122, 168, 184, 0.14) !important;
  color: #2E4A5E !important;
}
:deep(.el-menu-item.is-active) {
  background: rgba(122, 168, 184, 0.22) !important;
  color: #2E4A5E !important;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(93, 143, 160, 0.12);
  position: relative;
}
:deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  left: -10px;
  top: 22%;
  bottom: 22%;
  width: 3px;
  border-radius: 2px;
  background: linear-gradient(180deg, #7AA8B8 0%, #5D8FA0 100%);
}
:deep(.el-sub-menu .el-menu-item) {
  min-width: unset !important;
  padding-left: 44px !important;
  font-size: 13.5px;
}
:deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
  color: #3B6A7C !important;
}
.footer-hint {
  padding: 12px 20px;
  font-size: 12px;
  color: rgba(58, 90, 110, 0.7);
  border-top: 1px solid rgba(122, 168, 184, 0.18);
}
.footer-hint .text-muted { color: rgba(58, 90, 110, 0.5); }
</style>
