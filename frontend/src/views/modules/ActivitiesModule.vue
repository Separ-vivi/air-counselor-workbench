<template>
  <div class="module-page">
    <div class="page-header">
      <h2>活动管理</h2>
      <div>
        <el-button
          type="success"
          :icon="Download"
          :disabled="!checkedRows.length"
          @click="exportSelected"
        >导出选中（{{ checkedRows.length }}）</el-button>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增活动</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>活动列表 · 共 {{ total }} 条</span>
              <div style="display: flex; gap: 8px; flex-wrap: wrap">
                <el-select v-model="filterType" placeholder="全部类型" clearable size="small" style="width: 140px">
                  <el-option v-for="t in allTypes" :key="t" :label="t" :value="t" />
                </el-select>
                <el-select v-model="filterSemester" placeholder="全部学期" clearable filterable size="small" style="width: 160px">
                  <el-option v-for="s in semesterList" :key="s" :label="s" :value="s" />
                </el-select>
                <el-date-picker v-model="filterDateRange" type="daterange" range-separator="至"
                  start-placeholder="开始" end-placeholder="结束" format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD" size="small" style="width: 230px" />
                <el-input v-model="filterKw" placeholder="搜索活动名/组织者/地点" clearable size="small" style="width: 200px" />
              </div>
            </div>
          </template>
          <el-table
            :data="pagedList"
            v-loading="loading"
            stripe
            border
            highlight-current-row
            max-height="600"
            row-key="id"
            @row-click="selectActivity"
            @selection-change="onSelectionChange"
            @sort-change="onSort"
          >
            <el-table-column type="selection" width="45" reserve-selection />
            <el-table-column label="活动名称" prop="activity_name" min-width="180" show-overflow-tooltip sortable="custom" />
            <el-table-column label="类型" prop="activity_type" width="120" sortable="custom">
              <template #default="{ row }">
                <el-tag size="small" :type="typeTag(row.activity_type)">{{ row.activity_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="日期" prop="activity_date" width="120" sortable="custom" />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click.stop="openCreate(row)">编辑</el-button>
                <el-popconfirm title="确认删除？" @confirm="onDelete(row)">
                  <template #reference>
                    <el-button link type="danger" size="small" @click.stop>删除</el-button>
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
              layout="total, sizes, prev, pager, next"
              small
            />
          </div>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>
                <template v-if="currentActivity">🎯 {{ currentActivity.activity_name }} · 报名/参与</template>
                <template v-else>请选择左侧活动查看报名情况</template>
              </span>
              <el-button v-if="currentActivity" type="primary" size="small" :icon="Plus" @click="openSignup">添加报名</el-button>
            </div>
          </template>
          <el-empty v-if="!currentActivity" description="点击左侧任一活动" :image-size="80" />
          <el-table v-else :data="signups" v-loading="signupsLoading" stripe border max-height="530">
            <el-table-column label="学生" prop="student_name" width="120">
              <template #default="{ row }">
                <el-link type="primary" @click="$router.push(`/students/${row.student_id}`)">{{ row.student_name }}</el-link>
              </template>
            </el-table-column>
            <el-table-column label="学号" prop="student_no" width="140" />
            <el-table-column label="角色" prop="role" width="120" />
            <el-table-column label="状态" prop="status" width="110">
              <template #default="{ row }">
                <el-tag :type="row.status === '已参加' ? 'success' : 'info'" size="small">{{ row.status || '-' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="备注" prop="notes" show-overflow-tooltip />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="editSignup(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 活动编辑 -->
    <el-dialog v-model="dlg" :title="editing?.id ? '编辑活动' : '新增活动'" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="活动名称" prop="activity_name">
          <el-input v-model="form.activity_name" />
        </el-form-item>
        <el-form-item label="活动类型">
          <el-select v-model="form.activity_type" style="width: 100%" clearable>
            <el-option v-for="t in types" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="活动日期">
          <el-date-picker v-model="form.activity_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="组织者">
          <el-input v-model="form.organizer" />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="活动说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="onSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 报名编辑 -->
    <el-dialog v-model="signupDlg" :title="signupEditing?.id ? '编辑报名' : '添加报名'" width="480px">
      <el-form :model="signupForm" :rules="signupRules" ref="signupFormRef" label-width="90px">
        <el-form-item label="学生" prop="student_id">
          <StudentSelect v-model="signupForm.student_id" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="signupForm.role" style="width: 100%" clearable>
            <el-option v-for="r in roles" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="signupForm.status" style="width: 100%" clearable>
            <el-option label="已报名" value="已报名" />
            <el-option label="已参加" value="已参加" />
            <el-option label="缺席" value="缺席" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="signupForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="signupDlg = false">取消</el-button>
        <el-button type="primary" @click="saveSignup" :loading="signupSaving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import { activities as actApi } from '@/api/modules'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'
import { triggerDownload, stampedName } from '@/utils/download'

const studentStore = useStudentStore()
const types = ['学术科技', '文体艺术', '志愿公益', '思政教育', '实践创新', '其他']

// v3j-D · D2: 活动类型筛选（含 seed 里的所有类型）
const filterType = ref('')
// v3j-D 补丁2: 筛选选项完全从真实数据抽取（不掺硬编码常量，避免筛不到）
const allTypes = computed(() => {
  const s = new Set()
  list.value.forEach((r) => { if (r.activity_type) s.add(r.activity_type) })
  return Array.from(s)
})
const filteredList = computed(() => {
  let data = list.value
  if (filterType.value) data = data.filter((r) => (r.activity_type || '') === filterType.value)
  if (filterSemester.value) {
    data = data.filter(r => {
      if (r.semester) return r.semester === filterSemester.value
      if (r.activity_date) {
        const d = new Date(r.activity_date)
        const y = d.getFullYear()
        const m = d.getMonth() + 1
        const ay = m >= 9 ? y : y - 1
        const sem = `${ay}-${ay + 1}-${m >= 2 && m < 9 ? 2 : 1}`
        return sem === filterSemester.value
      }
      return false
    })
  }
  if (filterDateRange.value && filterDateRange.value.length === 2) {
    data = data.filter(r => r.activity_date && r.activity_date >= filterDateRange.value[0] && r.activity_date <= filterDateRange.value[1])
  }
  return data
})

const total = computed(() => filteredList.value.length)
const pagedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})
const roles = ['参与者', '组织者', '负责人', '志愿者', '嘉宾']

const list = ref([])
const filterKw = ref('')
const filterSemester = ref('')
const filterDateRange = ref(null)
const loading = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 学期列表（从数据动态提取）
const semesterList = computed(() => {
  const s = new Set()
  list.value.forEach(r => {
    if (r.semester) s.add(r.semester)
    else if (r.activity_date) {
      const d = new Date(r.activity_date)
      const y = d.getFullYear()
      const m = d.getMonth() + 1
      const ay = m >= 9 ? y : y - 1
      s.add(`${ay}-${ay + 1}-${m >= 2 && m < 9 ? 2 : 1}`)
    }
  })
  return [...s].filter(Boolean).sort().reverse()
})

const resetFilters = () => {
  filterType.value = ''
  filterKw.value = ''
  filterSemester.value = ''
  filterDateRange.value = null
  currentPage.value = 1
}
const currentActivity = ref(null)
const signups = ref([])
const signupsLoading = ref(false)

// v3j-B-b02 · 前端过滤已移除，改由后端 /activities?search=&sort_by=&order= 支持
const sortBy = ref('activity_date')
const sortOrder = ref('desc')
const checkedRows = ref([])
const onSelectionChange = (rows) => { checkedRows.value = rows }
const onSort = ({ prop, order }) => {
  sortBy.value = prop || 'activity_date'
  sortOrder.value = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : 'desc')
  reload()
}
let _searchTimer = null
watch(filterKw, () => {
  clearTimeout(_searchTimer)
  _searchTimer = setTimeout(() => reload(), 300)
})

const typeTag = (t) => {
  if (!t) return ''
  if (t.includes('学术') || t.includes('科技')) return 'success'
  if (t.includes('文体')) return 'warning'
  if (t.includes('志愿')) return ''
  return 'info'
}

const reload = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterKw.value) params.search = filterKw.value
    if (sortBy.value) params.sort_by = sortBy.value
    if (sortOrder.value) params.order = sortOrder.value
    const res = await actApi.list(params)
    list.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { loading.value = false }
}

