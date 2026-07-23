<template>
  <div class="interview-page">
    <div class="page-header">
      <h2>学生访谈管理</h2>
      <div class="page-actions">
        <el-button type="primary" @click="showAddDialog">新增记录</el-button>
      </div>
    </div>

    <!-- V5-h: 筛选栏 - 班级/学生/状态/类型 -->
    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="班级">
          <el-select v-model="filterClassId" placeholder="全部班级" filterable clearable style="width: 220px" @change="onFilterChange">
            <el-option v-for="c in allClasses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学生">
          <StudentSelect v-model="filterStudentId" style="width: 240px" @change="onFilterChange" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterStatus" placeholder="全部" clearable @change="onFilterChange" style="width: 120px">
            <el-option label="待进行" value="待进行" />
            <el-option label="已完成" value="已完成" />
            <el-option label="需跟进" value="需跟进" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filterType" placeholder="全部" clearable @change="onFilterChange" style="width: 120px">
            <el-option v-for="t in interviewTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="filterSemester" placeholder="全部学期" clearable @change="onFilterChange" style="width: 180px">
            <el-option v-for="s in semesterList" :key="s.code" :label="s.label" :value="s.code" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-label">总记录数</div>
        <div class="stat-value">{{ stats.total || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">待进行</div>
        <div class="stat-value pending">{{ stats.pending || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已完成</div>
        <div class="stat-value done">{{ stats.by_status?.['已完成'] || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">需跟进</div>
        <div class="stat-value follow">{{ stats.by_status?.['需跟进'] || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">访谈覆盖率</div>
        <div class="stat-value coverage">{{ coverageRate }}%</div>
        <div class="stat-sub">已访谈 {{ coveredStudentCount }} / {{ totalStudentCount }} 人</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">关注级别分布</div>
        <div ref="typeChartRef" class="chart-body"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">月度趋势</div>
        <div ref="trendChartRef" class="chart-body"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">访谈次数TOP5学生</div>
        <div ref="topChartRef" class="chart-body"></div>
      </div>
    </div>

    <!-- 数据表格 - 带排序 -->
    <div class="table-container">
      <el-table :data="paginatedData" style="width: 100%" v-loading="loading"
        :default-sort="{ prop: 'interview_date', order: 'descending' }">
        <el-table-column prop="student_no" label="学号" width="120" sortable />
        <el-table-column prop="student_name" label="姓名" width="100" sortable />
        <el-table-column prop="class_name" label="班级" width="150" show-overflow-tooltip sortable />
        <el-table-column prop="interview_date" label="访谈日期" width="120" sortable />
        <el-table-column prop="interview_type" label="类型" width="100" sortable>
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.interview_type)" size="small">{{ row.interview_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="interviewer" label="访谈人" width="100" sortable />
        <el-table-column prop="topic" label="主题" min-width="180" show-overflow-tooltip sortable />
        <el-table-column prop="status" label="状态" width="90" sortable>
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetailDialog(row)">详情</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="filteredData.length"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑访谈' : '新增访谈'" width="650px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="学生" required>
          <el-select v-model="form.student_id" filterable placeholder="选择学生" style="width: 100%;">
            <el-option v-for="s in students" :key="s.id" :label="`${s.student_no} - ${s.name}`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="访谈日期" required>
          <el-date-picker v-model="form.interview_date" type="date" placeholder="选择日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="访谈类型">
          <el-select v-model="form.interview_type" style="width: 100%;">
            <el-option v-for="t in interviewTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="访谈人">
          <el-input v-model="form.interviewer" placeholder="请输入访谈人" />
        </el-form-item>
        <el-form-item label="访谈地点">
          <el-input v-model="form.location" placeholder="请输入地点" />
        </el-form-item>
        <el-form-item label="访谈主题">
          <el-input v-model="form.topic" placeholder="请输入主题" />
        </el-form-item>
        <el-form-item label="访谈内容">
          <el-input v-model="form.content" type="textarea" :rows="4" placeholder="请输入访谈内容" />
        </el-form-item>
        <el-form-item label="学生反馈">
          <el-input v-model="form.feedback" type="textarea" :rows="3" placeholder="请输入学生反馈" />
        </el-form-item>
        <el-form-item label="后续跟进">
          <el-input v-model="form.follow_up" type="textarea" :rows="2" placeholder="请输入跟进计划" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%;">
            <el-option label="待进行" value="待进行" />
            <el-option label="已完成" value="已完成" />
            <el-option label="需跟进" value="需跟进" />
          </el-select>
        </el-form-item>
        <el-form-item label="提醒日期">
          <el-date-picker v-model="form.remind_date" type="date" placeholder="选择提醒日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="访谈详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="学生">{{ detailData.student_name }}</el-descriptions-item>
        <el-descriptions-item label="学号">{{ detailData.student_no }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{ detailData.class_name }}</el-descriptions-item>
        <el-descriptions-item label="访谈日期">{{ detailData.interview_date }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ detailData.interview_type }}</el-descriptions-item>
        <el-descriptions-item label="访谈人">{{ detailData.interviewer }}</el-descriptions-item>
        <el-descriptions-item label="地点">{{ detailData.location }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ detailData.status }}</el-descriptions-item>
        <el-descriptions-item label="主题" :span="2">{{ detailData.topic }}</el-descriptions-item>
        <el-descriptions-item label="内容" :span="2">{{ detailData.content }}</el-descriptions-item>
        <el-descriptions-item label="学生反馈" :span="2">{{ detailData.feedback }}</el-descriptions-item>
        <el-descriptions-item label="后续跟进" :span="2">{{ detailData.follow_up }}</el-descriptions-item>
        <el-descriptions-item label="提醒日期">{{ detailData.remind_date }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="showEditDialog(detailData)">编辑</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import request from '@/api/index'
import { useOrgStore } from '@/stores/org'
import StudentSelect from '@/components/StudentSelect.vue'

const orgStore = useOrgStore()
const loading = ref(false)
const submitting = ref(false)
const allData = ref([]) // 全量数据
const students = ref([])
const stats = ref({})
const interviewTypes = ['常规访谈', '预警访谈', '心理访谈', '学业访谈', '就业访谈', '其他']

// 图表相关
const typeChartRef = ref(null)
const trendChartRef = ref(null)
const topChartRef = ref(null)
let typeChart = null
let trendChart = null
let topChart = null
const chartData = ref({
  type_distribution: {},
  monthly_trend: [],
  top_students: []
})

// V5-h: 筛选条件
const filterClassId = ref(null)
const filterStudentId = ref(null)
const filterStatus = ref('')
const filterType = ref('')
const filterSemester = ref('')
const semesterList = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const detailData = ref({})
const form = ref({
  student_id: null,
  interview_date: '',
  interview_type: '常规访谈',
  interviewer: '',
  location: '',
  topic: '',
  content: '',
  feedback: '',
  follow_up: '',
  status: '已完成',
  remind_date: ''
})

const allClasses = computed(() => orgStore.allClasses || [])

// 学期代码 → 日期范围
const semesterDateRange = (code) => {
  // 格式如 2025-2026-1 → 第1学期: 2025-09-01 ~ 2026-01-31, 第2学期: 2026-02-01 ~ 2026-07-31
  const parts = code.split('-')
  if (parts.length !== 3) return null
  const startYear = parseInt(parts[0])
  const endYear = parseInt(parts[1])
  const sem = parseInt(parts[2])
  if (isNaN(startYear) || isNaN(endYear) || isNaN(sem)) return null
  if (sem === 1) {
    return { start: `${startYear}-09-01`, end: `${endYear}-01-31` }
  } else if (sem === 2) {
    return { start: `${endYear}-02-01`, end: `${endYear}-07-31` }
  }
  return null
}

// 前端过滤（班级 + 学生 + 状态 + 类型 + 学期）
const filteredData = computed(() => {
  let data = allData.value
  if (filterClassId.value) {
    const cls = allClasses.value.find(c => c.id === filterClassId.value)
    if (cls) data = data.filter(r => r.class_name === cls.name)
  }
  if (filterStudentId.value) {
    data = data.filter(r => r.student_id === filterStudentId.value)
  }
  if (filterStatus.value) {
    data = data.filter(r => r.status === filterStatus.value)
  }
  if (filterType.value) {
    data = data.filter(r => r.interview_type === filterType.value)
  }
  if (filterSemester.value) {
    const range = semesterDateRange(filterSemester.value)
    if (range) {
      data = data.filter(r => r.interview_date >= range.start && r.interview_date <= range.end)
    }
  }
  return data
})

// 分页数据
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredData.value.slice(start, start + pageSize.value)
})

// 覆盖率统计
const totalStudentCount = ref(0)
const coveredStudentCount = computed(() => {
  const ids = new Set(filteredData.value.map(r => r.student_id))
  return ids.size
})
const coverageRate = computed(() => {
  if (!totalStudentCount.value) return 0
  return ((coveredStudentCount.value / totalStudentCount.value) * 100).toFixed(1)
})

const getTypeTagType = (type) => {
  const map = { '常规访谈': '', '预警访谈': 'danger', '心理访谈': 'warning', '学业访谈': 'success', '就业访谈': 'info', '其他': 'info' }
  return map[type] || ''
}

const getStatusTagType = (status) => {
  const map = { '待进行': 'warning', '已完成': 'success', '需跟进': 'danger' }
  return map[status] || ''
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: 1, size: 1000 } // 拉全量做前端过滤
    const res = await request.get('/interview/', { params })
    allData.value = res.items || []
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await request.get('/interview/statistics')
    stats.value = res || {}
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadChartData = async () => {
  try {
    const res = await request.get('/interview/chart-data')
    chartData.value = res || { type_distribution: {}, monthly_trend: [], top_students: [] }
    await nextTick()
    initCharts()
  } catch (error) {
    console.error('加载图表数据失败:', error)
  }
}

const chartColors = ['#5B92E5', '#7BCFCB', '#4FC3B8', '#8FA9E5', '#5BC8D6', '#6BA5E0']

const initCharts = () => {
  // 1. 关注级别分布 - 环形饼图
  if (typeChartRef.value) {
    if (typeChart) typeChart.dispose()
    typeChart = echarts.init(typeChartRef.value)
    const typeData = Object.entries(chartData.value.type_distribution || {}).map(([name, value]) => ({ name, value }))
    typeChart.setOption({
      color: chartColors,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'horizontal', bottom: 0, textStyle: { fontSize: 11, color: '#7F8C8D' } },
      series: [{
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 13, fontWeight: 'bold' } },
        data: typeData.length ? typeData : [{ name: '暂无数据', value: 0 }]
      }]
    })
  }

  // 2. 月度趋势 - 折线图
  if (trendChartRef.value) {
    if (trendChart) trendChart.dispose()
    trendChart = echarts.init(trendChartRef.value)
    const months = (chartData.value.monthly_trend || []).map(m => m.month)
    const counts = (chartData.value.monthly_trend || []).map(m => m.count)
    trendChart.setOption({
      color: ['#5B92E5'],
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 16, top: 16, bottom: 30 },
      xAxis: { type: 'category', data: months, axisLabel: { fontSize: 10, color: '#7F8C8D', rotate: 30 } },
      yAxis: { type: 'value', minInterval: 1, axisLabel: { color: '#7F8C8D' }, splitLine: { lineStyle: { color: '#ECF1F7' } } },
      series: [{
        type: 'line',
        data: counts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(91,146,229,0.3)' },
          { offset: 1, color: 'rgba(91,146,229,0.02)' }
        ]) },
        lineStyle: { width: 2 }
      }]
    })
  }

  // 3. 访谈次数TOP5学生 - 横向柱状图
  if (topChartRef.value) {
    if (topChart) topChart.dispose()
    topChart = echarts.init(topChartRef.value)
    const top5 = (chartData.value.top_students || []).slice(0, 5).reverse()
    const names = top5.map(s => s.student_name)
    const vals = top5.map(s => s.count)
    topChart.setOption({
      color: ['#7BCFCB'],
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 60, right: 20, top: 10, bottom: 20 },
      xAxis: { type: 'value', minInterval: 1, axisLabel: { color: '#7F8C8D' }, splitLine: { lineStyle: { color: '#ECF1F7' } } },
      yAxis: { type: 'category', data: names, axisLabel: { color: '#2C3E50', fontSize: 12 } },
      series: [{
        type: 'bar',
        data: vals,
        barWidth: 16,
        itemStyle: { borderRadius: [0, 8, 8, 0], color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#7BCFCB' },
          { offset: 1, color: '#5B92E5' }
        ]) }
      }]
    })
  }
}

