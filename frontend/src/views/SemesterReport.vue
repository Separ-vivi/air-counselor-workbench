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
      <!-- 3. 总览卡片行 - 第1行 -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-title">学生总数</div>
          <div class="card-value">{{ summaryData?.total_students || 0 }}</div>
        </div>
        <div class="summary-card">
          <div class="card-title">班级总数</div>
          <div class="card-value">{{ summaryData?.total_classes || 0 }}</div>
        </div>
        <div class="summary-card">
          <div class="card-title">专业数</div>
          <div class="card-value">{{ summaryData?.total_majors || 0 }}</div>
        </div>
      </div>

      <!-- 总览卡片行 - 第2行 -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-title">平均成绩</div>
          <div class="card-value">{{ avgScore }} 分</div>
        </div>
        <div class="summary-card">
          <div class="card-title">挂科率</div>
          <div class="card-value" :style="{color: (academicsData?.fail_rate || 0) > 20 ? '#F56C6C' : '#2ECC71'}">{{ academicsData?.fail_rate || 0 }}%</div>
        </div>
        <div class="summary-card">
          <div class="card-title">预警人数</div>
          <div class="card-value warning">{{ warningCount }} 人</div>
        </div>
        <div class="summary-card">
          <div class="card-title">考勤异常次数</div>
          <div class="card-value" style="color:#E6A23C">{{ summaryData?.attendance_exception_count || 0 }}</div>
        </div>
      </div>

      <!-- 总览卡片行 - 第3行 -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-title">心理关注人数</div>
          <div class="card-value" style="color:#9B59B6">{{ summaryData?.psychology_attention_count || 0 }}</div>
        </div>
        <div class="summary-card">
          <div class="card-title">资助总人次</div>
          <div class="card-value" style="color:#5B92E5">{{ summaryData?.financial_aid_count || 0 }}</div>
        </div>
        <div class="summary-card">
          <div class="card-title">荣誉人次</div>
          <div class="card-value" style="color:#F39C12">{{ summaryData?.honor_count || 0 }}</div>
        </div>
        <div class="summary-card">
          <div class="card-title">违纪人数</div>
          <div class="card-value" style="color:#E74C3C">{{ summaryData?.discipline_count || 0 }}</div>
        </div>
        <div class="summary-card">
          <div class="card-title">党员人数</div>
          <div class="card-value" style="color:#C0392B">{{ summaryData?.party_member_count || 0 }}</div>
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

      <!-- 6. 成绩 Top 10 -->
      <div class="charts-row" v-if="academicsData?.top10?.length">
        <div class="chart-card" style="grid-column: 1 / -1">
          <h3>成绩 Top 10</h3>
          <el-table :data="academicsData?.top10 || []" style="width: 100%">
            <el-table-column prop="student_no" label="学号" width="120" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="class_name" label="班级" />
            <el-table-column prop="avg_score" label="平均分" width="100">
              <template #default="{ row }">
                {{ (row.avg_score || 0).toFixed(2) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 7. 考勤分析 -->
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

      <!-- 8. 心理档案 -->
      <div class="charts-row">
        <div class="chart-card">
          <h3>心理关注等级分布</h3>
          <div v-if="psychologyData?.by_attention_level && Object.keys(psychologyData.by_attention_level).length" ref="psychologyChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
        <div class="chart-card">
          <h3>咨询统计</h3>
          <div class="stat-cards">
            <div class="stat-item">
              <div class="stat-label">总咨询次数</div>
              <div class="stat-value" style="color:#5B92E5">{{ psychologyData?.total_counseling_count || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">需跟进人数</div>
              <div class="stat-value" style="color:#E74C3C">{{ psychologyData?.need_follow_up || 0 }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 9. 资助与荣誉 -->
      <div class="charts-row">
        <div class="chart-card">
          <h3>资助概览</h3>
          <div class="financial-cards">
            <div class="financial-item">
              <div class="fi-label">困难认定</div>
              <div class="fi-value">{{ financialAidData?.hardship_count || 0 }} 人</div>
            </div>
            <div class="financial-item">
              <div class="fi-label">助学金发放</div>
              <div class="fi-value">{{ formatAmount(financialAidData?.grant_total_amount) }} 元 / {{ financialAidData?.grant_count || 0 }} 人</div>
            </div>
            <div class="financial-item">
              <div class="fi-label">奖学金发放</div>
              <div class="fi-value">{{ formatAmount(financialAidData?.scholarship_total_amount) }} 元 / {{ financialAidData?.scholarship_count || 0 }} 人</div>
            </div>
            <div class="financial-item">
              <div class="fi-label">助学贷款</div>
              <div class="fi-value">{{ formatAmount(financialAidData?.loan_total_amount) }} 元</div>
            </div>
            <div class="financial-item">
              <div class="fi-label">勤工助学</div>
              <div class="fi-value">{{ financialAidData?.work_study_count || 0 }} 人次 / {{ formatAmount(financialAidData?.work_study_total_compensation) }} 元</div>
            </div>
          </div>
        </div>
        <div class="chart-card">
          <h3>荣誉级别分布</h3>
          <div v-if="honorsData?.by_level && Object.keys(honorsData.by_level).length" ref="honorChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
      </div>

      <!-- 10. 党团发展 + 活动参与 Top 10 -->
      <div class="charts-row">
        <div class="chart-card">
          <h3>党团发展进度</h3>
          <div v-if="partyData?.stages && Object.keys(partyData.stages).length" ref="partyChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
        <div class="chart-card">
          <h3>活动参与 Top 10</h3>
          <div v-if="activitiesData?.activity_ranking?.length" ref="activityChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
      </div>

      <!-- 11. 日常管理 -->
      <div class="charts-row">
        <div class="chart-card">
          <h3>请假统计</h3>
          <div v-if="dormitoryData?.leave_by_type && Object.keys(dormitoryData.leave_by_type).length" ref="leaveChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
        <div class="chart-card">
          <h3>访谈统计</h3>
          <div v-if="interviewsData?.by_type && Object.keys(interviewsData.by_type).length" ref="interviewChart" class="chart-container"></div>
          <div v-else class="chart-empty">暂无数据</div>
        </div>
        <div class="chart-card">
          <h3>访谈覆盖率</h3>
          <div class="stat-cards">
            <div class="stat-item">
              <div class="stat-label">覆盖率</div>
              <div class="stat-value" style="color:#5B92E5">{{ interviewsData?.coverage_rate || 0 }}%</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">被访谈/总学生</div>
              <div class="stat-value" style="color:#2C3E50; font-size:20px;">{{ interviewsData?.covered_student_count || 0 }} / {{ interviewsData?.total_student_count || 0 }}</div>
            </div>
          </div>
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
const partyChart = ref(null)
const activityChart = ref(null)
const attendanceTypeChart = ref(null)
const attendanceClassChart = ref(null)
const psychologyChart = ref(null)
const honorChart = ref(null)
const leaveChart = ref(null)
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
  }
  return labels[key] || key
}

const formatMetric = (key, value) => {
  if (value === null || value === undefined) return '-'
  if (key === 'avg_score') return value.toFixed(2) + ' 分'
  if (key === 'fail_rate') return value.toFixed(2) + '%'
  if (key === 'interview_coverage') return value.toFixed(1) + '%'
  return value
}

const formatDiff = (key, diff) => {
  if (diff === null || diff === undefined) return '-'
  if (key === 'avg_score') return (diff > 0 ? '+' : '') + diff.toFixed(2) + ' 分'
  if (key === 'fail_rate') return (diff > 0 ? '+' : '') + diff.toFixed(2) + '%'
  if (key === 'interview_coverage') return (diff > 0 ? '+' : '') + diff.toFixed(1) + '%'
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
      semesterReportApi.partyDevelopment(),
      semesterReportApi.employment(),
      semesterReportApi.activities(),
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
  renderPartyChart()
  renderActivityChart()
  renderAttendanceTypeChart()
  renderAttendanceClassChart()
  renderPsychologyChart()
  renderHonorChart()
  renderLeaveChart()
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

const renderPartyChart = () => {
  const stages = partyData.value?.stages
  if (!partyChart.value || !stages || !Object.keys(stages).length) return
  const chart = createChart(partyChart.value)
  if (!chart) return
  const names = Object.keys(stages)
  const values = Object.values(stages)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { rotate: 20, fontSize: 11 }
    },
    yAxis: { type: 'value', name: '人数' },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: { color: '#7BCFCB' },
      barMaxWidth: 50
    }]
  })
}