const exportSelected = async () => {
  if (!checkedRows.value.length) {
    ElMessage.warning('请先勾选要导出的活动')
    return
  }
  try {
    const ids = checkedRows.value.map(r => r.id)
    const blob = await actApi.exportByIds(ids)
    triggerDownload(blob, stampedName(`活动列表_选中${ids.length}条`))
    ElMessage.success(`已导出 ${ids.length} 条活动`)
  } catch (e) { ElMessage.error('导出失败') }
}
const exportAll = async () => {
  try {
    const params = {}
    if (filterKw.value) params.search = filterKw.value
    const blob = await actApi.exportAll(params)
    triggerDownload(blob, stampedName(`活动列表_全部`))
    ElMessage.success('已导出全部活动')
  } catch (e) { ElMessage.error('导出失败') }
}

const selectActivity = async (row) => {
  currentActivity.value = row
  signupsLoading.value = true
  try {
    const res = await actApi.listSignups(row.id)
    signups.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { signupsLoading.value = false }
}

const dlg = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({ activity_name: '', activity_type: '', activity_date: '', organizer: '', location: '', description: '' })
const form = reactive(defaultForm())
const rules = {
  activity_name: [{ required: true, message: '请填写活动名', trigger: 'blur' }]
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
      await actApi.update(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await actApi.create(form)
      ElMessage.success('已创建')
    }
    dlg.value = false
    reload()
  } finally { saving.value = false }
}
const onDelete = async (row) => {
  await actApi.remove(row.id)
  ElMessage.success('已删除')
  if (currentActivity.value?.id === row.id) { currentActivity.value = null; signups.value = [] }
  reload()
}

// signup
const signupDlg = ref(false)
const signupEditing = ref(null)
const signupSaving = ref(false)
const signupFormRef = ref(null)
const signupDefault = () => ({ student_id: null, role: '参与者', status: '已报名', notes: '' })
const signupForm = reactive(signupDefault())
const signupRules = { student_id: [{ required: true, message: '请选择学生', trigger: 'change' }] }
const openSignup = () => {
  signupEditing.value = null
  Object.assign(signupForm, signupDefault())
  signupDlg.value = true
}
const editSignup = (row) => {
  signupEditing.value = row
  Object.assign(signupForm, signupDefault(), row)
  signupDlg.value = true
}
const saveSignup = async () => {
  await signupFormRef.value?.validate()
  signupSaving.value = true
  try {
    if (signupEditing.value?.id) {
      await actApi.updateSignup(selected.value.id, signupEditing.value.id, signupForm)
    } else {
      await actApi.createSignup(selected.value.id, signupForm)
    }
    ElMessage.success('已保存')
    signupDlg.value = false
    studentStore.bumpRefresh()
    selectActivity(selected.value)
  } finally { signupSaving.value = false }
}

watch(() => studentStore.refreshBumper, () => {
  reload()
  if (selected.value) selectActivity(selected.value)
})
onMounted(reload)
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
