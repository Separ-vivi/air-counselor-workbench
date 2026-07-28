<template>
  <div class="tab-summary">
    <div class="summary-header">
      <h3>🌟 特色活动概览</h3>
      <el-button type="primary" @click="$router.push('/module/activities')">
        查看详情 <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>
    <el-row :gutter="16">
      <el-col :span="8" v-for="(stat, idx) in stats" :key="stat.label">
        <div class="summary-card">
          <div class="stat-value" :style="{ color: colors[idx % colors.length] }">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </el-col>
    </el-row>
    <div v-if="loading" class="empty-text">加载中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import { getClassFeaturedActivities } from '@/api/class360.js'

const props = defineProps({ cid: { type: Number, required: true } })
const loading = ref(false)
const data = ref([])
const colors = ['#5B92E5', '#4FC3B8', '#8FA9E5']

const stats = computed(() => {
  const list = Array.isArray(data.value) ? data.value : []
  const total = list.length
  const latest = list.length ? (list[0].activity_name || list[0].title || list[0].name || '—') : '暂无'
  const latestDate = list.length ? (list[0].activity_date || list[0].date || '—') : ''
  return [
    { label: '特色活动数', value: total || '—' },
    { label: '最近活动', value: latest.length > 10 ? latest.slice(0, 10) + '...' : latest },
    { label: '最近日期', value: latestDate || '—' }
  ]
})

async function load() {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    const res = await getClassFeaturedActivities(props.cid)
    data.value = Array.isArray(res) ? res : (res?.items || [])
  } catch { data.value = [] }
  finally { loading.value = false }
}

watch(() => props.cid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>

.tab-summary { padding: 8px 0; }
.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(91,146,229,0.15);
}
.summary-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2C3E50;
}
.summary-card {
  background: rgba(91,146,229,0.04);
  border: 1px solid rgba(91,146,229,0.12);
  border-radius: 16px;
  padding: 20px 16px;
  text-align: center;
  transition: all 0.25s ease;
  margin-bottom: 12px;
}
.summary-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(91,146,229,0.12);
  border-color: rgba(91,146,229,0.25);
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #5B92E5;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #6B7B8D;
  margin-top: 6px;
}
.empty-text {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 20px 0;
}
</style>