const loadStudents = async () => {
  try {
    const res = await request.get('/students/simple')
    students.value = Array.isArray(res) ? res : (res || [])
  } catch (error) {
    console.error('加载学生列表失败:', error)
  }
}

const onFilterChange = () => {
  currentPage.value = 1
  // 前端过滤自动生效，无需重新请求
}

const resetFilters = () => {
  filterClassId.value = null
  filterStudentId.value = null
  filterStatus.value = ''
  filterType.value = ''
  filterSemester.value = ''
  currentPage.value = 1
}

const loadSemesters = async () => {
  try {
    const res = await request.get('/semester-report/semesters')
    semesterList.value = Array.isArray(res) ? res : []
  } catch (error) {
    console.error('加载学期列表失败:', error)
  }
}

const loadTotalStudents = async () => {
  try {
    const res = await request.get('/interview/coverage')
    totalStudentCount.value = res?.total_students || 0
  } catch (error) {
    console.error('加载学生总数失败:', error)
  }
}

const showAddDialog = () => {
  isEdit.value = false
  editId.value = null
  form.value = {
    student_id: null,
    interview_date: '',
    interview_type: '常规访谈',
    interviewer: '',
    location: '',
    topic: '',
    content: '',
    feedback: '',
    follow_up: '',
    status: '已完成',
    remind_date: ''
  }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = { ...row }
  detailVisible.value = false
  dialogVisible.value = true
}

