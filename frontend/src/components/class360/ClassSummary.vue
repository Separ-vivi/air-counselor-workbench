<template>
  <div>
    <h3 style="margin-top:0">📊 班级概览</h3>
    <el-row :gutter="12">
      <el-col :span="6">
        <div class="stat-card" :style="cardStyle('blue')">
          <div class="stat-label">总人数</div>
          <div class="stat-value">{{ summary?.student_count ?? '—' }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" :style="cardStyle('green')">
          <div class="stat-label">党员数</div>
          <div class="stat-value">{{ summary?.party_member_count ?? 0 }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" :style="cardStyle('orange')">
          <div class="stat-label">困难生数</div>
          <div class="stat-value">{{ summary?.hardship_count ?? 0 }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" :style="cardStyle('red')">
          <div class="stat-label">预警人数</div>
          <div class="stat-value">{{ (summary?.warning_red_count || 0) + (summary?.warning_yellow_count || 0) }}</div>
        </div>
      </el-col>
    </el-row>

    <el-divider />

    <el-row :gutter="12">
      <el-col :span="12">
        <div class="macaron-card">
          <h3>班干部</h3>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="班主任">{{ classInfo?.class_teacher || '未指定' }}</el-descriptions-item>
            <el-descriptions-item label="班长">{{ classInfo?.monitor || '未指定' }}</el-descriptions-item>
            <el-descriptions-item label="团支书">{{ classInfo?.league_secretary || '未指定' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="macaron-card">
          <h3>关键指标</h3>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="挂科率">{{ fmtPct(summary?.fail_rate) }}</el-descriptions-item>
            <el-descriptions-item label="已就业签约数">{{ summary?.employed_count ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="心理关注人数">{{ summary?.psych_attention_count ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="奖学金累计金额">{{ fmtMoney(summary?.scholarship_total) }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>

    <!-- v3j-D · D3: 班级档案（口号/办公地点/特色） -->
    <el-divider />
    <div class="macaron-card class-archive">
      <div class="archive-head">
        <h3 style="margin:0">📇 班级档案</h3>
        <el-button size="small" type="primary" @click="openEdit">编辑档案</el-button>
      </div>
      <el-descriptions :column="2" size="small" border style="margin-top:10px">
        <el-descriptions-item label="班级口号">
          <span :class="{ 'archive-empty': !archive.slogan }">{{ archive.slogan || '未填写' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="办公地点">
          <span :class="{ 'archive-empty': !archive.office_location }">{{ archive.office_location || '未填写' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="班级特色" :span="2">
          <div v-if="archive.features" style="white-space: pre-line">{{ archive.features }}</div>
          <span v-else class="archive-empty">未填写（可点击右上「编辑档案」补充班级亮点、荣誉、传统等）</span>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- v3j-D · D3: 档案编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑班级档案" width="600px">
      <el-form :model="editForm" label-width="90px">
        <el-form-item label="班主任">
          <el-input v-model="editForm.class_teacher" />
        </el-form-item>
        <el-form-item label="班长">
          <el-input v-model="editForm.monitor" />
        </el-form-item>
        <el-form-item label="团支书">
          <el-input v-model="editForm.league_secretary" />
        </el-form-item>
        <el-form-item label="班级口号">
          <el-input v-model="editForm.slogan" placeholder="一句话代表班级精神" />
        </el-form-item>
        <el-form-item label="办公地点">
          <el-input v-model="editForm.office_location" placeholder="如：机械楼 302" />
        </el-form-item>
        <el-form-item label="班级特色">
          <el-input v-model="editForm.features" type="textarea" :rows="4" placeholder="班级亮点、荣誉、传统等，多条可换行" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="onEditSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
const props = defineProps({
  cid: { type: Number, required: true },
  classInfo: { type: Object, default: null },
  summary: { type: Object, default: null }
})

// v3j-D · D3: 档案卡片显示 + 编辑
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { updateClassInfo } from '@/api/class360.js'
const archive = reactive({
  slogan: '',
  office_location: '',
  features: '',
})
const syncArchive = () => {
  const src = props.summary || props.classInfo || {}
  archive.slogan = src.slogan || ''
  archive.office_location = src.office_location || ''
  archive.features = src.features || ''
}
watch(() => [props.summary, props.classInfo], syncArchive, { immediate: true, deep: true })

const editVisible = ref(false)
const editSaving = ref(false)
const editForm = reactive({
  class_teacher: '',
  monitor: '',
  league_secretary: '',
  slogan: '',
  office_location: '',
  features: '',
})
const openEdit = () => {
  const src = props.classInfo || props.summary || {}
  editForm.class_teacher = src.class_teacher || ''
  editForm.monitor = src.monitor || ''
  editForm.league_secretary = src.league_secretary || ''
  editForm.slogan = archive.slogan || ''
  editForm.office_location = archive.office_location || ''
  editForm.features = archive.features || ''
  editVisible.value = true
}
const onEditSave = async () => {
  editSaving.value = true
  try {
    const res = await updateClassInfo(props.cid, editForm)
    // 本地同步显示
    archive.slogan = res?.slogan || editForm.slogan
    archive.office_location = res?.office_location || editForm.office_location
    archive.features = res?.features || editForm.features
    // classInfo 反写（下次父组件刷新前先本地看到）
    if (props.classInfo) {
      props.classInfo.class_teacher = editForm.class_teacher
      props.classInfo.monitor = editForm.monitor
      props.classInfo.league_secretary = editForm.league_secretary
      props.classInfo.slogan = editForm.slogan
      props.classInfo.office_location = editForm.office_location
      props.classInfo.features = editForm.features
    }
    ElMessage.success('班级档案已保存')
    editVisible.value = false
  } catch (e) {
    ElMessage.error('保存失败: ' + (e?.message || '未知错误'))
  } finally {
    editSaving.value = false
  }
}


function fmtPct(v) {
  if (v == null) return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return '—'
  return (n > 1 ? n : n * 100).toFixed(1) + '%'
}
function fmtMoney(v) {
  if (v == null) return '—'
  return '¥ ' + Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const colorMap = {
  blue:   '#B7D8E4',
  green:  '#B7E4C7',
  orange: '#F5C7A0',
  red:    '#F8B4B4'
}
function cardStyle(color) {
  const c = colorMap[color] || '#B7D8E4'
  return {
    background: c + '22',
    borderColor: c
  }
}
</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: 14px 12px;
  border-radius: 12px;
  border: 1px solid;
  margin-bottom: 12px;
}
.stat-label { color: #4A7A8C; font-size: 13px; }
.stat-value { font-size: 28px; font-weight: 700; color: #3B6A7C; margin-top: 4px; }
.class-archive { margin-top: 8px; padding: 14px 16px; }
.archive-head { display: flex; justify-content: space-between; align-items: center; }
.archive-empty { color: #C0C4CC; font-style: italic; }
</style>
