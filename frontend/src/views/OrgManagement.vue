<template>
  <div class="org-management">
    <div class="page-header">
      <h2>🏛️ 组织架构管理</h2>
      <p class="sub">年级 / 专业 / 班级 三级架构 · 全 CRUD</p>
    </div>

    <el-tabs v-model="active" type="border-card">
      <el-tab-pane label="🎯 年级" name="grade">
        <div class="tab-actions">
          <el-button type="primary" :icon="Plus" @click="openGrade(null)">新增年级</el-button>
        </div>
        <el-table :data="grades" stripe border v-loading="loading.grade">
          <el-table-column label="ID" prop="id" width="80" />
          <el-table-column label="年级名称" prop="grade_name" />
          <el-table-column label="学年" prop="start_year" width="140">
            <template #default="{ row }">{{ row.start_year }} - {{ row.end_year || (row.start_year ? row.start_year + 4 : '') }}</template>
          </el-table-column>
          <el-table-column label="备注" prop="notes" show-overflow-tooltip />
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openGrade(row)">编辑</el-button>
              <el-popconfirm title="删除此年级会级联影响下属专业和班级，确定？" @confirm="delGrade(row)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="🎓 专业" name="major">
        <div class="tab-actions">
          <el-select v-model="filterGradeIdM" placeholder="按年级筛选" clearable style="width: 200px; margin-right: 12px" @change="loadMajors">
            <el-option v-for="g in grades" :key="g.id" :label="g.grade_name" :value="g.id" />
          </el-select>
          <el-button type="primary" :icon="Plus" @click="openMajor(null)">新增专业</el-button>
        </div>
        <el-table :data="majors" stripe border v-loading="loading.major">
          <el-table-column label="ID" prop="id" width="80" />
          <el-table-column label="专业名称" prop="major_name" />
          <el-table-column label="所属年级" prop="grade_name" width="180" />
          <el-table-column label="学制(年)" prop="duration" width="100" />
          <el-table-column label="备注" prop="notes" show-overflow-tooltip />
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openMajor(row)">编辑</el-button>
              <el-popconfirm title="确认删除该专业？" @confirm="delMajor(row)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="🏫 班级" name="class">
        <div class="tab-actions">
          <el-select v-model="filterGradeIdC" placeholder="按年级筛选" clearable style="width: 180px; margin-right: 8px" @change="loadClasses">
            <el-option v-for="g in grades" :key="g.id" :label="g.grade_name" :value="g.id" />
          </el-select>
          <el-select v-model="filterMajorIdC" placeholder="按专业筛选" clearable filterable style="width: 200px; margin-right: 12px" @change="loadClasses">
            <el-option v-for="m in majorsFiltered" :key="m.id" :label="m.major_name" :value="m.id" />
          </el-select>
          <el-button type="primary" :icon="Plus" @click="openClass(null)">新增班级</el-button>
        </div>
        <el-table :data="classes" stripe border v-loading="loading.class">
          <el-table-column label="ID" prop="id" width="80" />
          <el-table-column label="班级名称" prop="class_name" width="180" />
          <el-table-column label="所属专业" prop="major_name" width="160" />
          <el-table-column label="班主任" prop="class_teacher" width="120" />
          <el-table-column label="班长" prop="monitor" width="100" />
          <el-table-column label="团支书" prop="league_secretary" width="100" />
          <el-table-column label="学生数" prop="student_count" width="100" />
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="$router.push(`/classes/${row.id}`)">档案</el-button>
              <el-button link type="primary" size="small" @click="openClass(row)">编辑</el-button>
              <el-popconfirm title="确认删除该班级？" @confirm="delClass(row)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 年级 Dialog -->
    <el-dialog v-model="gradeDlg" :title="editingGrade?.id ? '编辑年级' : '新增年级'" width="480px">
      <el-form :model="gradeForm" :rules="gradeRules" ref="gradeFormRef" label-width="90px">
        <el-form-item label="年级名称" prop="grade_name">
          <el-input v-model="gradeForm.grade_name" placeholder="如 2025级" />
        </el-form-item>
        <el-form-item label="入学年份" prop="start_year">
          <el-input-number v-model="gradeForm.start_year" :min="2000" :max="2100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="gradeForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="gradeDlg = false">取消</el-button>
        <el-button type="primary" @click="submitGrade" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 专业 Dialog -->
    <el-dialog v-model="majorDlg" :title="editingMajor?.id ? '编辑专业' : '新增专业'" width="480px">
      <el-form :model="majorForm" :rules="majorRules" ref="majorFormRef" label-width="90px">
        <el-form-item label="所属年级" prop="grade_id">
          <el-select v-model="majorForm.grade_id" placeholder="选择年级" style="width: 100%">
            <el-option v-for="g in grades" :key="g.id" :label="g.grade_name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业名称" prop="major_name">
          <el-input v-model="majorForm.major_name" />
        </el-form-item>
        <el-form-item label="学制(年)">
          <el-input-number v-model="majorForm.duration" :min="1" :max="10" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="majorForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="majorDlg = false">取消</el-button>
        <el-button type="primary" @click="submitMajor" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 班级 Dialog -->
    <el-dialog v-model="classDlg" :title="editingClass?.id ? '编辑班级' : '新增班级'" width="520px">
      <el-form :model="classForm" :rules="classRules" ref="classFormRef" label-width="90px">
        <el-form-item label="所属专业" prop="major_id">
          <el-select v-model="classForm.major_id" placeholder="选择专业" filterable style="width: 100%">
            <el-option v-for="m in majors" :key="m.id" :label="`${m.grade_name || ''} ${m.major_name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级名称" prop="class_name">
          <el-input v-model="classForm.class_name" />
        </el-form-item>
        <el-form-item label="班主任">
          <el-input v-model="classForm.class_teacher" />
        </el-form-item>
        <el-form-item label="班长">
          <el-input v-model="classForm.monitor" />
        </el-form-item>
        <el-form-item label="团支书">
          <el-input v-model="classForm.league_secretary" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="classDlg = false">取消</el-button>
        <el-button type="primary" @click="submitClass" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  listGrades, createGrade, updateGrade, deleteGrade,
  listMajors, createMajor, updateMajor, deleteMajor,
  listClasses, createClass, updateClass, deleteClass
} from '@/api/org'
import { useOrgStore } from '@/stores/org'