const showDetailDialog = (row) => {
  detailData.value = { ...row }
  detailVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.student_id) { ElMessage.warning('请选择学生'); return }
  if (!form.value.interview_date) { ElMessage.warning('请选择访谈日期'); return }
  submitting.value = true
  try {
    if (isEdit.value) {
      await request.put(`/interview/${editId.value}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await request.post('/interview/', form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
    loadStats()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除 ${row.student_name} 的访谈记录吗？`, '提示', { type: 'warning' })
    await request.delete(`/interview/${row.id}`)
    ElMessage.success('删除成功')
    loadData()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(async () => {
  if (!orgStore.orgTree?.length) {
    try { await orgStore.loadTree() } catch (e) {}
  }
  loadData()
  loadStats()
  loadChartData()
  loadStudents()
  loadSemesters()
  loadTotalStudents()
  window.addEventListener('resize', handleChartResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleChartResize)
  if (typeChart) { typeChart.dispose(); typeChart = null }
  if (trendChart) { trendChart.dispose(); trendChart = null }
  if (topChart) { topChart.dispose(); topChart = null }
})

const handleChartResize = () => {
  typeChart?.resize()
  trendChart?.resize()
  topChart?.resize()
}
</script>

<style scoped>
.interview-page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; color: #2C3E50; }
.page-actions { display: flex; align-items: center; }
.stats-cards { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08); }
.stat-label { font-size: 13px; color: #7F8C8D; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: 700; color: #2C3E50; }
.stat-value.pending { color: #E6A23C; }
.stat-value.done { color: #67C23A; }
.stat-value.follow { color: #F56C6C; }
.stat-value.coverage { color: #5B92E5; }
.stat-sub { font-size: 11px; color: #7F8C8D; margin-top: 4px; }
.table-container { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08); }
.charts-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.chart-card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08); }
.chart-title { font-size: 14px; font-weight: 600; color: #2C3E50; margin-bottom: 8px; }
.chart-body { width: 100%; height: 260px; }
</style>
