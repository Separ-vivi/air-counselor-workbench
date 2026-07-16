<template>
  <div>
    <div class="tip macaron-card" style="padding:12px 16px;">
      <el-icon><InfoFilled /></el-icon>&nbsp;
      本表关联的是"学生参与专项工作项目的进度"。项目本身需要在工作台"项目追踪"页新建（V3-B 阶段），此处仅登记该生在具体项目中的进度、材料状态。
    </div>
    <CrudPanel
      title="📎 专项工作参与记录"
      :columns="columns"
      :fields="fields"
      :rows="rows"
      :loading="loading"
      :rules="rules"
      :default-form="{ progress: 0, material_status: '待提交' }"
      :on-reload="load"
      :on-create="handleCreate"
      :on-update="handleUpdate"
      :on-delete="handleDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import CrudPanel from '@/components/CrudPanel.vue'
import { s360 } from '@/api/student360.js'

const props = defineProps({ sid: { type: Number, required: true } })
const rows = ref([])
const loading = ref(false)

const columns = [
  { prop: 'project_name', label: '项目名称', minWidth: 200 },
  { prop: 'progress', label: '进度(%)', width: 100,
    formatter: (v) => v == null ? '—' : (v + '%') },
  { prop: 'material_status', label: '材料状态', width: 130, type: 'tag',
    tagType: (r) => r.material_status === '审核通过' ? 'success' :
      r.material_status === '已提交' ? 'primary' :
      r.material_status === '待催缴' ? 'warning' :
      r.material_status === '未通过' ? 'danger' : '' },
  { prop: 'notes', label: '备注', minWidth: 200 }
]
const fields = [
  {
    prop: 'project_id', label: '关联项目 ID',
    type: 'number', min: 1, step: 1,
    placeholder: '项目追踪功能上线后可下拉选择；当前先手动填写项目 ID'
  },
  { prop: 'progress', label: '进度（%）', type: 'number', min: 0, max: 100, step: 5 },
  {
    prop: 'material_status', label: '材料状态', type: 'select',
    options: ['待提交', '已提交', '审核通过', '待催缴', '未通过']
  },
  { prop: 'notes', label: '备注', type: 'textarea' }
]
const rules = { project_id: [{ required: true, message: '项目 ID 必填', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try {
    rows.value = await s360.projects.list(props.sid) || []
  } finally { loading.value = false }
}
async function handleCreate(p) { await s360.projects.create(props.sid, p) }
async function handleUpdate(id, p) { await s360.projects.update(props.sid, id, p) }
async function handleDelete(id) { await s360.projects.remove(props.sid, id) }

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
