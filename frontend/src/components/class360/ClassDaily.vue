<template>
  <div class="class-daily">
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

      <el-tabs v-model="activeSub" type="border-card">
        <el-tab-pane label="宿舍走访" name="dorm_visits">
          <el-table :data="raw.dorm_visits || []" stripe border max-height="500">
            <el-table-column label="学生" prop="student_name" width="120" />
            <el-table-column label="学号" prop="student_no" width="140" />
            <el-table-column label="走访日期" prop="visit_date" width="130" />
            <el-table-column label="宿舍号" prop="dorm_no" width="120" />
            <el-table-column label="走访情况" prop="situation" show-overflow-tooltip />
            <el-table-column label="备注" prop="notes" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="请假记录" name="leaves">
          <el-table :data="raw.leaves || []" stripe border max-height="500">
            <el-table-column label="学生" prop="student_name" width="120" />
            <el-table-column label="学号" prop="student_no" width="140" />
            <el-table-column label="请假类型" prop="leave_type" width="120" />
            <el-table-column label="开始时间" prop="start_date" width="130" />
            <el-table-column label="结束时间" prop="end_date" width="130" />
            <el-table-column label="事由" prop="reason" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="违纪记录" name="disciplines">
          <el-table :data="raw.disciplines || []" stripe border max-height="500">
            <el-table-column label="学生" prop="student_name" width="120" />
            <el-table-column label="学号" prop="student_no" width="140" />
            <el-table-column label="违纪类型" prop="discipline_type" width="140" />
            <el-table-column label="处分等级" prop="punishment_level" width="120">
              <template #default="{ row }">
                <el-tag size="small" :type="punishTag(row.punishment_level)">
                  {{ row.punishment_level || '-' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="日期" prop="incident_date" width="130" />
            <el-table-column label="描述" prop="description" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="宿舍谈心" name="dorm_chats">
          <el-table :data="raw.dorm_chats || []" stripe border max-height="500">
            <el-table-column label="学生" prop="student_name" width="120" />
            <el-table-column label="学号" prop="student_no" width="140" />
            <el-table-column label="谈心日期" prop="chat_date" width="130" />
            <el-table-column label="主题" prop="topic" width="150" />
            <el-table-column label="内容" prop="content" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="考勤异常" name="attendance">
          <el-table :data="raw.attendance || []" stripe border max-height="500">
            <el-table-column label="学生" prop="student_name" width="120" />
            <el-table-column label="学号" prop="student_no" width="140" />
            <el-table-column label="异常类型" prop="exception_type" width="130" />
            <el-table-column label="课程" prop="course_name" width="180" show-overflow-tooltip />
            <el-table-column label="日期" prop="date" width="130" />
            <el-table-column label="备注" prop="notes" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getClassDaily } from '@/api/class360'

const props = defineProps({
  cid: { type: [String, Number], required: true }
})

const loading = ref(false)
const raw = ref({})
const activeSub = ref('dorm_visits')

const statCards = ref([
  { label: '宿舍走访', value: 0, color: '#409EFF' },
  { label: '请假记录', value: 0, color: '#67C23A' },
  { label: '违纪记录', value: 0, color: '#F56C6C' },
  { label: '考勤异常', value: 0, color: '#E6A23C' }
])

const punishTag = (l) => {
  if (!l) return ''
  if (l.includes('开除') || l.includes('留校')) return 'danger'
  if (l.includes('记过')) return 'warning'
  if (l.includes('警告')) return 'info'
  return ''
}

const fetchData = async () => {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    const res = await getClassDaily(props.cid)
    raw.value = res || {}
    statCards.value[0].value = (raw.value.dorm_visits || []).length
    statCards.value[1].value = (raw.value.leaves || []).length
    statCards.value[2].value = (raw.value.disciplines || []).length
    statCards.value[3].value = (raw.value.attendance || []).length
  } finally {
    loading.value = false
  }
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
  font-size: 26px;
  font-weight: 600;
}
</style>
