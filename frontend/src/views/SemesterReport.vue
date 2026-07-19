<template>
  <div class="semester-report" v-loading="globalLoading">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <h2 class="page-title">学期报表</h2>
      <div class="page-actions">
        <el-button type="primary" :icon="Download" @click="handleExport" :loading="exporting">导出报表</el-button>
        <el-button :icon="Refresh" @click="refreshAll" :loading="globalLoading">刷新数据</el-button>
      </div>
    </div>

    <!-- 区域 1：总览卡片 -->
    <el-row :gutter="16" class="section-row">
      <el-col :span="6" v-for="stat in summaryCards" :key="stat.label">
        <el-card shadow="hover" class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-icon" :style="{ background: stat.bg, color: stat.color }">
            <el-icon :size="26"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value">{{ stat.value }}</div>
            <div v-if="stat.sub" class="stat-sub">{{ stat.sub }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 区域 2：三栏并排 -->
    <el-row :gutter="16" class="section-row">
      <el-col :span="8">
        <el-card shadow="never" class="chart-card triple-card" v-loading="summaryLoading">
          <template #header>
            <div class="card-header"><span class="ch-title">政治面貌分布</span></div>
          </template>
          <div v-if="summaryData" ref="politicalPieRef" class="chart-box" style="height:280px"></div>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="chart-card triple-card" v-loading="summaryLoading">
          <template #header>
            <div class="card-header"><span class="ch-title">校区 / 性别分布</span></div>
          </template>
          <div v-if="summaryData" ref="campusGenderBarRef" class="chart-box" style="height:280px"></div>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="chart-card triple-card" v-loading="partyLoading">
          <template #header>
            <div class="card-header"><span class="ch-title">党团发展进度</span></div>
          </template>
          <div v-if="partyData && partyData.stages" class="progress-block">
            <div v-for="stage in partyData.stages" :key="stage.name" class="progress-item">
              <div class="progress-label">
                <span>{{ stage.name }}</span>
                <span class="progress-count">{{ stage.count }} 人</span>
              </div>
              <el-progress
                :percentage="partyProgressPct(stage.count)"
                :color="progressColor"
                :stroke-width="14"
                :show-text="false"
              />
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 区域 3：学业数据 -->
    <el-row :gutter="16" class="section-row">
      <el-col :span="12">
        <el-card shadow="never" class="chart-card" v-loading="academicsLoading">
          <template #header>
            <div class="card-header"><span class="ch-title">各班平均成绩</span></div>
          </template>
          <div v-if="academicsData && academicsData.class_avg" ref="classAvgBarRef" class="chart-box-wide" style="height:300px"></div>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="chart-card" v-loading="academicsLoading">
          <template #header>
            <div class="card-header"><span class="ch-title">Top 10 学生</span></div>
          </template>
          <el-table v-if="academicsData && academicsData.top10" :data="academicsData.top10" size="small" stripe style="width:100%" max-height="280">
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="class_name" label="班级" />
            <el-table-column prop="avg_score" label="平均分" width="100" sortable>
              <template #default="{ row }">
                <span class="score-highlight">{{ row.avg_score }}</span>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" class="section-row">
      <el-col :span="24">
        <el-card shadow="never" class="chart-card" v-loading="academicsLoading">
          <template #header>
            <div class="card-header"><span class="ch-title">学业预警统计</span></div>
          </template>
          <div v-if="academicsData && academicsData.warning_stats" class="warning-stats-row">
            <div v-for="w in academicsData.warning_stats" :key="w.level" class="warning-stat-card" :class="'w-' + w.level">
              <div class="ws-count">{{ w.count }}</div>
              <div class="ws-label">{{ w.level_label }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 区域 4：就业跟踪 -->
    <el-row :gutter="16" class="section-row">
      <el-col :span="12">
        <el-card shadow="never" class="chart-card" v-loading="employmentLoading">
          <template #header>
            <div class="card-header"><span class="ch-title">就业状态分布</span></div>
          </template>
          <div v-if="employmentData && employmentData.distribution" ref="employmentPieRef" class="chart-box-wide" style="height:300px"></div>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="chart-card" v-loading="employmentLoading">
          <template #header>
            <div class="card-header"><span class="ch-title">就业率</span></div>
          </template>
          <div v-if="employmentData" class="employment-rate-block">
            <div class="employment-rate" :style="{ color: '#4FC3B8' }">
              {{ employmentData.employment_rate != null ? employmentData.employment_rate + '%' : '--' }}
            </div>
            <el-progress
              :percentage="employmentData.employment_rate || 0"
              :color="progressColor"
              :stroke-width="18"
              :show-text="false"
              style="margin-top: 20px;"
            />
            <div class="employment-meta">
              <span>已就业 {{ employmentData.employed_count || 0 }} 人</span>
              <span>总人数 {{ employmentData.total_count || 0 }} 人</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 区域 5：学生活动 -->
    <el-row :gutter="16" class="section-row">
      <el-col :span="24">
        <el-card shadow="never" class="chart-card" v-loading="activitiesLoading">
          <template #header>
            <div class="card-header"><span class="ch-title">活动参与人次 Top 10</span></div>
          </template>
          <div v-if="activitiesData && activitiesData.top10" ref="activitiesBarRef" class="chart-box-wide" style="height:300px"></div>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { Download, Refresh, User, UserFilled, WarningFilled, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { semesterReportApi } from '@/api/semesterReport.js'

/* ── 主色 ── */
const PRIMARY = '#5B92E5'
const ACCENT  = '#4FC3B8'
const palette = ['#5B92E5','#4FC3B8','#8FA9E5','#7BCFCB','#A6D5DE','#F5B7B7','#F5D78A','#8FD5C4']

/* ── state ── */
const globalLoading = ref(false)
const exporting = ref(false)
const summaryLoading = ref(false)
const academicsLoading = ref(false)
const partyLoading = ref(false)
const employmentLoading = ref(false)
const activitiesLoading = ref(false)

const summaryData = ref(null)
const academicsData = ref(null)
const partyData = ref(null)
const employmentData = ref(null)
const activitiesData = ref(null)

/* ── chart refs ── */
const politicalPieRef = ref(null)
const campusGenderBarRef = ref(null)
const classAvgBarRef = ref(null)
const employmentPieRef = ref(null)
const activitiesBarRef = ref(null)

let charts = []

/* ── summary cards ── */
const summaryCards = computed(() => {
  const d = summaryData.value || {}
  return [
    { label: '学生总数', value: d.total_students ?? '--', sub: d.class_count ? `${d.class_count} 个班级 · ${d.major_count || 0} 个专业` : '', icon: UserFilled, bg: 'linear-gradient(135deg, rgba(91,146,229,0.15), rgba(91,146,229,0.05))', color: PRIMARY },
    { label: '平均成绩', value: d.avg_score ?? '--', sub: '', icon: TrendCharts, bg: 'linear-gradient(135deg, rgba(79,195,184,0.15), rgba(79,195,184,0.05))', color: ACCENT },
    { label: '预警人数', value: d.warning_count ?? '--', sub: '', icon: WarningFilled, bg: 'linear-gradient(135deg, rgba(245,183,183,0.20), rgba(245,183,183,0.05))', color: '#E8836C' },
    { label: '就业率', value: d.employment_rate != null ? d.employment_rate + '%' : '--', sub: '', icon: User, bg: 'linear-gradient(135deg, rgba(143,169,229,0.18), rgba(143,169,229,0.05))', color: '#8FA9E5' },
  ]
})

/* ── helpers ── */
const progressColor = [
  { color: ACCENT, percentage: 20 },
  { color: '#8FA9E5', percentage: 50 },
  { color: PRIMARY, percentage: 80 },
  { color: '#4FC3B8', percentage: 100 },
]

function partyProgressPct(count) {
  const total = summaryData.value?.total_students || 1
  return Math.min(Math.round((count / total) * 100), 100)
}

function disposeCharts() {
  charts.forEach(c => c && c.dispose())
  charts = []
}

function initChart(domRef, option) {
  if (!domRef) return null
  // Dispose existing instance on same dom if any
  const existing = echarts.getInstanceByDom(domRef)
  if (existing) {
    existing.setOption(option, true)
    // Ensure it's tracked
    if (!charts.includes(existing)) charts.push(existing)
    return existing
  }
  const chart = echarts.init(domRef)
  chart.setOption(option)
  charts.push(chart)
  return chart
}

/* ── render charts ── */
function renderPoliticalPie() {
  if (!politicalPieRef.value || !summaryData.value?.political_dist) return
  const dist = summaryData.value.political_dist
  initChart(politicalPieRef.value, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 11, color: '#7B8B9C' } },
    color: palette,
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 13, fontWeight: 600 } },
      data: dist.map(d => ({ name: d.name, value: d.value }))
    }]
  })
}

