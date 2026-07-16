<template>
  <div class="module-page">
    <div class="page-header">
      <h2>💼 就业管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增记录</el-button>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="学生">
          <StudentSelect v-model="filter.student_id" style="width: 260px" @change="reload" />
        </el-form-item>
        <el-form-item label="就业状态">
          <el-select v-model="filter.status" placeholder="全部" clearable style="width: 180px" @change="reload">
            <el-option v-for="s in statusList" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="4" v-for="s in statusStats" :key="s.name">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ s.name }}</div>
          <div class="stat-value" :style="{ color: s.color }">{{ s.count }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <el-table :data="filteredList" v-loading="loading" stripe border max-height="600">
        <el-table-column label="学生" prop="student_name" width="110">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/students/${row.student_id}`)">{{ row.student_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="学号" prop="student_no" width="140" />
        <el-table-column label="班级" prop="class_name" min-width="140" show-overflow-tooltip />
        <el-table-column label="就业状态" prop="status" width="130">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ row.status || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="单位/院校" prop="company" min-width="200" show-overflow-tooltip />
        <el-table-column label="岗位/专业" prop="position" min-width="140" show-overflow-tooltip />
        <el-table-column label="签约日期" prop="sign_date" width="130" />
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

    <el-dialog v-model="dlg" :title="editing?.id ? '编辑就业记录' : '新增就业记录'" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="学生" prop="student_id">
          <StudentSelect v-model="form.student_id" />
        </el-form-item>
        <el-form-item label="就业状态" prop="status">
          <el-select v-model="form.status" style="width: 100%">
            <el-option v-for="s in statusList" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="单位/院校">
          <el-input v-model="form.company" />
        </el-form-item>
        <el-form-item label="岗位/专业">
          <el-input v-model="form.position" />
        </el-form-item>
        <el-form-item label="工作地点">
          <el-input v-model="form.work_location" />
        </el-form-item>
        <el-form-item label="签约日期">
          <el-date-picker v-model="form.sign_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="薪资(k)">
          <el-input v-model="form.salary" placeholder="如 8k / 15w" />
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
import { Plus } from '@element-plus/icons-vue'
import { employment as empApi } from '@/api/modules'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'

const studentStore = useStudentStore()
const statusList = ['已签约', '拟录用', '升学', '出国', '待业', '其他']
const statusColor = { 已签约: '#67C23A', 拟录用: '#409EFF', 升学: '#E6A23C', 出国: '#B48EAD', 待业: '#F56C6C', 其他: '#909399' }

const list = ref([])
const loading = ref(false)
const filter = reactive({ student_id: null, status: '' })

const filteredList = computed(() => {
  let rs = list.value
  if (filter.student_id) rs = rs.filter((r) => r.student_id === filter.student_id)
  if (filter.status) rs = rs.filter((r) => r.status === filter.status)
  return rs
})

const statusStats = computed(() =>
  statusList.map((s) => ({ name: s, count: list.value.filter((r) => r.status === s).length, color: statusColor[s] || '#909399' }))
)

const statusTag = (s) => {
  const m = { 已签约: 'success', 拟录用: 'primary', 升学: 'warning', 出国: '', 待业: 'danger', 其他: 'info' }
  return m[s] || ''
}

const reload = async () => {
  loading.value = true
  try {
    const res = await empApi.list()
    list.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { loading.value = false }
}

const dlg = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({ student_id: null, status: '', company: '', position: '', work_location: '', sign_date: '', salary: '', notes: '' })
const form = reactive(defaultForm())
const rules = {
  student_id: [{ required: true, message: '请选择学生', trigger: 'change' }],
  status: [{ required: true, message: '请选择就业状态', trigger: 'change' }]
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
      await empApi.update(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await empApi.create(form)
      ElMessage.success('已创建')
    }
    dlg.value = false
    studentStore.bumpRefresh()
    reload()
  } finally { saving.value = false }
}
const onDelete = async (row) => {
  await empApi.remove(row.id)
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
.stat-card { border-radius: 12px; text-align: center; }
.stat-label { color: #909399; font-size: 13px; margin-bottom: 6px; }
.stat-value { font-size: 22px; font-weight: 600; }
</style>
