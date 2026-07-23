<template>
  <div class="module-page">
    <div class="page-header">
      <h2>班会管理</h2>
      <div>
        <el-button
          type="success"
          :icon="Download"
          :disabled="!checkedRows.length"
          @click="exportSelected"
        >导出选中（{{ checkedRows.length }}）</el-button>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增班会</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="班级">
          <el-select v-model="filter.class_id" placeholder="全部班级" clearable filterable style="width: 220px" @change="reload">
            <el-option v-for="c in orgStore.allClasses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filter.theme" placeholder="主题/主持人/记录人/班级" clearable style="width: 240px" />
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
        <el-table-column label="班会主题" prop="theme" min-width="200" show-overflow-tooltip sortable="custom" />
        <el-table-column label="所属班级" prop="class_name" width="180" show-overflow-tooltip sortable="custom" />
        <el-table-column label="召开日期" prop="meeting_date" width="130" sortable="custom" />
        <el-table-column label="主持人" prop="host" width="120" sortable="custom" />
        <el-table-column label="出席人数" prop="attendance_count" width="100" align="center" sortable="custom" />
        <el-table-column label="记录人" prop="recorder" width="120" sortable="custom" />
        <el-table-column label="班主任出席" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <template v-if="row.teacher_attended">
              <el-tag type="success" size="small" style="margin-right:6px">已出席</el-tag>
              <span v-if="row.teacher_names">{{ row.teacher_names }}</span>
            </template>
            <el-tag v-else type="info" size="small">未出席</el-tag>
          </template>
        </el-table-column>
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

    <el-dialog v-model="dlg" :title="editing?.id ? '编辑班会' : '新增班会'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="班会主题" prop="theme">
          <el-input v-model="form.theme" />
        </el-form-item>
        <el-form-item label="所属班级" prop="class_id">
          <el-select v-model="form.class_id" filterable style="width: 100%">
            <el-option v-for="c in orgStore.allClasses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="召开日期">
          <el-date-picker v-model="form.meeting_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="主持人">
          <el-input v-model="form.host" />
        </el-form-item>
        <el-form-item label="记录人">
          <el-input v-model="form.recorder" />
        </el-form-item>
        <el-form-item label="出席人数">
          <el-input-number v-model="form.attendance_count" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="班主任出席">
          <div style="display:flex; gap:12px; align-items:center; width:100%">
            <el-switch v-model="form.teacher_attended" active-text="出席" inactive-text="未出席" inline-prompt />
            <el-input
              v-if="form.teacher_attended"
              v-model="form.teacher_names"
              placeholder="老师姓名，多位用逗号分隔"
              style="flex:1"
            />
          </div>
        </el-form-item>
        <el-form-item label="内容摘要">
          <el-input v-model="form.summary" type="textarea" :rows="3" />
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
import { classMeetings as mApi } from '@/api/modules'
import { useOrgStore } from '@/stores/org'
import { triggerDownload, stampedName } from '@/utils/download'

const orgStore = useOrgStore()

const list = ref([])
const loading = ref(false)
const filter = reactive({ class_id: null, theme: '', semester: '', dateRange: null })

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 学期列表（从数据动态提取）
const semesterList = computed(() => {
  const s = new Set()
  list.value.forEach(r => {
    if (r.semester) s.add(r.semester)
    else if (r.meeting_date) {
      const d = new Date(r.meeting_date)
      const y = d.getFullYear()
      const m = d.getMonth() + 1
      const ay = m >= 9 ? y : y - 1
      s.add(`${ay}-${ay + 1}-${m >= 2 && m < 9 ? 2 : 1}`)
    }
  })
  return [...s].filter(Boolean).sort().reverse()
})

const resetFilters = () => {
  filter.class_id = null
  filter.theme = ''
  filter.semester = ''
  filter.dateRange = null
  currentPage.value = 1
  reload()
}

// 前端筛选 + 分页
const filteredList = computed(() => {
  let data = list.value
  if (filter.semester) {
    data = data.filter(r => {
      if (r.semester) return r.semester === filter.semester
      if (r.meeting_date) {
        const d = new Date(r.meeting_date)
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
    data = data.filter(r => r.meeting_date && r.meeting_date >= filter.dateRange[0] && r.meeting_date <= filter.dateRange[1])
  }
  return data
})

const total = computed(() => filteredList.value.length)
const pagedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})

// v3j-B-b03 · 排序 + 搜索 + 多选
const sortBy = ref('meeting_date')
const sortOrder = ref('desc')
const checkedRows = ref([])
const onSelectionChange = (rows) => { checkedRows.value = rows }
const onSort = ({ prop, order }) => {
  sortBy.value = prop || 'meeting_date'
  sortOrder.value = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : 'desc')
  reload()
}
let _searchTimer = null
watch(() => filter.theme, () => {
  clearTimeout(_searchTimer)
  _searchTimer = setTimeout(() => reload(), 300)
})

const reload = async () => {
  loading.value = true
  try {
    const params = {}
    if (filter.class_id) params.class_id = filter.class_id
    if (filter.theme) params.search = filter.theme
    if (sortBy.value) params.sort_by = sortBy.value
    if (sortOrder.value) params.order = sortOrder.value
    const res = await mApi.list(params)
    list.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { loading.value = false }
}

const exportSelected = async () => {
  if (!checkedRows.value.length) { ElMessage.warning('请先勾选要导出的班会'); return }
  try {
    const ids = checkedRows.value.map(r => r.id)
    const blob = await mApi.exportByIds(ids)
    triggerDownload(blob, stampedName(`班会_选中${ids.length}条`))
    ElMessage.success(`已导出 ${ids.length} 条`)
  } catch (e) { ElMessage.error('导出失败') }
}
const exportAll = async () => {
  try {
    const params = {}
    if (filter.class_id) params.class_id = filter.class_id
    if (filter.theme) params.search = filter.theme
    const blob = await mApi.exportAll(params)
    triggerDownload(blob, stampedName(`班会_全部`))
    ElMessage.success('已导出全部')
  } catch (e) { ElMessage.error('导出失败') }
}

const dlg = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({ theme: '', class_id: null, meeting_date: '', host: '', recorder: '', attendance_count: 0, summary: '', notes: '', teacher_attended: false, teacher_names: '' })
const form = reactive(defaultForm())
const rules = {
  theme: [{ required: true, message: '请填写班会主题', trigger: 'blur' }],
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }]
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
      await mApi.update(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await mApi.create(form)
      ElMessage.success('已创建')
    }
    dlg.value = false
    reload()
  } finally { saving.value = false }
}
const onDelete = async (row) => {
  await mApi.remove(row.id)
  ElMessage.success('已删除')
  reload()
}

onMounted(() => {
  if (!orgStore.orgTree.length) orgStore.loadTree()
  reload()
})
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