const renderActivityChart = () => {
  const data = activitiesData.value?.activity_ranking || []
  if (!activityChart.value || !data.length) return
  const chart = createChart(activityChart.value)
  if (!chart) return
  const top10 = data.slice(0, 10).reverse()
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '30%' },
    xAxis: { type: 'value', name: '参与人次' },
    yAxis: {
      type: 'category',
      data: top10.map(d => d.title),
      axisLabel: { width: 120, overflow: 'truncate' }
    },
    series: [{
      type: 'bar',
      data: top10.map(d => d.participants),
      itemStyle: { color: '#8FA9E5' },
      barMaxWidth: 25
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

const renderHonorChart = () => {
  const data = honorsData.value?.by_level || {}
  if (!honorChart.value || !Object.keys(data).length) return
  const chart = createChart(honorChart.value)
  if (!chart) return
  const colorMap = { '国家级': '#E74C3C', '省级': '#F39C12', '校级': '#5B92E5', '院级': '#7BCFCB' }
  const names = Object.keys(data)
  const values = Object.values(data)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { fontSize: 12 }
    },
    yAxis: { type: 'value', name: '获奖人次' },
    series: [{
      type: 'bar',
      data: names.map((name, i) => ({
        value: values[i],
        itemStyle: { color: colorMap[name] || '#5B92E5' }
      })),
      barMaxWidth: 50
    }]
  })
}

