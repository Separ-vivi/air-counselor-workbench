<template>
  <div class="financial-aid-page">
    <div class="page-header">
      <h2>奖助贷</h2>
      <div class="header-info">
        <span class="coverage-badge">资助覆盖率 {{ (summary.coverage_rate * 100).toFixed(1) }}%</span>
      </div>
    </div>

    <!-- 顶部统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card" v-for="card in statCards" :key="card.key">
        <div class="stat-icon" :style="{ background: card.gradient }">
          <el-icon :size="22"><component :is="card.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ filteredSummary[card.key] || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 2×3 -->
    <div class="charts-grid">
      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">困难等级分布</span></template>
        <div ref="hardshipPieRef" class="chart-box"></div>
      </el-card>
      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">资助类型金额</span></template>
        <div ref="grantBarRef" class="chart-box"></div>
      </el-card>
      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">奖学金类型分布</span></template>
        <div ref="scholarshipRingRef" class="chart-box"></div>
      </el-card>
      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">荣誉级别分布</span></template>
        <div ref="honorPieRef" class="chart-box"></div>
      </el-card>
      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">学年资助趋势</span></template>
        <div ref="trendLineRef" class="chart-box"></div>
      </el-card>
      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">贷款类型分布</span></template>
        <div ref="loanPieRef" class="chart-box"></div>
      </el-card>
    </div>

    <!-- 下方区域：表格 + TOP卡片 -->
    <div class="bottom-layout">
      <!-- 左侧表格 -->
      <div class="table-panel">
        <el-card shadow="never" class="table-card">
          <template #header>
            <div class="table-header">
              <span class="chart-title">综合列表</span>
              <el-form :inline="true" class="filter-form">
                <el-form-item>
                  <el-select v-model="filterAidType" placeholder="资助类型" clearable style="width: 140px" @change="loadList">
                    <el-option label="困难认定" value="hardship" />
                    <el-option label="助学金" value="grant" />
                    <el-option label="奖学金" value="scholarship" />
                    <el-option label="助学贷款" value="loan" />
                    <el-option label="勤工助学" value="work_study" />
                    <el-option label="评优评先" value="honor" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-select v-model="filterYear" placeholder="学年" clearable style="width: 160px" @change="onYearChange">
                    <el-option v-for="y in semesters" :key="y" :label="y" :value="y" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-input v-model="filterSearch" placeholder="学号/姓名" clearable style="width: 180px" @clear="loadList" @keyup.enter="loadList" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="loadList">搜索</el-button>
                </el-form-item>
              </el-form>
            </div>
          </template>
          <el-table :data="listData" v-loading="listLoading" stripe border max-height="480" row-key="id">
            <el-table-column label="学生" prop="student_name" width="100">
              <template #default="{ row }">
                <el-link type="primary" @click="$router.push(`/students/${row.student_id}`)">{{ row.student_name }}</el-link>
              </template>
            </el-table-column>
            <el-table-column label="学号" prop="student_no" width="130" />
            <el-table-column label="班级" prop="class_name" min-width="140" show-overflow-tooltip />
            <el-table-column label="类型" prop="aid_type_label" width="100">
              <template #default="{ row }">
                <el-tag :type="typeTagMap[row.aid_type] || ''" size="small">{{ row.aid_type_label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="明细" prop="detail" min-width="140" show-overflow-tooltip />
            <el-table-column label="金额" prop="amount" width="110" align="right">
              <template #default="{ row }">
                <span v-if="row.amount > 0" style="color:#5B92E5;font-weight:600">¥{{ row.amount.toLocaleString() }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="学年" prop="academic_year" width="120" />
            <el-table-column label="备注" prop="extra" min-width="120" show-overflow-tooltip />
          </el-table>
          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="listTotal"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadList"
              @current-change="loadList"
            />
          </div>
        </el-card>
      </div>

      <!-- 右侧TOP卡片 -->
      <div class="top-panel">
        <el-card shadow="never" class="top-card">
          <template #header><span class="chart-title">TOP 资助学生</span></template>
          <div class="top-list">
            <div class="top-item" v-for="(stu, idx) in topRecipients" :key="idx">
              <span class="top-rank" :class="idx < 3 ? 'rank-hot' : ''">{{ idx + 1 }}</span>
              <div class="top-info">
                <div class="top-name">{{ stu.student_name }}</div>
                <div class="top-no">{{ stu.student_no }}</div>
              </div>
              <div class="top-amount">¥{{ stu.total_amount.toLocaleString() }}</div>
            </div>
            <el-empty v-if="!topRecipients.length" description="暂无数据" :image-size="60" />
          </div>
        </el-card>
        <el-card shadow="never" class="total-card">
          <div class="total-label">资助总金额</div>
          <div class="total-value">¥{{ (summary.total_amount || 0).toLocaleString() }}</div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import request from '@/api/index'
import {
  WarningFilled, Coin, Trophy, CreditCard, Briefcase, Medal
} from '@element-plus/icons-vue'

// ===== 状态 =====
const summary = ref({})
const chartData = ref({})
const listData = ref([])
const listTotal = ref(0)
const listLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const semesters = ref([])
const topRecipients = ref([])

const filterAidType = ref('')
const filterYear = ref('')
const filterSearch = ref('')

// 类型标签颜色
const typeTagMap = {
  hardship: 'warning',
  grant: 'success',
  scholarship: '',
  loan: 'danger',
  work_study: 'info',
  honor: 'success',
}

// 统计卡片配置
const statCards = [
  { key: 'hardship_count', label: '困难认定', icon: WarningFilled, gradient: 'linear-gradient(135deg,#5B92E5,#7BCFCB)' },
  { key: 'grant_count', label: '助学金', icon: Coin, gradient: 'linear-gradient(135deg,#7BCFCB,#4FC3B8)' },
  { key: 'scholarship_count', label: '奖学金', icon: Trophy, gradient: 'linear-gradient(135deg,#8FA9E5,#5B92E5)' },
  { key: 'loan_count', label: '助学贷款', icon: CreditCard, gradient: 'linear-gradient(135deg,#4FC3B8,#7BCFCB)' },
  { key: 'work_study_count', label: '勤工助学', icon: Briefcase, gradient: 'linear-gradient(135deg,#5B92E5,#8FA9E5)' },
  { key: 'honor_count', label: '评优评先', icon: Medal, gradient: 'linear-gradient(135deg,#7BCFCB,#8FA9E5)' },
]

// 按学年筛选后的统计值
const filteredSummary = computed(() => {
  if (!filterYear.value) return summary.value
  // 从列表数据中按学年重新计算统计
  const data = listData.value
  const s = { ...summary.value }
  const counts = { hardship_count: 0, grant_count: 0, scholarship_count: 0, loan_count: 0, work_study_count: 0, honor_count: 0 }
  data.forEach(r => {
    if (r.academic_year === filterYear.value) {
      const key = r.aid_type + '_count'
      if (counts[key] !== undefined) counts[key]++
    }
  })
  return { ...s, ...counts }
})

// 图表 ref
const hardshipPieRef = ref(null)
const grantBarRef = ref(null)
const scholarshipRingRef = ref(null)
const honorPieRef = ref(null)
const trendLineRef = ref(null)
const loanPieRef = ref(null)

let hardshipPie = null
let grantBar = null
let scholarshipRing = null
let honorPie = null
let trendLine = null
let loanPie = null

// 色板
const PALETTE = ['#5B92E5', '#7BCFCB', '#4FC3B8', '#8FA9E5', '#A8D5E2', '#6BA3D6', '#5CC4B8', '#95B8E8']

// ===== 数据加载 =====
const loadSummary = async () => {
  try {
    const res = await request.get('/financial-aid/summary')
    summary.value = res || {}
  } catch (e) { console.error('加载统计失败:', e) }
}

const loadChartData = async () => {
  try {
    const res = await request.get('/financial-aid/chart-data')
    chartData.value = res || {}
    topRecipients.value = res.top_recipients || []
  } catch (e) { console.error('加载图表数据失败:', e) }
}

const onYearChange = () => {
  loadList()
  loadSummary()
}

const loadList = async () => {
  listLoading.value = true
  try {
    const params = { page: currentPage.value, size: pageSize.value }
    if (filterAidType.value) params.aid_type = filterAidType.value
    if (filterYear.value) params.academic_year = filterYear.value
    if (filterSearch.value) params.search = filterSearch.value
    const res = await request.get('/financial-aid/list', { params })
    listData.value = res.items || []
    listTotal.value = res.total || 0
  } catch (e) {
    console.error('加载列表失败:', e)
    ElMessage.error('加载列表失败')
  } finally {
    listLoading.value = false
  }
}

const loadSemesters = async () => {
  try {
    const res = await request.get('/financial-aid/semesters')
    semesters.value = res || []
  } catch (e) { console.error('加载学年失败:', e) }
}

// ===== 图表渲染 =====
const initCharts = () => {
  const d = chartData.value
  // 困难等级分布饼图
  if (hardshipPieRef.value) {
    hardshipPie = echarts.init(hardshipPieRef.value)
    hardshipPie.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      color: PALETTE,
      series: [{
        type: 'pie', radius: ['0%', '70%'], center: ['50%', '50%'],
        label: { formatter: '{b}\n{d}%', fontSize: 12 },
        data: (d.hardship_distribution || []).map(i => ({ name: i.level || '未填写', value: i.count })),
      }],
    })
  }

  // 资助类型金额柱状图
  if (grantBarRef.value) {
    grantBar = echarts.init(grantBarRef.value)
    const grantData = d.grant_by_type || []
    grantBar.setOption({
      tooltip: { trigger: 'axis' },
      color: PALETTE,
      grid: { left: 60, right: 20, top: 20, bottom: 40 },
      xAxis: { type: 'category', data: grantData.map(i => i.type || '未填写'), axisLabel: { fontSize: 11 } },
      yAxis: { type: 'value', axisLabel: { formatter: v => v >= 10000 ? (v / 10000) + '万' : v } },
      series: [{
        type: 'bar', barWidth: '50%',
        data: grantData.map(i => i.amount),
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', formatter: p => p.value > 0 ? '¥' + (p.value >= 10000 ? (p.value / 10000).toFixed(1) + '万' : p.value) : '' },
      }],
    })
  }

  // 奖学金类型分布环形图
  if (scholarshipRingRef.value) {
    scholarshipRing = echarts.init(scholarshipRingRef.value)
    const schData = d.scholarship_by_type || []
    scholarshipRing.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c}人 ¥{d}%' },
      color: PALETTE,
      series: [{
        type: 'pie', radius: ['35%', '70%'], center: ['50%', '50%'],
        label: { formatter: '{b}\n{d}%', fontSize: 12 },
        data: schData.map(i => ({ name: i.type || '未填写', value: i.count })),
      }],
    })
  }

  // 荣誉级别分布饼图
  if (honorPieRef.value) {
    honorPie = echarts.init(honorPieRef.value)
    honorPie.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      color: PALETTE,
      series: [{
        type: 'pie', radius: ['0%', '70%'], center: ['50%', '50%'],
        label: { formatter: '{b}\n{d}%', fontSize: 12 },
        data: (d.honor_by_level || []).map(i => ({ name: i.level || '未填写', value: i.count })),
      }],
    })
  }

  // 学年资助趋势折线图
  if (trendLineRef.value) {
    trendLine = echarts.init(trendLineRef.value)
    const trendData = d.yearly_trend || []
    trendLine.setOption({
      tooltip: { trigger: 'axis', formatter: p => p[0] ? `${p[0].name}<br/>¥${p[0].value.toLocaleString()}` : '' },
      color: ['#5B92E5'],
      grid: { left: 70, right: 20, top: 20, bottom: 40 },
      xAxis: { type: 'category', data: trendData.map(i => i.year), axisLabel: { fontSize: 11, rotate: 20 } },
      yAxis: { type: 'value', axisLabel: { formatter: v => v >= 10000 ? (v / 10000).toFixed(0) + '万' : v } },
      series: [{
        type: 'line', smooth: true, symbol: 'circle', symbolSize: 8,
        data: trendData.map(i => i.total_amount),
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(91,146,229,0.3)' },
          { offset: 1, color: 'rgba(91,146,229,0.02)' },
        ]) },
        lineStyle: { width: 3 },
      }],
    })
  }

  // 贷款类型分布饼图
  if (loanPieRef.value) {
    loanPie = echarts.init(loanPieRef.value)
    loanPie.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      color: PALETTE,
      series: [{
        type: 'pie', radius: ['0%', '70%'], center: ['50%', '50%'],
        label: { formatter: '{b}\n{d}%', fontSize: 12 },
        data: (d.loan_by_type || []).map(i => ({ name: i.type || '未填写', value: i.count })),
      }],
    })
  }
}

