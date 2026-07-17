<template>
  <div class="module-page">
    <div class="page-header">
      <h2>💚 心理关怀</h2>
      <div>
        <el-button :icon="Bell" @click="loadReminders">提醒 ({{ reminders.length }})</el-button>
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
      </el-form>
    </el-card>

    <el-alert v-if="reminders.length" type="warning" show-icon :closable="false" style="margin-bottom: 12px">
      有 {{ reminders.length }} 条心理关注提醒需要处理
    </el-alert>

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
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Bell, Download } from '@element-plus/icons-vue'
import { psychology as psyApi } from '@/api/modules'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'
import { triggerDownload, stampedName } from '@/utils/download'

const studentStore = useStudentStore()

const levels = ['一级关注', '二级关注', '三级关注', '普通']
const list = ref([])
const reminders = ref([])
const loading = ref(false)
const filter = reactive({ student_id: null, attention_level: '', kw: '' })

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
  if (!l) return { background: '#F0F2F5', color: '#909399', border: 'none' }  // 无档案 → 灰
  if (l.includes('一')) return { background: '#FF9AA2', color: '#7A2E36', border: 'none', fontWeight: 600 }
  if (l.includes('二')) return { background: '#FFDAC1', color: '#8A4E1F', border: 'none', fontWeight: 600 }
  if (l.includes('三')) return { background: '#B5EAD7', color: '#1F5A46', border: 'none', fontWeight: 600 }
  if (l.includes('普通')) return { background: '#C7CEEA', color: '#3B4B7A', border: 'none', fontWeight: 600 }  // 普通 → 紫
  return { background: '#F0F2F5', color: '#909399', border: 'none' }
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
onMounted(() => { reload(); loadReminders() })
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
</style>
