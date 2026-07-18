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
        <el-form-item>
          <el-button @click="reload">查询</el-button>
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

    <el-card shadow="never">
      <el-table
        :data="list"
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import { party as partyApi } from '@/api/modules'
import http from '@/api/index.js'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'
import { triggerDownload, stampedName } from '@/utils/download'

const studentStore = useStudentStore()

const stages = [
  '递交入党申请书', '入党积极分子', '发展对象', '中共预备党员', '中共党员'
]
const stageColor = { '递交入党申请书': '#909399', '入党积极分子': '#409EFF', '发展对象': '#E6A23C', '中共预备党员': '#F56C6C', '中共党员': '#67C23A' }

const list = ref([])
const loading = ref(false)
const classes = ref([])
const filter = reactive({ student_id: null, stage: '', kw: '', class_id: null })

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
    const res = await http.get('/org/classes')  // v3j-C c01-hotfix1: 修 /classes 404
    classes.value = Array.isArray(res) ? res : (res?.items || res?.data || [])
  } catch (e) { classes.value = [] }
}

onMounted(() => { loadClasses(); reload() })
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.stat-card { border-radius: 12px; text-align: center; }
.stat-label { color: #909399; font-size: 13px; margin-bottom: 8px; }
.stat-value { font-size: 24px; font-weight: 600; }
</style>
