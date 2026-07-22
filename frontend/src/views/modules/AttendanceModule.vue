<template>
  <div class="attendance-page">
    <div class="page-header">
      <h2>查课考勤</h2>
      <div class="page-actions">
        <el-button @click="handleExport" :loading="exporting" plain>
          <el-icon><Download /></el-icon>导出Excel
        </el-button>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>新增记录
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#5B92E5,#7BCFCB)">
          <el-icon :size="22"><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">总异常次数</div>
          <div class="stat-value">{{ statsData.total || 0 }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#7BCFCB,#5B92E5)">
          <el-icon :size="22"><User /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">涉及学生数</div>
          <div class="stat-value">{{ statsData.student_count || 0 }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#E6A23C,#F5C76C)">
          <el-icon :size="22"><Timer /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">本周新增</div>
          <div class="stat-value accent-warn">{{ statsData.week_new || 0 }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#F56C6C,#F89898)">
          <el-icon :size="22"><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">旷课占比</div>
          <div class="stat-value accent-danger">{{ statsData.absent_ratio || 0 }}%</div>
        </div>
      </div>
    </div>

    <div class="main-layout">
      <!-- 左侧：筛选 + 表格 -->
      <div class="left-panel">
        <!-- 筛选栏 -->
        <el-card shadow="never" class="filter-card">
          <el-form :inline="true" class="filter-form">
            <el-form-item label="班级">
              <el-select v-model="filterClassId" placeholder="全部班级" filterable clearable style="width:180px" @change="loadData">
                <el-option v-for="c in allClasses" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="异常类型">
              <el-select v-model="filterType" placeholder="全部" clearable @change="loadData" style="width:110px">
                <el-option label="迟到" value="迟到" />
                <el-option label="早退" value="早退" />
                <el-option label="旷课" value="旷课" />
              </el-select>
            </el-form-item>
            <el-form-item label="学期">
              <el-select v-model="filterSemester" placeholder="全部学期" clearable @change="loadData" style="width:160px">
                <el-option v-for="s in semesterList" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
            <el-form-item label="日期范围">
              <el-date-picker v-model="filterDateRange" type="daterange" range-separator="至"
                start-placeholder="开始" end-placeholder="结束" format="YYYY-MM-DD"
                value-format="YYYY-MM-DD" style="width:240px" @change="loadData" />
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="filterKeyword" placeholder="姓名/学号/课程" clearable style="width:160px"
                @clear="loadData" @keyup.enter="loadData" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadData" plain>查询</el-button>
              <el-button @click="resetFilters">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 数据表格 -->
        <el-card shadow="never" class="table-card">
          <el-table :data="tableData" style="width:100%" v-loading="loading" row-key="id"
            :default-sort="{ prop: 'exception_date', order: 'descending' }">
            <el-table-column prop="student_no" label="学号" width="120" sortable />
            <el-table-column prop="student_name" label="姓名" width="90" sortable />
            <el-table-column prop="class_name" label="班级" width="140" show-overflow-tooltip sortable />
            <el-table-column prop="exception_date" label="日期" width="110" sortable />
            <el-table-column prop="course_name" label="课程" min-width="160" show-overflow-tooltip sortable />
            <el-table-column prop="exception_type" label="异常类型" width="100" sortable>
              <template #default="{ row }">
                <el-tag :type="typeTagMap[row.exception_type] || 'info'" size="small" effect="plain">
                  {{ row.exception_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              @current-change="loadData"
              @size-change="loadData"
            />
          </div>
        </el-card>
      </div>

      <!-- 右侧面板 -->
      <div class="right-panel">
        <!-- 高频异常学生 TOP5 -->
        <el-card shadow="never" class="side-card">
          <template #header>
            <span class="side-card-title">高频异常学生 TOP5</span>
          </template>
          <div class="top-list">
            <div v-for="(s, idx) in topStudents" :key="s.student_id" class="top-item">
              <span class="top-rank" :class="{ 'rank-top3': idx < 3 }">{{ idx + 1 }}</span>
              <div class="top-info">
                <span class="top-name">{{ s.student_name }}</span>
                <span class="top-class">{{ s.class_name }}</span>
              </div>
              <span class="top-count">{{ s.count }}次</span>
            </div>
            <el-empty v-if="!topStudents.length" description="暂无数据" :image-size="48" />
          </div>
        </el-card>

        <!-- 异常类型分布饼图 -->
        <el-card shadow="never" class="side-card">
          <template #header>
            <span class="side-card-title">异常类型分布</span>
          </template>
          <div ref="pieChartRef" class="pie-chart-container"></div>
        </el-card>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑考勤异常' : '新增考勤异常'" width="560px" destroy-on-close>
      <el-form :model="form" label-width="90px">
        <el-form-item label="学生" required>
          <el-select v-model="form.student_id" filterable remote :remote-method="searchStudents"
            placeholder="输入姓名/学号搜索" style="width:100%" :loading="studentSearchLoading">
            <el-option v-for="s in studentOptions" :key="s.id"
              :label="`${s.student_no} - ${s.name} (${s.class_name || ''})`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker v-model="form.exception_date" type="date" placeholder="选择日期"
            format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="课程名称">
          <el-input v-model="form.course_name" placeholder="请输入课程名称" />
        </el-form-item>
        <el-form-item label="异常类型" required>
          <el-select v-model="form.exception_type" style="width:100%">
            <el-option label="迟到" value="迟到" />
            <el-option label="早退" value="早退" />
            <el-option label="旷课" value="旷课" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import request from '@/api/index'
import { useOrgStore } from '@/stores/org'

const orgStore = useOrgStore()

// ===== 状态 =====
const loading = ref(false)
const submitting = ref(false)
const exporting = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const statsData = ref({})
const topStudents = ref([])
const pieChartRef = ref(null)
let pieChart = null

// 筛选条件
const filterClassId = ref(null)
const filterType = ref('')
const filterSemester = ref('')
const filterDateRange = ref(null)
const filterKeyword = ref('')

// 弹窗
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({
  student_id: null,
  exception_date: '',
  course_name: '',
  exception_type: '旷课',
  notes: ''
})

// 学生搜索
const studentOptions = ref([])
const studentSearchLoading = ref(false)

// 类型标签颜色
const typeTagMap = { '迟到': 'warning', '早退': '', '旷课': 'danger' }

// 班级列表
const allClasses = computed(() => orgStore.allClasses || [])

// 学期列表（动态生成近4年）
const semesterList = computed(() => {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth() + 1
  const list = []
  const startYear = y - 3
  for (let ay = startYear; ay <= y; ay++) {
    list.push(`${ay}-${ay + 1}-1`)
    list.push(`${ay}-${ay + 1}-2`)
  }
  // 过滤掉未来学期
  return list.filter(s => {
    const parts = s.split('-')
    const sy = parseInt(parts[0])
    const term = parseInt(parts[2])
    if (sy > y) return false
    if (sy === y && term === 2 && m < 2) return false
    return true
  }).reverse()
})

// ===== 数据加载 =====

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value
    }
    if (filterClassId.value) params.class_id = filterClassId.value
    if (filterType.value) params.exception_type = filterType.value
    if (filterSemester.value) params.semester = filterSemester.value
    if (filterKeyword.value) params.keyword = filterKeyword.value
    if (filterDateRange.value && filterDateRange.value.length === 2) {
      params.date_from = filterDateRange.value[0]
      params.date_to = filterDateRange.value[1]
    }
    const res = await request.get('/attendance/', { params })
    tableData.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    console.error('加载数据失败:', e)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await request.get('/attendance/stats')
    statsData.value = res || {}
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

const loadTopStudents = async () => {
  try {
    const res = await request.get('/attendance/top-students', { params: { limit: 5 } })
    topStudents.value = res || []
  } catch (e) {
    console.error('加载TOP学生失败:', e)
  }
}

const renderPieChart = () => {
  if (!pieChartRef.value) return
  if (!pieChart) {
    pieChart = echarts.init(pieChartRef.value)
  }
  const byType = statsData.value.by_type || {}
  const data = Object.entries(byType).map(([name, value]) => ({ name, value }))
  const colorMap = { '迟到': '#E6A23C', '早退': '#5B92E5', '旷课': '#F56C6C' }
  const colors = data.map(d => colorMap[d.name] || '#7BCFCB')

  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 12, color: '#606266' } },
    color: colors,
    series: [{
      type: 'pie',
      radius: ['40%', '68%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data
    }]
  })
}

// ===== 弹窗操作 =====

const searchStudents = async (query) => {
  if (!query || query.length < 1) { studentOptions.value = []; return }
  studentSearchLoading.value = true
  try {
    const res = await request.get('/students/simple')
    const all = Array.isArray(res) ? res : []
    const q = query.toLowerCase()
    studentOptions.value = all.filter(s =>
      s.name?.toLowerCase().includes(q) || s.student_no?.includes(q)
    ).slice(0, 50)
  } catch (e) {
    console.error('搜索学生失败:', e)
  } finally {
    studentSearchLoading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  editId.value = null
  form.value = {
    student_id: null,
    exception_date: '',
    course_name: '',
    exception_type: '旷课',
    notes: ''
  }
  studentOptions.value = []
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    student_id: row.student_id,
    exception_date: row.exception_date,
    course_name: row.course_name,
    exception_type: row.exception_type,
    notes: row.notes || ''
  }
  // 把当前学生加入选项
  studentOptions.value = [{
    id: row.student_id,
    name: row.student_name,
    student_no: row.student_no,
    class_name: row.class_name
  }]
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.student_id) { ElMessage.warning('请选择学生'); return }
  if (!form.value.exception_date) { ElMessage.warning('请选择日期'); return }
  if (!form.value.exception_type) { ElMessage.warning('请选择异常类型'); return }
  submitting.value = true
  try {
    if (isEdit.value) {
      await request.put(`/attendance/${editId.value}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await request.post('/attendance/', form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
    loadStats()
    loadTopStudents()
  } catch (e) {
    console.error('提交失败:', e)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除 ${row.student_name} 的考勤异常记录吗？`, '提示', { type: 'warning' })
    await request.delete(`/attendance/${row.id}`)
    ElMessage.success('删除成功')
    loadData()
    loadStats()
    loadTopStudents()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败:', e)
      ElMessage.error('删除失败')
    }
  }
}

