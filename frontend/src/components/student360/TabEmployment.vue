<template>
  <CrudPanel
    title="💼 就业信息 / 求职进度"
    :columns="columns"
    :fields="fields"
    :rows="rows"
    :loading="loading"
    :default-form="{ status: '未启动' }"
    :on-reload="load"
    :on-create="handleCreate"
    :on-update="handleUpdate"
    :on-delete="handleDelete"
  />
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import CrudPanel from '@/components/CrudPanel.vue'
import { s360 } from '@/api/student360.js'

const props = defineProps({ sid: { type: Number, required: true } })
const rows = ref([])
const loading = ref(false)

const columns = [
  { prop: 'intention_type', label: '意向类型', width: 100 },
  { prop: 'target_industry', label: '意向行业', minWidth: 120 },
  { prop: 'target_position', label: '意向岗位', minWidth: 140 },
  { prop: 'internship_company', label: '实习/入职单位', minWidth: 160 },
  { prop: 'status', label: '状态', width: 100, type: 'tag',
    tagType: (r) =>
      r.status === '签约' ? 'success' :
      r.status === '意向' ? 'warning' :
      r.status === '求职中' ? 'primary' : '' },
  { prop: 'offer_date', label: 'Offer 日期', width: 110 },
  { prop: 'salary_range', label: '薪资范围', minWidth: 120 },
  { prop: 'notes', label: '备注', minWidth: 140 }
]
const fields = [
  {
    prop: 'intention_type', label: '意向类型', type: 'select',
    options: ['就业', '升学', '考研', '出国', '考公', '参军', '灵活就业', '待定']
  },
  { prop: 'target_industry', label: '意向行业' },
  { prop: 'target_position', label: '意向岗位' },
  { prop: 'internship_company', label: '实习单位' },
  {
    prop: 'status', label: '状态', type: 'select',
    options: ['未启动', '求职中', '意向', '签约', '入职', '违约']
  },
  { prop: 'offer_date', label: 'Offer 日期', type: 'date' },
  { prop: 'salary_range', label: '薪资范围', placeholder: '例：8k-12k' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

async function load() {
  loading.value = true
  try {
    rows.value = await s360.employment.list(props.sid) || []
  } finally { loading.value = false }
}
async function handleCreate(p) { await s360.employment.create(props.sid, p) }
async function handleUpdate(id, p) { await s360.employment.update(props.sid, id, p) }
async function handleDelete(id) { await s360.employment.remove(props.sid, id) }

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>
