<template>
  <CrudPanel
    title="💚 心理谈心记录"
    :columns="columns"
    :fields="fields"
    :rows="rows"
    :loading="loading"
    :default-form="{ record_date: today }"
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
  { prop: 'record_date', label: '谈心日期', width: 120 },
  { prop: 'location', label: '地点', minWidth: 120 },
  { prop: 'topic', label: '话题', minWidth: 140 },
  { prop: 'emotion_tags', label: '情绪标签', minWidth: 120 },
  { prop: 'summary', label: '要点', minWidth: 200 },
  { prop: 'follow_up_plan', label: '跟进计划', minWidth: 160 },
  { prop: 'next_follow_date', label: '下次跟进', width: 120 }
]
const fields = [
  { prop: 'record_date', label: '谈心日期', type: 'date' },
  { prop: 'location', label: '地点', placeholder: '例：辅导员办公室 / 宿舍' },
  { prop: 'topic', label: '话题', placeholder: '例：学业焦虑、家庭矛盾' },
  { prop: 'emotion_tags', label: '情绪标签', placeholder: '例：焦虑,失眠,自我怀疑' },
  { prop: 'summary', label: '主要内容', type: 'textarea' },
  { prop: 'follow_up_plan', label: '跟进计划', type: 'textarea' },
  { prop: 'next_follow_date', label: '下次跟进', type: 'date' }
]

async function load() {
  loading.value = true
  try {
    rows.value = await s360.psychology.list(props.sid) || []
  } finally { loading.value = false }
}
async function handleCreate(p) { await s360.psychology.create(props.sid, p) }
async function handleUpdate(id, p) { await s360.psychology.update(props.sid, id, p) }
async function handleDelete(id) { await s360.psychology.remove(props.sid, id) }

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>