// ===== 导出 =====

const handleExport = async () => {
  exporting.value = true
  try {
    const params = {}
    if (filterClassId.value) params.class_id = filterClassId.value
    if (filterType.value) params.exception_type = filterType.value
    if (filterSemester.value) params.semester = filterSemester.value
    if (filterKeyword.value) params.keyword = filterKeyword.value
    if (filterDateRange.value && filterDateRange.value.length === 2) {
      params.date_from = filterDateRange.value[0]
      params.date_to = filterDateRange.value[1]
    }
    const res = await request.get('/attendance/export', { params, responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res]))
    const a = document.createElement('a')
    a.href = url
    a.download = '考勤异常.xlsx'
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    console.error('导出失败:', e)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

// ===== 重置 =====

const resetFilters = () => {
  filterClassId.value = null
  filterType.value = ''
  filterSemester.value = ''
  filterDateRange.value = null
  filterKeyword.value = ''
  currentPage.value = 1
  loadData()
}

// ===== 生命周期 =====

const handleResize = () => { pieChart?.resize() }

onMounted(async () => {
  if (!orgStore.orgTree?.length) {
    try { await orgStore.loadTree() } catch (e) {}
  }
  loadData()
  loadStats()
  loadTopStudents()
  await nextTick()
  renderPieChart()
  window.addEventListener('resize', handleResize)
})

// 监听 statsData 变化刷新饼图
watch(statsData, () => {
  nextTick(() => renderPieChart())
}, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
  pieChart = null
})
</script>

