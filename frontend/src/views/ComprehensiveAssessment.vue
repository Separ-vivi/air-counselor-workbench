<template>
  <div class="comprehensive-page">
    <div class="page-header">
      <h2>综测成绩管理</h2>
      <div class="page-actions">
        <el-select v-model="filterSemester" placeholder="选择学期" clearable @change="loadData" style="width: 160px; margin-right: 10px;">
          <el-option v-for="sem in semesters" :key="sem" :label="sem" :value="sem" />
        </el-select>
        <el-button type="primary" @click="showAddDialog">新增记录</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-label">记录总数</div>
        <div class="stat-value">{{ stats.count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均总分</div>
        <div class="stat-value">{{ stats.avg_total }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最高分</div>
        <div class="stat-value highlight">{{ stats.top_score }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最低分</div>
        <div class="stat-value">{{ stats.min_score }}</div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <el-table :data="tableData" style="width: 100%" v-loading="loading">
        <el-table-column prop="student_no" label="学号" width="120" />
        <el-table-column prop="student_name" label="姓名" width="100" />
        <el-table-column prop="class_name" label="班级" width="150" />
        <el-table-column prop="semester" label="学期" width="140" />
        <el-table-column prop="moral_score" label="德育" width="80" />
        <el-table-column prop="academic_score" label="智育" width="80" />
        <el-table-column prop="physical_score" label="体育" width="80" />
        <el-table-column prop="aesthetic_score" label="美育" width="80" />
        <el-table-column prop="labor_score" label="劳育" width="80" />
        <el-table-column prop="total_score" label="总分" width="80">
          <template #default="{ row }">
            <span class="total-score">{{ row.total_score }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="class_rank" label="排名" width="70" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadData"
        @current-change="loadData"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑记录' : '新增记录'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="学生" required>
          <el-select v-model="form.student_id" filterable placeholder="选择学生" style="width: 100%;">
            <el-option v-for="s in students" :key="s.id" :label="`${s.student_no} - ${s.name}`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学期" required>
          <el-input v-model="form.semester" placeholder="如 2025-2026-1" />
        </el-form-item>
        <el-form-item label="德育">
          <el-input-number v-model="form.moral_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="智育">
          <el-input-number v-model="form.academic_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="体育">
          <el-input-number v-model="form.physical_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="美育">
          <el-input-number v-model="form.aesthetic_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="劳育">
          <el-input-number v-model="form.labor_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/index'
import { listStudents } from '@/api/students'

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const semesters = ref([])
const students = ref([])
const stats = ref({})
const filterSemester = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({
  student_id: null,
  semester: '',
  moral_score: 80,
  academic_score: 80,
  physical_score: 80,
  aesthetic_score: 80,
  labor_score: 80,
  notes: ''
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value
    }
    if (filterSemester.value) params.semester = filterSemester.value
    
    const res = await request.get('/api/comprehensive/', { params })
    tableData.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadSemesters = async () => {
  try {
    const res = await request.get('/api/comprehensive/semesters')
    semesters.value = res.data || []
  } catch (error) {
    console.error('加载学期列表失败:', error)
  }
}

const loadStats = async () => {
  try {
    const params = {}
    if (filterSemester.value) params.semester = filterSemester.value
    const res = await request.get('/api/comprehensive/statistics', { params })
    stats.value = res.data || {}
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadStudents = async () => {
  try {
    const res = await listStudents({ size: 1000 })
    students.value = res.data?.items || []
  } catch (error) {
    console.error('加载学生列表失败:', error)
  }
}

const showAddDialog = () => {
  isEdit.value = false
  editId.value = null
  form.value = {
    student_id: null,
    semester: filterSemester.value || '',
    moral_score: 80,
    academic_score: 80,
    physical_score: 80,
    aesthetic_score: 80,
    labor_score: 80,
    notes: ''
  }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    student_id: row.student_id,
    semester: row.semester,
    moral_score: row.moral_score,
    academic_score: row.academic_score,
    physical_score: row.physical_score,
    aesthetic_score: row.aesthetic_score,
    labor_score: row.labor_score,
    notes: row.notes || ''
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.student_id) {
    ElMessage.warning('请选择学生')
    return
  }
  if (!form.value.semester) {
    ElMessage.warning('请填写学期')
    return
  }
  
  submitting.value = true
  try {
    if (isEdit.value) {
      await request.put(`/api/comprehensive/${editId.value}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await request.post('/api/comprehensive/', form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
    loadStats()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除 ${row.student_name} 的综测记录吗？`, '提示', {
      type: 'warning'
    })
    await request.delete(`/api/comprehensive/${row.id}`)
    ElMessage.success('删除成功')
    loadData()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadData()
  loadSemesters()
  loadStats()
  loadStudents()
})
</script>

<style scoped>
.comprehensive-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #2C3E50;
}

.page-actions {
  display: flex;
  align-items: center;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08);
}

.stat-label {
  font-size: 13px;
  color: #7F8C8D;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #2C3E50;
}

.stat-value.highlight {
  color: #5B92E5;
}

.table-container {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(91, 146, 229, 0.08);
}

.total-score {
  font-weight: 600;
  color: #5B92E5;
}
</style>
