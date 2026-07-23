<template>
  <div class="semester-report-page">
    <!-- 1. 页面头部 -->
    <div class="page-header">
      <h2>学期报表</h2>
      <div class="page-actions">
        <el-select v-model="currentSemester" placeholder="选择学期" @change="loadAllData" style="width: 200px; margin-right: 10px;">
          <el-option
            v-for="sem in semesters"
            :key="sem.code"
            :label="sem.label"
            :value="sem.code"
          />
        </el-select>
        <el-button type="primary" @click="exportReport" :loading="exporting">导出 Excel</el-button>
      </div>
    </div>

    <!-- 2. 空数据提示 -->
    <div v-if="!hasData" class="empty-state">
      <div class="empty-icon">📊</div>
      <div class="empty-text">暂无数据</div>
      <div class="empty-hint">请先在「学生管理」或「成绩管理」中导入数据</div>
    </div>

    <template v-else>
      <!-- 3. 总览卡片 - 紧凑 grid，不超过2行 -->
      <div class="summary-grid">
        <div class="summary-card-sm">
          <div class="card-title-sm">学生总数</div>
          <div class="card-value-sm">{{ summaryData?.total_students || 0 }}</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">班级总数</div>
          <div class="card-value-sm">{{ summaryData?.total_classes || 0 }}</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">专业数</div>
          <div class="card-value-sm">{{ summaryData?.total_majors || 0 }}</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">平均成绩</div>
          <div class="card-value-sm">{{ avgScore }} 分</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">挂科率</div>
          <div class="card-value-sm" :style="{color: (academicsData?.fail_rate || 0) > 20 ? '#E74C3C' : '#2ECC71'}">{{ academicsData?.fail_rate || 0 }}%</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">预警人数</div>
          <div class="card-value-sm warning">{{ warningCount }} 人</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">考勤异常</div>
          <div class="card-value-sm" style="color:#E6A23C">{{ summaryData?.attendance_exception_count || 0 }}</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">心理关注</div>
          <div class="card-value-sm" style="color:#9B59B6">{{ summaryData?.psychology_attention_count || 0 }}</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">资助总人次</div>
          <div class="card-value-sm" style="color:#5B92E5">{{ summaryData?.financial_aid_count || 0 }}</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">荣誉人次</div>
          <div class="card-value-sm" style="color:#F39C12">{{ summaryData?.honor_count || 0 }}</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">违纪人数</div>
          <div class="card-value-sm" style="color:#E74C3C">{{ summaryData?.discipline_count || 0 }}</div>
        </div>
        <div class="summary-card-sm">
          <div class="card-title-sm">累计党员</div>
          <div class="card-value-sm" style="color:#C0392B">{{ summaryData?.party_member_count || 0 }}</div>
        </div>
      </div>

      <!-- 4. 学期对比 -->
      <div v-if="isSemesterSelected && comparisonData && Object.keys(comparisonData).length" class="comparison-section">
        <h3>与上一学期对比</h3>
        <div class="comparison-cards">
          <div v-for="(item, key) in comparisonData" :key="key" class="comparison-card">
            <div class="metric-label">{{ getMetricLabel(key) }}</div>
            <div class="metric-current">{{ formatMetric(key, item?.current) }}</div>
            <div :class="['metric-change', (item?.diff || 0) > 0 ? 'up' : (item?.diff || 0) < 0 ? 'down' : '']">
              <span v-if="(item?.diff || 0) > 0">↑</span>
              <span v-else-if="(item?.diff || 0) < 0">↓</span>
              <span v-else>→</span>
              {{ formatDiff(key, item?.diff) }} ({{ item?.change_pct || 0 }}%)
            </div>
          </div>
        </div>
      </div>

      <!-- 5. 学业分析 -->
      <div class="charts-row">
        <div class="chart-card">
          <h3>班级平均成绩</h3>
          <div v-if="academicsData?.class_averages?.length" ref="classAvgChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
        <div class="chart-card">
          <h3>学业预警统计</h3>
          <div v-if="academicsData?.warning_stats?.length" ref="warningChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
      </div>

      <!-- 6. 考勤分析 -->
      <div class="charts-row">
        <div class="chart-card">
          <h3>考勤异常类型分布</h3>
          <div v-if="attendanceData?.by_type && Object.keys(attendanceData.by_type).length" ref="attendanceTypeChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
        <div class="chart-card">
          <h3>各班考勤异常</h3>
          <div v-if="attendanceData?.by_class?.length" ref="attendanceClassChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
      </div>

      <!-- 7. 心理关怀（合并：关注等级分布 + 咨询统计） -->
      <div class="charts-row">
        <div class="chart-card" style="grid-column: 1 / -1">
          <h3>心理关怀</h3>
          <div class="psychology-layout">
            <div class="psychology-chart-side">
              <div v-if="psychologyData?.by_attention_level && Object.keys(psychologyData.by_attention_level).length" ref="psychologyChart" class="chart-container"></div>
              <div v-else class="chart-empty">暂无数据</div>
            </div>
            <div class="psychology-stats-side">
              <div class="psychology-stat-item">
                <div class="psychology-stat-label">总咨询次数</div>
                <div class="psychology-stat-value" style="color:#5B92E5">{{ psychologyData?.total_counseling_count || 0 }}</div>
              </div>
              <div class="psychology-stat-item">
                <div class="psychology-stat-label">需跟进人数</div>
                <div class="psychology-stat-value" style="color:#E74C3C">{{ psychologyData?.need_follow_up || 0 }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 8. 综合数据（资助/荣誉/党团/活动/请假 合并为紧凑卡片） -->
      <div class="section-title">综合数据</div>
      <div class="compact-grid">
        <div class="compact-card">
          <div class="compact-card-title">资助</div>
          <div class="compact-card-body">
            <div class="compact-row"><span class="compact-label">困难认定</span><span class="compact-value">{{ financialAidData?.hardship_count || 0 }} 人</span></div>
            <div class="compact-row"><span class="compact-label">助学金</span><span class="compact-value">{{ financialAidData?.grant_count || 0 }} 人</span></div>
            <div class="compact-row"><span class="compact-label">奖学金</span><span class="compact-value">{{ financialAidData?.scholarship_count || 0 }} 人</span></div>
          </div>
        </div>
        <div class="compact-card">
          <div class="compact-card-title">荣誉</div>
          <div class="compact-card-body">
            <div v-for="(val, level) in honorsData?.by_level || {}" :key="level" class="compact-row">
              <span class="compact-label">{{ level }}</span>
              <span class="compact-value">{{ val }} 人次</span>
            </div>
            <div v-if="!honorsData?.by_level || !Object.keys(honorsData.by_level).length" class="compact-row">
              <span class="compact-label">暂无数据</span><span class="compact-value">-</span>
            </div>
          </div>
        </div>
        <div class="compact-card">
          <div class="compact-card-title">党团发展</div>
          <div class="compact-card-body">
            <div v-for="(val, stage) in partyData?.stages || {}" :key="stage" class="compact-row">
              <span class="compact-label">{{ stage }}</span>
              <span class="compact-value">{{ val }} 人</span>
            </div>
            <div v-if="!partyData?.stages || !Object.keys(partyData.stages).length" class="compact-row">
              <span class="compact-label">暂无数据</span><span class="compact-value">-</span>
            </div>
          </div>
        </div>
        <div class="compact-card">
          <div class="compact-card-title">活动</div>
          <div class="compact-card-body">
            <div class="compact-row"><span class="compact-label">参与总人次</span><span class="compact-value">{{ activitiesData?.total_participants || 0 }}</span></div>
            <div class="compact-row"><span class="compact-label">活动数量</span><span class="compact-value">{{ activitiesData?.activity_ranking?.length || 0 }}</span></div>
          </div>
        </div>
        <div class="compact-card">
          <div class="compact-card-title">请假</div>
          <div class="compact-card-body">
            <div v-for="(val, type) in dormitoryData?.leave_by_type || {}" :key="type" class="compact-row">
              <span class="compact-label">{{ type }}</span>
              <span class="compact-value">{{ val }} 次</span>
            </div>
            <div v-if="!dormitoryData?.leave_by_type || !Object.keys(dormitoryData.leave_by_type).length" class="compact-row">
              <span class="compact-label">暂无数据</span><span class="compact-value">-</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 9. 访谈统计 -->
      <div class="charts-row">
        <div class="chart-card">
          <h3>访谈统计 <span style="font-size:12px;color:#7F8C8D;font-weight:400;margin-left:8px;">覆盖率 {{ interviewsData?.coverage_rate || 0 }}% | {{ interviewsData?.covered_student_count || 0 }}/{{ interviewsData?.total_student_count || 0 }}人</span></h3>
          <div v-if="interviewsData?.by_type && Object.keys(interviewsData.by_type).length" ref="interviewChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import semesterReportApi from '@/api/semesterReport'
import { ElMessage } from 'element-plus'

// 数据 refs
const summaryData = ref({})
const academicsData = ref({})
const partyData = ref({})
const employmentData = ref({})
const activitiesData = ref({})
const attendanceData = ref({})
const psychologyData = ref({})
const disciplineData = ref({})
const financialAidData = ref({})
const honorsData = ref({})
const interviewsData = ref({})
const dormitoryData = ref({})
const semesters = ref([])
const currentSemester = ref('')
const comparisonData = ref({})
const exporting = ref(false)

// 图表 refs
const classAvgChart = ref(null)
const warningChart = ref(null)
const attendanceTypeChart = ref(null)
const attendanceClassChart = ref(null)
const psychologyChart = ref(null)
const interviewChart = ref(null)

let chartInstances = []

// 计算属性
const avgScore = computed(() => {
  const avgs = academicsData.value?.class_averages || []
  if (!avgs.length) return '0.00'
  const total = avgs.reduce((sum, item) => sum + (item.avg_score || 0), 0)
  return (total / avgs.length).toFixed(2)
})

const warningCount = computed(() => {
  const stats = academicsData.value?.warning_stats || []
  const abnormal = stats.filter(s => s.level !== 'normal')
  return abnormal.reduce((sum, s) => sum + (s.count || 0), 0)
})

const isSemesterSelected = computed(() => {
  return currentSemester.value && currentSemester.value !== 'all'
})

const hasData = computed(() => {
  return (summaryData.value?.total_students || 0) > 0
})

// 格式化辅助
const getMetricLabel = (key) => {
  const labels = {
    avg_score: '平均成绩',
    fail_rate: '挂科率',
    warning_count: '预警人数',
    activity_participants: '活动参与',
    attendance_exception_count: '考勤异常次数',
    psychology_attention_count: '心理关注人数',
    financial_aid_count: '资助人次',
    discipline_count: '违纪人数',
    honor_count: '荣誉人次',
    interview_count: '访谈次数',
    interview_coverage: '访谈覆盖率',
    party_member_diff: '党员人数变化',
    party_member_change: '党员人数变化',
  }
  return labels[key] || key
}

const formatMetric = (key, value) => {
  if (value === null || value === undefined) return '-'
  if (key === 'avg_score') return value.toFixed(2) + ' 分'
  if (key === 'fail_rate') return value.toFixed(2) + '%'
  if (key === 'interview_coverage') return value.toFixed(1) + '%'
  if (key === 'party_member_diff' || key === 'party_member_change') return value + ' 人'
  return value
}

const formatDiff = (key, diff) => {
  if (diff === null || diff === undefined) return '-'
  if (key === 'avg_score') return (diff > 0 ? '+' : '') + diff.toFixed(2) + ' 分'
  if (key === 'fail_rate') return (diff > 0 ? '+' : '') + diff.toFixed(2) + '%'
  if (key === 'interview_coverage') return (diff > 0 ? '+' : '') + diff.toFixed(1) + '%'
  if (key === 'party_member_diff' || key === 'party_member_change') return (diff > 0 ? '+' : '') + diff + ' 人'
  return (diff > 0 ? '+' : '') + diff
}

const formatAmount = (val) => {
  if (!val) return '0'
  return Number(val).toLocaleString()
}

// 数据加载
const loadAllData = async () => {
  try {
    const results = await Promise.allSettled([
      semesterReportApi.summary(currentSemester.value),
      semesterReportApi.academics(currentSemester.value),
      semesterReportApi.partyDevelopment(currentSemester.value),
      semesterReportApi.employment(currentSemester.value),
      semesterReportApi.activities(currentSemester.value),
      semesterReportApi.compare(currentSemester.value),
      semesterReportApi.attendance(currentSemester.value),
      semesterReportApi.psychology(currentSemester.value),
      semesterReportApi.discipline(currentSemester.value),
      semesterReportApi.financialAid(currentSemester.value),
      semesterReportApi.honors(currentSemester.value),
      semesterReportApi.interviews(currentSemester.value),
      semesterReportApi.dormitory(currentSemester.value)
    ])
    const get = (i) => results[i]?.status === 'fulfilled' ? results[i].value : null
    summaryData.value = get(0) || {}
    academicsData.value = get(1) || {}
    partyData.value = get(2) || {}
    employmentData.value = get(3) || {}
    activitiesData.value = get(4) || {}
    const compareRes = get(5)
    comparisonData.value = compareRes?.comparison || {}
    attendanceData.value = get(6) || {}
    psychologyData.value = get(7) || {}
    disciplineData.value = get(8) || {}
    financialAidData.value = get(9) || {}
    honorsData.value = get(10) || {}
    interviewsData.value = get(11) || {}
    dormitoryData.value = get(12) || {}

    await nextTick()
    renderCharts()
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  }
}

const loadSemesters = async () => {
  try {
    const res = await semesterReportApi.semesters()
    semesters.value = res || []
    if (semesters.value.length > 0) {
      currentSemester.value = semesters.value[0].code
    }
  } catch (error) {
    console.error('加载学期列表失败:', error)
  }
}

// 图表渲染
const renderCharts = () => {
  chartInstances.forEach(c => { try { c.dispose() } catch (e) {} })
  chartInstances = []

  renderClassAvgChart()
  renderWarningChart()
  renderAttendanceTypeChart()
  renderAttendanceClassChart()
  renderPsychologyChart()
  renderInterviewChart()
}

const createChart = (el) => {
  if (!el) return null
  const chart = echarts.init(el)
  chartInstances.push(chart)
  return chart
}

const renderClassAvgChart = () => {
  const data = academicsData.value?.class_averages || []
  if (!classAvgChart.value || !data.length) return
  const chart = createChart(classAvgChart.value)
  if (!chart) return
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: data.map(d => d.class_name),
      axisLabel: { rotate: 30, fontSize: 11 }
    },
    yAxis: { type: 'value', name: '平均分' },
    series: [{
      type: 'bar',
      data: data.map(d => d.avg_score),
      itemStyle: { color: '#5B92E5' },
      barMaxWidth: 40
    }]
  })
}

