<template>
  <div class="module-page">
    <div class="page-header">
      <h2>📊 成绩管理</h2>
      <div>
        <el-button
          type="success"
          :icon="Download"
          :disabled="!selected.length"
          @click="exportSelected"
        >导出选中（{{ selected.length }}）</el-button>
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
          <el-form-item label="搜索">
            <el-input v-model="filter.kw" placeholder="课程名/课程代码" clearable style="width: 200px" />
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
            <el-table-column label="课程代码" prop="course_code" width="120" sortable />
            <el-table-column label="课程名" prop="course_name" min-width="200" show-overflow-tooltip sortable />
            <el-table-column label="学分" prop="credit" width="80" align="center" sortable />
            <el-table-column label="分数" prop="score" width="90" align="center" sortable>
              <template #default="{ row }">
                <span :style="{ color: row.score < 60 ? '#F56C6C' : row.score < 75 ? '#E6A23C' : '#67C23A', fontWeight: 600 }">
                  {{ row.score ?? '-' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="成绩等级" prop="grade_level" width="110" sortable />
            <el-table-column label="重修" prop="is_makeup" width="80" align="center" sortable>
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
          <el-form-item label="搜索">
            <el-input v-model="classFilter.kw" placeholder="学号/姓名/课程名" clearable style="width: 200px" />
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
          <el-table
            :data="filteredClassGrades"
            stripe
            border
            max-height="400"
            @selection-change="onSelectionChange"
          >
            <el-table-column type="selection" width="45" reserve-selection />
            <el-table-column label="学号" prop="student_no" width="130" sortable />
            <el-table-column label="姓名" prop="student_name" width="100" sortable />
            <el-table-column label="学期" prop="semester" width="120" sortable />
            <el-table-column label="课程" prop="course_name" min-width="180" show-overflow-tooltip sortable />
            <el-table-column label="学分" prop="credit" width="70" align="center" sortable />
            <el-table-column label="分数" prop="score" width="80" align="center" sortable>
              <template #default="{ row }">
                <span :style="{ color: row.score < 60 ? '#F56C6C' : row.score < 75 ? '#E6A23C' : '#67C23A', fontWeight: 600 }">
                  {{ row.score ?? '-' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="成绩等级" prop="grade_level" width="100" sortable />
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
import { ElMessage } from 'element-plus'
import { grades as gradesApi } from '@/api/modules'
import { useOrgStore } from '@/stores/org'
import StudentSelect from '@/components/StudentSelect.vue'

const router = useRouter()
const orgStore = useOrgStore()

const tab = ref('class')

// 按学生
const studentId = ref(null)
const list = ref([])
const semesters = ref([])
const filter = reactive({ semester: '', kw: '' })
const loading = ref(false)

// v3j-B-b02 · 学生成绩明细：加课程名/代码模糊过滤
const filteredList = computed(() => {
  let rs = list.value
  if (filter.semester) rs = rs.filter((r) => r.semester === filter.semester)
  const kw = (filter.kw || '').trim()
  if (kw) {
    rs = rs.filter((r) => (r.course_name || '').includes(kw) || (r.course_code || '').includes(kw))
  }
  return rs
})

// v3j-B-b02 · 多选批量导出（针对班级视图的成绩明细 GradeRecord 表）
const selected = ref([])
const onSelectionChange = (rows) => { selected.value = rows }
const exportSelected = async () => {
  if (!selected.value.length) {
    ElMessage.warning('请先勾选要导出的成绩记录')
    return
  }
  try {
    const ids = selected.value.map(r => r.id).filter(Boolean)
    if (!ids.length) {
      ElMessage.warning('选中记录缺少 ID，无法导出')
      return
    }
    const blob = await gradesApi.exportByIds(ids)
    const url = URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = `成绩明细_选中${ids.length}条_${Date.now()}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success(`已导出 ${ids.length} 条成绩记录`)
  } catch (e) { ElMessage.error('导出失败') }
}

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
const classFilter = reactive({ semester: '', kw: '' })
const classData = ref({ students: [], grades: [], stats: {} })
const classLoading = ref(false)

const filteredClassGrades = computed(() => {
  const rs = classData.value.grades || []
  const kw = (classFilter.kw || '').trim()
  if (!kw) return rs
  return rs.filter((r) => (r.course_name || '').includes(kw) || (r.student_name || '').includes(kw) || (r.student_no || '').includes(kw))
})

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
  // 默认自动选第一个班，让 air 进来就有成绩数据看
  if (!classId.value && orgStore.orgTree?.length) {
    for (const g of orgStore.orgTree) {
      for (const m of (g.majors || [])) {
        if (m.classes?.length) {
          classId.value = m.classes[0].id
          reloadClass()
          return
        }
      }
    }
  }
})

// classId 变化时自动重载
watch(classId, reloadClass)
</script>

<style scoped>
.module-page { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.stat-card { border-radius: 12px; text-align: center; }
.stat-label { color: #909399; font-size: 13px; margin-bottom: 8px; }
.stat-value { font-size: 26px; font-weight: 600; }
</style>
