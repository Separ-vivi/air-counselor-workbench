<template>
  <div class="module-page">
    <div class="page-header">
      <h2>党团发展</h2>
      <div>
        <el-button
          type="success"
          :icon="Download"
          :disabled="!checkedRows.length"
          @click="exportSelected"
        >导出选中（{{ checkedRows.length }}）</el-button>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增记录</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="搜索">
          <el-input v-model="filter.kw" placeholder="学号/姓名/阶段/联系人/备注" clearable style="width: 240px" />
        </el-form-item>
        <el-form-item label="学生">
          <StudentSelect v-model="filter.student_id" style="width: 260px" @change="reload" />
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="filter.class_id" placeholder="全部班级" clearable filterable style="width: 220px" @change="reload">
            <el-option v-for="c in classes" :key="c.id" :label="c.class_name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="阶段">
          <el-select v-model="filter.stage" placeholder="全部阶段" clearable style="width: 220px" @change="reload">
            <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="filter.semester" placeholder="全部学期" clearable filterable style="width: 180px" @change="reload">
            <el-option v-for="s in semesterList" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker v-model="filter.dateRange" type="daterange" range-separator="至"
            start-placeholder="开始" end-placeholder="结束" format="YYYY-MM-DD"
            value-format="YYYY-MM-DD" style="width: 240px" @change="reload" />
        </el-form-item>
        <el-form-item>
          <el-button @click="reload">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="4" v-for="s in stageStats" :key="s.stage">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ s.stage }}</div>
          <div class="stat-value" :style="{ color: s.color }">{{ s.count }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 统计图表区域 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :sm="12" :lg="8">
        <div class="chart-card">
          <div class="chart-title">发展阶段分布</div>
          <div ref="stagePieRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="8">
        <div class="chart-card">
          <div class="chart-title">月度发展趋势</div>
          <div ref="monthlyTrendRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="8">
        <div class="chart-card">
          <div class="chart-title">TOP发展记录最多</div>
          <div ref="topStudentsRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <el-table
        :data="pagedList"
        v-loading="loading"
        stripe
        border
        max-height="600"
        row-key="id"
        @selection-change="onSelectionChange"
        @sort-change="onSort"
      >
        <el-table-column type="selection" width="45" reserve-selection />
        <el-table-column label="学生" prop="student_name" width="120" sortable="custom">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/students/${row.student_id}`)">{{ row.student_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="学号" prop="student_no" width="140" sortable="custom" />
        <el-table-column label="班级" prop="class_name" min-width="140" show-overflow-tooltip />
        <el-table-column label="发展阶段" prop="stage" width="150" sortable="custom">
          <template #default="{ row }">
            <el-tag :type="stageTag(row.stage)" size="small">{{ row.stage }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="阶段日期" prop="stage_date" width="130" sortable="custom" />
        <el-table-column label="联系人" prop="contact_person" width="120" sortable="custom" />
        <el-table-column label="备注" prop="notes" show-overflow-tooltip />
        <el-table-column label="操作" fixed="right" width="140">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openCreate(row)">编辑</el-button>
            <el-popconfirm title="确认删除？" @confirm="onDelete(row)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="reload"
          @current-change="reload"
        />
      </div>
    </el-card>

    <el-dialog v-model="dlg" :title="editing?.id ? '编辑党团进程' : '新增党团进程'" width="520px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="学生" prop="student_id">
          <StudentSelect v-model="form.student_id" />
        </el-form-item>
        <el-form-item label="发展阶段" prop="stage">
          <el-select v-model="form.stage" style="width: 100%" placeholder="选择阶段">
            <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="阶段日期">
          <el-date-picker v-model="form.stage_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_person" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="onSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import { party as partyApi } from '@/api/modules'
import http from '@/api/index.js'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'
import { triggerDownload, stampedName } from '@/utils/download'
import * as echarts from 'echarts'

const studentStore = useStudentStore()

const stages = [
  '递交入党申请书', '入党积极分子', '发展对象', '中共预备党员', '中共党员'
]
const stageColor = { '递交入党申请书': '#909399', '入党积极分子': '#409EFF', '发展对象': '#E6A23C', '中共预备党员': '#F56C6C', '中共党员': '#67C23A' }

const list = ref([])
const loading = ref(false)
const classes = ref([])
const filter = reactive({ student_id: null, stage: '', kw: '', class_id: null, semester: '', dateRange: null })

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 学期列表（从数据动态提取）
const semesterList = computed(() => {
  const s = new Set()
  list.value.forEach(r => {
    if (r.semester) s.add(r.semester)
    else if (r.stage_date) {
      const d = new Date(r.stage_date)
      const y = d.getFullYear()
      const m = d.getMonth() + 1
      const ay = m >= 9 ? y : y - 1
      s.add(`${ay}-${ay + 1}-${m >= 2 && m < 9 ? 2 : 1}`)
    }
  })
  return [...s].filter(Boolean).sort().reverse()
})

// 前端分页 + 筛选
const pagedList = computed(() => {
  let data = list.value
  if (filter.semester) {
    data = data.filter(r => {
      if (r.semester) return r.semester === filter.semester
      if (r.stage_date) {
        const d = new Date(r.stage_date)
        const y = d.getFullYear()
        const m = d.getMonth() + 1
        const ay = m >= 9 ? y : y - 1
        const sem = `${ay}-${ay + 1}-${m >= 2 && m < 9 ? 2 : 1}`
        return sem === filter.semester
      }
      return false
    })
  }
  if (filter.dateRange && filter.dateRange.length === 2) {
    data = data.filter(r => r.stage_date && r.stage_date >= filter.dateRange[0] && r.stage_date <= filter.dateRange[1])
  }
  total.value = data.length
  const start = (currentPage.value - 1) * pageSize.value
  return data.slice(start, start + pageSize.value)
})

const resetFilters = () => {
  filter.student_id = null
  filter.stage = ''
  filter.kw = ''
  filter.class_id = null
  filter.semester = ''
  filter.dateRange = null
  currentPage.value = 1
  reload()
}

// 冰蓝薄荷色系
const chartColors = ['#5B92E5', '#7BCFCB', '#4FC3B8', '#8FA9E5', '#A8D5E2', '#6BB5C9']

// 图表容器引用
const stagePieRef = ref(null)
const monthlyTrendRef = ref(null)
const topStudentsRef = ref(null)

// 图表实例
let stagePieChart = null
let monthlyTrendChart = null
let topStudentsChart = null

// 初始化阶段分布饼图
const initStagePie = (data) => {
  if (!stagePieRef.value) return
  if (stagePieChart) stagePieChart.dispose()
  stagePieChart = echarts.init(stagePieRef.value)
  const pieData = data.map((item, idx) => ({
    name: item.stage,
    value: item.count,
    itemStyle: { color: chartColors[idx % chartColors.length] }
  }))
  stagePieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#5A6B80', fontSize: 12 }
    },
    series: [{
      type: 'pie',
      radius: ['0%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#ECF1F7', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{c}人', color: '#5A6B80', fontSize: 11 },
      labelLine: { lineStyle: { color: '#B0C4DE' } },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.15)' },
        label: { fontSize: 13, fontWeight: 'bold' }
      },
      data: pieData
    }]
  })
}

// 初始化月度趋势折线图
const initMonthlyTrend = (data) => {
  if (!monthlyTrendRef.value) return
  if (monthlyTrendChart) monthlyTrendChart.dispose()
  monthlyTrendChart = echarts.init(monthlyTrendRef.value)
  const months = data.map(d => d.month)
  const counts = data.map(d => d.count)
  monthlyTrendChart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>新增: {c}人' },
    grid: { left: 45, right: 20, top: 20, bottom: 35 },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { color: '#5A6B80', fontSize: 11, rotate: months.length > 6 ? 30 : 0 },
      axisLine: { lineStyle: { color: '#C8D6E5' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#5A6B80', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E8EFF7', type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [{
      type: 'line',
      data: counts,
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      lineStyle: { color: '#5B92E5', width: 2.5 },
      itemStyle: { color: '#5B92E5', borderColor: '#fff', borderWidth: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(91,146,229,0.35)' },
          { offset: 1, color: 'rgba(91,146,229,0.05)' }
        ])
      }
    }]
  })
}

// 初始化TOP学生柱状图
const initTopStudents = (data) => {
  if (!topStudentsRef.value) return
  if (topStudentsChart) topStudentsChart.dispose()
  topStudentsChart = echarts.init(topStudentsRef.value)
  const names = data.map(d => d.student_name)
  const counts = data.map(d => d.count)
  topStudentsChart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>记录次数: {c}' },
    grid: { left: 70, right: 20, top: 20, bottom: 35 },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#5A6B80', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E8EFF7', type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'category',
      data: names.reverse(),
      axisLabel: { color: '#5A6B80', fontSize: 12 },
      axisLine: { lineStyle: { color: '#C8D6E5' } },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: counts.reverse(),
      barWidth: 18,
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#7BCFCB' },
          { offset: 1, color: '#4FC3B8' }
        ])
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#5B92E5' },
            { offset: 1, color: '#8FA9E5' }
          ])
        }
      },
      label: { show: true, position: 'right', color: '#5A6B80', fontSize: 11 }
    }]
  })
}

// 加载图表数据
const loadChartData = async () => {
  try {
    const res = await http.get('/party-progress/chart-data')
    const data = res?.data || res || {}
    if (data.stage_distribution?.length) initStagePie(data.stage_distribution)
    else initStagePie(stages.map(s => ({ stage: s, count: 0 })))
    if (data.monthly_trend?.length) initMonthlyTrend(data.monthly_trend)
    else initMonthlyTrend([])
    if (data.top_students?.length) initTopStudents(data.top_students)
    else initTopStudents([])
  } catch (e) {
    console.warn('党团图表数据加载失败，使用本地统计', e)
    // 降级：使用本地 stageStats 数据
    initStagePie(stages.map(s => ({ stage: s, count: list.value.filter(r => r.stage === s).length })))
    initMonthlyTrend([])
    initTopStudents([])
  }
}

// 窗口 resize 处理
const handleResize = () => {
  stagePieChart?.resize()
  monthlyTrendChart?.resize()
  topStudentsChart?.resize()
}

// v3j-B-b03 · 排序 + 搜索 + 多选
const sortBy = ref('stage_date')
const sortOrder = ref('desc')
const checkedRows = ref([])
const onSelectionChange = (rows) => { checkedRows.value = rows }
const onSort = ({ prop, order }) => {
  sortBy.value = prop || 'stage_date'
  sortOrder.value = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : 'desc')
  reload()
}
let _searchTimer = null
watch(() => filter.kw, () => {
  clearTimeout(_searchTimer)
  _searchTimer = setTimeout(() => reload(), 300)
})

const stageTag = (s) => {
  const m = { '递交入党申请书': 'info', '入党积极分子': 'primary', '发展对象': 'warning', '中共预备党员': 'danger', '中共党员': 'success' }
  return m[s] || ''
}
const stageStats = computed(() =>
  stages.map((s) => ({ stage: s, count: list.value.filter((r) => r.stage === s).length, color: stageColor[s] }))
)

const buildParams = () => {
  const params = {}
  if (filter.student_id) params.student_id = filter.student_id
  if (filter.stage) params.stage = filter.stage
  if (filter.class_id) params.class_id = filter.class_id
  if (filter.kw) params.search = filter.kw
  return params
}

const reload = async () => {
  loading.value = true
  try {
    const params = buildParams()
    if (sortBy.value) params.sort_by = sortBy.value
    if (sortOrder.value) params.order = sortOrder.value
    const res = await partyApi.list(params)
    list.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { loading.value = false }
}

const exportSelected = async () => {
  if (!checkedRows.value.length) { ElMessage.warning('请先勾选要导出的党团发展记录'); return }
  try {
    const ids = checkedRows.value.map(r => r.id)
    const blob = await partyApi.exportByIds(ids)
    triggerDownload(blob, stampedName(`党团发展_选中${ids.length}条`))
    ElMessage.success(`已导出 ${ids.length} 条`)
  } catch (e) { ElMessage.error('导出失败') }
}
const exportAll = async () => {
  try {
    const blob = await partyApi.exportAll(buildParams())
    triggerDownload(blob, stampedName(`党团发展_全部`))
    ElMessage.success('已导出全部')
  } catch (e) { ElMessage.error('导出失败') }
}

const dlg = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({ student_id: null, stage: '', stage_date: '', contact_person: '', notes: '' })
const form = reactive(defaultForm())
const rules = {
  student_id: [{ required: true, message: '请选择学生', trigger: 'change' }],
  stage: [{ required: true, message: '请选择阶段', trigger: 'change' }]
}
const openCreate = (row) => {
  editing.value = row
  Object.assign(form, defaultForm(), row || {})
  dlg.value = true
}
const onSave = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = { ...form }
    if (editing.value?.id) {
      await partyApi.update(editing.value.id, payload)
      ElMessage.success('已更新')
    } else {
      await partyApi.create(payload)
      ElMessage.success('已创建')
    }
    dlg.value = false
    studentStore.bumpRefresh()
    reload()
  } finally { saving.value = false }
}
const onDelete = async (row) => {
  await partyApi.remove(row.id)
  ElMessage.success('已删除')
  studentStore.bumpRefresh()
  reload()
}

watch(() => studentStore.refreshBumper, reload)

const loadClasses = async () => {
  try {
    const res = await http.get('/org/classes')
    classes.value = Array.isArray(res) ? res : (res?.items || res?.data || [])
  } catch (e) { classes.value = [] }
}

onMounted(() => {
  loadClasses()
  reload()
  loadChartData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  stagePieChart?.dispose()
  monthlyTrendChart?.dispose()
  topStudentsChart?.dispose()
  stagePieChart = null
  monthlyTrendChart = null
  topStudentsChart = null
})
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.stat-card { border-radius: 12px; text-align: center; }
.stat-label { color: #909399; font-size: 13px; margin-bottom: 8px; }
.stat-value { font-size: 24px; font-weight: 600; }

/* 图表区域样式 */
.chart-row { margin-bottom: 16px; }
.chart-card {
  background: #ECF1F7;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(91, 146, 229, 0.08);
  transition: box-shadow 0.2s;
}
.chart-card:hover {
  box-shadow: 0 4px 12px rgba(91, 146, 229, 0.15);
}
.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #3A4F6B;
  margin-bottom: 10px;
  padding-left: 4px;
}
.chart-container {
  width: 100%;
  height: 300px;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