const renderLeaveChart = () => {
  const data = dormitoryData.value?.leave_by_type || {}
  if (!leaveChart.value || !Object.keys(data).length) return
  const chart = createChart(leaveChart.value)
  if (!chart) return
  const colorMap = { '事假': '#5B92E5', '病假': '#F56C6C', '其他': '#95A5A6' }
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
        itemStyle: { color: colorMap[name] || '#7BCFCB' }
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
    // 处理 blob 响应
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
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #2C3E50;
}

.page-actions {
  display: flex;
  align-items: center;
}

/* 对比区域 */
.comparison-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08);
}

.comparison-section h3 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #5B92E5;
}

.comparison-cards {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.comparison-card {
  background: linear-gradient(135deg, #ECF1F7 0%, #F5F8FC 100%);
  border-radius: 8px;
  padding: 12px 16px;
  min-width: 140px;
}

.metric-label {
  font-size: 12px;
  color: #7F8C8D;
  margin-bottom: 4px;
}

.metric-current {
  font-size: 20px;
  font-weight: 600;
  color: #2C3E50;
}

.metric-change {
  font-size: 12px;
  margin-top: 4px;
}

.metric-change.up { color: #2ECC71; }
.metric-change.down { color: #E74C3C; }

/* 总览卡片 */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.summary-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08);
}

.card-title {
  font-size: 13px;
  color: #7F8C8D;
  margin-bottom: 8px;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  color: #2C3E50;
}

.card-value.warning { color: #E74C3C; }
.card-value.success { color: #2ECC71; }

/* 图表区域 */
.charts-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08);
}

.chart-card h3 {
  margin: 0 0 16px 0;
  font-size: 15px;
  color: #2C3E50;
}

.chart-container {
  height: 280px;
}

.chart-empty {
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #C0C4CC;
  font-size: 14px;
}

/* 统计卡片（心理咨询） */
.stat-cards {
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 48px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: #7F8C8D;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
}

/* 资助卡片 */
.financial-cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 8px 0;
}

.financial-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: linear-gradient(135deg, #F5F8FC 0%, #ECF1F7 100%);
  border-radius: 8px;
}

.fi-label {
  font-size: 13px;
  color: #7F8C8D;
}

.fi-value {
  font-size: 14px;
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
