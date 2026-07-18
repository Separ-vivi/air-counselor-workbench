<template>
  <CrudPanel
    title="学生工作 / 干部任职"
    :columns="columns"
    :fields="fields"
    :rows="rows"
    :loading="loading"
    :rules="rules"
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
  { prop: 'position', label: '职务', minWidth: 140 },
  { prop: 'term', label: '任期', minWidth: 140 },
  { prop: 'notes', label: '备注', minWidth: 200 }
]
const fields = [
  {
    prop: 'position', label: '职务',
    placeholder: '例：班长 / 团支书 / 学生会主席 / 社团社长'
  },
  { prop: 'term', label: '任期', placeholder: '例：2025.09 - 2026.06' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]
const rules = { position: [{ required: true, message: '职务必填', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try {
    rows.value = await s360.cadres.list(props.sid) || []
  } finally { loading.value = false }
}
async function handleCreate(p) { await s360.cadres.create(props.sid, p) }
async function handleUpdate(id, p) { await s360.cadres.update(props.sid, id, p) }
async function handleDelete(id) { await s360.cadres.remove(props.sid, id) }

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>
