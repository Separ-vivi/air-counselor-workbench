<template>
  <div>
    <div class="panel-head">
      <div><span class="title">🎨 特色活动</span><span class="count text-muted"> · 共 {{ rows.length }} 个</span></div>
      <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" stripe border size="small" max-height="560">
      <el-table-column type="index" width="55" label="#" />
      <el-table-column prop="title" label="活动名称" min-width="200" show-overflow-tooltip sortable />
      <el-table-column prop="activity_type" label="类型" width="120" sortable>
        <template #default="{ row }">
          <el-tag v-if="row.activity_type" size="small" effect="plain">{{ row.activity_type }}</el-tag>
          <span v-else class="text-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="activity_date" label="开始" width="120" sortable />
      <el-table-column prop="end_date" label="结束" width="120" sortable />
      <el-table-column prop="location" label="地点" min-width="140" show-overflow-tooltip sortable />
      <el-table-column prop="status" label="状态" width="100" sortable>
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="signup_count" label="本班参与" width="110" align="center" sortable>
        <template #default="{ row }">
          <b :style="{color:'#4A7A8C'}">{{ row.signup_count }}</b> 人
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && !rows.length" description="本班暂无参与的活动记录" :image-size="80" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getClassFeaturedActivities } from '@/api/class360.js'

const props = defineProps({ cid: { type: Number, required: true } })
const rows = ref([])
const loading = ref(false)

function statusLabel(s) {
  return { draft: '草稿', ongoing: '进行中', done: '已结束', completed: '已结束', cancelled: '已取消' }[s] || (s || '—')
}
function statusType(s) {
  return { draft: 'info', ongoing: 'primary', done: 'success', completed: 'success', cancelled: 'danger' }[s] || 'info'
}

async function load() {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    rows.value = (await getClassFeaturedActivities(props.cid)) || []
  } catch (e) { rows.value = [] } finally { loading.value = false }
}

watch(() => props.cid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.panel-head { display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px; }
.panel-head .title { font-weight: 600; color: #4A7A8C; font-size: 15px; }
.text-muted { color: #909399; font-size: 12px; }
</style>
