<template>
  <div class="faq-page">
    <div class="page-header">
      <h2>FAQ 常见问题</h2>
      <div class="header-actions">
        <el-select v-model="categoryFilter" placeholder="全部分类" clearable style="width:180px">
          <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
        </el-select>
        <el-radio-group v-model="publishFilter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="published">已发布</el-radio-button>
          <el-radio-button label="draft">草稿</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :icon="Plus" @click="onCreate">新建 FAQ</el-button>
        <el-dropdown @command="onExport" style="margin-left:8px">
          <el-button :icon="Download">导出</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="excel">导出 Excel</el-dropdown-item>
              <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
              <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="hint-bar">
      沉淀学生常问的问题，让答疑话术可复用。发布后可用于自动回复参考。
    </div>

    <el-empty v-if="!loading && filteredList.length === 0" description="还没有 FAQ 条目，点右上角新建" />

    <el-collapse v-model="activeIds" v-loading="loading" class="faq-collapse">
      <el-collapse-item v-for="f in filteredList" :key="f.id" :name="String(f.id)">
        <template #title>
          <div class="faq-title-row">
            <el-tag v-if="f.category" size="small" round type="info">{{ f.category }}</el-tag>
            <el-tag v-if="!f.is_published" size="small" round type="warning">草稿</el-tag>
            <el-tag v-else size="small" round type="success">已发布</el-tag>
            <span class="faq-q">{{ f.question }}</span>
          </div>
        </template>
        <div class="faq-answer">{{ f.answer }}</div>
        <div class="faq-actions">
          <el-button link type="primary" @click="onEdit(f)">✏️ 编辑</el-button>
          <el-button link :type="f.is_published ? 'warning' : 'primary'" @click="onTogglePublish(f)">
            {{ f.is_published ? '⬇️ 撤回草稿' : '⬆️ 发布' }}
          </el-button>
          <el-button link type="danger" @click="onDelete(f)">🗑️ 删除</el-button>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑 FAQ' : '新建 FAQ'" width="720px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="分类">
          <el-select v-model="form.category" allow-create filterable placeholder="选择或新增" style="width:100%">
            <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题" required>
          <el-input v-model="form.question" placeholder="学生常问的问题" />
        </el-form-item>
        <el-form-item label="答案" required>
          <el-input v-model="form.answer" type="textarea" :rows="8" placeholder="标准回答话术" />
        </el-form-item>
        <el-form-item label="发布">
          <el-switch v-model="form.is_published" active-text="已发布" inactive-text="草稿" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import { faqsApi } from '@/api/knowledge.js'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const categoryFilter = ref('')
const publishFilter = ref('all')
const activeIds = ref([])

const categoryOptions = ['奖学金', '助学金', '宿舍', '选课', '毕业', '就业', '心理', '党团', '其他']

const dialogVisible = ref(false)
const form = ref({ id: null, category: '', question: '', answer: '', is_published: true })

const filteredList = computed(() => {
  let arr = list.value
  if (categoryFilter.value) arr = arr.filter(f => f.category === categoryFilter.value)
  if (publishFilter.value === 'published') arr = arr.filter(f => f.is_published)
  else if (publishFilter.value === 'draft') arr = arr.filter(f => !f.is_published)
  return arr
})

async function load() {
  loading.value = true
  try {
    list.value = await faqsApi.list() || []
  } catch (e) {
    list.value = []
  }
  loading.value = false
}

function onCreate() {
  form.value = { id: null, category: '', question: '', answer: '', is_published: true }
  dialogVisible.value = true
}

function onEdit(f) {
  form.value = { id: f.id, category: f.category || '', question: f.question, answer: f.answer, is_published: !!f.is_published }
  dialogVisible.value = true
}

async function onSave() {
  if (!form.value.question?.trim() || !form.value.answer?.trim()) {
    ElMessage.warning('问题和答案不能为空')
    return
  }
  saving.value = true
  try {
    const payload = {
      category: form.value.category || '其他',
      question: form.value.question,
      answer: form.value.answer,
      is_published: !!form.value.is_published,
    }
    if (form.value.id) {
      await faqsApi.update(form.value.id, payload)
    } else {
      await faqsApi.create(payload)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error('保存失败')
  }
  saving.value = false
}

async function onTogglePublish(f) {
  try {
    await faqsApi.update(f.id, { is_published: !f.is_published })
    ElMessage.success(f.is_published ? '已撤回为草稿' : '已发布')
    await load()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function onDelete(f) {
  try {
    await ElMessageBox.confirm(`确认删除该 FAQ？`, '确认', { type: 'warning' })
    await faqsApi.remove(f.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function onExport(format) {
  const url = `/api/faqs/export?format=${format}`
  if (format === 'json') {
    fetch(url).then(r => r.json()).then(data => {
      const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'})
      downloadBlob(blob, `FAQ导出_${new Date().toISOString().slice(0,10)}.json`)
    })
  } else {
    window.open(url, '_blank')
  }
}
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<style scoped>
.faq-page { padding: 20px; }
.page-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
}
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.hint-bar {
  background: #EEF3F5; color: #5C7A87; padding: 8px 14px;
  border-radius: 8px; font-size: 13px; margin-bottom: 16px;
}
.faq-collapse { background: #fff; border-radius: 10px; padding: 4px 16px; }
.faq-title-row { display: flex; gap: 8px; align-items: center; flex: 1; }
.faq-q { font-weight: 500; color: #303133; }
.faq-answer {
  white-space: pre-wrap; line-height: 1.75; color: #606266;
  background: #FAFBFC; border-radius: 6px; padding: 12px; margin-bottom: 12px;
}
.faq-actions { display: flex; gap: 8px; padding-top: 4px; }
</style>
