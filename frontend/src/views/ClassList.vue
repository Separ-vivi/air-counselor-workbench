<template>
  <div class="class-list">
    <el-tabs v-model="activeTab" class="page-tabs">
      <el-tab-pane label="班级列表" name="classes">
        <div class="page-header">
          <h2>班级管理</h2>
          <div>
            <el-button :icon="Refresh" @click="reload">刷新组织树</el-button>
            <el-button :icon="Download" @click="exportAll">导出全部</el-button>
            <el-button type="primary" :icon="Setting" @click="$router.push('/org')">管理组织架构</el-button>
          </div>
        </div>

        <el-card shadow="never" style="margin-bottom: 16px">
          <el-form :inline="true">
            <el-form-item label="年级">
              <el-select v-model="filter.gradeId" placeholder="全部" clearable style="width: 160px">
                <el-option v-for="g in orgStore.grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="专业">
              <el-select v-model="filter.majorId" placeholder="全部" clearable filterable style="width: 200px">
                <el-option v-for="m in majorOptions" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="关键字">
              <el-input v-model="filter.keyword" placeholder="班级名 / 班主任 / 班长" clearable style="width: 220px" />
            </el-form-item>
            <el-form-item label="排序">
              <el-select v-model="filter.sortBy" style="width: 160px">
                <el-option label="默认（年级/专业）" value="" />
                <el-option label="班级名（升）" value="name_asc" />
                <el-option label="班级名（降）" value="name_desc" />
                <el-option label="人数（多→少）" value="count_desc" />
                <el-option label="人数（少→多）" value="count_asc" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 双柱状图 -->
        <el-row :gutter="16" v-if="filteredClasses.length" style="margin-bottom: 16px">
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center">
                  <span>📊 各班学生人数</span>
                  <span style="font-size:12px;color:#909399">共 {{ filteredClasses.length }} 个班级</span>
                </div>
              </template>
              <div ref="classBarRef" style="width: 100%; height: 260px"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center">
                  <span>📈 各班平均成绩</span>
                  <span style="font-size:12px;color:#909399">按全部课程均分</span>
                </div>
              </template>
              <div ref="avgBarRef" style="width: 100%; height: 260px"></div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col v-for="c in filteredClasses" :key="c.id" :span="8" style="margin-bottom: 16px">
            <el-card shadow="hover" class="class-card" @click.stop="goClass(c.id)">
              <div class="cc-top">
                <div class="cc-name">🏫 {{ c.name }}</div>
                <el-tag size="small" type="info">{{ c.grade_name }}</el-tag>
              </div>
              <div class="cc-major">{{ c.major_name }}</div>
              <div class="cc-count">
                <span class="cc-num">{{ c.student_count ?? '-' }}</span>
                <span class="cc-unit">名学生</span>
              </div>
              <div class="cc-footer">
                <el-button type="primary" text size="small" @click.stop="goClass(c.id)">查看班级 360</el-button>
              </div>
            </el-card>
          </el-col>

          <el-col v-if="!filteredClasses.length" :span="24">
            <el-empty description="没有符合条件的班级" />
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="班主任管理" name="teachers">
        <div class="page-header">
          <h2>班主任管理</h2>
          <div>
            <el-button
              type="success"
              :icon="Download"
              :disabled="!teachersCheckedRows.length"
              @click="exportTeachersSelected"
            >导出选中（{{ teachersCheckedRows.length }}）</el-button>
            <el-button :icon="Download" @click="exportTeachersAll">导出全部</el-button>
            <el-button type="primary" :icon="Plus" @click="openTeacherCreate(null)">新增班主任</el-button>
          </div>
        </div>

        <el-card shadow="never" style="margin-bottom: 16px">
          <el-form :inline="true">
            <el-form-item label="搜索">
              <el-input v-model="teacherFilter.kw" placeholder="姓名/工号/院系/电话/邮箱" clearable style="width: 260px" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never">
          <el-table
            :data="teacherList"
            v-loading="teacherLoading"
            stripe
            border
            max-height="640"
            row-key="id"
            @selection-change="onTeacherSelectionChange"
            @sort-change="onTeacherSort"
          >
            <el-table-column type="selection" width="45" reserve-selection />
            <el-table-column label="姓名" prop="name" width="120" sortable="custom" />
            <el-table-column label="工号" prop="teacher_no" width="140" sortable="custom" />
            <el-table-column label="所带班级" prop="class_name" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="!row.class_id">未分配</span>
                <el-link v-else type="primary" @click="$router.push(`/classes/${row.class_id}`)">{{ row.class_name || orgStore.getClassName(row.class_id) }}</el-link>
              </template>
            </el-table-column>
            <el-table-column label="院系" prop="department" width="180" show-overflow-tooltip sortable="custom" />
            <el-table-column label="职称" prop="title" width="120" sortable="custom" />
            <el-table-column label="电话" prop="phone" width="140" sortable="custom" />
            <el-table-column label="办公地点" prop="office" width="140" show-overflow-tooltip sortable="custom" />
            <el-table-column label="邮箱" prop="email" min-width="180" show-overflow-tooltip sortable="custom" />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openTeacherCreate(row)">编辑</el-button>
                <el-popconfirm title="确认删除？" @confirm="onTeacherDelete(row)">
                  <template #reference>
                    <el-button link type="danger" size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-dialog v-model="teacherDlg" :title="teacherEditing?.id ? '编辑班主任' : '新增班主任'" width="560px">
          <el-form :model="teacherForm" :rules="teacherRules" ref="teacherFormRef" label-width="110px">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="teacherForm.name" />
            </el-form-item>
            <el-form-item label="工号">
              <el-input v-model="teacherForm.teacher_no" />
            </el-form-item>
            <el-form-item label="所带班级">
              <el-select v-model="teacherForm.class_id" filterable clearable style="width: 100%">
                <el-option v-for="c in orgStore.allClasses" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="院系">
              <el-input v-model="teacherForm.department" />
            </el-form-item>
            <el-form-item label="职称">
              <el-input v-model="teacherForm.title" />
            </el-form-item>
            <el-form-item label="电话">
              <el-input v-model="teacherForm.phone" />
            </el-form-item>
            <el-form-item label="办公地点" prop="office">
              <el-input v-model="teacherForm.office" placeholder="如：文远楼403" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="teacherForm.email" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="teacherForm.notes" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="teacherDlg = false">取消</el-button>
            <el-button type="primary" @click="onTeacherSave" :loading="teacherSaving">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useRouter } from 'vue-router'
