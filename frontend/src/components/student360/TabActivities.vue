<template>
  <div class="tab-summary">
    <div class="summary-header">
      <h3>🎨 活动参与概览</h3>
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
import { s360 } from '@/api/student360.js'

const props = defineProps({ sid: { type: Number, required: true } })
const loading = ref(false)
const rows = ref([])
const colors = ['#5B92E5', '#4FC3B8', '#8FA9E5']

const stats = computed(() => {
  const list = rows.value || []
  if (!list.length) return [
    { label: '参与活动数', value: '—' },
    { label: '总积分', value: '—' },
    { label: '最近活动', value: '—' }
  ]
  const total = list.length
  const totalPoints = list.reduce((s, r) => s + (Number(r.points) || 0), 0)
  const latest = list[0]?.activity_title || list[0]?.activity_name || list[0]?.title || '—'
  return [
    { label: '参与活动数', value: total },
    { label: '总积分', value: totalPoints || '—' },
    { label: '最近活动', value: latest.length > 10 ? latest.slice(0, 10) + '...' : latest }
  ]
})

async function load() {
  loading.value = true
  try {
    rows.value = await s360.activities.list(props.sid) || []
  } catch { rows.value = [] }
  finally { loading.value = false }
}

watch(() => props.sid, load, { immediate: false })
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
