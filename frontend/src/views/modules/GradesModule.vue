<template>
  <div class="module-page">
    <div class="page-header">
      <h2>📊 成绩管理</h2>
      <div>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
        <el-button type="primary" :icon="View" @click="$router.push('/module/warnings')">学业预警看板</el-button>
      </div>
    </div>

    <el-tabs v-model="tab" style="margin-bottom: 16px">
      <el-tab-pane label="👤 按学生查看" name="student" />
      <el-tab-pane label="🏫 按班级查看" name="class" />
    </el-tabs>

    <!-- 按学生视图 -->
    <template v-if="tab === 'student'">
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
    </template>

    <!-- 按班级视图 -->
    <template v-else>
      <el-card shadow="never" style="margin-bottom: 16px">
        <el-form :inline="true">
          <el-form-item label="选择班级" required>
            <el-select v-model="classId" placeholder="请选择班级" filterable clearable style="width: 300px" @change="reloadClass">
              <el-option v-for="c in orgStore.allClasses" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="学期">
            <el-select v-model="classFilter.semester" placeholder="全部" clearable filterable style="width: 200px" @change="reloadClass">
              <el-option v-for="s in semesters" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card shadow="never" v-if="!classId">
        <el-empty description="请先选择班级查看成绩汇总" :image-size="80" />
      </el-card>

      <template v-else>
        <el-row :gutter="16" style="margin-bottom: 16px">
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-label">班级人数</div>
              <div class="stat-value" style="color: #409EFF">{{ classData.stats?.total_students || 0 }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-label">总成绩条数</div>
              <div class="stat-value" style="color: #67C23A">{{ classData.stats?.total_courses || 0 }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-label">班级平均分</div>
              <div class="stat-value" style="color: #E6A23C">{{ classData.stats?.avg_score || 0 }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-label">不及格数</div>
              <div class="stat-value" style="color: #F56C6C">{{ classData.stats?.fail_count || 0 }}</div>
            </el-card>
          </el-col>
        </el-row>

        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header>
            <span>学生成绩汇总 · {{ classData.students?.length || 0 }} 人</span>
          </template>
          <el-table :data="classData.students || []" stripe border v-loading="classLoading" max-height="360">
            <el-table-column label="学号" prop="student_no" width="140" />
            <el-table-column label="姓名" prop="name" width="120" />
            <el-table-column label="总课程数" prop="total_courses" width="110" align="center" sortable />
            <el-table-column label="平均分" prop="avg_score" width="110" align="center" sortable>
              <template #default="{ row }">
                <span :style="{ color: row.avg_score < 60 ? '#F56C6C' : row.avg_score < 75 ? '#E6A23C' : '#67C23A', fontWeight: 600 }">
                  {{ row.avg_score }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="不及格数" prop="fail_count" width="110" align="center" sortable>
              <template #default="{ row }">
                <el-tag v-if="row.fail_count > 0" type="danger" size="small">{{ row.fail_count }}</el-tag>
                <span v-else>0</span>
              </template>
            </el-table-column>
            <el-table-column label="及格率(%)" prop="pass_rate" width="110" align="center" sortable />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="primary" @click="goStudent(row.student_id)">查看明细</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <span>成绩明细 · 共 {{ classData.grades?.length || 0 }} 条</span>
          </template>
          <el-table :data="classData.grades || []" stripe border max-height="400">
            <el-table-column label="学号" prop="student_no" width="130" />
            <el-table-column label="姓名" prop="student_name" width="100" />
            <el-table-column label="学期" prop="semester" width="120" />
            <el-table-column label="课程" prop="course_name" min-width="180" show-overflow-tooltip />
            <el-table-column label="学分" prop="credit" width="70" align="center" />
            <el-table-column label="分数" prop="score" width="80" align="center" sortable>
              <template #default="{ row }">
                <span :style="{ color: row.score < 60 ? '#F56C6C' : row.score < 75 ? '#E6A23C' : '#67C23A', fontWeight: 600 }">
                  {{ row.score ?? '-' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="成绩等级" prop="grade_level" width="100" />
          </el-table>
        </el-card>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Download, View } from '@element-plus/icons-vue'
import { grades as gradesApi } from '@/api/modules'
import { useOrgStore } from '@/stores/org'
import StudentSelect from '@/components/StudentSelect.vue'

const router = useRouter()
const orgStore = useOrgStore()

const tab = ref('student')

// 按学生
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

// 按班级
const classId = ref(null)
const classFilter = reactive({ semester: '' })
const classData = ref({ students: [], grades: [], stats: {} })
const classLoading = ref(false)

const reloadClass = async () => {
  if (!classId.value) {
    classData.value = { students: [], grades: [], stats: {} }
    return
  }
  classLoading.value = true
  try {
    const params = classFilter.semester ? { semester: classFilter.semester } : {}
    const res = await gradesApi.byClass(classId.value, params)
    classData.value = res || { students: [], grades: [], stats: {} }
  } finally { classLoading.value = false }
}

const goStudent = (sid) => {
  router.push(`/students/${sid}`)
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
  if (!orgStore.orgTree?.length) {
    try { await orgStore.loadTree() } catch (e) {}
  }
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