import { Refresh, Setting, Download, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { exportClassesAll } from '@/api/org'
import { triggerDownload, stampedName } from '@/utils/download'
import { useOrgStore } from '@/stores/org'
import { classTeachers as tApi } from '@/api/modules'

const router = useRouter()
const orgStore = useOrgStore()

// ===== Tab 切换 =====
const activeTab = ref('classes')

// ===== 班级列表 Tab =====
const filter = reactive({ gradeId: null, majorId: null, keyword: '', sortBy: '' })

const majorOptions = computed(() => {
  const all = orgStore.allMajors
  return filter.gradeId ? all.filter((m) => m.grade_id === filter.gradeId) : all
})

const filteredClasses = computed(() => {
  let list = orgStore.allClasses
  if (filter.gradeId) list = list.filter((c) => c.grade_id === filter.gradeId)
  if (filter.majorId) list = list.filter((c) => c.major_id === filter.majorId)
  const kw = filter.keyword.trim()
  if (kw) {
    list = list.filter(
      (c) =>
        (c.name || '').includes(kw) ||
        (c.class_teacher || '').includes(kw) ||
        (c.monitor || '').includes(kw)
    )
  }
  const sb = filter.sortBy
  if (sb) {
    const arr = [...list]
    if (sb === 'name_asc')  arr.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    if (sb === 'name_desc') arr.sort((a, b) => (b.name || '').localeCompare(a.name || ''))
    if (sb === 'count_desc') arr.sort((a, b) => (b.student_count || 0) - (a.student_count || 0))
    if (sb === 'count_asc')  arr.sort((a, b) => (a.student_count || 0) - (b.student_count || 0))
    return arr
  }
  return list
})

const goClass = (id) => router.push(`/classes/${id}`)
const classBarRef = ref(null)
const avgBarRef = ref(null)
let classBarChart = null
let avgBarChart = null
const macaronColors = ['#F8B4B4','#F9E79F','#B7E4C7','#B7D8E4','#D5B7E4','#F5C7A0','#FCB69F','#A8E6CF','#FFD3B6','#FF8B94','#C7CEEA','#FEC8D8']

function renderClassBar() {
  if (!classBarRef.value) return
  const cd = filteredClasses.value.map(c => ({ name: c.name, value: c.student_count || 0, id: c.id }))
  if (!classBarChart) classBarChart = echarts.init(classBarRef.value)
  classBarChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: p => `${p[0].name}<br/>${p[0].marker} 学生人数：<b>${p[0].value}</b> 人` },
    grid: { left: 8, right: 12, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: 'category', data: cd.map(x => x.name), axisLine: { lineStyle: { color: '#DCDFE6' } }, axisLabel: { color: '#606266', fontSize: 11, rotate: cd.length > 8 ? 20 : 0, interval: 0 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#E4E7ED' } }, axisLabel: { color: '#909399', fontSize: 11 } },
    series: [{
      type: 'bar', barWidth: '46%',
      data: cd.map((x, i) => ({ value: x.value, name: x.name, itemStyle: { color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: macaronColors[i % macaronColors.length] },
          { offset: 1, color: '#FFFFFF' }
        ]
      }, borderRadius: [8, 8, 0, 0] } })),
      label: { show: true, position: 'top', color: '#606266', fontSize: 11, fontWeight: 500 }
    }]
  })
  classBarChart.off('click')
}

