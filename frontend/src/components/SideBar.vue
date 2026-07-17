<template>
  <aside class="sidebar-root">
    <div class="brand">
      <el-icon class="brand-icon"><School /></el-icon>
      <div class="brand-info">
        <div class="brand-text">辅导员工作平台</div>
        <div class="brand-ver">V4</div>
      </div>
    </div>

    <el-menu
      class="side-menu"
      :default-active="$route.path"
      router
      background-color="transparent"
      text-color="#12324D"
      active-text-color="#0B2A48"
    >
      <el-menu-item index="/dashboard"><el-icon><DataBoard /></el-icon><span>驾驶舱</span></el-menu-item>
      <el-menu-item index="/students"><el-icon><User /></el-icon><span>学生管理</span></el-menu-item>
      <el-menu-item index="/classes"><el-icon><OfficeBuilding /></el-icon><span>班级管理</span></el-menu-item>
      <el-menu-item index="/org"><el-icon><Grid /></el-icon><span>三级架构</span></el-menu-item>
      <el-menu-item index="/smart-import"><el-icon><Upload /></el-icon><span>智能导入</span></el-menu-item>

      <el-sub-menu index="modules">
        <template #title><el-icon><Menu /></el-icon><span>业务模块</span></template>
        <el-menu-item index="/module/grades"><el-icon><Notebook /></el-icon><span>成绩管理</span></el-menu-item>
        <el-menu-item index="/module/warnings"><el-icon><WarningFilled /></el-icon><span>学业预警</span></el-menu-item>
        <el-menu-item index="/module/party"><el-icon><Flag /></el-icon><span>党团发展</span></el-menu-item>
        <el-menu-item index="/module/psychology"><el-icon><Sunny /></el-icon><span>心理关怀</span></el-menu-item>
        <el-menu-item index="/module/family"><el-icon><HomeFilled /></el-icon><span>家庭档案</span></el-menu-item>
        <el-menu-item index="/module/cadres"><el-icon><Medal /></el-icon><span>学生干部</span></el-menu-item>
        <el-menu-item index="/module/activities"><el-icon><TrophyBase /></el-icon><span>学生活动</span></el-menu-item>
        <el-menu-item index="/module/employment"><el-icon><Suitcase /></el-icon><span>就业跟踪</span></el-menu-item>
        <el-menu-item index="/module/meetings"><el-icon><ChatDotSquare /></el-icon><span>班会记录</span></el-menu-item>
        <el-menu-item index="/module/teachers"><el-icon><UserFilled /></el-icon><span>班主任组</span></el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="productivity">
        <template #title><el-icon><Compass /></el-icon><span>效率中心</span></template>
        <el-menu-item index="/notes"><el-icon><EditPen /></el-icon><span>记事本</span></el-menu-item>
        <el-menu-item index="/calendar"><el-icon><Calendar /></el-icon><span>校历倒计时</span></el-menu-item>
        <el-menu-item index="/projects"><el-icon><Collection /></el-icon><span>项目追踪</span></el-menu-item>
        <el-menu-item index="/summary"><el-icon><PieChart /></el-icon><span>周汇总</span></el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="helper">
        <template #title><el-icon><Reading /></el-icon><span>辅助工具</span></template>
        <el-menu-item index="/knowledge"><el-icon><Files /></el-icon><span>知识库</span></el-menu-item>
        <el-menu-item index="/faqs"><el-icon><QuestionFilled /></el-icon><span>FAQ</span></el-menu-item>
        <el-menu-item index="/templates"><el-icon><Document /></el-icon><span>文档模板</span></el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/system"><el-icon><Setting /></el-icon><span>系统设置</span></el-menu-item>
    </el-menu>

    <div class="footer-hint">
      <div class="text-muted">⌘ K 全局搜索</div>
    </div>
  </aside>
</template>

<script setup>
// 只做导航，无逻辑
</script>

<style scoped>
/* V4-hotfix7: 中饱和蓝回归 (air: 深空蓝太深, 上一版方向对) - 但真正干掉"白边土"四个真凶: 顶白光叠加/inset白线/border白/底部泛白 */
.sidebar-root {
  width: 220px;
  height: 100vh;
  /* 单层中饱和蓝渐变, 收敛底部不再泛白到 #C4DDEE */
  background: linear-gradient(180deg, #5A9DD1 0%, #78B4DE 40%, #A0C9E7 100%);
  color: #0E2A44;
  /* 边框改冷调蓝细边, 不再是白 */
  border-right: 1px solid rgba(150, 190, 225, 0.5);
  /* 去 inset 白线, 只留右侧投影 */
  box-shadow: 2px 0 14px rgba(60, 110, 165, 0.22);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  position: relative;
}
/* 顶部质感光条: 80px + 起点透明度降到 0.28 (原 0.55), 只保留一丝 iOS 磨砂反射不刺眼 */
.sidebar-root::before {
  content: '';
  position: absolute;
  left: 0; right: 0; top: 0;
  height: 80px;
  background: linear-gradient(180deg, rgba(255,255,255,0.28) 0%, rgba(255,255,255,0.06) 60%, rgba(255,255,255,0) 100%);
  pointer-events: none;
  z-index: 0;
}
.sidebar-root > * { position: relative; z-index: 1; }

.brand {
  padding: 18px 16px 14px;
  /* v4-hotfix6 沿用: 分界线白半透 iOS 磨砂风 + 底部阴影双层 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 1px 0 rgba(30, 70, 110, 0.12);
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-icon {
  font-size: 22px !important;
  color: #1F4A6B;
  flex-shrink: 0;
}
.brand-info {
  min-width: 0;
  flex: 1;
  overflow: hidden;
}
.brand-text {
  font-weight: 600;
  font-size: 14px;
  color: #12324D;
  letter-spacing: 0.3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}
.brand-ver {
  color: rgba(30, 60, 90, 0.68);
  font-size: 11px;
  margin-top: 2px;
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.side-menu {
  flex: 1;
  border-right: none !important;
  padding: 8px 0;
  background: transparent !important;
}
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: #12324D !important;
  border-radius: 10px !important;
  margin: 3px 10px !important;
  transition: all .2s ease;
  font-weight: 500;
}
:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.42) !important;
  color: #0B2A48 !important;
  backdrop-filter: blur(8px);
}
:deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.62) !important;
  color: #0B2A48 !important;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(60, 110, 150, 0.18), inset 0 1px 0 rgba(255,255,255,0.8);
  position: relative;
  backdrop-filter: blur(8px);
}
:deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  left: -10px;
  top: 22%;
  bottom: 22%;
  width: 3px;
  border-radius: 2px;
  background: linear-gradient(180deg, #4A90C7 0%, #2A6FA8 100%);
}
:deep(.el-sub-menu .el-menu-item) {
  min-width: unset !important;
  padding-left: 44px !important;
  font-size: 13.5px;
}
:deep(.el-menu-item .el-icon),
:deep(.el-sub-menu__title .el-icon) {
  font-size: 16px;
  margin-right: 8px;
  vertical-align: middle;
  color: inherit;
}
:deep(.el-sub-menu .el-menu-item .el-icon) {
  font-size: 15px;
  margin-right: 6px;
  opacity: 0.85;
}
:deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
  color: #3B6A7C !important;
}
.footer-hint {
  padding: 12px 20px;
  font-size: 12px;
  color: rgba(58, 90, 110, 0.7);
  border-top: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 -1px 0 rgba(30, 70, 110, 0.12);
}
.footer-hint .text-muted { color: rgba(58, 90, 110, 0.5); }
</style>
