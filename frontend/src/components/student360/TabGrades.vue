<template>
  <div class="tab-grades">
    <div class="grades-toolbar">
      <el-select v-model="filterSemester" placeholder="全部学期" clearable size="small" style="width:180px" @change="load">
        <el-option v-for="s in semesterOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" size="small" @click="showAdd = true" :icon="Plus">添加成绩</el-button>
    </div>

    <div class="stats-row">
      <div class="stat-box" v-for="(stat, idx) in stats" :key="stat.label">
        <div class="stat-val" :style="{color: colors[idx % colors.length]}">{{ stat.value }}</div>
        <div class="stat-lbl">{{ stat.label }}</div>
      </div>
    </div>

    <el-table :data="filteredRows" stripe size="small" max-height="360" v-loading="loading" empty-text="暂无成绩记录">
      <el-table-column prop="semester" label="学期" width="140" />
      <el-table-column prop="course_name" label="课程" min-width="160" show-overflow-tooltip />
      <el-table-column prop="score" label="成绩" width="80" align="center">
        <template #default="{row}">
          <span :style="{color: row.score < 60 ? '#F56C6C' : '', fontWeight: row.score < 60 ? '700' : '400'}">{{ row.score ?? '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="gpa" label="绩点" width="70" align="center" />
      <el-table-column prop="credit" label="学分" width="70" align="center" />
      <el-table-column label="操作" width="120" align="center">
        <template #default="{row}">
          <el-button link type="primary" size="small" @click="startEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="showAdd" :title="editRow ? '编辑成绩' : '添加成绩'" width="460px" append-to-body>
      <el-form :model="form" label-width="70px">
        <el-form-item label="学期"><el-input v-model="form.semester" placeholder="如 2025-2026-1" /></el-form-item>
        <el-form-item label="课程名"><el-input v-model="form.course_name" /></el-form-item>
        <el-form-item label="成绩"><el-input-number v-model="form.score" :min="0" :max="100" :precision="1" /></el-form-item>
        <el-form-item label="绩点"><el-input-number v-model="form.gpa" :min="0" :max="5" :precision="2" /></el-form-item>
        <el-form-item label="学分"><el-input-number v-model="form.credit" :min="0" :max="10" :precision="1" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { s360 } from '@/api/student360.js'

const props = defineProps({ sid: { type: Number, required: true } })
const loading = ref(false)
const rows = ref([])
const filterSemester = ref('')
const showAdd = ref(false)
const editRow = ref(null)
const colors = ['#5B92E5', '#4FC3B8', '#8FA9E5']

const form = ref({ semester: '', course_name: '', score: 80, gpa: 3.2, credit: 1.0 })

const semesterOptions = computed(() => {
  const set = new Set(rows.value.map(r => r.semester).filter(Boolean))
  return [...set].sort().reverse()
})
const filteredRows = computed(() => {
  if (!filterSemester.value) return rows.value
  return rows.value.filter(r => r.semester === filterSemester.value)
})

const stats = computed(() => {
  const list = filteredRows.value
  if (!list.length) return [
    { label: '平均分', value: '—' }, { label: 'GPA', value: '—' }, { label: '课程数', value: 0 }
  ]
  const scores = list.map(r => Number(r.score)).filter(v => !isNaN(v))
  const gpas = list.map(r => Number(r.gpa)).filter(v => !isNaN(v))
  const avg = scores.length ? (scores.reduce((a,b)=>a+b,0)/scores.length).toFixed(1) : '—'
  const gpa = gpas.length ? (gpas.reduce((a,b)=>a+b,0)/gpas.length).toFixed(2) : '—'
  const fails = scores.filter(v => v < 60).length
  return [
    { label: '平均分', value: avg },
    { label: 'GPA', value: gpa },
    { label: '挂科', value: fails ? `${fails}门` : '0门' }
  ]
})

async function load() {
  loading.value = true
  try {
    rows.value = await s360.grades.list(props.sid) || []
  } catch { rows.value = [] }
  finally { loading.value = false }
}

function startEdit(row) {
  editRow.value = row
  form.value = { semester: row.semester, course_name: row.course_name, score: row.score ?? 80, gpa: row.gpa ?? 3.2, credit: row.credit ?? 1.0 }
  showAdd.value = true
}

async function onSave() {
  if (!form.value.semester || !form.value.course_name) {
    ElMessage.warning('学期和课程名不能为空')
    return
  }
  try {
    if (editRow.value) {
      await s360.grades.update(props.sid, editRow.value.id, form.value)
      ElMessage.success('已更新')
    } else {
      await s360.grades.create(props.sid, form.value)
      ElMessage.success('已添加')
    }
    showAdd.value = false
    editRow.value = null
    await load()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除 ${row.course_name} 的成绩？`, '确认', { type: 'warning' })
    await s360.grades.remove(props.sid, row.id)
    ElMessage.success('已删除')
    await load()
  } catch {}
}

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.tab-grades { padding: 4px 0; }
.grades-toolbar { display: flex; gap: 10px; margin-bottom: 14px; }
.stats-row { display: flex; gap: 12px; margin-bottom: 14px; }
.stat-box {
  flex: 1; background: rgba(91,146,229,0.05); border: 1px solid rgba(91,146,229,0.12);
  border-radius: 10px; padding: 12px; text-align: center;
}
.stat-val { font-size: 22px; font-weight: 700; line-height: 1.2; }
.stat-lbl { font-size: 12px; color: #6B7B8D; margin-top: 4px; }
</style>