const renderWarningChart = () => {
  const data = academicsData.value?.warning_stats || []
  if (!warningChart.value || !data.length) return
  const chart = createChart(warningChart.value)
  if (!chart) return
  const colorMap = { red: '#E74C3C', yellow: '#F39C12', normal: '#2ECC71' }
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      label: { show: true, formatter: '{b}: {c}人' },
      data: data.map(d => ({
        name: d.level_label,
        value: d.count,
        itemStyle: { color: colorMap[d.level] || '#95A5A6' }
      }))
    }]
  })
}

const renderAttendanceTypeChart = () => {
  const data = attendanceData.value?.by_type || {}
  if (!attendanceTypeChart.value || !Object.keys(data).length) return
  const chart = createChart(attendanceTypeChart.value)
  if (!chart) return
  const colorMap = { '迟到': '#F39C12', '早退': '#E6A23C', '旷课': '#E74C3C' }
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      label: { show: true, formatter: '{b}: {c}次' },
      data: Object.entries(data).map(([name, value]) => ({
        name,
        value,
        itemStyle: { color: colorMap[name] || '#5B92E5' }
      }))
    }]
  })
}

const renderAttendanceClassChart = () => {
  const data = attendanceData.value?.by_class || []
  if (!attendanceClassChart.value || !data.length) return
  const chart = createChart(attendanceClassChart.value)
  if (!chart) return
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: data.map(d => d.class_name),
      axisLabel: { rotate: 30, fontSize: 11 }
    },
    yAxis: { type: 'value', name: '异常次数' },
    series: [{
      type: 'bar',
      data: data.map(d => d.count),
      itemStyle: { color: '#E6A23C' },
      barMaxWidth: 40
    }]
  })
}

