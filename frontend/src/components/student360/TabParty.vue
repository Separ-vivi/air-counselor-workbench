<template>
  <CrudPanel
    title="🎯 党团发展进程"
    :columns="columns"
    :fields="fields"
    :rows="rows"
    :loading="loading"
    :rules="rules"
    :default-form="{ stage: '入党申请人' }"
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

const props = defineProps({
  sid: { type: Number, required: true }
})

const rows = ref([])
const loading = ref(false)

const stageOptions = [
  '入党申请人', '积极分子', '发展对象', '中共预备党员', '中共党员'
]
const columns = [
  { prop: 'stage', label: '发展阶段', width: 120, type: 'tag',
    tagType: (r) =>
      r.stage === '中共党员' ? 'success'
      : r.stage === '中共预备党员' ? 'warning'
      : r.stage === '发展对象' ? 'primary' : '' },
  { prop: 'stage_date', label: '阶段日期', width: 120 },
  { prop: 'contact_person', label: '培养联系人', minWidth: 120 },
  { prop: 'notes', label: '备注', minWidth: 200 }
]
const fields = [
  { prop: 'stage', label: '发展阶段', type: 'select', options: stageOptions },
  { prop: 'stage_date', label: '阶段日期', type: 'date' },
  { prop: 'contact_person', label: '培养联系人' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]
const rules = { stage: [{ required: true, message: '发展阶段必填', trigger: 'change' }] }

async function load() {
  loading.value = true
  try {
    rows.value = await s360.party.list(props.sid) || []
  } finally { loading.value = false }
}
async function handleCreate(p) { await s360.party.create(props.sid, p) }
async function handleUpdate(id, p) { await s360.party.update(props.sid, id, p) }
async function handleDelete(id) { await s360.party.remove(props.sid, id) }

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>
