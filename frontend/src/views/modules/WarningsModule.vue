<template>
  <div class="module-page">
    <div class="page-header">
      <h2>🚦 学业预警</h2>
      <div>
        <el-button :icon="Refresh" @click="reload">刷新</el-button>
        <el-button type="primary" :icon="Refresh" :loading="recalcing" @click="doRecalc">重新计算</el-button>
        <el-button :icon="Download" @click="exportExcel">导出</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="学期">
          <el-select v-model="filter.semester" placeholder="全部学期" clearable filterable style="width: 180px" @change="reload">
            <el-option v-for="s in semesters" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="预警等级">
          <el-select v-model="filter.level" placeholder="全部" clearable style="width: 160px" @change="reload">
            <el-option label="红色（严重）" value="红色" />
            <el-option label="黄色（一般）" value="黄色" />
            <el-option label="蓝色（提醒）" value="蓝色" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="filter.class_name" placeholder="全部班级" clearable filterable style="width: 200px" @change="reload">
            <el-option v-for="c in orgStore.allClasses" :key="c.id" :label="c.name" :value="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="学生">
          <StudentSelect v-model="filter.student_id" style="width: 220px" @change="reload" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">预警学生总数</div>
          <div class="stat-value" style="color: #F56C6C">{{ stats.total }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">红色预警</div>
          <div class="stat-value" style="color: #F56C6C">{{ stats.red }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">黄色预警</div>
          <div class="stat-value" style="color: #E6A23C">{{ stats.yellow }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">蓝色提醒</div>
          <div class="stat-value" style="color: #409EFF">{{ stats.blue }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <el-table :data="filteredRows" stripe border v-loading="loading" max-height="600">
        <el-table-column label="学生" prop="student_name" width="110">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/students/${row.student_id || row.id}`)">
              {{ row.student_name || row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="学号" prop="student_no" width="140" />
        <el-table-column label="班级" prop="class_name" min-width="160" show-overflow-tooltip />
        <el-table-column label="预警等级" prop="warning_level" width="110">
          <template #default="{ row }">
            <el-tag :type="levelTag(row.warning_level)" size="small">{{ row.warning_level || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="预警原因" prop="warning_reason" min-width="200" show-overflow-tooltip />
        <el-table-column label="不及格门数" prop="fail_count" width="110" align="center" />
        <el-table-column label="GPA" prop="gpa" width="90" />
        <el-table-column label="学期" prop="semester" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import { grades as gradesApi } from '@/api/modules'
import { useOrgStore } from '@/stores/org'
import { useStudentStore } from '@/stores/student'
import StudentSelect from '@/components/StudentSelect.vue'

const orgStore = useOrgStore()
const studentStore = useStudentStore()

const list = ref([])
const semesters = ref([])
const loading = ref(false)
const recalcing = ref(false)
const filter = reactive({ semester: '', level: '', class_name: '', student_id: null })

const filteredRows = computed(() => {
  let rs = list.value
  if (filter.level) rs = rs.filter((r) => (r.warning_level || '').includes(filter.level.slice(0, 1)) || r.warning_level === filter.level)
  if (filter.class_name) rs = rs.filter((r) => r.class_name === filter.class_name)
  if (filter.student_id) rs = rs.filter((r) => r.student_id === filter.student_id || r.id === filter.student_id)
  return rs
})

const stats = computed(() => {
  const s = { total: filteredRows.value.length, red: 0, yellow: 0, blue: 0 }
  filteredRows.value.forEach((r) => {
    const l = r.warning_level || ''
    if (l.includes('红')) s.red++
    else if (l.includes('黄')) s.yellow++
    else if (l.includes('蓝')) s.blue++
  })
  return s
})

const levelTag = (l) => {
  if (!l) return ''
  if (l.includes('红')) return 'danger'
  if (l.includes('黄')) return 'warning'
  if (l.includes('蓝')) return 'primary'
  return 'info'
}

const reload = async () => {
  loading.value = true
  try {
    const params = {}
    if (filter.semester) params.semester = filter.semester
    const res = await gradesApi.warnings(params)
    list.value = Array.isArray(res) ? res : (res?.items || res?.data || [])
  } finally { loading.value = false }
}

const loadSemesters = async () => {
  try {
    const res = await gradesApi.semesters()
    semesters.value = Array.isArray(res) ? res : (res?.items || [])
  } catch (e) { semesters.value = [] }
}

const doRecalc = async () => {
  recalcing.value = true
  try {
    await gradesApi.recalculateWarnings()
    ElMessage.success('重新计算完成')
    reload()
  } finally { recalcing.value = false }
}

const exportExcel = async () => {
  try {
    const blob = await gradesApi.exportWarnings()
    const url = URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url; a.download = `warnings_${Date.now()}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {}
}

watch(() => studentStore.refreshBumper, reload)
onMounted(() => {
  if (!orgStore.orgTree.length) orgStore.loadTree()
  loadSemesters()
  reload()
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
