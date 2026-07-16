<template>
  <div class="tpl-page">
    <div class="page-header">
      <h2>📄 文档模板</h2>
      <div class="header-actions">
        <el-button :icon="Document" @click="drawerVisible = true">📎 已生成文档</el-button>
        <el-button type="primary" :icon="Plus" @click="onCreate">新建模板</el-button>
      </div>
    </div>

    <div class="hint-bar">
      预置常用文书模板（个人情况说明、家访通知、评优推荐信等），支持变量占位符：
      <code>{{'{{ 姓名 }}'}}</code> <code>{{'{{ 学号 }}'}}</code> <code>{{'{{ 性别 }}'}}</code>
      <code>{{'{{ 专业 }}'}}</code> <code>{{'{{ 班级 }}'}}</code> <code>{{'{{ 政治面貌 }}'}}</code>
      一键根据学生数据生成个性化文书。
    </div>

    <el-empty v-if="!loading && list.length === 0" description="还没有模板，点右上角新建" />

    <div class="tpl-grid" v-loading="loading">
      <div
        v-for="t in list"
        :key="t.id"
        class="tpl-card"
      >
        <div class="tpl-head">
          <el-tag size="small" round>{{ t.template_type || '未分类' }}</el-tag>
        </div>
        <div class="tpl-name">{{ t.name }}</div>
        <div class="tpl-preview">{{ t.content }}</div>
        <div class="tpl-actions">
          <el-button link type="primary" @click="onPreview(t)">👁️ 预览</el-button>
          <el-button link type="primary" @click="onGenerate(t)">✨ 生成文书</el-button>
        </div>
      </div>
    </div>

    <!-- 新建模板对话框 -->
    <el-dialog v-model="dialogVisible" title="新建模板" width="800px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如：家访通知模板" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.template_type" allow-create filterable placeholder="选择或新增" style="width:100%">
            <el-option v-for="t in typeOptions" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板内容" required>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="12"
            placeholder="可使用变量：{{姓名}} {{学号}} {{性别}} {{专业}} {{班级}} {{政治面貌}}"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 预览模板 -->
    <el-dialog v-model="previewVisible" :title="previewTpl?.name || '预览'" width="720px">
      <div class="preview-content">{{ previewTpl?.content }}</div>
    </el-dialog>

    <!-- 生成文书对话框 -->
    <el-dialog v-model="generateVisible" title="生成文书" width="720px">
      <el-form :model="genForm" label-width="80px">
        <el-form-item label="模板">
          <el-input :model-value="genForm.tpl_name" disabled />
        </el-form-item>
        <el-form-item label="选择学生" required>
          <el-select
            v-model="genForm.student_id"
            filterable
            remote
            :remote-method="onSearchStu"
            :loading="stuLoading"
            placeholder="按姓名/学号搜索"
            style="width:100%"
          >
            <el-option
              v-for="s in stuOptions"
              :key="s.id"
              :label="`${s.name} (${s.student_no}) - ${s.class_name || ''}`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="文档标题">
          <el-input v-model="genForm.title" placeholder="留空则用模板名+学生姓名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="onDoGenerate">生成</el-button>
      </template>
    </el-dialog>

    <!-- 已生成文档抽屉 -->
    <el-drawer v-model="drawerVisible" title="📎 已生成文档" size="560px">
      <div v-loading="docLoading">
        <el-empty v-if="documents.length === 0" description="还没有生成过文书" />
        <div v-for="d in documents" :key="d.id" class="doc-item">
          <div class="doc-head">
            <span class="doc-title">{{ d.title }}</span>
            <el-tag v-if="d.student_name" size="small" round>{{ d.student_name }}</el-tag>
          </div>
          <div class="doc-time">{{ formatDate(d.created_at) }}</div>
          <div class="doc-preview">{{ d.content }}</div>
          <div class="doc-actions">
            <el-button link type="primary" @click="onViewDoc(d)">📖 查看全文</el-button>
            <el-button link type="danger" @click="onDeleteDoc(d)">🗑️ 删除</el-button>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 查看/编辑生成文档 -->
    <el-dialog v-model="docViewVisible" :title="docViewData?.title || '文档'" width="800px">
      <el-input
        v-if="docViewData"
        v-model="docViewData.content"
        type="textarea"
        :rows="20"
      />
      <template #footer>
        <el-button @click="docViewVisible = false">关闭</el-button>
        <el-button type="primary" @click="onSaveDoc">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document } from '@element-plus/icons-vue'
import { templatesApi, documentsApi } from '@/api/knowledge.js'
import { searchStudents } from '@/api/students.js'

const list = ref([])
const loading = ref(false)
const saving = ref(false)

const typeOptions = ['个人情况说明', '家访通知', '评优推荐信', '奖学金申请', '党员发展', '证明信', '其他']

const dialogVisible = ref(false)
const form = ref({ name: '', template_type: '', content: '' })

const previewVisible = ref(false)
const previewTpl = ref(null)

// 生成文书
const generateVisible = ref(false)
const generating = ref(false)
const genForm = ref({ tpl_id: null, tpl_name: '', student_id: null, title: '' })
const stuOptions = ref([])
const stuLoading = ref(false)