<style scoped>
.attendance-page { padding: 20px; background: #ECF1F7; min-height: 100vh; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; color: #2C3E50; font-size: 20px; }
.page-actions { display: flex; gap: 8px; }

/* 统计卡片 */
.stats-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.stat-card {
  background: #fff; border-radius: 12px; padding: 18px 20px;
  display: flex; align-items: center; gap: 14px;
  box-shadow: 0 2px 8px rgba(91,146,229,0.08);
}
.stat-icon {
  width: 44px; height: 44px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0;
}
.stat-info { flex: 1; }
.stat-label { font-size: 13px; color: #7F8C8D; margin-bottom: 4px; }
.stat-value { font-size: 26px; font-weight: 700; color: #2C3E50; }
.stat-value.accent-warn { color: #E6A23C; }
.stat-value.accent-danger { color: #F56C6C; }

/* 主布局 */
.main-layout { display: flex; gap: 16px; }
.left-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 16px; }
.right-panel { width: 280px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }

/* 筛选栏 */
.filter-card { border-radius: 12px; }
.filter-card :deep(.el-card__body) { padding: 14px 20px 0; }
.filter-form :deep(.el-form-item) { margin-bottom: 14px; }

/* 表格 */
.table-card { border-radius: 12px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }

/* 右侧面板卡片 */
.side-card { border-radius: 12px; }
.side-card-title { font-size: 14px; font-weight: 600; color: #2C3E50; }

/* TOP列表 */
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
.top-rank.rank-top3 { background: linear-gradient(135deg,#5B92E5,#7BCFCB); color: #fff; }
.top-info { flex: 1; min-width: 0; }
.top-name { font-size: 13px; color: #2C3E50; font-weight: 500; display: block; }
.top-class { font-size: 11px; color: #7F8C8D; display: block; }
.top-count { font-size: 14px; font-weight: 700; color: #5B92E5; flex-shrink: 0; }

/* 饼图 */
.pie-chart-container { width: 100%; height: 220px; }
</style>
