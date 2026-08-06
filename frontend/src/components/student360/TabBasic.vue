<template>
  <div>
    <!-- 基本信息卡（只读汇总 · 已在顶部卡片显示，此处补充详细字段） -->
    <div class="macaron-card">
      <h3>基础信息详细</h3>
      <el-descriptions :column="3" size="small" border>
        <el-descriptions-item label="学号">{{ student?.student_no || '—' }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ student?.name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ student?.gender || '—' }}</el-descriptions-item>
        <el-descriptions-item label="出生日期">{{ student?.birth_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="政治面貌">{{ student?.political_status || '—' }}</el-descriptions-item>
        <el-descriptions-item label="生源地">{{ student?.birth_source || '—' }}</el-descriptions-item>
        <el-descriptions-item label="所在班级">{{ student?.class_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="所在专业">{{ student?.major_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="所在年级">{{ student?.grade_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ student?.phone || '—' }}</el-descriptions-item>
        <el-descriptions-item label="家长电话">{{ student?.parent_phone || '—' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ student?.email || '—' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">{{ student?.notes || '—' }}</el-descriptions-item>
      </el-descriptions>
      <div class="tip">
        <el-icon><InfoFilled /></el-icon>&nbsp;基础字段编辑请点击顶部「编辑基础信息」按钮
      </div>
    </div>

    <!-- 学籍异动子分区 -->
    <div class="macaron-card">
      <CrudPanel
        title="学籍异动记录"
        :columns="columns"
        :fields="fields"
        :rows="rows"
        :loading="loading"
        :rules="rules"
        :default-form="{ change_type: '转专业' }"
        :on-reload="load"
        :on-create="handleCreate"
        :on-update="handleUpdate"
        :on-delete="handleDelete"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import CrudPanel from '@/components/CrudPanel.vue'
import { s360 } from '@/api/student360.js'

const props = defineProps({
  sid: { type: Number, required: true },
  student: { type: Object, default: null },
  summary: { type: Object, default: null }
})
const emit = defineEmits(['refresh-header'])

const rows = ref([])
const loading = ref(false)

const columns = [
  { prop: 'change_type', label: '异动类型', minWidth: 110 },
  { prop: 'start_date', label: '开始日期', width: 110 },
  { prop: 'end_date', label: '结束日期', width: 110 },
  { prop: 'original_info', label: '原情况', minWidth: 140 },
  { prop: 'target_info', label: '变更后', minWidth: 140 },
  { prop: 'reason', label: '原因', minWidth: 160 },
  { prop: 'notes', label: '备注', minWidth: 100 }
]
const fields = [
  {
    prop: 'change_type', label: '异动类型', type: 'select',
    options: ['转专业', '休学', '复学', '参军入伍', '退役复学', '转学出去', '退学']
  },
  { prop: 'start_date', label: '开始日期', type: 'date' },
  { prop: 'end_date',   label: '结束日期', type: 'date' },
  { prop: 'original_info', label: '原情况', placeholder: '例：软件工程 / 请假事由 …' },
  { prop: 'target_info',   label: '变更后', placeholder: '例：人工智能 / 复学班级 …' },
  { prop: 'reason', label: '原因', type: 'textarea' },
  { prop: 'attachment', label: '附件（URL）' },
  { prop: 'notes', label: '备注' }
]
const rules = { change_type: [{ required: true, message: '异动类型必填', trigger: 'change' }] }

async function load() {
  loading.value = true
  try {
    rows.value = await s360.statusChanges.list(props.sid) || []
  } finally { loading.value = false }
}
async function handleCreate(payload) { await s360.statusChanges.create(props.sid, payload) }
async function handleUpdate(id, payload) { await s360.statusChanges.update(props.sid, id, payload) }
async function handleDelete(id) { await s360.statusChanges.remove(props.sid, id) }

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
