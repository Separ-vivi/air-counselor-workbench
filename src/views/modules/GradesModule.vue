<template>
  <div class="module-page">
    <div class="page-header">
      <h2>📊 成绩管理</h2>
      <div>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
        <el-button type="primary" :icon="View" @click="$router.push('/module/warnings')">学业预警看板</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="选择学生" required>
          <StudentSelect v-model="studentId" style="width: 300px" @change="reload" />
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="filter.semester" placeholder="全部" clearable filterable style="width: 200px">
            <el-option v-for="s in semesters" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" v-if="!studentId">
      <el-empty description="请先选择学生查看成绩明细" :image-size="80" />
    </el-card>

    <template v-else>
      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-label">总课程数</div>
            <div class="stat-value" style="color: #409EFF">{{ stats.total }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-label">及格</div>
            <div class="stat-value" style="color: #67C23A">{{ stats.pass }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-label">不及格</div>
            <div class="stat-value" style="color: #F56C6C">{{ stats.fail }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-label">平均分</div>
            <div class="stat-value" style="color: #E6A23C">{{ stats.avg }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never">
        <template #header>
          <span>成绩明细 · 共 {{ filteredList.length }} 条</span>
        </template>
        <el-table :data="filteredList" stripe border v-loading="loading" max-height="600">
          <el-table-column label="学期" prop="semester" width="140" sortable />
          <el-table-column label="课程代码" prop="course_code" width="120" />
          <el-table-column label="课程名" prop="course_name" min-width="200" show-overflow-tooltip />
          <el-table-column label="学分" prop="credit" width="80" align="center" />
          <el-table-column label="分数" prop="score" width="90" align="center" sortable>
            <template #default="{ row }">
              <span :style="{ color: row.score < 60 ? '#F56C6C' : row.score < 75 ? '#E6A23C' : '#67C23A', fontWeight: 600 }">
                {{ row.score ?? '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="成绩等级" prop="grade_level" width="110" />
          <el-table-column label="重修" prop="is_makeup" width="80" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_makeup" type="warning" size="small">重修</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Download, View } from '@element-plus/icons-vue'
import { grades as gradesApi } from '@/api/modules'
import StudentSelect from '@/components/StudentSelect.vue'

const studentId = ref(null)
const list = ref([])
const semesters = ref([])
const filter = reactive({ semester: '' })
const loading = ref(false)

const filteredList = computed(() => {
  if (!filter.semester) return list.value
  return list.value.filter((r) => r.semester === filter.semester)
})

const stats = computed(() => {
  const rs = filteredList.value
  const total = rs.length
  const fail = rs.filter((r) => (r.score ?? 100) < 60).length
  const scores = rs.map((r) => Number(r.score)).filter((x) => !isNaN(x))
  const avg = scores.length ? (scores.reduce((s, v) => s + v, 0) / scores.length).toFixed(2) : '-'
  return { total, pass: total - fail, fail, avg }
})

const reload = async () => {
  if (!studentId.value) return
  loading.value = true
  try {
    const res = await gradesApi.studentGrades(studentId.value)
    list.value = Array.isArray(res) ? res : (res?.items || res?.grades || [])
  } finally { loading.value = false }
}

const exportAll = async () => {
  try {
    const blob = await gradesApi.exportAll()
    const url = URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url; a.download = `grades_${Date.now()}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {}
}

watch(studentId, reload)
onMounted(async () => {
  try {
    const res = await gradesApi.semesters()
    semesters.value = Array.isArray(res) ? res : (res?.items || [])
  } catch (e) {}
})
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.stat-card { border-radius: 12px; text-align: center; }
.stat-label { color: #909399; font-size: 13px; margin-bottom: 8px; }
.stat-value { font-size: 26px; font-weight: 600; }
</style>
