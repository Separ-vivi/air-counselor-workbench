<template>
  <div class="class-psychology">
    <el-row :gutter="16" v-if="loading" style="margin-bottom: 16px">
      <el-col :span="24"><el-skeleton :rows="3" animated /></el-col>
    </el-row>

    <template v-else>
      <div class="psy-stat-row">
        <el-card shadow="hover" class="stat-card psy-stat-cell" v-for="stat in statCards" :key="stat.label">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
        </el-card>
      </div>

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
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span>心理记录（共 {{ records.length }} 条）</span>
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button label="table">明细表格</el-radio-button>
              <el-radio-button label="timeline">时间轴</el-radio-button>
            </el-radio-group>
          </div>
        </template>
        <!-- v3j-D · D1: 明细表格视图 -->
        <el-table v-if="viewMode === 'table'" :data="records" stripe border max-height="500">
          <el-table-column label="学生" prop="student_name" width="120" sortable />
          <el-table-column label="学号" prop="student_no" width="140" sortable />
          <el-table-column label="关注等级" width="110">
            <template #default="{ row }">
              <el-tag :style="levelTagStyle(row.attention_level)" size="small">
                {{ row.attention_level || '-' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="测评时间" prop="assessment_date" width="130" sortable />
          <el-table-column label="咨询次数" prop="counseling_count" width="100" align="center" sortable />
          <el-table-column label="备注" prop="notes" show-overflow-tooltip sortable />
        </el-table>
        <!-- v3j-D · D1: 时间轴视图 -->
        <div v-else class="psy-timeline-wrap">
          <el-empty v-if="!timelineRecords.length" description="暂无心理记录" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="item in timelineRecords"
              :key="item.id"
              :timestamp="item.assessment_date || '未填写日期'"
              :color="timelineDotColor(item.attention_level)"
              placement="top"
            >
              <div class="psy-timeline-card">
                <div class="psy-timeline-head">
                  <span class="psy-stu">{{ item.student_name }}</span>
                  <span class="psy-no">{{ item.student_no }}</span>
                  <el-tag :style="levelTagStyle(item.attention_level)" size="small">
                    {{ item.attention_level || '-' }}
                  </el-tag>
                  <span v-if="item.counseling_count" class="psy-meta">咨询 {{ item.counseling_count }} 次</span>
                  <span v-if="item.location" class="psy-meta">📍 {{ item.location }}</span>
                </div>
                <div v-if="item.topic" class="psy-topic"><strong>主题：</strong>{{ item.topic }}</div>
                <div v-if="item.summary" class="psy-summary">{{ item.summary }}</div>
                <div v-if="item.next_follow_date" class="psy-meta psy-follow">
                  🕒 下次跟进：{{ item.next_follow_date }}
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
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
  { label: '三级关注', value: 0, color: '#67C23A' },
  { label: '普通关注', value: 0, color: '#909399' }
])

// v3j-C c02-hotfix2 · 心理关注 tag 底色对齐饼图马卡龙
// v3j-D · D1: 视图切换（表格 / 时间轴）
const viewMode = ref('table')
const timelineRecords = computed(() => {
  return [...records.value].sort((a, b) => {
    const da = a.assessment_date || ''
    const db = b.assessment_date || ''
    return db.localeCompare(da)
  })
})
const timelineDotColor = (l) => {
  const s = String(l || '')
  if (s.includes('一')) return '#FF9AA2'
  if (s.includes('二')) return '#FFDAC1'
  if (s.includes('三')) return '#B5EAD7'
  if (s.includes('普通')) return '#C7CEEA'
  return '#DCDFE6'  // 无档案 → 灰
}

const levelTagStyle = (l) => {
  if (!l) return { background: '#F0F2F5', color: '#909399', border: 'none' }  // 无档案 → 灰
  if (l.includes('一')) return { background: '#FF9AA2', color: '#7A2E36', border: 'none', fontWeight: 600 }
  if (l.includes('二')) return { background: '#FFDAC1', color: '#8A4E1F', border: 'none', fontWeight: 600 }
  if (l.includes('三')) return { background: '#B5EAD7', color: '#1F5A46', border: 'none', fontWeight: 600 }
  if (l.includes('普通')) return { background: '#C7CEEA', color: '#3B4B7A', border: 'none', fontWeight: 600 }  // 普通 → 紫
  return { background: '#F0F2F5', color: '#909399', border: 'none' }  // 兜底 → 灰
}
const levelTag = () => ''  

const fetchData = async () => {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    const res = await getClassPsychology(props.cid)
    records.value = Array.isArray(res) ? res : (res?.records || [])
    computeStats()
  } finally {
    // 关键：renderChart 必须在 loading=false 之后
    // 否则 v-else 里的 chartRef 还没挂载, renderChart 里 chartRef.value=null 直接 return, 饼图永远画不出来
    loading.value = false
    await nextTick()
    renderChart()
  }
}

const computeStats = () => {
  const total = records.value.length
  const cnt = { '一级': 0, '二级': 0, '三级': 0, '普通': 0 }
  records.value.forEach((r) => {
    const lv = r.attention_level || ''
    if (lv.includes('一')) cnt['一级']++
    else if (lv.includes('二')) cnt['二级']++
    else if (lv.includes('三')) cnt['三级']++
    else if (lv.includes('普通')) cnt['普通']++
  })
  statCards.value[0].value = total
  statCards.value[1].value = cnt['一级']
  statCards.value[2].value = cnt['二级']
  statCards.value[3].value = cnt['三级']
  statCards.value[4].value = cnt['普通']
}

const renderChart = () => {
  if (!chartRef.value) return
  // 切班级时 chartRef 会重新挂载, 老的 chartIns 绑的 DOM 已经不在了, 必须 dispose 重建
  if (chartIns && chartIns.getDom() !== chartRef.value) {
    chartIns.dispose()
    chartIns = null
  }
  if (!chartIns) chartIns = echarts.init(chartRef.value)
  const data = [
    // v3j-D · 心理关注饼图：4 档马卡龙 + 灰色无档案
    { name: '一级重点关注', value: statCards.value[1].value, itemStyle: { color: '#FF9AA2' } },
    { name: '二级关注', value: statCards.value[2].value, itemStyle: { color: '#FFDAC1' } },
    { name: '三级关注', value: statCards.value[3].value, itemStyle: { color: '#B5EAD7' } },
    { name: '普通关注', value: statCards.value[4].value, itemStyle: { color: '#C7CEEA' } },
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
.psy-timeline-wrap {
  padding: 12px 8px;
  max-height: 560px;
  overflow-y: auto;
}
.psy-timeline-card {
  background: #FAFBFC;
  border: 1px solid #EBEEF5;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 4px;
}
.psy-timeline-head {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.psy-stu {
  font-weight: 600;
  color: #303133;
}
.psy-no {
  color: #909399;
  font-size: 12px;
}
.psy-meta {
  color: #909399;
  font-size: 12px;
}
.psy-topic {
  color: #606266;
  font-size: 13px;
  margin-bottom: 4px;
}
.psy-summary {
  color: #303133;
  font-size: 13px;
  line-height: 1.6;
  background: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  margin-top: 4px;
}
.psy-follow {
  margin-top: 6px;
  color: #E6A23C;
}


.psy-stat-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.psy-stat-cell {
  flex: 1 1 0;
  min-width: 130px;
}
</style>