const orgStore = useOrgStore()
const active = ref('grade')

const grades = ref([])
const majors = ref([])
const classes = ref([])
const loading = reactive({ grade: false, major: false, class: false })
const saving = ref(false)

const filterGradeIdM = ref(null)
const filterGradeIdC = ref(null)
const filterMajorIdC = ref(null)
const majorsFiltered = computed(() => {
  return filterGradeIdC.value ? majors.value.filter((m) => m.grade_id === filterGradeIdC.value) : majors.value
})
watch(filterGradeIdC, () => { filterMajorIdC.value = null })

// ---------- Grade ----------
const gradeDlg = ref(false)
const editingGrade = ref(null)
const gradeFormRef = ref(null)
const gradeForm = reactive({ grade_name: '', start_year: new Date().getFullYear(), notes: '' })
const gradeRules = {
  grade_name: [{ required: true, message: '请填写年级名', trigger: 'blur' }],
  start_year: [{ required: true, message: '请填写入学年份', trigger: 'blur' }]
}

const loadGrades = async () => {
  loading.grade = true
  try {
    grades.value = (await listGrades()) || []
  } finally { loading.grade = false }
}
const openGrade = (row) => {
  editingGrade.value = row
  Object.assign(gradeForm, {
    grade_name: row?.grade_name || '',
    start_year: row?.start_year || new Date().getFullYear(),
    notes: row?.notes || ''
  })
  gradeDlg.value = true
}
const submitGrade = async () => {
  await gradeFormRef.value?.validate()
  saving.value = true
  try {
    if (editingGrade.value?.id) {
      await updateGrade(editingGrade.value.id, gradeForm)
      ElMessage.success('已更新')
    } else {
      await createGrade(gradeForm)
      ElMessage.success('已创建')
    }
    gradeDlg.value = false
    await loadGrades()
    orgStore.loadTree(true)
  } finally { saving.value = false }
}
const delGrade = async (row) => {
  await deleteGrade(row.id)
  ElMessage.success('已删除')
  loadGrades()
  orgStore.loadTree(true)
}

