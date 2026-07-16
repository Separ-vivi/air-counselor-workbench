<template>
  <div class="class-activities">
    <el-row :gutter="16" v-if="loading">
      <el-col :span="24"><el-skeleton :rows="3" animated /></el-col>
    </el-row>

    <template v-else>
      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :span="8" v-for="stat in statCards" :key="stat.label">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span>活动参与明细（共 {{ list.length }} 条）</span>
            <el-input
              v-model="filterText"
              placeholder="搜索活动名 / 学生"
              clearable
              size="small"
              style="width: 260px"
              :prefix-icon="Search"
            />
          </div>
        </template>
        <el-table :data="filteredList" stripe border max-height="600">
          <el-table-column label="学生" prop="student_name" width="120" />
          <el-table-column label="学号" prop="student_no" width="140" />
          <el-table-column label="活动名称" prop="activity_name" min-width="180" show-overflow-tooltip />
          <el-table-column label="活动类型" prop="activity_type" width="130">
            <template #default="{ row }">
              <el-tag size="small" :type="typeTag(row.activity_type)">
                {{ row.activity_type || '-' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="角色" prop="role" width="120" />
          <el-table-column label="活动日期" prop="activity_date" width="130" />
          <el-table-column label="备注" prop="notes" show-overflow-tooltip />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getClassActivities } from '@/api/class360'

const props = defineProps({
  classId: { type: [String, Number], required: true }
})

const loading = ref(false)
const list = ref([])
const filterText = ref('')

const statCards = ref([
  { label: '活动总参与人次', value: 0, color: '#409EFF' },
  { label: '涉及学生数', value: 0, color: '#67C23A' },
  { label: '涉及活动数', value: 0, color: '#E6A23C' }
])

const typeTag = (t) => {
  if (!t) return ''
  if (t.includes('学术') || t.includes('科技')) return 'success'
  if (t.includes('文体')) return 'warning'
  if (t.includes('志愿') || t.includes('公益')) return ''
  return 'info'
}

const filteredList = computed(() => {
  const kw = filterText.value.trim()
  if (!kw) return list.value
  return list.value.filter(
    (r) =>
      (r.activity_name || '').includes(kw) ||
      (r.student_name || '').includes(kw) ||
      (r.student_no || '').includes(kw)
  )
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getClassActivities(props.classId)
    list.value = Array.isArray(res) ? res : (res?.activities || [])
    computeStats()
  } finally {
    loading.value = false
  }
}

const computeStats = () => {
  const total = list.value.length
  const students = new Set(list.value.map((r) => r.student_id || r.student_no).filter(Boolean))
  const acts = new Set(list.value.map((r) => r.activity_name).filter(Boolean))
  statCards.value[0].value = total
  statCards.value[1].value = students.size
  statCards.value[2].value = acts.size
}

watch(() => props.classId, fetchData)
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
