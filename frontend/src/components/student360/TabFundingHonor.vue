<template>
  <div class="tab-summary">
    <div class="summary-header">
      <h3>💰 资助与荣誉概览</h3>
      <el-button type="primary" @click="$router.push('/module/financial-aid')">
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
const hardship = ref([])
const scholarships = ref([])
const honors = ref([])
const grants = ref([])
const colors = ['#5B92E5', '#4FC3B8', '#8FA9E5', '#7BCFCB']

const stats = computed(() => {
  const honorCount = honors.value.length
  const hardshipCount = hardship.value.length
  const grantCount = grants.value.length
  const totalAmount = [
    ...scholarships.value.map(r => Number(r.amount) || 0),
    ...grants.value.map(r => Number(r.amount) || 0)
  ].reduce((a, b) => a + b, 0)
  return [
    { label: '获奖数', value: honorCount || '—' },
    { label: '资助记录', value: (hardshipCount + grantCount) || '—' },
    { label: '奖学金', value: scholarships.value.length || '—' },
    { label: '总金额', value: totalAmount ? '¥' + totalAmount.toLocaleString() : '—' }
  ]
})

async function load() {
  loading.value = true
  try {
    const [h, s, ho, g] = await Promise.all([
      s360.hardship.list(props.sid).catch(() => []),
      s360.scholarships.list(props.sid).catch(() => []),
      s360.honors.list(props.sid).catch(() => []),
      s360.grants.list(props.sid).catch(() => [])
    ])
    hardship.value = h || []
    scholarships.value = s || []
    honors.value = ho || []
    grants.value = g || []
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
