<template>
  <div class="class-funding">
    <el-row :gutter="16" v-if="loading">
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
        <template #header><span>困难认定等级分布</span></template>
        <div ref="hardshipChart" style="width: 100%; height: 260px"></div>
      </el-card>

      <el-tabs v-model="activeSub" type="border-card">
        <el-tab-pane label="困难认定" name="hardship">
          <el-table :data="raw.hardship || []" stripe border max-height="450">
            <el-table-column label="学生" prop="student_name" width="120" sortable />
            <el-table-column label="学号" prop="student_no" width="140" sortable />
            <el-table-column label="困难等级" prop="hardship_level" width="130" sortable>
              <template #default="{ row }">
                <el-tag :style="hardshipTagStyle(row.hardship_level)" size="small">
                  {{ row.hardship_level || '-' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="认定学年" prop="school_year" width="130" sortable />
            <el-table-column label="家庭情况" prop="family_situation" show-overflow-tooltip sortable />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="国家助学金" name="grants">
          <el-table :data="raw.grants || []" stripe border max-height="450">
            <el-table-column label="学生" prop="student_name" width="120" sortable />
            <el-table-column label="学号" prop="student_no" width="140" sortable />
            <el-table-column label="等级" prop="grant_level" width="110" sortable />
            <el-table-column label="金额" prop="amount" width="120" sortable>
              <template #default="{ row }">¥{{ row.amount || 0 }}</template>
            </el-table-column>
            <el-table-column label="学年" prop="school_year" width="130" sortable />
            <el-table-column label="备注" prop="notes" show-overflow-tooltip sortable />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="奖学金" name="scholarships">
          <el-table :data="raw.scholarships || []" stripe border max-height="450">
            <el-table-column label="学生" prop="student_name" width="120" sortable />
            <el-table-column label="学号" prop="student_no" width="140" sortable />
            <el-table-column label="奖学金" prop="scholarship_name" width="180" sortable />
            <el-table-column label="等级" prop="level" width="100" sortable />
            <el-table-column label="金额" prop="amount" width="120" sortable>
              <template #default="{ row }">¥{{ row.amount || 0 }}</template>
            </el-table-column>
            <el-table-column label="学年" prop="school_year" width="130" sortable />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="助学贷款" name="loans">
          <el-table :data="raw.loans || []" stripe border max-height="450">
            <el-table-column label="学生" prop="student_name" width="120" sortable />
            <el-table-column label="学号" prop="student_no" width="140" sortable />
            <el-table-column label="贷款类型" prop="loan_type" width="130" sortable />
            <el-table-column label="金额" prop="amount" width="120" sortable>
              <template #default="{ row }">¥{{ row.amount || 0 }}</template>
            </el-table-column>
            <el-table-column label="状态" prop="status" width="120" sortable />
            <el-table-column label="学年" prop="school_year" sortable />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="勤工助学" name="work_study">
          <el-table :data="raw.work_study || []" stripe border max-height="450">
            <el-table-column label="学生" prop="student_name" width="120" sortable />
            <el-table-column label="学号" prop="student_no" width="140" sortable />
            <el-table-column label="岗位" prop="position" width="150" sortable />
            <el-table-column label="工作时长(h)" prop="hours" width="120" sortable />
            <el-table-column label="薪资" prop="salary" width="120" sortable>
              <template #default="{ row }">¥{{ row.salary || 0 }}</template>
            </el-table-column>
            <el-table-column label="学年" prop="school_year" sortable />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { getClassFunding } from '@/api/class360'

const props = defineProps({
  cid: { type: [String, Number], required: true }
})

const loading = ref(false)
const raw = ref({})
const activeSub = ref('hardship')
const hardshipChart = ref(null)
let chartIns = null

const statCards = ref([
  { label: '困难认定人数', value: 0, color: '#F56C6C' },
  { label: '获国家助学金', value: 0, color: '#E6A23C' },
  { label: '获奖学金人次', value: 0, color: '#67C23A' },
  { label: '资助总金额', value: '¥0', color: '#409EFF' }
])

// v3j-C c02-hotfix2 · 困难 tag 底色对齐饼图马卡龙
const hardshipTagStyle = (l) => {
  if (!l) return { background: '#F5F7FA', color: '#909399', border: 'none' }
  if (l.includes('特别')) return { background: '#FF9AA2', color: '#7A2E36', border: 'none', fontWeight: 600 }
  if (l.includes('一般')) return { background: '#B5EAD7', color: '#1F5A46', border: 'none', fontWeight: 600 }
  return { background: '#FFDAC1', color: '#8A4E1F', border: 'none', fontWeight: 600 }  // 困难
}
// 兼容旧引用
const hardshipTag = () => ''  

const fetchData = async () => {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    const res = await getClassFunding(props.cid)
    // 兼容 {hardship,grants,scholarships,loans,work_study} 或 array
    raw.value = Array.isArray(res) ? { hardship: res } : (res || {})
    computeStats()
  } finally {
    loading.value = false
  }
  // v3j-C c01-hotfix1: renderChart 必须在 loading=false 之后调用，
  // 否则 v-else 分支还未渲染 hardshipChart ref 是 null，饼图不出现
  await nextTick()
  renderChart()
}

const computeStats = () => {
  const { hardship = [], grants = [], scholarships = [], loans = [], work_study = [] } = raw.value
  const totalMoney =
    (grants.reduce((s, r) => s + (Number(r.amount) || 0), 0) || 0) +
    (scholarships.reduce((s, r) => s + (Number(r.amount) || 0), 0) || 0) +
    (work_study.reduce((s, r) => s + (Number(r.salary) || 0), 0) || 0)
  statCards.value[0].value = hardship.length
  statCards.value[1].value = grants.length
  statCards.value[2].value = scholarships.length
  statCards.value[3].value = '¥' + totalMoney.toLocaleString()
}

const renderChart = () => {
  if (!hardshipChart.value) return
  if (!chartIns) chartIns = echarts.init(hardshipChart.value)
  const hs = raw.value.hardship || []
  // v3j-C c01 · 修 bug：seed 实际值为「特别困难/困难/一般困难」，此处 3 档匹配
  const cnt = { 特别困难: 0, 困难: 0, 一般困难: 0 }
  hs.forEach((r) => {
    const lv = r.hardship_level || ''
    if (lv.includes('特别')) cnt['特别困难']++
    else if (lv.includes('一般')) cnt['一般困难']++
    else if (lv.includes('困难')) cnt['困难']++
  })
  chartIns.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        data: [
          { name: '特别困难', value: cnt['特别困难'], itemStyle: { color: '#FF9AA2' } },
          { name: '困难', value: cnt['困难'], itemStyle: { color: '#FFDAC1' } },
          { name: '一般困难', value: cnt['一般困难'], itemStyle: { color: '#B5EAD7' } }
        ]
      }
    ]
  })
}

watch(() => props.cid, fetchData)
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
  font-size: 24px;
  font-weight: 600;
}
</style>
