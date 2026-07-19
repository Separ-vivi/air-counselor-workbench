<template>
  <div class="semester-report-page">
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
        <el-button type="primary" @click="exportReport">导出 Excel</el-button>
      </div>
    </div>

    <!-- 差值统计卡片 -->
    <div v-if="comparisonData && Object.keys(comparisonData).length" class="comparison-section">
      <h3>与上一学期对比</h3>
      <div class="comparison-cards">
        <div v-for="(item, key) in comparisonData" :key="key" class="comparison-card">
          <div class="metric-label">{{ getMetricLabel(key) }}</div>
          <div class="metric-current">{{ formatMetric(key, item.current) }}</div>
          <div :class="['metric-change', item.diff > 0 ? 'up' : item.diff < 0 ? 'down' : '']">
            <span v-if="item.diff > 0">↑</span>
            <span v-else-if="item.diff < 0">↓</span>
            <span v-else>→</span>
            {{ formatDiff(key, item.diff) }} ({{ item.change_pct }}%)
          </div>
        </div>
      </div>
    </div>

    <!-- 总览卡片 -->
    <div class="summary-cards">
      <div class="summary-card">
        <div class="card-title">学生总数</div>
        <div class="card-value">{{ summaryData.total_students || 0 }}</div>
      </div>
      <div class="summary-card">
        <div class="card-title">班级总数</div>
        <div class="card-value">{{ summaryData.total_classes || 0 }}</div>
      </div>
      <div class="summary-card">
        <div class="card-title">平均成绩</div>
        <div class="card-value">{{ avgScore }} 分</div>
      </div>
      <div class="summary-card">
        <div class="card-title">预警人数</div>
        <div class="card-value warning">{{ warningCount }} 人</div>
      </div>
      <div class="summary-card">
        <div class="card-title">就业率</div>
        <div class="card-value success">{{ employmentRate }}%</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <div class="chart-card">
        <h3>班级平均成绩</h3>
        <div ref="classAvgChart" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <h3>学业预警统计</h3>
        <div ref="warningChart" class="chart-container"></div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>成绩 Top 10</h3>
        <el-table :data="academicsData.top10" style="width: 100%">
          <el-table-column prop="student_no" label="学号" width="120" />
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="class_name" label="班级" />
          <el-table-column prop="avg_score" label="平均分" width="100">
            <template #default="{ row }">
              {{ row.avg_score.toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>党团发展进度</h3>
        <div ref="partyChart" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <h3>活动参与 Top 10</h3>
        <div ref="activityChart" class="chart-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import semesterReportApi from '@/api/semesterReport'
import { ElMessage } from 'element-plus'

const summaryData = ref({})
const academicsData = ref({})
const partyData = ref({})
const employmentData = ref({})
const activitiesData = ref({})
const semesters = ref([])
const currentSemester = ref('')
const comparisonData = ref({})

const classAvgChart = ref(null)
const warningChart = ref(null)
const partyChart = ref(null)
const activityChart = ref(null)

let chartInstances = []

const avgScore = computed(() => {
  const avgs = academicsData.value.class_averages || []
  if (!avgs.length) return '0.00'
  const total = avgs.reduce((sum, item) => sum + item.avg_score, 0)
  return (total / avgs.length).toFixed(2)
})

const warningCount = computed(() => {
  const stats = academicsData.value.warning_stats || []
  const abnormal = stats.filter(s => s.level !== 'normal')
  return abnormal.reduce((sum, s) => sum + s.count, 0)
})

const employmentRate = computed(() => {
  return employmentData.value.employment_rate || '0.00'
})

const getMetricLabel = (key) => {
  const labels = {
    avg_score: '平均成绩',
    fail_rate: '挂科率',
    warning_count: '预警人数',
    activity_participants: '活动参与'
  }
  return labels[key] || key
}

const formatMetric = (key, value) => {
  if (value === null || value === undefined) return '-'
  if (key === 'avg_score') return value.toFixed(2) + ' 分'
  if (key === 'fail_rate') return value.toFixed(2) + '%'
  return value
}

const formatDiff = (key, diff) => {
  if (diff === null || diff === undefined) return '-'
  if (key === 'avg_score') return (diff > 0 ? '+' : '') + diff.toFixed(2) + ' 分'
  if (key === 'fail_rate') return (diff > 0 ? '+' : '') + diff.toFixed(2) + '%'
  return (diff > 0 ? '+' : '') + diff
}

const loadAllData = async () => {
  try {
    const [summaryRes, academicsRes, partyRes, employmentRes, activitiesRes, compareRes] = await Promise.all([
      semesterReportApi.summary(),
      semesterReportApi.academics(currentSemester.value),
      semesterReportApi.partyDevelopment(),
      semesterReportApi.employment(),
      semesterReportApi.activities(),
      semesterReportApi.compare(currentSemester.value)
    ])
    summaryData.value = summaryRes || {}
    academicsData.value = academicsRes || {}
    partyData.value = partyRes || {}
    employmentData.value = employmentRes || {}
    activitiesData.value = activitiesRes || {}
    comparisonData.value = compareRes?.comparison || {}
    
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

const renderCharts = () => {
  chartInstances.forEach(c => c.dispose())
  chartInstances = []

  // 班级平均成绩柱状图
  if (classAvgChart.value && academicsData.value.class_averages?.length) {
    const chart = echarts.init(classAvgChart.value)
    const data = academicsData.value.class_averages
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
    chartInstances.push(chart)
  }

  // 预警统计饼图
  if (warningChart.value && academicsData.value.warning_stats?.length) {
    const chart = echarts.init(warningChart.value)
    const data = academicsData.value.warning_stats
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
    chartInstances.push(chart)
  }

  // 党团发展柱状图
  if (partyChart.value && partyData.value.stages) {
    const chart = echarts.init(partyChart.value)
    const stages = partyData.value.stages
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
    chartInstances.push(chart)
  }

  // 活动参与 Top 10 横向柱状图
  if (activityChart.value && activitiesData.value.activity_ranking?.length) {
    const chart = echarts.init(activityChart.value)
    const data = activitiesData.value.activity_ranking.slice(0, 10).reverse()
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '30%' },
      xAxis: { type: 'value', name: '参与人次' },
      yAxis: {
        type: 'category',
        data: data.map(d => d.title),
        axisLabel: { width: 120, overflow: 'truncate' }
      },
      series: [{
        type: 'bar',
        data: data.map(d => d.participants),
        itemStyle: { color: '#8FA9E5' },
        barMaxWidth: 25
      }]
    })
    chartInstances.push(chart)
  }
}

const exportReport = async () => {
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
    ElMessage.error('导出失败')
  }
}

onMounted(async () => {
  await loadSemesters()
  await loadAllData()
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

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
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
  height: 300px;
}
</style>
