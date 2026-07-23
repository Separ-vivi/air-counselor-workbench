<template>
  <div class="module-page">
    <div class="page-header">
      <h2>心理关怀</h2>
      <div>
        <el-button :icon="Bell" @click="loadReminders">提醒 ({{ reminders.length }})</el-button>
        <el-button
          type="warning"
          :disabled="!checkedRows.length"
          :loading="batchReminding"
          @click="onBatchMarkReminded(true)"
        >批量标记已提醒（{{ checkedRows.length }}）</el-button>
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
          <el-input v-model="filter.kw" placeholder="学生姓名/学号/备注" clearable style="width: 220px" />
        </el-form-item>
        <el-form-item label="学生">
          <StudentSelect v-model="filter.student_id" style="width: 260px" @change="reload" />
        </el-form-item>
        <el-form-item label="关注等级">
          <el-select v-model="filter.attention_level" placeholder="全部" clearable style="width: 180px" @change="reload">
            <el-option v-for="l in levels" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="提醒状态">
          <el-select v-model="filter.reminded_state" placeholder="全部" clearable style="width: 140px">
            <el-option label="仅未提醒" value="unreminded" />
            <el-option label="仅已提醒" value="reminded" />
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
      </el-form>
    </el-card>

    <el-alert v-if="reminders.length" type="warning" show-icon :closable="false" style="margin-bottom: 12px">
      有 {{ reminders.length }} 条心理关注提醒需要处理
    </el-alert>

    <!-- 统计图表区域 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :sm="12" :lg="8">
        <div class="chart-card">
          <div class="chart-title">关注等级分布</div>
          <div ref="levelDistRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="8">
        <div class="chart-card">
          <div class="chart-title">月度咨询趋势</div>
          <div ref="monthlyTrendRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="8">
        <div class="chart-card">
          <div class="chart-title">情绪标签分布</div>
          <div ref="emotionTagsRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <!-- TOP关注学生卡片 -->
    <div class="top-students-section" v-if="topStudents.length">
      <div class="chart-title" style="margin-bottom: 12px;">TOP关注学生</div>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :lg="8" v-for="(stu, idx) in topStudents" :key="stu.student_no" style="margin-bottom: 12px;">
          <div class="top-student-card">
            <div class="top-student-rank" :style="{ background: rankColors[idx] || '#8FA9E5' }">{{ idx + 1 }}</div>
            <div class="top-student-info">
              <div class="top-student-name">{{ stu.student_name }}</div>
              <div class="top-student-no">{{ stu.student_no }}</div>
            </div>
            <div class="top-student-count">
              <span class="count-number">{{ stu.count }}</span>
              <span class="count-label">次咨询</span>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

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
        <el-table-column label="学生" prop="student_name" width="110" sortable="custom">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/students/${row.student_id}`)">{{ row.student_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="学号" prop="student_no" width="140" sortable="custom" />
        <el-table-column label="班级" prop="class_name" min-width="140" show-overflow-tooltip sortable="custom" />
        <el-table-column label="关注等级" prop="attention_level" width="120" sortable="custom">
          <template #default="{ row }">
            <el-tag :style="lvTagStyle(row.attention_level)" size="small">{{ row.attention_level || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="测评日期" prop="assessment_date" width="130" sortable="custom" />
        <el-table-column label="咨询次数" prop="counseling_count" width="100" align="center" sortable="custom" />
        <el-table-column label="下次跟进" prop="next_follow_up" width="130" sortable="custom" />
        <el-table-column label="备注" prop="notes" show-overflow-tooltip />
        <el-table-column label="已提醒" prop="reminded" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.reminded"
              :loading="row._remindLoading"
              @change="toggleReminded(row)"
              inline-prompt
              active-text="已"
              inactive-text="未"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
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
          @size-change="currentPage = 1"
        />
      </div>
    </el-card>

    <el-dialog v-model="dlg" :title="editing?.id ? '编辑心理档案' : '新增心理档案'" width="520px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="学生" prop="student_id">
          <StudentSelect v-model="form.student_id" />
        </el-form-item>
        <el-form-item label="关注等级" prop="attention_level">
          <el-select v-model="form.attention_level" style="width: 100%" placeholder="选择等级">
            <el-option v-for="l in levels" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="测评日期">
          <el-date-picker v-model="form.assessment_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="咨询次数">
          <el-input-number v-model="form.counseling_count" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="下次跟进">
          <el-date-picker v-model="form.next_follow_up" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" />
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
import { Plus, Bell, Download } from '@element-plus/icons-vue'
import { psychology as psyApi } from '@/api/modules'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'
import { triggerDownload, stampedName } from '@/utils/download'
import * as echarts from 'echarts'
import http from '@/api/index.js'

const studentStore = useStudentStore()

const levels = ['一级关注', '二级关注', '三级关注', '普通']
const list = ref([])
const reminders = ref([])
const loading = ref(false)
const filter = reactive({ student_id: null, attention_level: '', kw: '', reminded_state: '', semester: '', dateRange: null })

// 冰蓝薄荷色系
const chartColors = ['#5B92E5', '#7BCFCB', '#4FC3B8', '#8FA9E5', '#A8D5E2', '#6BB5C9', '#95B8D1']
const rankColors = ['#5B92E5', '#7BCFCB', '#4FC3B8', '#8FA9E5', '#A8D5E2']

// 图表容器引用
const levelDistRef = ref(null)
const monthlyTrendRef = ref(null)
const emotionTagsRef = ref(null)

// 图表实例
let levelDistChart = null
let monthlyTrendChart = null
let emotionTagsChart = null

// TOP关注学生数据
const topStudents = ref([])

// 初始化关注等级分布环形图
const initLevelDist = (data) => {
  if (!levelDistRef.value) return
  if (levelDistChart) levelDistChart.dispose()
  levelDistChart = echarts.init(levelDistRef.value)
  const pieData = data.map((item, idx) => ({
    name: item.level,
    value: item.count,
    itemStyle: { color: chartColors[idx % chartColors.length] }
  }))
  levelDistChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#5A6B80', fontSize: 12 }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
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

// 初始化月度咨询趋势折线图
const initMonthlyTrend = (data) => {
  if (!monthlyTrendRef.value) return
  if (monthlyTrendChart) monthlyTrendChart.dispose()
  monthlyTrendChart = echarts.init(monthlyTrendRef.value)
  const months = data.map(d => d.month)
  const counts = data.map(d => d.count)
  monthlyTrendChart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>咨询: {c}次' },
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
      lineStyle: { color: '#7BCFCB', width: 2.5 },
      itemStyle: { color: '#7BCFCB', borderColor: '#fff', borderWidth: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(123,207,203,0.35)' },
          { offset: 1, color: 'rgba(123,207,203,0.05)' }
        ])
      }
    }]
  })
}

// 初始化情绪标签分布柱状图
const initEmotionTags = (data) => {
  if (!emotionTagsRef.value) return
  if (emotionTagsChart) emotionTagsChart.dispose()
  emotionTagsChart = echarts.init(emotionTagsRef.value)
  const tags = data.map(d => d.tag)
  const counts = data.map(d => d.count)
  emotionTagsChart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>出现频次: {c}' },
    grid: { left: 50, right: 20, top: 20, bottom: 35 },
    xAxis: {
      type: 'category',
      data: tags,
      axisLabel: { color: '#5A6B80', fontSize: 11, rotate: tags.length > 5 ? 25 : 0 },
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
      type: 'bar',
      data: counts.map((val, idx) => ({
        value: val,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [
            { offset: 0, color: '#8FA9E5' },
            { offset: 1, color: chartColors[idx % chartColors.length] }
          ]),
          borderRadius: [6, 6, 0, 0]
        }
      })),
      barWidth: 28,
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [
            { offset: 0, color: '#5B92E5' },
            { offset: 1, color: '#4FC3B8' }
          ])
        }
      },
      label: { show: true, position: 'top', color: '#5A6B80', fontSize: 11 }
    }]
  })
}

// 加载图表数据
const loadChartData = async () => {
  try {
    const res = await http.get('/psychology/chart-data')
    const data = res?.data || res || {}
    if (data.level_distribution?.length) initLevelDist(data.level_distribution)
    else initLevelDist(levels.map(l => ({ level: l, count: 0 })))
    if (data.monthly_trend?.length) initMonthlyTrend(data.monthly_trend)
    else initMonthlyTrend([])
    if (data.emotion_tags_distribution?.length) initEmotionTags(data.emotion_tags_distribution)
    else initEmotionTags([])
    if (data.top_students?.length) topStudents.value = data.top_students.slice(0, 5)
    else topStudents.value = []
  } catch (e) {
    console.warn('心理图表数据加载失败，使用本地统计', e)
    // 降级：使用本地统计
    const localLevelDist = levels.map(l => ({
      level: l,
      count: list.value.filter(r => r.attention_level === l).length
    }))
    initLevelDist(localLevelDist)
    initMonthlyTrend([])
    initEmotionTags([])
    topStudents.value = []
  }
}

// 窗口 resize 处理
const handleResize = () => {
  levelDistChart?.resize()
  monthlyTrendChart?.resize()
  emotionTagsChart?.resize()
}

// v3j-B-b03 · 排序 + 搜索 + 多选
const sortBy = ref('assessment_date')
const sortOrder = ref('desc')
const checkedRows = ref([])
const onSelectionChange = (rows) => { checkedRows.value = rows }
const onSort = ({ prop, order }) => {
  sortBy.value = prop || 'assessment_date'
  sortOrder.value = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : 'desc')
  reload()
}
let _searchTimer = null
watch(() => filter.kw, () => {
  clearTimeout(_searchTimer)
  _searchTimer = setTimeout(() => reload(), 300)
})

const lvTag = (l) => {
  if (!l) return ''
  if (l.includes('一')) return 'danger'
  if (l.includes('二')) return 'warning'
  if (l.includes('三')) return 'info'
  return ''
}

// v3j-D · 心理关注等级马卡龙化（对齐 ClassPsychology）
const lvTagStyle = (l) => {
  if (!l) return { background: '#F0F2F5', color: '#909399', border: 'none' }
  if (l.includes('一')) return { background: '#FF9AA2', color: '#7A2E36', border: 'none', fontWeight: 600 }
  if (l.includes('二')) return { background: '#FFDAC1', color: '#8A4E1F', border: 'none', fontWeight: 600 }
  if (l.includes('三')) return { background: '#B5EAD7', color: '#1F5A46', border: 'none', fontWeight: 600 }
  if (l.includes('普通')) return { background: '#C7CEEA', color: '#3B4B7A', border: 'none', fontWeight: 600 }
  return { background: '#F0F2F5', color: '#909399', border: 'none' }
}

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 学期列表（从数据动态提取）
const semesterList = computed(() => {
  const s = new Set()
  list.value.forEach(r => {
    if (r.semester) s.add(r.semester)
    else if (r.record_date || r.assessment_date) {
      const d = new Date(r.record_date || r.assessment_date)
      const y = d.getFullYear()
      const m = d.getMonth() + 1
      const ay = m >= 9 ? y : y - 1
      s.add(`${ay}-${ay + 1}-${m >= 2 && m < 9 ? 2 : 1}`)
    }
  })
  return [...s].filter(Boolean).sort().reverse()
})

const resetFilters = () => {
  filter.student_id = null
  filter.attention_level = ''
  filter.kw = ''
  filter.reminded_state = ''
  filter.semester = ''
  filter.dateRange = null
  currentPage.value = 1
  reload()
}

// 前端二次过滤（提醒状态 + 学期 + 日期范围） + 分页
const filteredList = computed(() => {
  let rs = list.value
  if (filter.reminded_state === 'reminded') rs = rs.filter((r) => !!r.reminded)
  else if (filter.reminded_state === 'unreminded') rs = rs.filter((r) => !r.reminded)
  if (filter.semester) {
    rs = rs.filter(r => {
      if (r.semester) return r.semester === filter.semester
      const dStr = r.record_date || r.assessment_date
      if (dStr) {
        const d = new Date(dStr)
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
    rs = rs.filter(r => {
      const dStr = r.record_date || r.assessment_date
      return dStr && dStr >= filter.dateRange[0] && dStr <= filter.dateRange[1]
    })
  }
  return rs
})

const total = computed(() => filteredList.value.length)
const pagedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})

// v3h: 单条切换已提醒
const toggleReminded = async (row) => {
  row._remindLoading = true
  try {
    const res = await psyApi.toggleReminded(row.id)
    row.reminded = !!res?.reminded
    row.reminded_at = res?.reminded_at || null
    ElMessage.success(row.reminded ? '已标记为已提醒' : '已恢复为未提醒')
    await loadReminders()
  } catch (e) {
    row.reminded = !row.reminded
    ElMessage.error('切换提醒状态失败')
  } finally {
    row._remindLoading = false
  }
}

// v3h: 批量标记已提醒
const batchReminding = ref(false)
const onBatchMarkReminded = async (reminded) => {
  if (!checkedRows.value.length) { ElMessage.warning('请先勾选要提醒的记录'); return }
  batchReminding.value = true
  try {
    const ids = checkedRows.value.map(r => r.id)
    const res = await psyApi.batchMarkReminded(ids, reminded)
    ElMessage.success(`已批量标记 ${res?.updated ?? ids.length} 条为${reminded ? '已提醒' : '未提醒'}`)
    await reload()
    await loadReminders()
  } catch (e) {
    ElMessage.error('批量标记失败')
  } finally { batchReminding.value = false }
}

const reload = async () => {
  loading.value = true
  try {
    const params = {}
    if (filter.student_id) params.student_id = filter.student_id
    if (filter.attention_level) params.attention_level = filter.attention_level
    if (filter.kw) params.search = filter.kw
    if (sortBy.value) params.sort_by = sortBy.value
    if (sortOrder.value) params.order = sortOrder.value
    const res = await psyApi.list(params)
    list.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { loading.value = false }
}

const exportSelected = async () => {
  if (!checkedRows.value.length) { ElMessage.warning('请先勾选要导出的心理档案'); return }
  try {
    const ids = checkedRows.value.map(r => r.id)
    const blob = await psyApi.exportByIds(ids)
    triggerDownload(blob, stampedName(`心理关怀_选中${ids.length}条`))
    ElMessage.success(`已导出 ${ids.length} 条`)
  } catch (e) { ElMessage.error('导出失败') }
}
const exportAll = async () => {
  try {
    const params = {}
    if (filter.student_id) params.student_id = filter.student_id
    if (filter.attention_level) params.attention_level = filter.attention_level
    if (filter.kw) params.search = filter.kw
    const blob = await psyApi.exportAll(params)
    triggerDownload(blob, stampedName(`心理关怀_全部`))
    ElMessage.success('已导出全部')
  } catch (e) { ElMessage.error('导出失败') }
}

const loadReminders = async () => {
  try {
    const res = await psyApi.reminders()
    reminders.value = Array.isArray(res) ? res : (res?.items || [])
  } catch (e) { reminders.value = [] }
}

const dlg = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({ student_id: null, attention_level: '', assessment_date: '', counseling_count: 0, next_follow_up: '', notes: '' })
const form = reactive(defaultForm())
const rules = {
  student_id: [{ required: true, message: '请选择学生', trigger: 'change' }],
  attention_level: [{ required: true, message: '请选择关注等级', trigger: 'change' }]
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
    if (editing.value?.id) {
      await psyApi.update(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await psyApi.create(form)
      ElMessage.success('已创建')
    }
    dlg.value = false
    studentStore.bumpRefresh()
    reload()
  } finally { saving.value = false }
}
const onDelete = async (row) => {
  await psyApi.remove(row.id)
  ElMessage.success('已删除')
  studentStore.bumpRefresh()
  reload()
}

watch(() => studentStore.refreshBumper, reload)
onMounted(() => {
  reload()
  loadReminders()
  loadChartData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  levelDistChart?.dispose()
  monthlyTrendChart?.dispose()
  emotionTagsChart?.dispose()
  levelDistChart = null
  monthlyTrendChart = null
  emotionTagsChart = null
})
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }

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

/* TOP关注学生卡片样式 */
.top-students-section {
  margin-bottom: 16px;
  padding: 16px;
  background: #ECF1F7;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(91, 146, 229, 0.08);
}
.top-student-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #F5F8FC;
  border-radius: 10px;
  border: 1px solid #DDE5F0;
  transition: all 0.2s;
}
.top-student-card:hover {
  background: #EDF2FA;
  border-color: #B8CCE8;
  box-shadow: 0 2px 8px rgba(91, 146, 229, 0.12);
}
.top-student-rank {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}
.top-student-info {
  flex: 1;
  min-width: 0;
}
.top-student-name {
  font-size: 14px;
  font-weight: 600;
  color: #3A4F6B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.top-student-no {
  font-size: 12px;
  color: #8A9BB5;
  margin-top: 2px;
}
.top-student-count {
  text-align: center;
  flex-shrink: 0;
}
.count-number {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #5B92E5;
  line-height: 1.1;
}
.count-label {
  display: block;
  font-size: 11px;
  color: #8A9BB5;
  margin-top: 2px;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
