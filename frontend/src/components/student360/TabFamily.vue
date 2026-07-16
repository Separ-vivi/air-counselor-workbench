<template>
  <CrudPanel
    title="🏠 家庭联络记录"
    :columns="columns"
    :fields="fields"
    :rows="rows"
    :loading="loading"
    :default-form="{ contact_date: today }"
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
const today = new Date().toISOString().slice(0, 10)

const columns = [
  { prop: 'contact_date', label: '联系日期', width: 120 },
  { prop: 'parent_name', label: '家长姓名', minWidth: 120 },
  { prop: 'contact_method', label: '方式', width: 100 },
  { prop: 'topic', label: '话题', minWidth: 140 },
  { prop: 'conclusion', label: '结论/沟通要点', minWidth: 200 },
  { prop: 'attachment', label: '附件', minWidth: 120 }
]
const fields = [
  { prop: 'contact_date', label: '联系日期', type: 'date' },
  { prop: 'parent_name', label: '家长姓名' },
  {
    prop: 'contact_method', label: '联系方式', type: 'select',
    options: ['电话', '微信', '短信', '面谈', '家访', '视频']
  },
  { prop: 'topic', label: '沟通话题', placeholder: '例：学业情况、心理状态' },
  { prop: 'conclusion', label: '沟通结论', type: 'textarea' },
  { prop: 'attachment', label: '附件（URL）' }
]

async function load() {
  loading.value = true
  try {
    rows.value = await s360.family.list(props.sid) || []
  } finally { loading.value = false }
}
async function handleCreate(p) { await s360.family.create(props.sid, p) }
async function handleUpdate(id, p) { await s360.family.update(props.sid, id, p) }
async function handleDelete(id) { await s360.family.remove(props.sid, id) }

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>
