<template>
  <CrudPanel
    title="📊 学业成绩明细"
    :columns="columns"
    :fields="fields"
    :rows="rows"
    :loading="loading"
    :rules="rules"
    :default-form="{ semester: currentSemester, is_repair: false }"
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
  sid: { type: Number, required: true },
  student: { type: Object, default: null }
})

const rows = ref([])
const loading = ref(false)
const currentSemester = new Date().getMonth() >= 6
  ? `${new Date().getFullYear()}-秋`
  : `${new Date().getFullYear()}-春`

const columns = [
  { prop: 'semester', label: '学期', width: 100 },
  { prop: 'course_name', label: '课程', minWidth: 180 },
  { prop: 'score', label: '成绩', width: 80,
    formatter: (v) => (v == null ? '—' : Number(v).toFixed(1)) },
  { prop: 'gpa', label: '绩点', width: 80,
    formatter: (v) => (v == null ? '—' : Number(v).toFixed(2)) },
  { prop: 'credit', label: '学分', width: 80,
    formatter: (v) => (v == null ? '—' : Number(v).toFixed(1)) },
  { prop: 'is_repair', label: '是否重修', width: 90,
    formatter: (v) => (v ? '是' : '否') }
]
const fields = [
  { prop: 'semester', label: '学期', placeholder: '例：2025-秋' },
  { prop: 'course_name', label: '课程名称' },
  { prop: 'score', label: '成绩(0-100)', type: 'number', min: 0, max: 100, step: 0.5, precision: 1 },
  { prop: 'gpa', label: '绩点', type: 'number', min: 0, max: 5, step: 0.1, precision: 2 },
  { prop: 'credit', label: '学分', type: 'number', min: 0, max: 20, step: 0.5, precision: 1 },
  { prop: 'is_repair', label: '是否重修', type: 'switch' }
]
const rules = {
  semester: [{ required: true, message: '学期必填', trigger: 'blur' }],
  course_name: [{ required: true, message: '课程必填', trigger: 'blur' }]
}

async function load() {
  loading.value = true
  try {
    rows.value = await s360.grades.list(props.sid) || []
  } finally { loading.value = false }
}
async function handleCreate(p) { await s360.grades.create(props.sid, p) }
async function handleUpdate(id, p) { await s360.grades.update(props.sid, id, p) }
async function handleDelete(id) { await s360.grades.remove(props.sid, id) }

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>
