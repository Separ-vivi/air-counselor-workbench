<template>
  <div class="dashboard">
    <HeroCard :hero-countdowns="heroCountdowns" />

    <StatCards :stat-cards="statCards" />

    <ChartSection ref="chartSectionRef" :dash="dash" :week-events="weekEvents" @go-warning="goWarning" />

    <!-- V6.11: AI 智能预警 + 效率中心并排 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="12">
        <AIWarningCard ref="aiWarningRef" />
      </el-col>
      <el-col :span="12">
        <EfficiencyCenter :prod-stats="prodStats" />
      </el-col>
    </el-row>

    <ShortcutsGrid />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, markRaw } from 'vue'
import {
  UserFilled, Reading, Flag, Trophy
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { dashboard as getDashboard } from '@/api/modules'
import { productivityDashboard, eventsApi } from '@/api/productivity'

import HeroCard from './components/dashboard/HeroCard.vue'
import StatCards from './components/dashboard/StatCards.vue'
import ChartSection from './components/dashboard/ChartSection.vue'
import EfficiencyCenter from './components/dashboard/EfficiencyCenter.vue'
import ShortcutsGrid from './components/dashboard/ShortcutsGrid.vue'
import AIWarningCard from './components/dashboard/AIWarningCard.vue'

const router = useRouter()
const chartSectionRef = ref(null)
const aiWarningRef = ref(null)

const dash = ref({
  total_students: 0, total_classes: 0, total_majors: 0,
  red_count: 0, yellow_count: 0, normal_count: 0,
  major_distribution: [], class_distribution: [], tag_distribution: []
})
const prodStats = ref({ todo_active: 0, todo_urgent_week: 0, todo_overdue: 0, projects_active: 0, countdowns_top: [] })
const weekEvents = ref([])
const heroCountdowns = ref([])

const statCards = ref([
  { label: '在校学生',       value: 0, icon: markRaw(UserFilled), bg: 'rgba(91, 146, 229, 0.14)',  color: '#5B92E5' },
  { label: '班级数量',       value: 0, icon: markRaw(Reading),    bg: 'rgba(79, 195, 184, 0.14)',  color: '#4FC3B8' },
  { label: '党员/发展对象', value: 0, icon: markRaw(Flag),       bg: 'rgba(143, 169, 229, 0.14)', color: '#7B92D6' },
  { label: '本月活动',       value: 0, icon: markRaw(Trophy),     bg: 'rgba(123, 207, 203, 0.16)', color: '#5FB8AC' }
])

const goWarning = () => router.push('/ai-warnings')

onMounted(async () => {
  try {
    const res = await getDashboard()
    const d = res || {}
    dash.value = {
      total_students: d.total_students ?? d.student_count ?? 0,
      total_classes: d.total_classes ?? d.class_count ?? 0,
      total_majors: d.total_majors ?? 0,
      red_count: d.red_count ?? 0,
      yellow_count: d.yellow_count ?? 0,
      normal_count: d.normal_count ?? Math.max(0, (d.total_students ?? 0) - (d.red_count ?? 0) - (d.yellow_count ?? 0)),
      major_distribution: d.major_distribution || [],
      class_distribution: d.class_distribution || [],
      tag_distribution: d.tag_distribution || []
    }
    statCards.value[0].value = dash.value.total_students
    statCards.value[1].value = dash.value.total_classes
    statCards.value[2].value = d.party_count ?? d.total_party ?? 0
    statCards.value[3].value = d.month_activities ?? d.activity_count ?? 0
    await nextTick()
    chartSectionRef.value?.renderCharts()
  } catch (e) {
    // 拦截器已提示，页面用空态展示
  }
  try {
    const pd = await productivityDashboard()
    if (pd) prodStats.value = pd
  } catch (e) {
    // 空态
  }
  try {
    const we = await eventsApi.week(0)
    weekEvents.value = we?.events || []
  } catch (e) { weekEvents.value = [] }
  try {
    heroCountdowns.value = (prodStats.value.countdowns_top || []).slice(0, 3)
  } catch (e) { heroCountdowns.value = [] }
})
</script>

<style scoped>
.dashboard {
  padding: 8px;
  min-height: calc(100vh - 100px);
  background: transparent;
}

/* 卡片高度对齐 + el-row/el-col 弹性布局 */
.dashboard :deep(.el-row) { display: flex; flex-wrap: wrap; }
.dashboard :deep(.el-col) { display: flex; }
.dashboard :deep(.el-col > .el-card) {
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
.dashboard :deep(.el-col > .el-card:hover) {
  transform: translateY(-2px);
  box-shadow:
    0 4px 14px rgba(90, 130, 180, 0.12),
    0 12px 28px rgba(90, 130, 180, 0.10);
  border-color: rgba(160, 195, 225, 0.75) !important;
}
.dashboard :deep(.el-col > .el-card > .el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
