<template>
  <aside class="sidebar-root">
    <div class="brand">
      <el-icon class="brand-icon"><School /></el-icon>
      <div class="brand-info">
        <div class="brand-text">辅导员工作平台</div>
        <div class="brand-ver">V6.1</div>
      </div>
    </div>

    <el-menu
      class="side-menu"
      :default-active="$route.path"
      router
      background-color="transparent"
      text-color="rgba(255,255,255,0.86)"
      active-text-color="rgba(255,255,255,0.86)"
    >
      <!-- 第1组 工作台 -->
      <el-sub-menu index="workspace">
        <template #title><el-icon><HomeFilled /></el-icon><span>工作台</span></template>
        <el-menu-item index="/dashboard"><el-icon><DataBoard /></el-icon><span>驾驶舱</span></el-menu-item>
        <el-menu-item index="/smart-import"><el-icon><Upload /></el-icon><span>智能导入</span></el-menu-item>
      </el-sub-menu>

      <!-- 第2组 学生与班级 -->
      <el-sub-menu index="students-classes">
        <template #title><el-icon><UserFilled /></el-icon><span>学生与班级</span></template>
        <el-menu-item index="/students"><el-icon><User /></el-icon><span>学生管理</span></el-menu-item>
        <el-menu-item index="/classes"><el-icon><OfficeBuilding /></el-icon><span>班级管理</span></el-menu-item>
      </el-sub-menu>

      <!-- 第3组 业务模块 -->
      <el-sub-menu index="modules">
        <template #title><el-icon><Menu /></el-icon><span>业务模块</span></template>
        <el-menu-item index="/module/grades"><el-icon><Notebook /></el-icon><span>成绩管理</span></el-menu-item>
        <el-menu-item index="/module/warnings"><el-icon><WarningFilled /></el-icon><span>学业预警</span></el-menu-item>
        <el-menu-item index="/module/party"><el-icon><Flag /></el-icon><span>党团发展</span></el-menu-item>
        <el-menu-item index="/module/psychology"><el-icon><Sunny /></el-icon><span>心理关怀</span></el-menu-item>
        <el-menu-item index="/module/interview"><el-icon><ChatDotSquare /></el-icon><span>学生访谈</span></el-menu-item>
        <el-menu-item index="/module/attendance"><el-icon><List /></el-icon><span>查课考勤</span></el-menu-item>
        <el-menu-item index="/module/family"><el-icon><HomeFilled /></el-icon><span>家庭档案</span></el-menu-item>
        <el-menu-item index="/module/cadres"><el-icon><Medal /></el-icon><span>学生干部</span></el-menu-item>
        <el-menu-item index="/module/activities"><el-icon><TrophyBase /></el-icon><span>学生活动</span></el-menu-item>
        <el-menu-item index="/module/meetings"><el-icon><ChatDotSquare /></el-icon><span>班会记录</span></el-menu-item>
        <el-menu-item index="/module/employment"><el-icon><Suitcase /></el-icon><span>就业跟踪</span></el-menu-item>
        <el-menu-item index="/module/financial-aid"><el-icon><Coin /></el-icon><span>奖助贷</span></el-menu-item>
      </el-sub-menu>

      <!-- 第4组 效率与组织 -->
      <el-sub-menu index="productivity">
        <template #title><el-icon><Compass /></el-icon><span>效率与组织</span></template>
        <el-menu-item index="/notes"><el-icon><EditPen /></el-icon><span>记事本</span></el-menu-item>
        <el-menu-item index="/calendar"><el-icon><Calendar /></el-icon><span>校历倒计时</span></el-menu-item>
        <el-menu-item index="/projects"><el-icon><Collection /></el-icon><span>项目追踪</span></el-menu-item>
        <el-menu-item index="/summary"><el-icon><PieChart /></el-icon><span>周汇总</span></el-menu-item>
        <el-menu-item index="/semester-report"><el-icon><TrendCharts /></el-icon><span>学期报表</span></el-menu-item>
      </el-sub-menu>

      <!-- 第5组 知识中心 -->
      <el-sub-menu index="knowledge-center">
        <template #title><el-icon><Reading /></el-icon><span>知识中心</span></template>
        <el-menu-item index="/knowledge"><el-icon><Files /></el-icon><span>知识库·AI助手</span></el-menu-item>
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
/* V4-hotfix10 (air 2026-07-18): B 冰蓝薄荷渐变侧栏 - 从"你好计时器"卡拿到的 B 色系锁到侧栏, 深底 + 白字 高对比不刺眼 */
.sidebar-root {
  width: 220px;
  height: 100vh;
  background: linear-gradient(180deg, #5B92E5 0%, #7BCFCB 100%);
  color: #FFFFFF;
  border-right: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow: 2px 0 16px rgba(50, 100, 160, 0.24);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  position: relative;
}
/* 顶部质感光条: 淡白, 不刺眼 */
.sidebar-root::before {
  content: '';
  position: absolute;
  left: 0; right: 0; top: 0;
  height: 80px;
  background: linear-gradient(180deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.04) 60%, rgba(255,255,255,0) 100%);
  pointer-events: none;
  z-index: 0;
}
.sidebar-root > * { position: relative; z-index: 1; }

.brand {
  padding: 18px 16px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.10);
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-icon {
  font-size: 22px !important;
  color: rgba(255, 255, 255, 0.94);
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
  color: rgba(255, 255, 255, 0.94);
  letter-spacing: 0.3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}
.brand-ver {
  color: rgba(255, 255, 255, 0.78);
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
  color: #FFFFFF !important;
  border-radius: 10px !important;
  margin: 3px 10px !important;
  transition: all .2s ease;
  font-weight: 500;
}
:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.20) !important;
  color: #FFFFFF !important;
  backdrop-filter: blur(8px);
}
:deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.32) !important;
  color: #FFFFFF !important;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(40, 90, 140, 0.20), inset 0 1px 0 rgba(255,255,255,0.6);
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
  background: #FFFFFF;
  box-shadow: 0 0 6px rgba(255,255,255,0.6);
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
  color: #FFFFFF !important;
  background: rgba(255, 255, 255, 0.10) !important;
}
.footer-hint {
  padding: 12px 20px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.78);
  border-top: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: 0 -1px 0 rgba(255, 255, 255, 0.10);
}
.footer-hint .text-muted { color: rgba(255, 255, 255, 0.62); }
</style>