// 已生成文档
const drawerVisible = ref(false)
const documents = ref([])
const docLoading = ref(false)

const docViewVisible = ref(false)
const docViewData = ref(null)

async function load() {
  loading.value = true
  try {
    list.value = await templatesApi.list() || []
  } catch (e) {
    list.value = []
  }
  loading.value = false
}

function onCreate() {
  form.value = { name: '', template_type: '', content: '' }
  dialogVisible.value = true
}

async function onSave() {
  if (!form.value.name?.trim() || !form.value.content?.trim()) {
    ElMessage.warning('名称和内容不能为空')
    return
  }
  saving.value = true
  try {
    await templatesApi.create({
      name: form.value.name,
      template_type: form.value.template_type || '其他',
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

function onPreview(t) {
  previewTpl.value = t
  previewVisible.value = true
}

function onGenerate(t) {
  genForm.value = { tpl_id: t.id, tpl_name: t.name, student_id: null, title: '' }
  stuOptions.value = []
  generateVisible.value = true
}

async function onSearchStu(kw) {
  if (!kw) { stuOptions.value = []; return }
  stuLoading.value = true
  try {
    const res = await searchStudents(kw, 20)
    stuOptions.value = Array.isArray(res) ? res : (res?.items || [])
  } catch (e) {
    stuOptions.value = []
  }
  stuLoading.value = false
}

async function onDoGenerate() {
  if (!genForm.value.student_id) {
    ElMessage.warning('请选择学生')
    return
  }
  const stu = stuOptions.value.find(s => s.id === genForm.value.student_id)
  const title = genForm.value.title || `${genForm.value.tpl_name} - ${stu?.name || ''}`
  generating.value = true
  try {
    const res = await documentsApi.generate({
      template_id: genForm.value.tpl_id,
      student_id: genForm.value.student_id,
      title,
      doc_type: '',
    })
    ElMessage.success('已生成，可在"已生成文档"中查看')
    generateVisible.value = false
    // 直接打开查看
    const doc = await documentsApi.get(res.id)
    docViewData.value = doc
    docViewVisible.value = true
  } catch (e) {
    ElMessage.error('生成失败')
  }
  generating.value = false
}

async function loadDocuments() {
  docLoading.value = true
  try {
    documents.value = await documentsApi.list() || []
  } catch (e) {
    documents.value = []
  }
  docLoading.value = false
}

async function onViewDoc(d) {
  try {
    docViewData.value = await documentsApi.get(d.id)
    docViewVisible.value = true
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

async function onSaveDoc() {
  if (!docViewData.value?.id) return
  try {
    await documentsApi.update(docViewData.value.id, { content: docViewData.value.content })
    ElMessage.success('已保存')
    docViewVisible.value = false
    await loadDocuments()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function onDeleteDoc(d) {
  try {
    await ElMessageBox.confirm(`确认删除「${d.title}」？`, '确认', { type: 'warning' })
    await documentsApi.remove(d.id)
    ElMessage.success('已删除')
    await loadDocuments()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function formatDate(s) {
  if (!s) return ''
  return String(s).slice(0, 16)
}

import { watch } from 'vue'
watch(drawerVisible, (v) => { if (v) loadDocuments() })

onMounted(load)
</script>

<style scoped>
.tpl-page { padding: 20px; }
.page-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
}
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 12px; align-items: center; }
.hint-bar {
  background: #EEF3F5; color: #5C7A87; padding: 8px 14px;
  border-radius: 8px; font-size: 13px; margin-bottom: 16px; line-height: 1.8;
}
.hint-bar code {
  background: #DCEBF0; padding: 2px 6px; border-radius: 4px;
  font-family: monospace; color: #3B6A7C; margin: 0 2px;
}
.tpl-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;
}
.tpl-card {
  background: #fff; border: 1px solid #E4E7ED; border-radius: 10px;
  padding: 14px 16px; display: flex; flex-direction: column; min-height: 180px;
  transition: all .18s;
}
.tpl-card:hover { box-shadow: 0 4px 16px rgba(74,122,140,.15); transform: translateY(-1px); }
.tpl-head { margin-bottom: 8px; }
.tpl-name { font-weight: 600; font-size: 15px; color: #303133; margin-bottom: 8px; }
.tpl-preview {
  color: #909399; font-size: 12px; line-height: 1.6; flex: 1;
  display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
  background: #FAFBFC; padding: 8px; border-radius: 4px;
}
.tpl-actions { display: flex; gap: 8px; margin-top: 10px; }
.preview-content { white-space: pre-wrap; line-height: 1.75; padding: 12px; background: #FAFBFC; border-radius: 6px; }
.doc-item {
  background: #fff; border: 1px solid #EBEEF5; border-radius: 8px;
  padding: 12px; margin-bottom: 12px;
}
.doc-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.doc-title { font-weight: 600; color: #303133; }
.doc-time { color: #909399; font-size: 12px; margin-bottom: 6px; }
.doc-preview {
  color: #606266; font-size: 13px; line-height: 1.6; padding: 6px 0;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.doc-actions { display: flex; gap: 8px; padding-top: 6px; }
</style>
