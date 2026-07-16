<template>
  <div class="kb-page">
    <div class="page-header">
      <h2>📚 知识库</h2>
      <div class="header-actions">
        <el-select v-model="typeFilter" placeholder="全部分类" clearable style="width:180px" @change="load">
          <el-option v-for="t in typeOptions" :key="t" :label="t" :value="t" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="onCreate">新建条目</el-button>
      </div>
    </div>

    <div class="hint-bar">
      辅导员日常工作参考：政策文件、工作手册、答疑话术、学生管理经验沉淀。
    </div>

    <el-empty v-if="!loading && filteredList.length === 0" description="还没有知识库条目，点右上角新建" />

    <div class="kb-grid" v-loading="loading">
      <div
        v-for="d in filteredList"
        :key="d.id"
        class="kb-card"
        @click="onView(d)"
      >
        <div class="kb-card-head">
          <el-tag size="small" round>{{ d.doc_type || '未分类' }}</el-tag>
          <span class="kb-time">{{ formatDate(d.created_at) }}</span>
        </div>
        <div class="kb-title">{{ d.title }}</div>
        <div class="kb-content">{{ d.content }}</div>
        <div class="kb-actions" @click.stop>
          <el-button link type="primary" @click="onView(d)">📖 查看</el-button>
          <el-button link type="danger" @click="onDelete(d)">🗑️ 删除</el-button>
        </div>
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '知识库条目' : '新建知识库条目'" width="720px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="如：奖学金评定办法（2024版）" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.doc_type" allow-create filterable placeholder="选择或新增分类" style="width:100%">
            <el-option v-for="t in typeOptions" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="form.content" type="textarea" :rows="12" placeholder="可粘贴政策文件、工作手册、话术等纯文本内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看对话框 -->
    <el-dialog v-model="viewVisible" :title="viewData?.title || '查看'" width="800px">
      <div class="view-meta">
        <el-tag size="small" round>{{ viewData?.doc_type || '未分类' }}</el-tag>
      </div>
      <div class="view-content">{{ viewData?.content }}</div>
      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api/knowledge.js'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const typeFilter = ref('')

const typeOptions = ['政策文件', '工作手册', '答疑话术', '经验沉淀', '通知模板', '其他']

const dialogVisible = ref(false)
const form = ref({ id: null, title: '', doc_type: '', content: '' })

const viewVisible = ref(false)
const viewData = ref(null)

const filteredList = computed(() => {
  if (!typeFilter.value) return list.value
  return list.value.filter(d => d.doc_type === typeFilter.value)
})

async function load() {
  loading.value = true
  try {
    list.value = await knowledgeApi.list() || []
  } catch (e) {
    list.value = []
  }
  loading.value = false
}

function onCreate() {
  form.value = { id: null, title: '', doc_type: '', content: '' }
  dialogVisible.value = true
}

async function onView(d) {
  try {
    viewData.value = await knowledgeApi.get(d.id)
    viewVisible.value = true
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

async function onSave() {
  if (!form.value.title?.trim() || !form.value.content?.trim()) {
    ElMessage.warning('标题和内容不能为空')
    return
  }
  saving.value = true
  try {
    await knowledgeApi.create({
      title: form.value.title,
      doc_type: form.value.doc_type || '其他',
      content: form.value.content,
    })
    ElMessage.success('已保存')
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error('保存失败')
  }
  saving.value = false
}

async function onDelete(d) {
  try {
    await ElMessageBox.confirm(`确认删除「${d.title}」？`, '确认', { type: 'warning' })
    await knowledgeApi.remove(d.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function formatDate(s) {
  if (!s) return ''
  return String(s).slice(0, 10)
}

onMounted(load)
</script>

<style scoped>
.kb-page { padding: 20px; }
.page-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
}
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 12px; align-items: center; }
.hint-bar {
  background: #EEF3F5; color: #5C7A87; padding: 8px 14px;
  border-radius: 8px; font-size: 13px; margin-bottom: 16px;
}
.kb-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;
}
.kb-card {
  background: #fff; border: 1px solid #E4E7ED; border-radius: 10px;
  padding: 14px 16px; cursor: pointer; transition: all .18s;
  display: flex; flex-direction: column; min-height: 160px;
}
.kb-card:hover { box-shadow: 0 4px 16px rgba(74,122,140,.15); transform: translateY(-1px); }
.kb-card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.kb-time { color: #909399; font-size: 12px; }
.kb-title { font-weight: 600; font-size: 15px; color: #303133; margin-bottom: 6px; }
.kb-content {
  color: #606266; font-size: 13px; line-height: 1.6;
  flex: 1; overflow: hidden;
  display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical;
}
.kb-actions { display: flex; gap: 8px; margin-top: 10px; padding-top: 10px; border-top: 1px dashed #EBEEF5; }
.view-meta { margin-bottom: 12px; }
.view-content {
  white-space: pre-wrap; line-height: 1.75; color: #303133;
  max-height: 60vh; overflow-y: auto; padding: 12px;
  background: #FAFBFC; border-radius: 6px;
}
</style>
