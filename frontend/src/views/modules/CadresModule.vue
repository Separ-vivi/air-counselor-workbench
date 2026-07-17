<template>
  <div class="module-page">
    <div class="page-header">
      <h2>👥 学生干部</h2>
      <div>
        <el-button :icon="Document" @click="loadDirectory">干部名录</el-button>
        <el-button
          type="success"
          :icon="Download"
          :disabled="!checkedRows.length"
          @click="exportSelected"
        >导出选中（{{ checkedRows.length }}）</el-button>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增干部</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="搜索">
          <el-input v-model="filter.kw" placeholder="学号/姓名/职务/组织" clearable style="width: 240px" />
        </el-form-item>
        <el-form-item label="学生">
          <StudentSelect v-model="filter.student_id" style="width: 260px" @change="reload" />
        </el-form-item>
        <el-form-item label="职务">
          <el-input v-model="filter.position" placeholder="职务关键字" clearable style="width: 180px" @keyup.enter="reload" @clear="reload" />
        </el-form-item>
        <el-form-item label="任职级别">
          <el-select v-model="filter.level" placeholder="全部" clearable style="width: 160px" @change="reload">
            <el-option v-for="l in levels" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

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
        <el-table-column label="学生" prop="student_name" width="110" sortable="custom">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/students/${row.student_id}`)">{{ row.student_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="学号" prop="student_no" width="140" sortable="custom" />
        <el-table-column label="班级" prop="class_name" min-width="140" show-overflow-tooltip />
        <el-table-column label="职务" prop="position" width="180" show-overflow-tooltip sortable="custom" />
        <el-table-column label="级别" prop="level" width="100" sortable="custom">
          <template #default="{ row }">
            <el-tag :type="levelTag(row.level)" size="small">{{ row.level || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="组织" prop="organization" min-width="160" show-overflow-tooltip sortable="custom" />
        <el-table-column label="任职起始" prop="start_date" width="130" sortable="custom" />
        <el-table-column label="任职结束" prop="end_date" width="130" sortable="custom" />
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
    </el-card>

    <el-dialog v-model="dlg" :title="editing?.id ? '编辑干部记录' : '新增干部记录'" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="学生" prop="student_id">
          <StudentSelect v-model="form.student_id" />
        </el-form-item>
        <el-form-item label="职务" prop="position">
          <el-select
            v-model="form.position"
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入职务"
            style="width: 100%"
          >
            <el-option v-for="p in positions" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="任职级别">
          <el-select v-model="form.level" style="width: 100%" clearable>
            <el-option v-for="l in levels" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属组织">
          <el-select
            v-model="form.organization"
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入组织"
            style="width: 100%"
          >
            <el-option v-for="o in organizations" :key="o" :label="o" :value="o" />
          </el-select>
        </el-form-item>
        <el-form-item label="任职起始">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="任职结束">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
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

    <el-dialog v-model="dirDlg" title="干部名录" width="720px">
      <el-table :data="directory" stripe border max-height="500">
        <el-table-column label="姓名" prop="student_name" width="120" />
        <el-table-column label="学号" prop="student_no" width="140" />
        <el-table-column label="班级" prop="class_name" show-overflow-tooltip />
        <el-table-column label="职务" prop="position" min-width="150" show-overflow-tooltip />
        <el-table-column label="级别" prop="level" width="100" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Document, Download } from '@element-plus/icons-vue'
import { cadres as cadresApi } from '@/api/modules'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'
import { triggerDownload, stampedName } from '@/utils/download'

const studentStore = useStudentStore()
const levels = ['校级', '院级', '班级', '团支部']
// v3j-C c01 · 职务/组织建议常量（含党支部系列）
const positions = [
  '班长', '副班长', '团支书', '学习委员', '生活委员', '文艺委员',
  '体育委员', '宣传委员', '心理委员', '组织委员', '纪律委员',
  '学生会主席', '团委副书记',
  '党支部书记', '党支部组织委员', '党支部宣传委员', '党支部纪检委员'
]
const organizations = [
  '班委会', '团支部', '党支部', '院学生会', '校学生会', '院团委', '校团委'
]
const list = ref([])
const directory = ref([])
const loading = ref(false)
const filter = reactive({ student_id: null, position: '', level: '', kw: '' })

// v3j-B-b03 · 排序 + 搜索 + 多选
const sortBy = ref('position')
const sortOrder = ref('asc')
const checkedRows = ref([])
const onSelectionChange = (rows) => { checkedRows.value = rows }
const onSort = ({ prop, order }) => {
  sortBy.value = prop || 'position'
  sortOrder.value = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : 'asc')
  reload()
}
let _searchTimer = null
watch(() => filter.kw, () => {
  clearTimeout(_searchTimer)
  _searchTimer = setTimeout(() => reload(), 300)
})

const levelTag = (l) => {
  if (l === '校级') return 'danger'
  if (l === '院级') return 'warning'
  if (l === '班级') return 'primary'
  return 'info'
}

const buildParams = () => {
  const params = {}
  if (filter.student_id) params.student_id = filter.student_id
  if (filter.position) params.position = filter.position
  if (filter.level) params.level = filter.level
  if (filter.kw) params.search = filter.kw
  return params
}

const reload = async () => {
  loading.value = true
  try {
    const params = buildParams()
    if (sortBy.value) params.sort_by = sortBy.value
    if (sortOrder.value) params.order = sortOrder.value
    const res = await cadresApi.list(params)
    list.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { loading.value = false }
}

const exportSelected = async () => {
  if (!checkedRows.value.length) { ElMessage.warning('请先勾选要导出的干部记录'); return }
  try {
    const ids = checkedRows.value.map(r => r.id)
    const blob = await cadresApi.exportByIds(ids)
    triggerDownload(blob, stampedName(`学生干部_选中${ids.length}条`))
    ElMessage.success(`已导出 ${ids.length} 条`)
  } catch (e) { ElMessage.error('导出失败') }
}
const exportAll = async () => {
  try {
    const blob = await cadresApi.exportAll(buildParams())
    triggerDownload(blob, stampedName(`学生干部_全部`))
    ElMessage.success('已导出全部')
  } catch (e) { ElMessage.error('导出失败') }
}

const dirDlg = ref(false)
const loadDirectory = async () => {
  try {
    const res = await cadresApi.directory()
    directory.value = Array.isArray(res) ? res : (res?.items || [])
    dirDlg.value = true
  } catch (e) {}
}

const dlg = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({ student_id: null, position: '', level: '', organization: '', start_date: '', end_date: '', notes: '' })
const form = reactive(defaultForm())
const rules = {
  student_id: [{ required: true, message: '请选择学生', trigger: 'change' }],
  position: [{ required: true, message: '请填写职务', trigger: 'blur' }]
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
      await cadresApi.update(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await cadresApi.create(form)
      ElMessage.success('已创建')
    }
    dlg.value = false
    studentStore.bumpRefresh()
    reload()
  } finally { saving.value = false }
}
const onDelete = async (row) => {
  await cadresApi.remove(row.id)
  ElMessage.success('已删除')
  studentStore.bumpRefresh()
  reload()
}

watch(() => studentStore.refreshBumper, reload)
onMounted(reload)
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
</style>