function renderAvgBar() {
  if (!avgBarRef.value) return
  const cd = filteredClasses.value.map(c => ({ name: c.name, value: c.avg_score || 0, id: c.id }))
  if (!avgBarChart) avgBarChart = echarts.init(avgBarRef.value)
  avgBarChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: p => `${p[0].name}<br/>${p[0].marker} 平均成绩：<b>${p[0].value}</b> 分` },
    grid: { left: 8, right: 12, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: 'category', data: cd.map(x => x.name), axisLine: { lineStyle: { color: '#DCDFE6' } }, axisLabel: { color: '#606266', fontSize: 11, rotate: cd.length > 8 ? 20 : 0, interval: 0 } },
    yAxis: { type: 'value', min: 0, max: 100, splitLine: { lineStyle: { type: 'dashed', color: '#E4E7ED' } }, axisLabel: { color: '#909399', fontSize: 11 } },
    series: [{
      type: 'bar', barWidth: '46%',
      data: cd.map((x, i) => ({ value: x.value, name: x.name, itemStyle: { color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: macaronColors[i % macaronColors.length] },
          { offset: 1, color: '#FFFFFF' }
        ]
      }, borderRadius: [8, 8, 0, 0] } })),
      label: { show: true, position: 'top', color: '#606266', fontSize: 11, fontWeight: 500, formatter: (p) => p.value ? p.value.toFixed(1) : '—' }
    }]
  })
  avgBarChart.off('click')
}

const resizeCharts = () => {
  try { classBarChart?.resize() } catch(e) {}
  try { avgBarChart?.resize() } catch(e) {}
}
watch(filteredClasses, () => { nextTick(() => { renderClassBar(); renderAvgBar() }) })
onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  try { classBarChart?.dispose() } catch(e) {}
  try { avgBarChart?.dispose() } catch(e) {}
})

const reload = () => orgStore.loadTree(true)

const exportAll = async () => {
  try {
    const params = {}
    if (filter.gradeId) params.grade_id = filter.gradeId
    if (filter.majorId) params.major_id = filter.majorId
    if (filter.keyword.trim()) params.search = filter.keyword.trim()
    const blob = await exportClassesAll(params)
    triggerDownload(blob, stampedName('班级列表'))
    ElMessage.success('已导出班级列表')
  } catch (e) { ElMessage.error('导出失败') }
}

