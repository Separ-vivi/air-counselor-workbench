<template>
  <div>
    <div class="panel-head">
      <div><span class="title">🎯 本班党团进度</span></div>
      <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
    </div>

    <!-- 6 阶段人数分布 -->
    <el-row :gutter="12" class="mb-16">
      <el-col v-for="s in stages" :key="s.key" :span="4">
        <div class="stage-card">
          <div class="stage-label">{{ s.label }}</div>
          <div class="stage-value">{{ stageCounts[s.key] || 0 }}</div>
          <div class="stage-hint">人</div>
        </div>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="rows" border stripe size="small" height="440" empty-text="暂无本班党团数据">
      <el-table-column prop="student_no" label="学号" width="130" />
      <el-table-column prop="name" label="姓名" width="100">
        <template #default="{ row }">
          <router-link v-if="row.student_id" :to="`/students/${row.student_id}`" class="link">{{ row.name }}</router-link>
          <span v-else>{{ row.name || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="stage" label="当前阶段" width="140">
        <template #default="{ row }">
          <el-tag :type="stageTag(row.stage)" size="small">{{ row.stage || '—' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="join_date" label="阶段日期" width="140" />
      <el-table-column prop="notes" label="备注" min-width="180" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getClassParty } from '@/api/class360.js'

const props = defineProps({ cid: { type: Number, required: true } })
const rows = ref([])
const loading = ref(false)

const stages = [
  { key: '群众',       label: '群众' },
  { key: '入党申请人', label: '申请人' },
  { key: '积极分子',   label: '积极分子' },
  { key: '发展对象',   label: '发展对象' },
  { key: '预备党员',   label: '预备党员' },
  { key: '正式党员',   label: '正式党员' }
]
const stageCounts = computed(() => {
  const map = {}
  rows.value.forEach(r => {
    const s = r.stage || '群众'
    map[s] = (map[s] || 0) + 1
  })
  return map
})
function stageTag(s) {
  if (s === '正式党员') return 'success'
  if (s === '预备党员') return 'warning'
  if (s === '发展对象') return 'primary'
  if (s === '积极分子') return 'info'
  return ''
}

async function load() {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    rows.value = await getClassParty(props.cid) || []
  } finally { loading.value = false }
}
watch(() => props.cid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.panel-head { display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px; }
.panel-head .title { font-weight: 600; color: var(--color-sidebar-active); font-size: 15px; }
.stage-card {
  background: var(--color-macaron-blue);
  border-radius: 12px;
  padding: 12px 8px;
  text-align: center;
}
.stage-label { color: var(--color-sidebar-active); font-size: 12px; }
.stage-value { font-size: 22px; font-weight: 700; color: var(--color-sidebar-active); }
.stage-hint { color: var(--color-text-secondary); font-size: 11px; }
.link { color: var(--color-sidebar); }
</style>
