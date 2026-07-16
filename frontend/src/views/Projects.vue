<template>
  <div class="projects-page">
    <div class="page-header">
      <h2>📌 项目追踪</h2>
      <div class="header-actions">
        <el-input
          v-model="keyword"
          placeholder="搜索项目名"
          clearable
          :prefix-icon="Search"
          style="width: 220px"
          @keyup.enter="load"
          @clear="load"
        />
        <el-radio-group v-model="statusFilter" size="default" @change="load">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="active">进行中</el-radio-button>
          <el-radio-button label="completed">已完成</el-radio-button>
          <el-radio-button label="archived">归档</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :icon="Plus" @click="onCreate">新建项目</el-button>
      </div>
    </div>

    <el-empty v-if="!loading && projects.length === 0" description="还没有项目，点右上角新建" />

    <div class="p-grid" v-loading="loading">
      <el-card
        v-for="p in projects"
        :key="p.id"
        shadow="hover"
        class="p-card"
        :class="`status-${p.status}`"
      >
        <div class="p-header">
          <span class="p-name" @click="onOpen(p)">{{ p.name }}</span>
          <el-tag :type="statusTag(p.status)" size="small">{{ statusLabel(p.status) }}</el-tag>
        </div>
        <div class="p-desc" v-if="p.description">{{ p.description }}</div>
        <el-progress :percentage="p.progress" :stroke-width="10" class="p-progress" />
        <div class="p-meta">
          <span><el-icon><User /></el-icon>&nbsp;{{ p.student_count }} 人</span>
          <span v-if="p.start_date || p.end_date">
            <el-icon><Calendar /></el-icon>
            &nbsp;{{ p.start_date || '?' }} ~ {{ p.end_date || '?' }}
          </span>
        </div>
        <div class="p-actions">
          <el-button link :icon="View" @click="onOpen(p)">详情</el-button>
          <el-button link :icon="Edit" @click="onEdit(p)">编辑</el-button>
          <el-button link :icon="Delete" @click="onDelete(p)">删除</el-button>
        </div>
      </el-card>
    </div>

    <!-- 项目 CRUD 弹窗 -->
    <el-dialog v-model="editDialog" :title="form.id ? '编辑项目' : '新建项目'" width="520px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="项目名称" maxlength="200" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio-button label="active">进行中</el-radio-button>
            <el-radio-button label="completed">已完成</el-radio-button>
            <el-radio-button label="archived">归档</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="开始">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="结束">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="进度">
          <el-slider v-model="form.progress" :min="0" :max="100" show-input />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="onSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 项目详情 drawer -->
    <el-drawer v-model="detailDrawer" :title="detail?.name" size="600px">
      <div v-if="detail" class="detail-body">
        <div class="detail-summary">
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="状态">
              <el-tag :type="statusTag(detail.status)" size="small">{{ statusLabel(detail.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="进度">{{ detail.progress }}%</el-descriptions-item>
            <el-descriptions-item label="开始">{{ detail.start_date || '-' }}</el-descriptions-item>
            <el-descriptions-item label="结束">{{ detail.end_date || '-' }}</el-descriptions-item>
            <el-descriptions-item label="说明" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="member-section">
          <div class="section-title">
            👥 参与学生 ({{ detail.members?.length || 0 }})
            <el-button size="small" type="primary" :icon="Plus" @click="onAddMember">添加</el-button>
          </div>
          <el-empty v-if="!detail.members || detail.members.length === 0" description="暂无成员" :image-size="80" />
          <el-table v-else :data="detail.members" border size="small">
            <el-table-column prop="student_name" label="姓名" width="90" />
            <el-table-column prop="student_no" label="学号" width="120" />
            <el-table-column prop="class_name" label="班级" width="140" />
            <el-table-column label="材料" width="110">
              <template #default="{ row }">
                <el-tag :type="matStatusTag(row.material_status)" size="small">
                  {{ matStatusLabel(row.material_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="80">
              <template #default="{ row }">{{ row.progress }}%</template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link :icon="Edit" size="small" @click="onEditMember(row)" />
                <el-button link :icon="Delete" size="small" @click="onDelMember(row)" />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-drawer>

    <!-- 添加/编辑成员 -->
    <el-dialog v-model="memberDialog" :title="memberForm.ps_id ? '编辑成员' : '添加成员'" width="440px">
      <el-form :model="memberForm" label-width="80px">
        <el-form-item label="学生" required v-if="!memberForm.ps_id">
          <el-select
            v-model="memberForm.student_id"
            filterable
            remote
            :remote-method="searchStudents"
            :loading="studentSearchLoading"
            placeholder="输入姓名/学号搜索"
            style="width:100%"
          >
            <el-option
              v-for="s in studentOpts"
              :key="s.id"
              :label="`${s.name} · ${s.student_no}`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="材料">
          <el-radio-group v-model="memberForm.material_status">
            <el-radio-button label="pending">待提交</el-radio-button>
            <el-radio-button label="submitted">已提交</el-radio-button>
            <el-radio-button label="approved">已通过</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="进度">
          <el-slider v-model="memberForm.progress" :min="0" :max="100" show-input />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="memberForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memberDialog = false">取消</el-button>
        <el-button type="primary" @click="onSaveMember" :loading="savingMember">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, View, Search, User, Calendar } from '@element-plus/icons-vue'
import { projectsApi } from '@/api/productivity.js'
import http from '@/api/index.js'

const projects = ref([])
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref('')

const editDialog = ref(false)
const saving = ref(false)
const form = ref({
  id: null, name: '', start_date: '', end_date: '',
  status: 'active', progress: 0, description: '',
})

const detailDrawer = ref(false)
const detail = ref(null)

const memberDialog = ref(false)
const savingMember = ref(false)
const memberForm = ref({
  ps_id: null, student_id: null,
  material_status: 'pending', progress: 0, notes: '',
})
const studentOpts = ref([])
const studentSearchLoading = ref(false)

async function load() {
  loading.value = true
  try {
    const params = {}
    if (statusFilter.value) params.status = statusFilter.value
    if (keyword.value) params.keyword = keyword.value
    const { data } = await projectsApi.list(params)
    projects.value = data || []
  } finally { loading.value = false }
}

function statusLabel(s) { return ({ active: '进行中', completed: '已完成', archived: '归档' })[s] || s }
function statusTag(s)   { return ({ active: 'primary', completed: 'success', archived: 'info' })[s] || '' }
function matStatusLabel(s) { return ({ pending: '待提交', submitted: '已提交', approved: '已通过' })[s] || s }
function matStatusTag(s)   { return ({ pending: 'warning', submitted: 'primary', approved: 'success' })[s] || '' }

function onCreate() {
  form.value = { id: null, name: '', start_date: '', end_date: '', status: 'active', progress: 0, description: '' }
  editDialog.value = true
}
function onEdit(p) { form.value = { ...p }; editDialog.value = true }

async function onSave() {
  if (!form.value.name) { ElMessage.warning('项目名称不能为空'); return }
  saving.value = true
  try {
    if (form.value.id) await projectsApi.update(form.value.id, form.value)
    else await projectsApi.create(form.value)
    ElMessage.success('已保存')
    editDialog.value = false
    load()
  } finally { saving.value = false }
}

async function onDelete(p) {
  try {
    await ElMessageBox.confirm(`确认删除「${p.name}」及全部成员关系？`, '提示', { type: 'warning' })
    await projectsApi.remove(p.id)
    ElMessage.success('已删除')
    load()
  } catch {}
}

async function onOpen(p) {
  const { data } = await projectsApi.get(p.id)
  detail.value = data
  detailDrawer.value = true
}

// ------- 成员管理 -------
function onAddMember() {
  memberForm.value = { ps_id: null, student_id: null, material_status: 'pending', progress: 0, notes: '' }
  studentOpts.value = []
  memberDialog.value = true
}
function onEditMember(m) {
  memberForm.value = {
    ps_id: m.ps_id, student_id: m.student_id,
    material_status: m.material_status, progress: m.progress, notes: m.notes,
  }
  memberDialog.value = true
}

async function searchStudents(q) {
  if (!q) { studentOpts.value = []; return }
  studentSearchLoading.value = true
  try {
    const { data } = await http.get('/students', { params: { keyword: q, limit: 20 } })
    studentOpts.value = data.items || data || []
  } catch { studentOpts.value = [] }
  finally { studentSearchLoading.value = false }
}

async function onSaveMember() {
  if (!memberForm.value.ps_id && !memberForm.value.student_id) {
    ElMessage.warning('请选择学生'); return
  }
  savingMember.value = true
  try {
    if (memberForm.value.ps_id) {
      await projectsApi.updateMember(detail.value.id, memberForm.value.ps_id, memberForm.value)
    } else {
      await projectsApi.addMember(detail.value.id, memberForm.value)
    }
    ElMessage.success('已保存')
    memberDialog.value = false
    const { data } = await projectsApi.get(detail.value.id)
    detail.value = data
    load()
  } finally { savingMember.value = false }
}

async function onDelMember(m) {
  try {
    await ElMessageBox.confirm(`移除「${m.student_name}」？`, '提示', { type: 'warning' })
    await projectsApi.removeMember(detail.value.id, m.ps_id)
    ElMessage.success('已移除')
    const { data } = await projectsApi.get(detail.value.id)
    detail.value = data
    load()
  } catch {}
}

onMounted(load)
</script>

<style scoped>
.projects-page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 12px; flex-wrap: wrap; }

.p-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.p-card { transition: transform .12s; }
.p-card:hover { transform: translateY(-2px); }
.p-card.status-completed { opacity: .8; }
.p-card.status-archived  { opacity: .55; }

.p-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.p-name { font-weight: 600; font-size: 15px; cursor: pointer; color: #3A3A3A; }
.p-name:hover { color: #4A7A8C; }
.p-desc { font-size: 12px; color: #7B7B7B; margin-bottom: 8px; min-height: 32px; }
.p-progress { margin: 8px 0; }
.p-meta {
  display: flex; gap: 14px; font-size: 12px; color: #7B7B7B;
  margin: 8px 0;
}
.p-meta span { display: inline-flex; align-items: center; }
.p-actions { display: flex; justify-content: flex-end; gap: 4px; border-top: 1px dashed rgba(0,0,0,.06); padding-top: 6px; margin-top: 4px; }

.detail-body { padding: 0 8px; }
.member-section { margin-top: 20px; }
.section-title {
  display: flex; justify-content: space-between; align-items: center;
  font-weight: 600; margin-bottom: 12px;
}
</style>