function renderCampusGenderBar() {
  if (!campusGenderBarRef.value || !summaryData.value?.campus_gender) return
  const cg = summaryData.value.campus_gender
  const campuses = [...new Set(cg.map(d => d.campus))]
  const genders = [...new Set(cg.map(d => d.gender))]
  initChart(campusGenderBarRef.value, {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { bottom: 0, textStyle: { fontSize: 11, color: '#7B8B9C' } },
    color: [PRIMARY, ACCENT],
    grid: { left: 40, right: 16, top: 12, bottom: 36 },
    xAxis: { type: 'category', data: campuses, axisLabel: { fontSize: 11, color: '#7B8B9C' }, axisLine: { lineStyle: { color: '#E0E6ED' } } },
    yAxis: { type: 'value', axisLabel: { fontSize: 11, color: '#7B8B9C' }, splitLine: { lineStyle: { color: 'rgba(200,215,235,0.35)' } } },
    series: genders.map(g => ({
      name: g,
      type: 'bar',
      stack: 'total',
      barWidth: 28,
      itemStyle: { borderRadius: g === genders[genders.length - 1] ? [4, 4, 0, 0] : [0, 0, 0, 0] },
      data: campuses.map(c => {
        const found = cg.find(d => d.campus === c && d.gender === g)
        return found ? found.count : 0
      })
    }))
  })
}

