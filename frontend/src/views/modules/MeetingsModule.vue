<template>
  <div class="module-page">
    <div class="page-header">
      <h2>📋 班会管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增班会</el-button>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="班级">
          <el-select v-model="filter.class_id" placeholder="全部班级" clearable filterable style="width: 220px" @change="reload">
            <el-option v-for="c in orgStore.classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="filter.theme" placeholder="主题关键字" clearable style="width: 200px" @keyup.enter="reload" @clear="reload" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" stripe border max-height="600">
        <el-table-column label="班会主题" prop="theme" min-width="200" show-overflow-tooltip />
        <el-table-column label="所属班级" prop="class_name" width="180" show-overflow-tooltip />
        <el-table-column label="召开日期" prop="meeting_date" width="130" />
        <el-table-column label="主持人" prop="host" width="120" />
        <el-table-column label="出席人数" prop="attendance_count" width="100" align="center" />
        <el-table-column label="记录人" prop="recorder" width="120" />
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

    <el-dialog v-model="dlg" :title="editing?.id ? '编辑班会' : '新增班会'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="班会主题" prop="theme">
          <el-input v-model="form.theme" />
        </el-form-item>
        <el-form-item label="所属班级" prop="class_id">
          <el-select v-model="form.class_id" filterable style="width: 100%">
            <el-option v-for="c in orgStore.classes" :key="c.id" :label="c.name" :value="c.id" />
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
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { classMeetings as mApi } from '@/api/modules'
import { useOrgStore } from '@/stores/org'

const orgStore = useOrgStore()

const list = ref([])
const loading = ref(false)
const filter = reactive({ class_id: null, theme: '' })

const reload = async () => {
  loading.value = true
  try {
    const params = {}
    if (filter.class_id) params.class_id = filter.class_id
    if (filter.theme) params.theme = filter.theme
    const res = await mApi.list(params)
    list.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { loading.value = false }
}

const dlg = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({ theme: '', class_id: null, meeting_date: '', host: '', recorder: '', attendance_count: 0, summary: '', notes: '' })
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
</style>
