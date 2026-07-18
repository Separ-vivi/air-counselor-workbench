<template>
  <div>
    <div class="tip macaron-card" style="padding:12px 16px;">
      <el-icon><InfoFilled /></el-icon>&nbsp;
      本表关联的是"活动报名/参与"关系记录。若要新建活动本身，请去 <router-link to="/module/activities">活动管理</router-link>。
    </div>
    <CrudPanel
      title="活动参与"
      :columns="columns"
      :fields="fields"
      :rows="rows"
      :loading="loading"
      :rules="rules"
      :on-reload="load"
      :on-create="handleCreate"
      :on-delete="handleDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import CrudPanel from '@/components/CrudPanel.vue'
import { s360 } from '@/api/student360.js'
import * as activitiesApi from '@/api/modules.js'

const props = defineProps({ sid: { type: Number, required: true } })
const rows = ref([])
const activities = ref([])
const loading = ref(false)

function statusOf(row) {
  if (row.checked_in) return '已签到'
  if (row.signed_up) return '已报名'
  return '未报名'
}

const columns = [
  { prop: 'activity_title', label: '活动名称', minWidth: 180,
    formatter: (v, row) => v || row.activity_name || row.title || '—' },
  { prop: 'activity_type', label: '类型', width: 110 },
  { prop: 'activity_date', label: '活动日期', width: 120 },
  { prop: 'location', label: '地点', minWidth: 120 },
  { prop: 'status', label: '参与状态', width: 100, formatter: (_v, row) => statusOf(row) },
  { prop: 'points', label: '积分', width: 80 }
]
const fields = [
  {
    prop: 'activity_id', label: '关联活动', type: 'select', options: []
  }
]
const rules = { activity_id: [{ required: true, message: '请选择活动', trigger: 'change' }] }

async function loadActivities() {
  try {
    const data = await activitiesApi.activities.list()
    activities.value = data?.items || data || []
    fields[0].options = activities.value.map(a => ({
      value: a.id,
      label: `${a.title || a.name || '活动 #' + a.id}${a.start_date ? ' · ' + a.start_date : ''}`
    }))
  } catch { activities.value = [] }
}

async function load() {
  loading.value = true
  try {
    rows.value = await s360.activities.list(props.sid) || []
  } finally { loading.value = false }
}
async function handleCreate(p) { await s360.activities.create(props.sid, p) }
async function handleDelete(id) { await s360.activities.remove(props.sid, id) }

watch(() => props.sid, load, { immediate: false })
onMounted(async () => { await loadActivities(); await load() })
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