function renderClassAvgBar() {
  if (!classAvgBarRef.value || !academicsData.value?.class_avg) return
  const ca = academicsData.value.class_avg
  initChart(classAvgBarRef.value, {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 60, right: 16, top: 12, bottom: 30 },
    color: [PRIMARY],
    xAxis: { type: 'category', data: ca.map(d => d.class_name), axisLabel: { fontSize: 10, color: '#7B8B9C', rotate: 30 }, axisLine: { lineStyle: { color: '#E0E6ED' } } },
    yAxis: { type: 'value', axisLabel: { fontSize: 11, color: '#7B8B9C' }, splitLine: { lineStyle: { color: 'rgba(200,215,235,0.35)' } } },
    series: [{
      type: 'bar',
      barWidth: 22,
      itemStyle: { borderRadius: [4, 4, 0, 0], color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: PRIMARY }, { offset: 1, color: ACCENT }]) },
      data: ca.map(d => d.avg_score)
    }]
  })
}

function renderEmploymentPie() {
  if (!employmentPieRef.value || !employmentData.value?.distribution) return
  const dist = employmentData.value.distribution
  initChart(employmentPieRef.value, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 11, color: '#7B8B9C' } },
    color: [ACCENT, PRIMARY, '#F5D78A', '#F5B7B7', '#8FA9E5'],
    series: [{
      type: 'pie',
      radius: ['40%', '68%'],
      center: ['50%', '42%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, fontSize: 11, color: '#5A6A7A', formatter: '{b}\n{d}%' },
      data: dist.map(d => ({ name: d.name, value: d.value }))
    }]
  })
}

