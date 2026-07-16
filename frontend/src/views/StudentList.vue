<template>
  <div class="student-list">
    <div class="page-header">
      <h2>📋 学生管理</h2>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="openCreate">新增学生</el-button>
        <el-button :icon="Upload" @click="$router.push('/smart-import')">批量导入</el-button>
        <el-button :icon="Download" @click="exportAll">导出</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.search"
            placeholder="姓名/学号/拼音"
            clearable
            style="width: 220px"
            :prefix-icon="Search"
            @keyup.enter="reload"
            @clear="reload"
          />
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
            <el-option label="预备党员" value="预备党员" />
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
      <el-table
        v-loading="loading"
        :data="list"
        stripe
        border
        highlight-current-row
        @sort-change="onSort"
      >
        <el-table-column label="学号" prop="student_no" width="140" sortable="custom" />
        <el-table-column label="姓名" prop="name" width="110" sortable="custom">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/students/${row.id}`)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="性别" prop="gender" width="70" />
        <el-table-column label="班级" prop="class_name" min-width="160" show-overflow-tooltip />
        <el-table-column label="专业" prop="major" min-width="140" show-overflow-tooltip />
        <el-table-column label="政治面貌" prop="political_status" width="110" />
        <el-table-column label="生源地" prop="birth_source" width="120" show-overflow-tooltip />
        <el-table-column label="电话" prop="phone" width="130" />
        <el-table-column label="操作" fixed="right" width="180">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="$router.push(`/students/${row.id}`)">档案</el-button>
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
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="reload"
          @current-change="reload"
        />
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
                <el-option label="预备党员" value="预备党员" />
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
              <el-input v-model="form.birth_source" placeholder="省份/城市" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, Upload, Download, Refresh } from '@element-plus/icons-vue'
import {
  listStudents,
  createStudent,
  updateStudent,
  deleteStudent,
  exportStudents
} from '@/api/students'
import { useOrgStore } from '@/stores/org'
import { useStudentStore } from '@/stores/student'

const orgStore = useOrgStore()
const studentStore = useStudentStore()

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const filters = reactive({
  search: '',
  class_name: '',
  major: '',
  gender: '',
  political_status: '',
  birth_source: '',
  sort_by: '',
  order: ''
})

const dialogVisible = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({
  student_no: '',
  name: '',
  gender: '',
  class_id: null,
  birth_date: '',
  political_status: '',
  phone: '',
  email: '',
  parent_phone: '',
  birth_source: '',
  notes: ''
})
const form = reactive(defaultForm())
const rules = {
  student_no: [{ required: true, message: '请填写学号', trigger: 'blur' }],
  name: [{ required: true, message: '请填写姓名', trigger: 'blur' }]
}

const reload = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value
    }
    if (filters.search) params.search = filters.search
    if (filters.class_name) params.class_name = filters.class_name
    if (filters.major) params.major = filters.major
    if (filters.gender) params.gender = filters.gender
    if (filters.political_status) params.political_status = filters.political_status
    if (filters.birth_source) params.birth_source = filters.birth_source
    if (filters.sort_by) params.sort_by = filters.sort_by
    if (filters.order) params.order = filters.order

    const res = await listStudents(params)
    // 兼容多种返回结构
    if (Array.isArray(res)) {
      list.value = res
      total.value = res.length
    } else if (res?.items) {
      list.value = res.items
      total.value = res.total || res.items.length
    } else if (res?.data) {
      list.value = res.data
      total.value = res.total || res.data.length
    } else {
      list.value = []
      total.value = 0
    }
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  Object.assign(filters, {
    search: '',
    class_name: '',
    major: '',
    gender: '',
    political_status: '',
    birth_source: '',
    sort_by: '',
    order: ''
  })
  page.value = 1
  reload()
}

const onSort = ({ prop, order }) => {
  filters.sort_by = prop || ''
  filters.order = order === 'descending' ? 'desc' : (order === 'ascending' ? 'asc' : '')
  reload()
}

const openCreate = () => {
  editing.value = null
  Object.assign(form, defaultForm())
  dialogVisible.value = true
}
const openEdit = (row) => {
  editing.value = row
  Object.assign(form, defaultForm(), row, { class_id: row.class_id ?? null })
  dialogVisible.value = true
}
const onClose = () => {
  formRef.value?.resetFields()
}

const onSubmit = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    // 组装 payload，去掉空串
    const payload = {}
    Object.keys(form).forEach((k) => {
      if (form[k] !== '' && form[k] !== null && form[k] !== undefined) payload[k] = form[k]
    })
    if (editing.value) {
      await updateStudent(editing.value.id, payload)
      ElMessage.success('已更新')
    } else {
      await createStudent(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    studentStore.bumpRefresh()
    reload()
  } finally {
    saving.value = false
  }
}

const onDelete = async (row) => {
  await deleteStudent(row.id)
  ElMessage.success('已删除')
  studentStore.bumpRefresh()
  reload()
}

const exportAll = async () => {
  try {
    const blob = await exportStudents()
    const url = URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = `students_${Date.now()}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {}
}

onMounted(() => {
  if (!orgStore.orgTree.length) orgStore.loadTree()
  reload()
})
</script>

<style scoped>
.student-list { padding: 4px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { margin: 0; color: #303133; font-size: 22px; }
</style>
