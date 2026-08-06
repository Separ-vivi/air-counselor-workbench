<template>
  <div class="module-page">
    <div class="page-header">
      <h2>班主任管理</h2>
      <div>
        <el-button
          type="success"
          :icon="Download"
          :disabled="!checkedRows.length"
          @click="exportSelected"
        >导出选中（{{ checkedRows.length }}）</el-button>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增班主任</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="搜索">
          <el-input v-model="filter.kw" placeholder="姓名/工号/院系/电话/邮箱" clearable style="width: 260px" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table
        :data="list"
        v-loading="loading"
        stripe
        border
        max-height="640"
        row-key="id"
        @selection-change="onSelectionChange"
        @sort-change="onSort"
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

    <el-dialog v-model="dlg" :title="editing?.id ? '编辑班主任' : '新增班主任'" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="工号">
          <el-input v-model="form.teacher_no" />
        </el-form-item>
        <el-form-item label="所带班级">
          <el-select v-model="form.class_id" filterable clearable style="width: 100%">
            <el-option v-for="c in orgStore.allClasses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="院系">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="职称">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="办公地点" prop="office">
          <el-input v-model="form.office" placeholder="如：文远楼403" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
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
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import { classTeachers as tApi } from '@/api/modules'
import { useOrgStore } from '@/stores/org'
import { triggerDownload, stampedName } from '@/utils/download'

const orgStore = useOrgStore()

const list = ref([])
const loading = ref(false)
const filter = reactive({ kw: '' })

// v3j-B-b03 · 排序 + 搜索 + 多选
const sortBy = ref('name')
const sortOrder = ref('asc')
const checkedRows = ref([])
const onSelectionChange = (rows) => { checkedRows.value = rows }
const onSort = ({ prop, order }) => {
  sortBy.value = prop || 'name'
  sortOrder.value = order === 'ascending' ? 'asc' : (order === 'descending' ? 'desc' : 'asc')
  reload()
}
let _searchTimer = null
watch(() => filter.kw, () => {
  clearTimeout(_searchTimer)
  _searchTimer = setTimeout(() => reload(), 300)
})

const buildParams = () => {
  const params = {}
  if (filter.kw) params.search = filter.kw
  return params
}

const reload = async () => {
  loading.value = true
  try {
    const params = buildParams()
    if (sortBy.value) params.sort_by = sortBy.value
    if (sortOrder.value) params.order = sortOrder.value
    const res = await tApi.list(params)
    list.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { loading.value = false }
}

const exportSelected = async () => {
  if (!checkedRows.value.length) { ElMessage.warning('请先勾选要导出的班主任'); return }
  try {
    const ids = checkedRows.value.map(r => r.id)
    const blob = await tApi.exportByIds(ids)
    triggerDownload(blob, stampedName(`班主任_选中${ids.length}条`))
    ElMessage.success(`已导出 ${ids.length} 条`)
  } catch (e) { ElMessage.error('导出失败') }
}
const exportAll = async () => {
  try {
    const blob = await tApi.exportAll(buildParams())
    triggerDownload(blob, stampedName(`班主任_全部`))
    ElMessage.success('已导出全部')
  } catch (e) { ElMessage.error('导出失败') }
}

const dlg = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({ name: '', teacher_no: '', class_id: null, department: '', title: '', phone: '', office: '', email: '', notes: '' })
const form = reactive(defaultForm())
const rules = {
  name: [{ required: true, message: '请填写姓名', trigger: 'blur' }]
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
      await tApi.update(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await tApi.create(form)
      ElMessage.success('已创建')
    }
    dlg.value = false
    reload()
  } finally { saving.value = false }
}
const onDelete = async (row) => {
  await tApi.remove(row.id)
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
</style>
