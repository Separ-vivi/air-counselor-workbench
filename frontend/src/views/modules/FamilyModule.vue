<template>
  <div class="module-page">
    <div class="page-header">
      <h2>家庭联络</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate(null)">新增记录</el-button>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="学生">
          <StudentSelect v-model="filter.student_id" style="width: 260px" @change="reload" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-select v-model="filter.contact_type" placeholder="全部" clearable style="width: 160px" @change="reload">
            <el-option v-for="t in contactTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" stripe border max-height="600">
        <el-table-column label="学生" prop="student_name" width="110">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/students/${row.student_id}`)">{{ row.student_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="学号" prop="student_no" width="140" />
        <el-table-column label="联系人" prop="contact_name" width="120" />
        <el-table-column label="关系" prop="relationship" width="100" />
        <el-table-column label="联系方式" prop="contact_type" width="120" />
        <el-table-column label="联系日期" prop="contact_date" width="130" />
        <el-table-column label="沟通主题" prop="topic" min-width="160" show-overflow-tooltip />
        <el-table-column label="沟通内容" prop="content" min-width="200" show-overflow-tooltip />
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

    <el-dialog v-model="dlg" :title="editing?.id ? '编辑家庭联络' : '新增家庭联络'" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="学生" prop="student_id">
          <StudentSelect v-model="form.student_id" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact_name">
          <el-input v-model="form.contact_name" />
        </el-form-item>
        <el-form-item label="关系">
          <el-select v-model="form.relationship" style="width: 100%" clearable>
            <el-option v-for="r in relations" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系方式">
          <el-select v-model="form.contact_type" style="width: 100%" clearable>
            <el-option v-for="t in contactTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系日期">
          <el-date-picker v-model="form.contact_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="沟通主题">
          <el-input v-model="form.topic" />
        </el-form-item>
        <el-form-item label="沟通内容">
          <el-input v-model="form.content" type="textarea" :rows="3" />
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
import { family as familyApi } from '@/api/modules'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'

const studentStore = useStudentStore()
const contactTypes = ['电话', '微信', '当面', '短信', '视频', '邮件']
const relations = ['父亲', '母亲', '监护人', '祖父', '祖母', '外祖父', '外祖母', '兄弟', '姐妹', '其他']

const list = ref([])
const loading = ref(false)
const filter = reactive({ student_id: null, contact_type: '' })

const reload = async () => {
  loading.value = true
  try {
    const params = {}
    if (filter.student_id) params.student_id = filter.student_id
    if (filter.contact_type) params.contact_type = filter.contact_type
    const res = await familyApi.list(params)
    list.value = Array.isArray(res) ? res : (res?.items || [])
  } finally { loading.value = false }
}

const dlg = ref(false)
const editing = ref(null)
const saving = ref(false)
const formRef = ref(null)
const defaultForm = () => ({ student_id: null, contact_name: '', relationship: '', contact_type: '', contact_date: '', topic: '', content: '' })
const form = reactive(defaultForm())
const rules = {
  student_id: [{ required: true, message: '请选择学生', trigger: 'change' }],
  contact_name: [{ required: true, message: '请填写联系人', trigger: 'blur' }]
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
      await familyApi.update(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await familyApi.create(form)
      ElMessage.success('已创建')
    }
    dlg.value = false
    studentStore.bumpRefresh()
    reload()
  } finally { saving.value = false }
}
const onDelete = async (row) => {
  await familyApi.remove(row.id)
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
