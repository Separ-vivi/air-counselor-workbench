<template>
  <div class="smart-import">
    <div class="inline-back-bar">
      <el-button link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span style="margin-left:4px;font-weight:500">返回</span>
      </el-button>
    </div>
    <div class="page-header">
      <h2>智能导入</h2>
      <p class="sub">支持 6 种台账类型 · 3 步走完成 · 自动字段映射 + 冲突策略</p>
    </div>

    <el-alert type="info" :closable="false" style="margin-bottom:16px">
      <template #title>
        <span style="margin-right:12px">📎 需要模板？</span>
        <el-button size="small" type="primary" plain @click="downloadTemplate('students')">花名册模板</el-button>
        <el-button size="small" type="primary" plain @click="downloadTemplate('grades_wide')">成绩单模板(宽表·推荐)</el-button>
        <el-button size="small" type="primary" plain @click="downloadTemplate('grades')">成绩单模板(长表)</el-button>
        <el-button size="small" type="primary" plain @click="downloadTemplate('party')">党团发展模板</el-button>
      </template>
    </el-alert>

    <el-card shadow="never">
      <el-steps :active="step" simple finish-status="success" style="margin-bottom: 24px">
        <el-step title="选择类型 & 上传文件" icon="Upload" />
        <el-step title="预览 & 字段映射" icon="Reading" />
        <el-step title="确认导入" icon="Check" />
      </el-steps>

      <!-- Step 1 -->
      <div v-if="step === 0">
        <el-form label-width="140px" style="max-width: 720px; margin: 0 auto">
          <el-form-item label="数据类型" required>
            <el-radio-group v-model="dataType">
              <el-radio-button v-for="t in dataTypes" :key="t.key" :value="t.key">{{ t.icon }} {{ t.label }}</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="冲突策略">
            <el-radio-group v-model="conflictStrategy">
              <el-radio value="skip">跳过重复</el-radio>
              <el-radio value="update">更新覆盖</el-radio>
              <el-radio value="error">遇冲突报错</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="上传文件">
            <el-upload
              ref="uploadRef"
              drag
              :auto-upload="false"
              :on-change="onFileChange"
              :on-remove="onFileRemove"
              :file-list="fileList"
              :limit="1"
              accept=".xlsx,.xls,.csv"
              :on-exceed="() => ElMessage.warning('每次仅可上传 1 个文件；如需换文件请先点清除已上传')"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">拖拽文件到此处，或 <em>点击选择</em></div>
              <template #tip>
                <div class="el-upload__tip">支持 .xlsx / .xls / .csv；宽表(每列一门课)和长表都能识别</div>
              </template>
            </el-upload>
            <el-button v-if="file" size="small" style="margin-top:8px" @click="clearFileBtn">🗑 清除已上传文件</el-button>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="detecting" :disabled="!file || !dataType" @click="doDetect">下一步 · 智能识别</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Step 2 -->
      <div v-if="step === 1">
        <el-alert
          v-if="detectResult?.warnings?.length"
          :title="'检测警告：' + detectResult.warnings.join('；')"
          type="warning"
          show-icon
          style="margin-bottom: 12px"
        />
        <el-descriptions :column="4" size="small" border style="margin-bottom: 12px">
          <el-descriptions-item label="数据类型">{{ typeLabel(dataType) }}</el-descriptions-item>
          <el-descriptions-item label="总行数">{{ detectResult?.total_rows ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="有效行">{{ detectResult?.valid_rows ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="Import ID">{{ detectResult?.import_id || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 12px 0">字段映射（源 → 目标）</h4>
        <el-table :data="mapping" border stripe size="small">
          <el-table-column label="源列名（文件表头）" prop="source" min-width="200" />
          <el-table-column label="示例值" prop="sample" min-width="180" show-overflow-tooltip />
          <el-table-column label="→ 目标字段" width="260">
            <template #default="{ row }">
              <el-select v-model="row.target" clearable filterable placeholder="选择目标字段" style="width: 100%">
                <el-option v-for="f in targetFields" :key="f.key" :label="`${f.label}（${f.key}）`" :value="f.key" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="必填" prop="required" width="70" align="center">
            <template #default="{ row }">
              <el-tag v-if="isRequired(row.target)" size="small" type="danger">必填</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <h4 style="margin: 20px 0 12px">预览前 5 行</h4>
        <el-table :data="previewRows" border stripe size="small">
          <el-table-column v-for="h in previewHeaders" :key="h" :label="h" :prop="h" show-overflow-tooltip />
        </el-table>

        <div style="text-align: right; margin-top: 16px">
          <el-button @click="step = 0">上一步</el-button>
          <el-button type="primary" :loading="confirming" @click="doConfirm">下一步 · 确认导入</el-button>
        </div>
      </div>

      <!-- Step 3 -->
      <div v-if="step === 2">
        <el-result
          :icon="importResult?.success === false ? 'error' : 'success'"
          :title="importResult?.success === false ? '导入失败' : '导入完成'"
          :sub-title="resultSubTitle"
        >
          <template #extra>
            <el-button type="primary" @click="reset">再导入一批</el-button>
            <el-button @click="$router.push('/students')">前往学生列表</el-button>
          </template>
        </el-result>

        <el-descriptions v-if="importResult" :column="3" border size="small" style="margin-top: 12px">
          <el-descriptions-item label="总行数">{{ importResult.total ?? importResult.total_rows ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="成功">{{ importResult.success_count ?? importResult.imported ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="失败">{{ importResult.fail_count ?? importResult.failed ?? '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="importResult?.errors?.length" style="margin-top: 16px">
          <h4>错误明细</h4>
          <el-table :data="importResult.errors.slice(0, 50)" border stripe size="small">
            <el-table-column label="行号" prop="row" width="80" />
            <el-table-column label="错误信息" prop="message" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, ArrowLeft } from '@element-plus/icons-vue'
import { detectFile, confirmImport } from '@/api/smartImport'

const router = useRouter()
const goBack = () => { if (window.history.length > 1) router.back(); else router.push('/') }
const downloadTemplate = (type) => {
  const url = `/api/import/template?type=${type}`
  window.open(url, '_blank')
}
const onFileRemove = () => { file.value = null; fileList.value = [] }
const clearFileBtn = () => {
  file.value = null
  fileList.value = []
  uploadRef.value && uploadRef.value.clearFiles && uploadRef.value.clearFiles()
  ElMessage.success('已清除，可重新选择文件')
}

const uploadRef = ref(null)
const step = ref(0)
const dataType = ref('students')
const conflictStrategy = ref('skip')
const file = ref(null)
const fileList = ref([])
const detecting = ref(false)
const confirming = ref(false)

const dataTypes = [
  { key: 'students',      label: '花名册',         icon: '📋' },
  { key: 'grades',        label: '成绩单',         icon: '📊' },
  { key: 'party',         label: '党团发展',       icon: '🚩' },
  { key: 'hardship',      label: '资助/困难认定', icon: '💰' },
  { key: 'scholarship',   label: '奖助学金',       icon: '🏅' },
  { key: 'honor',         label: '评优荣誉',       icon: '🌟' }
]

// 各类型对应的目标字段（覆盖核心字段，供映射下拉）
const fieldMap = {
  students: [
    { key: 'student_no', label: '学号', required: true },
    { key: 'name', label: '姓名', required: true },
    { key: 'gender', label: '性别' },
    { key: 'class_name', label: '班级' },
    { key: 'major', label: '专业' },
    { key: 'grade', label: '年级' },
    { key: 'birth_date', label: '出生日期' },
    { key: 'political_status', label: '政治面貌' },
    { key: 'phone', label: '电话' },
    { key: 'email', label: '邮箱' },
    { key: 'parent_phone', label: '家长电话' },
    { key: 'birth_source', label: '生源地' },
    { key: 'notes', label: '备注' }
  ],
  grades: [
    { key: 'student_no', label: '学号', required: true },
    { key: 'course_name', label: '课程名' },
    { key: 'course_code', label: '课程代码' },
    { key: 'credit', label: '学分' },
    { key: 'score', label: '分数' },
    { key: 'grade_level', label: '成绩等级' },
    { key: 'semester', label: '学期' },
    { key: 'is_makeup', label: '是否重修' }
  ],
  party: [
    { key: 'student_no', label: '学号', required: true },
    { key: 'stage', label: '发展阶段', required: true },
    { key: 'stage_date', label: '阶段日期' },
    { key: 'contact_person', label: '联系人' },
    { key: 'notes', label: '备注' }
  ],
  hardship: [
    { key: 'student_no', label: '学号', required: true },
    { key: 'hardship_level', label: '困难等级', required: true },
    { key: 'school_year', label: '学年' },
    { key: 'family_situation', label: '家庭情况' }
  ],
  scholarship: [
    { key: 'student_no', label: '学号', required: true },
    { key: 'scholarship_name', label: '奖学金名称', required: true },
    { key: 'level', label: '等级' },
    { key: 'amount', label: '金额' },
    { key: 'school_year', label: '学年' }
  ],
  honor: [
    { key: 'student_no', label: '学号', required: true },
    { key: 'honor_name', label: '荣誉名称', required: true },
    { key: 'honor_level', label: '级别' },
    { key: 'award_date', label: '获奖日期' },
    { key: 'granting_org', label: '颁发单位' }
  ]
}
const targetFields = computed(() => fieldMap[dataType.value] || [])
const isRequired = (key) => targetFields.value.find((f) => f.key === key)?.required === true

const detectResult = ref(null)
const mapping = ref([])
const previewRows = ref([])
const previewHeaders = ref([])
const importResult = ref(null)

const typeLabel = (k) => dataTypes.find((t) => t.key === k)?.label || k

const resultSubTitle = computed(() => {
  if (!importResult.value) return ''
  if (importResult.value.success === false) return importResult.value.message || '请检查错误明细'
  const s = importResult.value.success_count ?? importResult.value.imported ?? 0
  const f = importResult.value.fail_count ?? importResult.value.failed ?? 0
  return `成功 ${s} 条，失败 ${f} 条`
})

const onFileChange = (uploadFile) => {
  file.value = uploadFile.raw
  fileList.value = [uploadFile]
}

const doDetect = async () => {
  if (!file.value) return ElMessage.warning('请先选择文件')
  detecting.value = true
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    fd.append('data_type', dataType.value)
    const res = await detectFile(fd)
    detectResult.value = res || {}
    // 兼容不同结构
    const headers = res?.headers || res?.columns || (res?.preview?.[0] ? Object.keys(res.preview[0]) : [])
    const samples = res?.samples || {}
    const suggested = res?.suggested_mapping || res?.mapping || {}
    mapping.value = headers.map((h) => ({
      source: h,
      sample: samples[h] || (res?.preview?.[0]?.[h] ?? ''),
      target: suggested[h] || guessMapping(h)
    }))
    previewHeaders.value = headers
    previewRows.value = (res?.preview || []).slice(0, 5)
    step.value = 1
  } finally {
    detecting.value = false
  }
}

/** 简单启发：源列名包含关键字则直接匹配 */
const guessMapping = (h) => {
  const s = (h || '').toLowerCase()
  for (const f of targetFields.value) {
    if (s.includes(f.key) || (f.label && h.includes(f.label))) return f.key
  }
  return ''
}

const doConfirm = async () => {
  // 检查必填字段是否已映射
  const mapped = new Set(mapping.value.map((m) => m.target).filter(Boolean))
  const missing = targetFields.value.filter((f) => f.required && !mapped.has(f.key))
  if (missing.length) {
    return ElMessage.error('以下必填字段未映射：' + missing.map((f) => f.label).join('、'))
  }
  confirming.value = true
  try {
    const payload = {
      data_type: dataType.value,
      mapping: mapping.value
        .filter((m) => m.target)
        .map((m) => ({ source: m.source, target: m.target })),
      conflict_strategy: conflictStrategy.value,
      import_id: detectResult.value?.import_id
    }
    const res = await confirmImport(payload)
    importResult.value = res || { success: true }
    step.value = 2
  } finally {
    confirming.value = false
  }
}

const reset = () => {
  step.value = 0
  file.value = null
  fileList.value = []
  detectResult.value = null
  mapping.value = []
  previewRows.value = []
  previewHeaders.value = []
  importResult.value = null
  uploadRef.value?.clearFiles?.()
}
</script>

<style scoped>
.smart-import { padding: 4px; }
.inline-back-bar { margin-bottom: 8px; padding: 4px 0; }
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.page-header .sub { color: #909399; margin: 4px 0 0; font-size: 13px; }
</style>