function renderActivitiesBar() {
  if (!activitiesBarRef.value || !activitiesData.value?.top10) return
  const top = activitiesData.value.top10
  initChart(activitiesBarRef.value, {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 24, top: 12, bottom: 30 },
    color: [ACCENT],
    xAxis: { type: 'value', axisLabel: { fontSize: 11, color: '#7B8B9C' }, splitLine: { lineStyle: { color: 'rgba(200,215,235,0.35)' } } },
    yAxis: { type: 'category', data: top.map(d => d.name).reverse(), axisLabel: { fontSize: 11, color: '#5A6A7A' }, axisLine: { lineStyle: { color: '#E0E6ED' } } },
    series: [{
      type: 'bar',
      barWidth: 16,
      itemStyle: { borderRadius: [0, 4, 4, 0], color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: PRIMARY }, { offset: 1, color: ACCENT }]) },
      data: top.map(d => d.count).reverse()
    }]
  })
}

/* ── data loading ── */
async function loadSummary() {
  summaryLoading.value = true
  try {
    summaryData.value = await semesterReportApi.summary()
    await nextTick()
    renderPoliticalPie()
    renderCampusGenderBar()
  } catch (e) { console.error('summary error', e) }
  finally { summaryLoading.value = false }
}

async function loadAcademics() {
  academicsLoading.value = true
  try {
    academicsData.value = await semesterReportApi.academics()
    await nextTick()
    renderClassAvgBar()
  } catch (e) { console.error('academics error', e) }
  finally { academicsLoading.value = false }
}

async function loadParty() {
  partyLoading.value = true
  try {
    partyData.value = await semesterReportApi.partyDevelopment()
  } catch (e) { console.error('party error', e) }
  finally { partyLoading.value = false }
}

async function loadEmployment() {
  employmentLoading.value = true
  try {
    employmentData.value = await semesterReportApi.employment()
    await nextTick()
    renderEmploymentPie()
  } catch (e) { console.error('employment error', e) }
  finally { employmentLoading.value = false }
}

async function loadActivities() {
  activitiesLoading.value = true
  try {
    activitiesData.value = await semesterReportApi.activities()
    await nextTick()
    renderActivitiesBar()
  } catch (e) { console.error('activities error', e) }
  finally { activitiesLoading.value = false }
}

async function refreshAll() {
  globalLoading.value = true
  disposeCharts()
  await Promise.all([loadSummary(), loadAcademics(), loadParty(), loadEmployment(), loadActivities()])
  globalLoading.value = false
}