// ===== 班主任管理 Tab =====
const teacherList = ref([])
const teacherLoading = ref(false)
const teacherFilter = reactive({ kw: '' })
const teacherSortBy = ref('name')
const teacherSortOrder = ref('asc')
const teachersCheckedRows = ref([])
const onTeacherSelectionChange = (rows) => { teachersCheckedRows.value = rows }
const onTeacherSort = ({ prop, order }) => {
  teacherSortBy.value = prop || 'name'
  teacherSortOrder.value = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : 'asc')
  reloadTeachers()
}
let _teacherSearchTimer = null
watch(() => teacherFilter.kw, () => {
  clearTimeout(_teacherSearchTimer)
  _teacherSearchTimer = setTimeout(() => reloadTeachers(), 300)
})

const buildTeacherParams = () => {
  const params = {}
  if (teacherFilter.kw) params.search = teacherFilter.kw
  return params
}

const reloadTeachers = async () => {
  teacherLoading.value = true
  try {
    const params = buildTeacherParams()
    if (teacherSortBy.value) params.sort_by = teacherSortBy.value
    if (teacherSortOrder.value) params.order = teacherSortOrder.value
    const res = await tApi.list(params)
    teacherList.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { teacherLoading.value = false }
}

const exportTeachersSelected = async () => {
  if (!teachersCheckedRows.value.length) { ElMessage.warning('请先勾选要导出的班主任'); return }
  try {
    const ids = teachersCheckedRows.value.map(r => r.id)
    const blob = await tApi.exportByIds(ids)
    triggerDownload(blob, stampedName(`班主任_选中${ids.length}条`))
    ElMessage.success(`已导出 ${ids.length} 条`)
  } catch (e) { ElMessage.error('导出失败') }
}
const exportTeachersAll = async () => {
  try {
    const blob = await tApi.exportAll(buildTeacherParams())
    triggerDownload(blob, stampedName(`班主任_全部`))
    ElMessage.success('已导出全部')
  } catch (e) { ElMessage.error('导出失败') }
}

const teacherDlg = ref(false)
const teacherEditing = ref(null)
const teacherSaving = ref(false)
const teacherFormRef = ref(null)
const defaultTeacherForm = () => ({ name: '', teacher_no: '', class_id: null, department: '', title: '', phone: '', office: '', email: '', notes: '' })
const teacherForm = reactive(defaultTeacherForm())
const teacherRules = {
  name: [{ required: true, message: '请填写姓名', trigger: 'blur' }]
}
const openTeacherCreate = (row) => {
  teacherEditing.value = row
  Object.assign(teacherForm, defaultTeacherForm(), row || {})
  teacherDlg.value = true
}
const onTeacherSave = async () => {
  await teacherFormRef.value?.validate()
  teacherSaving.value = true
  try {
    if (teacherEditing.value?.id) {
      await tApi.update(teacherEditing.value.id, teacherForm)
      ElMessage.success('已更新')
    } else {
      await tApi.create(teacherForm)
      ElMessage.success('已创建')
    }
    teacherDlg.value = false
    reloadTeachers()
  } finally { teacherSaving.value = false }
}
const onTeacherDelete = async (row) => {
  await tApi.remove(row.id)
  ElMessage.success('已删除')
  reloadTeachers()
}

onMounted(() => {
  window.addEventListener('resize', resizeCharts)
  nextTick(() => { renderClassBar(); renderAvgBar() })
  if (!orgStore.orgTree.length) orgStore.loadTree()
  window.addEventListener('system-reinit-done', () => orgStore.loadTree(true))
  // 班主任数据也预加载
  if (!orgStore.orgTree.length) orgStore.loadTree()
  reloadTeachers()
})
</script>

<style scoped>
.class-list { padding: 4px; }
.page-tabs :deep(.el-tabs__header) { margin-bottom: 12px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.class-card {
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.class-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}
.cc-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cc-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.cc-major {
  color: #606266;
  font-size: 13px;
  margin: 8px 0;
}
.cc-count {
  padding: 8px 0;
  border-top: 1px dashed #EBEEF5;
  border-bottom: 1px dashed #EBEEF5;
  margin: 8px 0;
}
.cc-num {
  color: #4A7A8C;
  font-size: 26px;
  font-weight: 700;
}
.cc-unit {
  color: #909399;
  margin-left: 6px;
  font-size: 13px;
}
.cc-footer {
  text-align: right;
}
</style>
