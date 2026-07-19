<template>
  <div class="student-list">
    <div class="page-header">
      <h2>学生管理</h2>
      <div class="header-actions">
        <el-button :type="showAllIdCards ? 'warning' : 'default'" @click="showAllIdCards = !showAllIdCards"
          :title="showAllIdCards ? '当前显示明文，点击切换为脱敏' : '当前脱敏，点击显示明文（含身份证号）'">
          {{ showAllIdCards ? '🔓 明文' : '🔒 脱敏' }}
        </el-button>
        <el-button @click="tagManageDialog = true; loadAllTags()">🏷️ 管理标签</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增学生</el-button>
        <el-button :icon="Upload" @click="$router.push('/smart-import')">批量导入</el-button>
        <el-button type="success" :icon="Download" :disabled="!selected.length" @click="exportSelected">导出选中（{{ selected.length }}）</el-button>
        <el-button type="warning" :icon="Download" :disabled="!selected.length" @click="exportSelectedFull">导出选中·完整档案（{{ selected.length }}）</el-button>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="搜索">
          <el-input v-model="filters.search" placeholder="姓名/学号/拼音" clearable style="width: 220px"
            :prefix-icon="Search" @keyup.enter="reload" @clear="reload" />
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="filters.class_name" placeholder="全部班级" clearable filterable style="width: 200px" @change="reload">
            <el-option v-for="c in orgStore.allClasses" :key="c.id" :label="c.name" :value="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="filters.major" placeholder="全部专业" clearable filterable style="width: 200px" @change="reload">
            <el-option v-for="m in orgStore.allMajors" :key="m.id" :label="m.name" :value="m.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="filters.gender" placeholder="全部" clearable style="width: 100px" @change="reload">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="政治面貌">
          <el-select v-model="filters.political_status" placeholder="全部" clearable style="width: 160px" @change="reload">
            <el-option label="群众" value="群众" />
            <el-option label="共青团员" value="共青团员" />
            <el-option label="中共预备党员" value="中共预备党员" />
            <el-option label="中共党员" value="中共党员" />
          </el-select>
        </el-form-item>
        <el-form-item label="生源地">
          <el-input v-model="filters.birth_source" placeholder="省份/城市" clearable style="width: 140px" @keyup.enter="reload" @clear="reload" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="reload" :icon="Refresh">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" stripe border highlight-current-row @sort-change="onSort"
        @selection-change="onSelectionChange" row-key="id" ref="tableRef">
        <el-table-column type="selection" width="55" reserve-selection />
        <el-table-column label="学号" prop="student_no" width="140" sortable="custom" />
        <el-table-column label="姓名" prop="name" width="110" sortable="custom">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/students/${row.id}`)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="性别" prop="gender" width="90" sortable="custom" />
        <el-table-column label="班级" prop="class_name" min-width="160" show-overflow-tooltip sortable="custom" />
        <el-table-column label="专业" prop="major" min-width="140" show-overflow-tooltip sortable="custom" />
        <el-table-column label="政治面貌" prop="political_status" width="110" sortable="custom" />
        <el-table-column label="标签" width="200">
          <template #default="{ row }">
            <div class="tag-cell">
              <span v-for="t in getStudentTags(row)" :key="t.id"
                class="tag-pill"
                :style="{ background: t.color + '22', color: t.color, borderColor: t.color + '44' }">
                <span class="tag-dot" :style="{ background: t.color }"></span>
                {{ t.name }}
              </span>
              <el-button link type="primary" size="small" @click="openStudentTagDialog(row)" style="flex-shrink:0">
                <el-icon><Edit /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="生源地" prop="birth_source" width="140" show-overflow-tooltip sortable="custom" />
        <el-table-column label="身份证号" prop="id_card" min-width="140" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.id_card && row.id_card.length >= 10">
              {{ showAllIdCards ? row.id_card : (row.id_card.slice(0,6) + '********' + row.id_card.slice(-4)) }}
            </span>
            <span v-else style="color:#c0c4cc">—</span>
          </template>
        </el-table-column>
        <el-table-column label="校区" prop="campus" width="90" sortable="custom" />
        <el-table-column label="宿舍" prop="dorm_building" min-width="160" show-overflow-tooltip sortable="custom">
          <template #default="{ row }">
            <el-tag v-if="row.is_off_campus" size="small" type="warning">外宿</el-tag>
            <span v-else-if="row.dorm_building || row.dorm_room">{{ row.dorm_building }}·{{ row.dorm_room }}</span>
            <span v-else style="color:#c0c4cc">—</span>
          </template>
        </el-table-column>
        <el-table-column label="电话" prop="phone" width="130" sortable="custom" />
        <el-table-column label="操作" fixed="right" width="140">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除该学生？" @confirm="onDelete(row)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 12px; text-align: right">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :page-sizes="[20, 50, 100, 200]"
          :total="total" layout="total, sizes, prev, pager, next, jumper" background @size-change="reload"
          @current-change="reload" />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑学生' : '新增学生'" width="640px" @close="onClose">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="学号" prop="student_no">
              <el-input v-model="form.student_no" placeholder="如 20250501" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-radio-group v-model="form.gender">
                <el-radio value="男">男</el-radio>
                <el-radio value="女">女</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出生日期">
              <el-date-picker v-model="form.birth_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属班级">
              <el-select v-model="form.class_id" placeholder="选择班级" filterable clearable style="width: 100%">
                <el-option v-for="c in orgStore.allClasses" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="政治面貌">
              <el-select v-model="form.political_status" clearable style="width: 100%">
                <el-option label="群众" value="群众" />
                <el-option label="共青团员" value="共青团员" />
                <el-option label="中共预备党员" value="中共预备党员" />
                <el-option label="中共党员" value="中共党员" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="form.phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="form.email" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="家长电话">
              <el-input v-model="form.parent_phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="生源地">
              <el-input v-model="form.birth_source" placeholder="如 福州市·鼓楼区" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身份证号">
              <el-input v-model="form.id_card" placeholder="18位身份证" maxlength="18" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="校区">
              <el-select v-model="form.campus" clearable placeholder="选择校区" style="width: 100%">
                <el-option label="铜盘校区" value="铜盘校区" />
                <el-option label="旗山校区" value="旗山校区" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="宿舍楼">
              <el-input v-model="form.dorm_building" placeholder="如 3号楼" :disabled="form.is_off_campus" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="房间号">
              <el-input v-model="form.dorm_room" placeholder="如 401" :disabled="form.is_off_campus" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="外宿">
              <el-switch v-model="form.is_off_campus" active-text="外宿" inactive-text="住校" />
            </el-form-item>
          </el-col>
          <el-col :span="24" v-if="form.is_off_campus">
            <el-form-item label="外宿地址">
              <el-input v-model="form.off_campus_address" placeholder="详细地址" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.notes" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 标签管理对话框 -->
    <el-dialog v-model="tagManageDialog" title="标签管理" width="520px" destroy-on-close>
      <div class="tag-manage-section">
        <div class="tag-manage-list">
          <div v-if="allTags.length === 0" class="tag-manage-empty">暂无标签，请在下方创建</div>
          <div v-for="tag in allTags" :key="tag.id" class="tag-manage-item">
            <span class="tag-pill" :style="{ background: tag.color + '22', color: tag.color, borderColor: tag.color + '44' }">
              <span class="tag-dot" :style="{ background: tag.color }"></span>
              {{ tag.name }}
            </span>
            <el-button link type="danger" size="small" @click="onDeleteTag(tag)">删除</el-button>
          </div>
        </div>
        <el-divider />
        <div class="tag-create-form">
          <div style="font-weight:600;margin-bottom:8px;font-size:14px;">新建标签</div>
          <el-form :inline="true">
            <el-form-item label="名称">
              <el-input v-model="newTag.name" placeholder="标签名称" style="width:140px" maxlength="20" />
            </el-form-item>
            <el-form-item label="颜色">
              <div class="color-picker-row">
                <div v-for="c in presetColors" :key="c" class="color-dot"
                  :class="{ selected: newTag.color === c }"
                  :style="{ background: c }" @click="newTag.color = c" />
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="onCreateTag" :loading="tagCreating" :disabled="!newTag.name.trim()">创建</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-dialog>

    <!-- 学生标签编辑对话框 -->
    <el-dialog v-model="studentTagDialog" :title="`编辑标签 - ${editingStudent?.name || ''}`" width="460px" destroy-on-close>
      <div v-if="allTags.length === 0" class="tag-manage-empty">
        暂无标签，请先在「管理标签」中创建
      </div>
      <div v-else class="student-tag-check-list">
        <div v-for="tag in allTags" :key="tag.id" class="student-tag-check-item"
          @click="toggleStudentTag(tag)">
          <el-checkbox :model-value="isStudentTagChecked(tag.id)" @click.stop />
          <span class="tag-pill" :style="{ background: tag.color + '22', color: tag.color, borderColor: tag.color + '44' }">
            <span class="tag-dot" :style="{ background: tag.color }"></span>
            {{ tag.name }}
          </span>
          <el-button link type="danger" size="small" @click.stop="removeStudentTagInline(tag)" style="margin-left:auto">✕</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Upload, Download, Refresh, Edit } from '@element-plus/icons-vue'
import {
  listStudents, createStudent, updateStudent, deleteStudent,
  exportStudents, exportStudentsByIds, exportStudentsFull
} from '@/api/students'
import { useOrgStore } from '@/stores/org'
import { useStudentStore } from '@/stores/student'
import { triggerDownload, stampedName } from '@/utils/download'
import { tagsApi } from '@/api/tags.js'

const orgStore = useOrgStore()
const studentStore = useStudentStore()

const list = ref([])
const selected = ref([])
const tableRef = ref(null)
const onSelectionChange = (rows) => { selected.value = rows }
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const showAllIdCards = ref(false)

const filters = reactive({
  search: '', class_name: '', major: '', gender: '',
  political_status: '', birth_source: '', sort_by: '', order: ''
})

const dialogVisible = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({
  student_no: '', name: '', gender: '', class_id: null, birth_date: '',
  political_status: '', phone: '', email: '', parent_phone: '', birth_source: '',
  id_card: '', campus: '', dorm_building: '', dorm_room: '',
  is_off_campus: false, off_campus_address: '', notes: ''
})
const form = reactive(defaultForm())
const rules = {
  student_no: [{ required: true, message: '请填写学号', trigger: 'blur' }],
  name: [{ required: true, message: '请填写姓名', trigger: 'blur' }]
}

// ========== 标签相关 ==========
const presetColors = ['#5B92E5', '#7BCFCB', '#F8B4B4', '#B7E4C7', '#D5B7E4', '#F5C7A0', '#F9E79F', '#B7D8E4']
const allTags = ref([])
const tagManageDialog = ref(false)
const tagCreating = ref(false)
const newTag = reactive({ name: '', color: '#5B92E5' })

// 学生标签缓存 { studentId: [tagObj, ...] }
const studentTagCache = ref({})
const studentTagDialog = ref(false)
const editingStudent = ref(null)

async function loadAllTags() {
  try {
    const data = await tagsApi.list()
    allTags.value = Array.isArray(data) ? data : (data?.items || [])
  } catch { allTags.value = [] }
}

async function onCreateTag() {
  if (!newTag.name.trim()) return
  tagCreating.value = true
  try {
    await tagsApi.create({ name: newTag.name.trim(), color: newTag.color })
    ElMessage.success('标签已创建')
    newTag.name = ''
    newTag.color = '#5B92E5'
    await loadAllTags()
  } catch (e) {
    ElMessage.error('创建失败')
  } finally { tagCreating.value = false }
}

async function onDeleteTag(tag) {
  try {
    await ElMessageBox.confirm(`确认删除标签「${tag.name}」？`, '删除标签', { type: 'warning' })
  } catch { return }
  try {
    await tagsApi.remove(tag.id)
    ElMessage.success('已删除')
    await loadAllTags()
    // 清除缓存中该标签
    for (const sid of Object.keys(studentTagCache.value)) {
      studentTagCache.value[sid] = studentTagCache.value[sid].filter(t => t.id !== tag.id)
    }
  } catch { ElMessage.error('删除失败') }
}

function getStudentTags(row) {
  return studentTagCache.value[row.id] || []
}

async function openStudentTagDialog(row) {
  editingStudent.value = row
  studentTagDialog.value = true
  if (!allTags.length) await loadAllTags()
  // 加载该学生的标签
  try {
    const data = await tagsApi.getStudentTags(row.id)
    studentTagCache.value[row.id] = Array.isArray(data) ? data : (data?.tags || [])
  } catch {
    if (!studentTagCache.value[row.id]) studentTagCache.value[row.id] = []
  }
}

function isStudentTagChecked(tagId) {
  const sid = editingStudent.value?.id
  if (!sid) return false
  return (studentTagCache.value[sid] || []).some(t => t.id === tagId)
}

async function toggleStudentTag(tag) {
  const sid = editingStudent.value?.id
  if (!sid) return
  const checked = isStudentTagChecked(tag.id)
  try {
    if (checked) {
      await tagsApi.removeStudentTag(sid, tag.id)
      studentTagCache.value[sid] = (studentTagCache.value[sid] || []).filter(t => t.id !== tag.id)
    } else {
      await tagsApi.addStudentTag(sid, tag.id)
      if (!studentTagCache.value[sid]) studentTagCache.value[sid] = []
      studentTagCache.value[sid].push(tag)
    }
  } catch { ElMessage.error('操作失败') }
}

async function removeStudentTagInline(tag) {
  const sid = editingStudent.value?.id
  if (!sid) return
  try {
    await tagsApi.removeStudentTag(sid, tag.id)
    studentTagCache.value[sid] = (studentTagCache.value[sid] || []).filter(t => t.id !== tag.id)
    ElMessage.success(`已移除标签「${tag.name}」`)
  } catch { ElMessage.error('移除标签失败') }
}

// ========== 列表操作 ==========
const reload = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.search) params.search = filters.search
    if (filters.class_name) params.class_name = filters.class_name
    if (filters.major) params.major = filters.major
    if (filters.gender) params.gender = filters.gender
    if (filters.political_status) params.political_status = filters.political_status
    if (filters.birth_source) params.birth_source = filters.birth_source
    if (filters.sort_by) params.sort_by = filters.sort_by
    if (filters.order) params.order = filters.order
    const res = await listStudents(params)
    if (Array.isArray(res)) { list.value = res; total.value = res.length }
    else if (res?.items) { list.value = res.items; total.value = res.total || res.items.length }
    else if (res?.data) { list.value = res.data; total.value = res.total || res.data.length }
    else { list.value = []; total.value = 0 }
    // 加载学生标签
    loadStudentTagsBatch()
  } finally { loading.value = false }
}

async function loadStudentTagsBatch() {
  for (const row of list.value) {
    try {
      const data = await tagsApi.getStudentTags(row.id)
      studentTagCache.value[row.id] = Array.isArray(data) ? data : (data?.tags || [])
    } catch {
      if (!studentTagCache.value[row.id]) studentTagCache.value[row.id] = []
    }
  }
}

const resetFilter = () => {
  Object.assign(filters, { search: '', class_name: '', major: '', gender: '', political_status: '', birth_source: '', sort_by: '', order: '' })
  page.value = 1
  reload()
}

const onSort = ({ prop, order }) => {
  filters.sort_by = prop || ''
  filters.order = order === 'descending' ? 'desc' : (order === 'ascending' ? 'asc' : '')
  reload()
}

const openCreate = () => { editing.value = null; Object.assign(form, defaultForm()); dialogVisible.value = true }
const openEdit = (row) => { editing.value = row; Object.assign(form, defaultForm(), row, { class_id: row.class_id ?? null }); dialogVisible.value = true }
const onClose = () => { formRef.value?.resetFields() }

const onSubmit = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = {}
    Object.keys(form).forEach((k) => {
      if (form[k] !== '' && form[k] !== null && form[k] !== undefined) payload[k] = form[k]
    })
    if (editing.value) { await updateStudent(editing.value.id, payload); ElMessage.success('已更新') }
    else { await createStudent(payload); ElMessage.success('已创建') }
    dialogVisible.value = false
    studentStore.bumpRefresh()
    reload()
  } finally { saving.value = false }
}

const onDelete = async (row) => {
  await deleteStudent(row.id)
  ElMessage.success('已删除')
  studentStore.bumpRefresh()
  reload()
}

const exportSelected = async () => {
  if (!selected.value.length) { ElMessage.warning('请先勾选要导出的学生'); return }
  try {
    const ids = selected.value.map(r => r.id)
    const blob = await exportStudentsByIds(ids)
    triggerDownload(blob, stampedName(`学生名单_选中${ids.length}人`))
    ElMessage.success(`已导出 ${ids.length} 名学生`)
  } catch (e) { ElMessage.error('导出失败') }
}

const exportSelectedFull = async () => {
  if (!selected.value.length) { ElMessage.warning('请先勾选要导出的学生'); return }
  try {
    const ids = selected.value.map(r => r.id)
    const blob = await exportStudentsFull(ids)
    triggerDownload(blob, stampedName(`学生完整档案_选中${ids.length}人`))
    ElMessage.success(`已导出 ${ids.length} 名学生的完整档案`)
  } catch (e) { ElMessage.error('导出失败') }
}

const exportAll = async () => {
  try {
    const params = {}
    if (filters.search) params.keyword = filters.search
    if (filters.class_name) params.class_name = filters.class_name
    if (filters.major) params.major = filters.major
    if (filters.gender) params.gender = filters.gender
    if (filters.political_status) params.political_status = filters.political_status
    if (filters.birth_source) params.birth_source = filters.birth_source
    const blob = await exportStudents(params)
    const url = URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    const stamp = new Date().toISOString().slice(0,19).replace(/[-T:]/g,'')
    const tag = Object.values(params).filter(Boolean).length ? '_筛选' : '_全部'
    a.download = `students${tag}_${stamp}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success(tag === '_筛选' ? '已按当前筛选导出' : '已导出全部学生')
  } catch (e) { ElMessage.error('导出失败') }
}

onMounted(() => {
  if (!orgStore.orgTree.length) orgStore.loadTree()
  loadAllTags()
  reload()
  window.addEventListener('system-reinit-done', () => { orgStore.loadTree(true); reload() })
})
</script>

<style scoped>
.student-list { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; color: #303133; font-size: 22px; }

.tag-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
  border: 1px solid;
  white-space: nowrap;
  line-height: 1.6;
}

.tag-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tag-manage-section { padding: 0 4px; }
.tag-manage-list { max-height: 240px; overflow-y: auto; }
.tag-manage-empty { color: #909399; text-align: center; padding: 16px; font-size: 13px; }
.tag-manage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #F0F3F8;
}

.color-picker-row { display: flex; gap: 6px; }
.color-dot {
  width: 24px; height: 24px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.15s;
}
.color-dot:hover { transform: scale(1.15); }
.color-dot.selected { border-color: #303133; box-shadow: 0 0 0 2px #fff, 0 0 0 4px currentColor; }

.tag-create-form { margin-top: 4px; }

.student-tag-check-list { max-height: 320px; overflow-y: auto; }
.student-tag-check-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s;
}
.student-tag-check-item:hover { background: #F5F8FC; }
</style>