// ===== resize =====
const handleResize = () => {
  hardshipPie?.resize()
  grantBar?.resize()
  scholarshipRing?.resize()
  honorPie?.resize()
  trendLine?.resize()
  loanPie?.resize()
}

// ===== 生命周期 =====
onMounted(async () => {
  await Promise.all([loadSummary(), loadChartData(), loadSemesters()])
  loadList()
  await nextTick()
  initCharts()
  window.addEventListener('resize', handleResize)
})

watch(chartData, () => { nextTick(() => initCharts()) }, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  hardshipPie?.dispose(); hardshipPie = null
  grantBar?.dispose(); grantBar = null
  scholarshipRing?.dispose(); scholarshipRing = null
  honorPie?.dispose(); honorPie = null
  trendLine?.dispose(); trendLine = null
  loanPie?.dispose(); loanPie = null
})
</script>

<style scoped>
.financial-aid-page { padding: 20px; background: #ECF1F7; min-height: 100vh; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; color: #2C3E50; font-size: 20px; }
.coverage-badge {
  background: linear-gradient(135deg, #5B92E5, #7BCFCB);
  color: #fff; padding: 6px 16px; border-radius: 20px;
  font-size: 13px; font-weight: 600; letter-spacing: 0.5px;
}

/* 统计卡片 */
.stats-cards { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin-bottom: 16px; }
.stat-card {
  background: #fff; border-radius: 12px; padding: 16px 18px;
  display: flex; align-items: center; gap: 12px;
  box-shadow: 0 2px 8px rgba(91,146,229,0.08);
  transition: transform .2s;
}
.stat-card:hover { transform: translateY(-2px); }
.stat-icon {
  width: 42px; height: 42px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0;
}
.stat-info { flex: 1; min-width: 0; }
.stat-label { font-size: 12px; color: #7F8C8D; margin-bottom: 2px; }
.stat-value { font-size: 24px; font-weight: 700; color: #2C3E50; }

/* 图表区域 */
.charts-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 16px; }
.chart-card { border-radius: 12px; }
.chart-card :deep(.el-card__header) { padding: 12px 18px; border-bottom: 1px solid #ECF1F7; }
.chart-title { font-size: 14px; font-weight: 600; color: #2C3E50; }
.chart-box { height: 220px; }

/* 底部布局 */
.bottom-layout { display: flex; gap: 16px; }
.table-panel { flex: 1; min-width: 0; }
.top-panel { width: 280px; flex-shrink: 0; display: flex; flex-direction: column; gap: 14px; }

.table-card { border-radius: 12px; }
.table-card :deep(.el-card__header) { padding: 12px 18px; }
.table-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.filter-form { display: flex; flex-wrap: wrap; gap: 0; }
.filter-form :deep(.el-form-item) { margin-bottom: 0; margin-right: 8px; }
.pagination-wrap { margin-top: 14px; display: flex; justify-content: flex-end; }

/* TOP卡片 */
.top-card { border-radius: 12px; }
.top-card :deep(.el-card__header) { padding: 12px 18px; border-bottom: 1px solid #ECF1F7; }
.top-list { display: flex; flex-direction: column; gap: 10px; }
.top-item {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 0; border-bottom: 1px solid #ECF1F7;
}
.top-item:last-child { border-bottom: none; }
.top-rank {
  width: 22px; height: 22px; border-radius: 6px; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  background: #ECF1F7; color: #7F8C8D; flex-shrink: 0;
}
.top-rank.rank-hot { background: linear-gradient(135deg, #5B92E5, #7BCFCB); color: #fff; }
.top-info { flex: 1; min-width: 0; }
.top-name { font-size: 13px; font-weight: 600; color: #2C3E50; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.top-no { font-size: 11px; color: #95A5A6; }
.top-amount { font-size: 14px; font-weight: 700; color: #5B92E5; white-space: nowrap; }

/* 总金额卡片 */
.total-card { border-radius: 12px; text-align: center; padding: 8px 0; }
.total-label { font-size: 13px; color: #7F8C8D; margin-bottom: 6px; }
.total-value { font-size: 28px; font-weight: 800; background: linear-gradient(135deg, #5B92E5, #7BCFCB); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* 响应式 */
@media (max-width: 1200px) {
  .stats-cards { grid-template-columns: repeat(3, 1fr); }
  .charts-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .stats-cards { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
  .bottom-layout { flex-direction: column; }
  .top-panel { width: 100%; }
}
</style>