async function handleExport() {
  exporting.value = true
  try {
    const blob = await semesterReportApi.export()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '学期报表.xlsx'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

/* ── resize ── */
function handleResize() {
  charts.forEach(c => c && c.resize())
}

onMounted(() => {
  refreshAll()
  window.addEventListener('resize', handleResize)
})

// Watch data changes to re-render charts
watch(summaryData, async () => {
  await nextTick()
  renderPoliticalPie()
  renderCampusGenderBar()
})

watch(academicsData, async () => {
  await nextTick()
  renderClassAvgBar()
})

watch(employmentData, async () => {
  await nextTick()
  renderEmploymentPie()
})

watch(activitiesData, async () => {
  await nextTick()
  renderActivitiesBar()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  disposeCharts()
})
</script>

<style scoped>
.semester-report {
  padding: 20px 24px;
  min-height: 100%;
  background: #F6F9FC;
}

/* ── 页面顶栏 ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1E3A56;
  letter-spacing: 0.5px;
  margin: 0;
}
.page-actions {
  display: flex;
  gap: 10px;
}
.page-actions .el-button--primary {
  background: linear-gradient(135deg, #5B92E5, #4FC3B8);
  border: none;
  border-radius: 10px;
  font-weight: 600;
}
.page-actions .el-button--primary:hover {
  opacity: 0.9;
}

/* ── section rows ── */
.section-row {
  margin-bottom: 16px;
}
.semester-report :deep(.el-row) {
  display: flex;
  flex-wrap: wrap;
}
.semester-report :deep(.el-col) {
  display: flex;
}
.semester-report :deep(.el-col > .el-card) {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 16px !important;
  background: linear-gradient(180deg, #FFFFFF 0%, #F3F8FE 100%) !important;
  border: 1px solid rgba(200, 215, 235, 0.55) !important;
  box-shadow:
    0 2px 10px rgba(90, 130, 180, 0.06),
    0 6px 22px rgba(90, 130, 180, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}
.semester-report :deep(.el-col > .el-card:hover) {
  transform: translateY(-2px);
  box-shadow:
    0 4px 14px rgba(90, 130, 180, 0.12),
    0 12px 28px rgba(90, 130, 180, 0.10);
  border-color: rgba(160, 195, 225, 0.75) !important;
}
.semester-report :deep(.el-col > .el-card > .el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* ── stat-card (same as Dashboard) ── */
.stat-card {
  border-radius: 12px;
  border: none;
}
.stat-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
  padding: 18px 12px !important;
}
.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .2s ease;
}
.stat-card:hover .stat-icon { transform: scale(1.05); }
.stat-body { text-align: center; width: 100%; }
.stat-body .stat-label {
  color: #7B8B9C;
  font-size: 13px;
  text-align: center;
}
.stat-body .stat-value {
  color: #1E3A56;
  font-size: 24px;
  font-weight: 700;
  margin-top: 4px;
  text-align: center;
  letter-spacing: 0.5px;
}
.stat-sub {
  color: #909BA6;
  font-size: 11px;
  margin-top: 4px;
}

/* ── chart card ── */
.chart-card :deep(.el-card__header) {
  padding: 12px 18px;
  background: transparent;
  border-bottom: 1px solid rgba(220, 226, 232, 0.5);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ch-title {
  font-weight: 600;
  font-size: 14px;
  color: #2E5A7F;
  letter-spacing: 0.4px;
}
.chart-box {
  width: 100%;
  height: 220px;
}
.chart-box-wide {
  width: 100%;
  height: 260px;
}
.triple-card {
  height: 100%;
}
.triple-card :deep(.el-card__body) {
  padding: 12px 16px;
}

/* ── 党团进度条 ── */
.progress-block {
  padding: 8px 0;
}
.progress-item {
  margin-bottom: 14px;
}
.progress-item:last-child {
  margin-bottom: 0;
}
.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 13px;
  color: #3A4A5A;
}
.progress-count {
  font-weight: 600;
  color: #5B92E5;
  font-size: 12px;
}

/* ── 学业预警卡片 ── */
.warning-stats-row {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 16px 0;
}
.warning-stat-card {
  flex: 1;
  max-width: 180px;
  text-align: center;
  padding: 20px 16px;
  border-radius: 14px;
  background: linear-gradient(180deg, #FFFFFF 0%, #F3F8FE 100%);
  border: 1px solid rgba(91, 146, 229, 0.10);
  transition: transform .2s ease, box-shadow .2s ease;
}
.warning-stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(91, 146, 229, 0.10);
}
.ws-count {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.ws-label {
  font-size: 13px;
  margin-top: 6px;
  font-weight: 500;
}
.w-red .ws-count { color: #E74C3C; }
.w-red .ws-label { color: #E8836C; }
.w-yellow .ws-count { color: #E6A23C; }
.w-yellow .ws-label { color: #D4A24C; }
.w-normal .ws-count { color: #4FC3B8; }
.w-normal .ws-label { color: #5AAF9E; }

/* ── 就业率 ── */
.employment-rate-block {
  text-align: center;
  padding: 16px 0;
}
.employment-rate {
  font-size: 48px;
  font-weight: 800;
  letter-spacing: 1px;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
}
.employment-meta {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
  font-size: 13px;
  color: #7B8B9C;
}

/* ── top10 score ── */
.score-highlight {
  font-weight: 700;
  color: #5B92E5;
}
</style>