const renderPsychologyChart = () => {
  const data = psychologyData.value?.by_attention_level || {}
  if (!psychologyChart.value || !Object.keys(data).length) return
  const chart = createChart(psychologyChart.value)
  if (!chart) return
  const colorMap = { '一级关注': '#E74C3C', '二级关注': '#F39C12', '三级关注': '#3498DB', '普通': '#2ECC71' }
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      label: { show: true, formatter: '{b}: {c}人' },
      data: Object.entries(data).map(([name, value]) => ({
        name,
        value,
        itemStyle: { color: colorMap[name] || '#95A5A6' }
      }))
    }]
  })
}

const renderInterviewChart = () => {
  const data = interviewsData.value?.by_type || {}
  if (!interviewChart.value || !Object.keys(data).length) return
  const chart = createChart(interviewChart.value)
  if (!chart) return
  const colors = ['#5B92E5', '#7BCFCB', '#F39C12', '#E74C3C', '#9B59B6', '#2ECC71']
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      label: { show: true, formatter: '{b}: {c}次' },
      data: Object.entries(data).map(([name, value], i) => ({
        name,
        value,
        itemStyle: { color: colors[i % colors.length] }
      }))
    }]
  })
}

// 导出
const exportReport = async () => {
  exporting.value = true
  try {
    const res = await semesterReportApi.export(currentSemester.value)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `学期报表_${currentSemester.value || 'all'}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

// 生命周期
onMounted(async () => {
  await loadSemesters()
  await loadAllData()
})

onBeforeUnmount(() => {
  chartInstances.forEach(c => { try { c.dispose() } catch (e) {} })
  chartInstances = []
})
</script>

<style scoped>
.semester-report-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  color: #2C3E50;
}

.page-actions {
  display: flex;
  align-items: center;
}

/* 紧凑总览卡片 grid - 每行4个，共3行12个 */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.summary-card-sm {
  background: #fff;
  border-radius: 8px;
  padding: 10px 12px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(91, 146, 229, 0.08);
}

.card-title-sm {
  font-size: 11px;
  color: #7F8C8D;
  margin-bottom: 4px;
}

.card-value-sm {
  font-size: 20px;
  font-weight: 700;
  color: #2C3E50;
}

.card-value-sm.warning { color: #E74C3C; }
.card-value-sm.success { color: #2ECC71; }

/* 对比区域 */
.comparison-section {
  background: #fff;
  border-radius: 12px;
  padding: 14px 18px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08);
}

.comparison-section h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #5B92E5;
}

.comparison-cards {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.comparison-card {
  background: linear-gradient(135deg, #ECF1F7 0%, #F5F8FC 100%);
  border-radius: 8px;
  padding: 10px 14px;
  min-width: 130px;
}

.metric-label {
  font-size: 11px;
  color: #7F8C8D;
  margin-bottom: 3px;
}

.metric-current {
  font-size: 18px;
  font-weight: 600;
  color: #2C3E50;
}

.metric-change {
  font-size: 11px;
  margin-top: 3px;
}

.metric-change.up { color: #2ECC71; }
.metric-change.down { color: #E74C3C; }

/* 图表区域 */
.charts-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08);
}

.chart-card h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #2C3E50;
}

.chart-container {
  height: 200px;
}

.chart-empty {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #C0C4CC;
  font-size: 14px;
}

/* 心理关怀合并布局 */
.psychology-layout {
  display: flex;
  align-items: stretch;
  gap: 24px;
  min-height: 200px;
}

.psychology-chart-side {
  flex: 1;
  min-width: 0;
}

.psychology-chart-side .chart-container,
.psychology-chart-side .chart-empty {
  height: 200px;
}

.psychology-stats-side {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 28px;
  padding: 0 16px;
  min-width: 160px;
  border-left: 1px solid #ECF1F7;
}

.psychology-stat-item {
  text-align: center;
}

.psychology-stat-label {
  font-size: 12px;
  color: #7F8C8D;
  margin-bottom: 6px;
}

.psychology-stat-value {
  font-size: 28px;
  font-weight: 700;
}

/* 综合数据紧凑卡片 */
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #2C3E50;
  margin: 16px 0 10px 0;
}

.compact-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}

.compact-card {
  background: #fff;
  border-radius: 8px;
  padding: 10px 12px;
  box-shadow: 0 1px 4px rgba(91, 146, 229, 0.08);
}

.compact-card-title {
  font-size: 13px;
  font-weight: 600;
  color: #5B92E5;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid #ECF1F7;
}

.compact-card-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.compact-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 0;
}

.compact-label {
  font-size: 11px;
  color: #7F8C8D;
}

.compact-value {
  font-size: 13px;
  font-weight: 600;
  color: #2C3E50;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-text {
  font-size: 18px;
  font-weight: 600;
  color: #2C3E50;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: #7F8C8D;
}
</style>
