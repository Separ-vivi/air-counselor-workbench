<template>
  <div class="module-page">
    <div class="page-header">
      <h2>🚦 学业预警</h2>
      <div>
        <el-button :icon="Refresh" @click="reload">刷新</el-button>
        <el-button type="primary" :icon="Refresh" :loading="recalcing" @click="doRecalc">重新计算</el-button>
        <el-button
          type="success"
          :icon="Download"
          :disabled="!checkedRows.length"
          @click="exportSelected"
        >导出选中（{{ checkedRows.length }}）</el-button>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="搜索">
          <el-input v-model="filter.kw" placeholder="姓名/学号/预警原因" clearable style="width: 220px" />
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="filter.semester" placeholder="全部学期" clearable filterable style="width: 180px" @change="reload">
            <el-option v-for="s in semesters" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="预警等级">
          <el-select v-model="filter.level" placeholder="全部" clearable style="width: 160px" @change="reload">
            <el-option label="红色（严重）" value="红色" />
            <el-option label="黄色（一般）" value="黄色" />
            <el-option label="蓝色（提醒）" value="蓝色" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="filter.class_name" placeholder="全部班级" clearable filterable style="width: 200px" @change="reload">
            <el-option v-for="c in orgStore.allClasses" :key="c.id" :label="c.name" :value="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="学生">
          <StudentSelect v-model="filter.student_id" style="width: 220px" @change="reload" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">预警学生总数</div>
          <div class="stat-value" style="color: #F56C6C">{{ stats.total }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">红色预警</div>
          <div class="stat-value" style="color: #F56C6C">{{ stats.red }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">黄色预警</div>
          <div class="stat-value" style="color: #E6A23C">{{ stats.yellow }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">蓝色提醒</div>
          <div class="stat-value" style="color: #409EFF">{{ stats.blue }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <el-table
        :data="filteredRows"
        stripe
        border
        v-loading="loading"
        max-height="600"
        row-key="id"
        @selection-change="onSelectionChange"
        @sort-change="onSort"
      >
        <el-table-column type="selection" width="45" reserve-selection />
        <el-table-column label="学生" prop="student_name" width="110" sortable="custom">
          <template #default="{ row }">
            <el-link type="primary" @click="openFailDetail(row)">
              {{ row.student_name || row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="学号" prop="student_no" width="140" sortable="custom" />
        <el-table-column label="班级" prop="class_name" min-width="160" show-overflow-tooltip sortable="custom" />
        <el-table-column label="预警等级" prop="warning_level" width="120" sortable="custom">
          <template #default="{ row }">
            <span :style="{
              background: levelBg(row.warning_level),
              color: levelFg(row.warning_level),
              padding: '3px 10px', borderRadius: '10px', fontWeight: 600, fontSize: '12px'
            }">{{ row.warning_level || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="预警原因" prop="warning_reason" min-width="200" show-overflow-tooltip />
        <el-table-column label="不及格门数" prop="fail_count" width="110" align="center" sortable="custom" />
        <el-table-column label="GPA" prop="gpa" width="90" sortable="custom" />
        <el-table-column label="学期" prop="semester" width="120" sortable="custom" />
      </el-table>
    </el-card>

    <!-- v3j-C c02-hotfix2 · 学业预警学生点击弹挂科明细，不再跳 360 -->
    <el-dialog v-model="failDetailVisible" :title="failDetailTitle" width="720px" :destroy-on-close="true">
      <el-table :data="failDetailList" v-loading="failDetailLoading" stripe border max-height="480">
        <el-table-column label="学期" prop="semester" width="130" />
        <el-table-column label="课程" prop="course_name" min-width="180" show-overflow-tooltip />
        <el-table-column label="学分" prop="credit" width="70" align="center" />
        <el-table-column label="分数" prop="score" width="90" align="center">
          <template #default="{ row }">
            <span :style="{ color: '#F56C6C', fontWeight: 600, background: '#FDECEC', padding: '2px 8px', borderRadius: '8px' }">
              {{ row.score ?? '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="重修" prop="is_makeup" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_makeup" type="warning" size="small">重修</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer><el-button @click="failDetailVisible = false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import { grades as gradesApi } from '@/api/modules'
import { useOrgStore } from '@/stores/org'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'
import { triggerDownload, stampedName } from '@/utils/download'

const orgStore = useOrgStore()
const studentStore = useStudentStore()

const list = ref([])
const semesters = ref([])
const loading = ref(false)
const recalcing = ref(false)
const filter = reactive({ semester: '', level: '', class_name: '', student_id: null, kw: '' })

// v3j-B-b03 · 排序 + 搜索 + 多选
const sortBy = ref('warning_level')
const sortOrder = ref('desc')
const checkedRows = ref([])
const onSelectionChange = (rows) => { checkedRows.value = rows }
const onSort = ({ prop, order }) => {
  sortBy.value = prop || 'warning_level'
  sortOrder.value = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : 'desc')
  reload()
}
let _searchTimer = null
watch(() => filter.kw, () => {
  clearTimeout(_searchTimer)
  _searchTimer = setTimeout(() => reload(), 300)
})

// 客户端二次过滤：level/class_name/student_id 三个筛选保持前端过滤（后端 search 已含所有关键字）
const filteredRows = computed(() => {
  let rs = list.value
  if (filter.level) rs = rs.filter((r) => (r.warning_level || '').includes(filter.level.slice(0, 1)) || r.warning_level === filter.level)
  if (filter.class_name) rs = rs.filter((r) => r.class_name === filter.class_name)
  if (filter.student_id) rs = rs.filter((r) => r.student_id === filter.student_id || r.id === filter.student_id)
  return rs
})

const stats = computed(() => {
  const s = { total: filteredRows.value.length, red: 0, yellow: 0, blue: 0 }
  filteredRows.value.forEach((r) => {
    const l = r.warning_level || ''
    if (l.includes('红')) s.red++
    else if (l.includes('黄')) s.yellow++
    else if (l.includes('蓝')) s.blue++
  })
  return s
})

const levelTag = (l) => {
  if (!l) return ''
  if (l.includes('红')) return 'danger'
  if (l.includes('黄')) return 'warning'
  if (l.includes('蓝')) return 'primary'
  return 'info'
}

// v3j-C c02-hotfix2 · 预警等级用整 cell 底色高亮（air 原话：什么等级给什么颜色）
const levelBg = (l) => {
  if (!l) return '#F5F7FA'
  const s = String(l)
  if (s.includes('一级') || s.includes('红')) return '#FDECEC'  // 浅红
  if (s.includes('二级') || s.includes('橙')) return '#FEF4E7'  // 浅橙
  if (s.includes('三级') || s.includes('黄') || s.includes('蓝')) return '#FEF9E7'  // 浅黄
  return '#F5F7FA'
}
const levelFg = (l) => {
  if (!l) return '#909399'
  const s = String(l)
  if (s.includes('一级') || s.includes('红')) return '#F56C6C'
  if (s.includes('二级') || s.includes('橙')) return '#E6A23C'
  if (s.includes('三级') || s.includes('黄') || s.includes('蓝')) return '#B88F00'
  return '#909399'
}
// 兼容旧引用
const dotColor = levelBg

// v3j-C c02-hotfix2 · 挂科明细弹窗
const failDetailVisible = ref(false)
const failDetailLoading = ref(false)
const failDetailTitle = ref('')
const failDetailList = ref([])
const openFailDetail = async (row) => {
  const sid = row.student_id || row.id
  if (!sid) return
  failDetailTitle.value = `${row.student_name || row.name || '学生'} 挂科明细`
  failDetailVisible.value = true
  failDetailLoading.value = true
  try {
    const res = await gradesApi.studentGrades(sid)
    const all = Array.isArray(res) ? res : (res?.items || [])
    // 只保留挂科（<60）
    failDetailList.value = all.filter(g => g.score != null && g.score < 60)
    if (!failDetailList.value.length) {
      ElMessage.info('该学生无挂科记录')
    }
  } catch (e) {
    ElMessage.error('拉取挂科明细失败')
    failDetailList.value = []
  } finally {
    failDetailLoading.value = false
  }
}

const reload = async () => {
  loading.value = true
  try {
    const params = {}
    if (filter.semester) params.semester = filter.semester
    if (filter.kw) params.search = filter.kw
    if (sortBy.value) params.sort_by = sortBy.value
    if (sortOrder.value) params.order = sortOrder.value
    const res = await gradesApi.warnings(params)
    list.value = Array.isArray(res) ? res : (res?.items || res?.data || [])
  } finally { loading.value = false }
}

const loadSemesters = async () => {
  try {
    const res = await gradesApi.semesters()
    semesters.value = Array.isArray(res) ? res : (res?.items || [])
  } catch (e) { semesters.value = [] }
}

const doRecalc = async () => {
  recalcing.value = true
  try {
    await gradesApi.recalculateWarnings()
    ElMessage.success('重新计算完成')
    reload()
  } finally { recalcing.value = false }
}

const exportSelected = async () => {
  if (!checkedRows.value.length) { ElMessage.warning('请先勾选要导出的预警记录'); return }
  try {
    const ids = checkedRows.value.map(r => r.id)
    const blob = await gradesApi.exportWarningsByIds(ids)
    triggerDownload(blob, stampedName(`学业预警_选中${ids.length}条`))
    ElMessage.success(`已导出 ${ids.length} 条`)
  } catch (e) { ElMessage.error('导出失败') }
}
const exportAll = async () => {
  try {
    const blob = await gradesApi.exportWarnings()
    triggerDownload(blob, stampedName(`学业预警_全部`))
    ElMessage.success('已导出全部')
  } catch (e) { ElMessage.error('导出失败') }
}

watch(() => studentStore.refreshBumper, reload)
onMounted(() => {
  if (!orgStore.orgTree.length) orgStore.loadTree()
  loadSemesters()
  reload()
})
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.stat-card { border-radius: 12px; text-align: center; }
.stat-label { color: #909399; font-size: 13px; margin-bottom: 8px; }
.stat-value { font-size: 26px; font-weight: 600; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
</style>
