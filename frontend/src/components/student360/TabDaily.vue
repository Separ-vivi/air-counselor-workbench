<template>
  <div class="tab-summary">
    <div class="summary-header">
      <h3>🏨 日常管理概览</h3>
      <el-button type="primary" @click="$router.push('/module/attendance')">
        查看详情 <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>
    <el-row :gutter="16">
      <el-col :span="6" v-for="(stat, idx) in stats" :key="stat.label">
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
const leaves = ref([])
const disciplines = ref([])
const attendance = ref([])
const dormVisits = ref([])
const colors = ['#5B92E5', '#4FC3B8', '#8FA9E5', '#7BCFCB']

const stats = computed(() => {
  const leaveCount = leaves.value.length
  const disciplineCount = disciplines.value.length
  const attendanceCount = attendance.value.length
  const visitCount = dormVisits.value.length
  return [
    { label: '请假次数', value: leaveCount || '—' },
    { label: '违纪次数', value: disciplineCount || '—' },
    { label: '考勤异常', value: attendanceCount || '—' },
    { label: '宿舍走访', value: visitCount || '—' }
  ]
})

async function load() {
  loading.value = true
  try {
    const [l, d, a, dv] = await Promise.all([
      s360.leaves.list(props.sid).catch(() => []),
      s360.disciplines.list(props.sid).catch(() => []),
      s360.attendance.list(props.sid).catch(() => []),
      s360.dormVisits.list(props.sid).catch(() => [])
    ])
    leaves.value = l || []
    disciplines.value = d || []
    attendance.value = a || []
    dormVisits.value = dv || []
  } finally { loading.value = false }
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
