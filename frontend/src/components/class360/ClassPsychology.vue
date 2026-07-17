<template>
  <div class="class-psychology">
    <el-row :gutter="16" v-if="loading" style="margin-bottom: 16px">
      <el-col :span="24"><el-skeleton :rows="3" animated /></el-col>
    </el-row>

    <template v-else>
      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :span="6" v-for="stat in statCards" :key="stat.label">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" style="margin-bottom: 16px">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span>心理关注等级分布</span>
            <span style="font-size: 12px; color: #909399">本班学生总数：{{ totalStudentCount }}</span>
          </div>
        </template>
        <div ref="chartRef" style="width: 100%; height: 260px"></div>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <span>心理记录明细（共 {{ records.length }} 条）</span>
        </template>
        <el-table :data="records" stripe border max-height="500">
          <el-table-column label="学生" prop="student_name" width="120" />
          <el-table-column label="学号" prop="student_no" width="140" />
          <el-table-column label="关注等级" width="110">
            <template #default="{ row }">
              <el-tag :type="levelTag(row.attention_level)" size="small">
                {{ row.attention_level || '-' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="测评时间" prop="assessment_date" width="130" />
          <el-table-column label="咨询次数" prop="counseling_count" width="100" align="center" />
          <el-table-column label="备注" prop="notes" show-overflow-tooltip />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { getClassPsychology } from '@/api/class360'

const props = defineProps({
  cid: { type: [String, Number], required: true },
  classStudentCount: { type: Number, default: 0 }  // 本班学生总数（父组件传入）
})

const loading = ref(false)
const records = ref([])
const chartRef = ref(null)
let chartIns = null

// 本班学生总数：优先用父组件传入的 classStudentCount，fallback 到记录数
const totalStudentCount = computed(() => {
  if (props.classStudentCount && props.classStudentCount > 0) return props.classStudentCount
  return records.value.length
})

const statCards = ref([
  { label: '心理档案总数', value: 0, color: '#409EFF' },
  { label: '一级重点关注', value: 0, color: '#F56C6C' },
  { label: '二级关注', value: 0, color: '#E6A23C' },
  { label: '三级关注', value: 0, color: '#909399' }
])

const levelTag = (l) => {
  if (l && l.includes('一')) return 'danger'
  if (l && l.includes('二')) return 'warning'
  if (l && l.includes('三')) return 'info'
  return ''
}

const fetchData = async () => {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    const res = await getClassPsychology(props.cid)
    records.value = Array.isArray(res) ? res : (res?.records || [])
    computeStats()
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

const computeStats = () => {
  const total = records.value.length
  const cnt = { '一级': 0, '二级': 0, '三级': 0 }
  records.value.forEach((r) => {
    const lv = r.attention_level || ''
    if (lv.includes('一')) cnt['一级']++
    else if (lv.includes('二')) cnt['二级']++
    else if (lv.includes('三')) cnt['三级']++
  })
  statCards.value[0].value = total
  statCards.value[1].value = cnt['一级']
  statCards.value[2].value = cnt['二级']
  statCards.value[3].value = cnt['三级']
}

const renderChart = () => {
  if (!chartRef.value) return
  if (!chartIns) chartIns = echarts.init(chartRef.value)
  const data = [
    { name: '一级重点关注', value: statCards.value[1].value, itemStyle: { color: '#F56C6C' } },
    { name: '二级关注', value: statCards.value[2].value, itemStyle: { color: '#E6A23C' } },
    { name: '三级关注', value: statCards.value[3].value, itemStyle: { color: '#909399' } },
    { name: '无档案', value: Math.max(0, totalStudentCount.value - records.value.length), itemStyle: { color: '#DCDFE6' } }
  ]
  chartIns.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { fontSize: 12 } },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        data,
        label: { formatter: '{b}: {c} ({d}%)' }
      }
    ]
  })
}

watch(() => props.cid, fetchData)
watch(() => props.classStudentCount, () => {
  // 学生总数变化时，重画饼图（不重新拉数据）
  if (records.value.length || props.classStudentCount) renderChart()
})
onMounted(fetchData)
</script>

<style scoped>
.stat-card {
  border-radius: 12px;
  text-align: center;
}
.stat-label {
  color: #909399;
  font-size: 13px;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 26px;
  font-weight: 600;
}
</style>