// ---------- Major ----------
const majorDlg = ref(false)
const editingMajor = ref(null)
const majorFormRef = ref(null)
const majorForm = reactive({ major_name: '', grade_id: null, duration: 4, notes: '' })
const majorRules = {
  major_name: [{ required: true, message: '请填写专业名', trigger: 'blur' }],
  grade_id: [{ required: true, message: '请选择所属年级', trigger: 'change' }]
}
const loadMajors = async () => {
  loading.major = true
  try {
    const gid = filterGradeIdM.value
    const list = (await listMajors(gid)) || []
    // 补上 grade_name
    majors.value = list.map((m) => ({
      ...m,
      grade_name: grades.value.find((g) => g.id === m.grade_id)?.grade_name || ''
    }))
  } finally { loading.major = false }
}
const openMajor = (row) => {
  editingMajor.value = row
  Object.assign(majorForm, {
    major_name: row?.major_name || '',
    grade_id: row?.grade_id || filterGradeIdM.value || null,
    duration: row?.duration || 4,
    notes: row?.notes || ''
  })
  majorDlg.value = true
}
const submitMajor = async () => {
  await majorFormRef.value?.validate()
  saving.value = true
  try {
    if (editingMajor.value?.id) {
      await updateMajor(editingMajor.value.id, majorForm)
      ElMessage.success('已更新')
    } else {
      await createMajor(majorForm)
      ElMessage.success('已创建')
    }
    majorDlg.value = false
    await loadMajors()
    orgStore.loadTree(true)
  } finally { saving.value = false }
}
const delMajor = async (row) => {
  await deleteMajor(row.id)
  ElMessage.success('已删除')
  loadMajors()
  orgStore.loadTree(true)
}

// ---------- Class ----------
const classDlg = ref(false)
const editingClass = ref(null)
const classFormRef = ref(null)
const classForm = reactive({ class_name: '', major_id: null, class_teacher: '', monitor: '', league_secretary: '' })
const classRules = {
  class_name: [{ required: true, message: '请填写班级名', trigger: 'blur' }],
  major_id: [{ required: true, message: '请选择所属专业', trigger: 'change' }]
}
const loadClasses = async () => {
  loading.class = true
  try {
    const params = {}
    if (filterMajorIdC.value) params.major_id = filterMajorIdC.value
    else if (filterGradeIdC.value) params.grade_id = filterGradeIdC.value
    const list = (await listClasses(params)) || []
    classes.value = list.map((c) => ({
      ...c,
      major_name: majors.value.find((m) => m.id === c.major_id)?.major_name || c.major_name || ''
    }))
  } finally { loading.class = false }
}
const openClass = (row) => {
  editingClass.value = row
  Object.assign(classForm, {
    class_name: row?.class_name || '',
    major_id: row?.major_id || filterMajorIdC.value || null,
    class_teacher: row?.class_teacher || '',
    monitor: row?.monitor || '',
    league_secretary: row?.league_secretary || ''
  })
  classDlg.value = true
}
const submitClass = async () => {
  await classFormRef.value?.validate()
  saving.value = true
  try {
    if (editingClass.value?.id) {
      await updateClass(editingClass.value.id, classForm)
      ElMessage.success('已更新')
    } else {
      await createClass(classForm)
      ElMessage.success('已创建')
    }
    classDlg.value = false
    await loadClasses()
    orgStore.loadTree(true)
  } finally { saving.value = false }
}
const delClass = async (row) => {
  await deleteClass(row.id)
  ElMessage.success('已删除')
  loadClasses()
  orgStore.loadTree(true)
}

onMounted(async () => {
  await loadGrades()
  await loadMajors()
  await loadClasses()
})
</script>

<style scoped>
.org-management { padding: 4px; }
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.page-header .sub { color: #909399; margin: 4px 0 0; font-size: 13px; }
.tab-actions { margin-bottom: 12px; display: flex; align-items: center; }
</style>
