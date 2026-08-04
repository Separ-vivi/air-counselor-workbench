<template>
  <div class="kb-page">
    <el-tabs v-model="activeTab" class="kb-tabs">
      <!-- ========== Tab 1: 文档工具箱 ========== -->
      <el-tab-pane label="文档工具箱" name="docbox">
        <div class="page-header">
          <h2>文档工具箱</h2>
          <div class="header-actions">
            <el-input
              v-model="searchText"
              placeholder="搜索文档名称…"
              :prefix-icon="Search"
              clearable
              style="width: 200px"
              @input="onSearch"
            />
            <el-button type="primary" :icon="Upload" @click="triggerUpload">上传文档</el-button>
            <el-button :icon="Link" @click="showAddLink = true">添加链接</el-button>
          </div>
        </div>

        <!-- 分类卡片区域 -->
        <div v-loading="loading" class="categories-grid">
          <div
            v-for="(cat, catKey) in categoryOrder"
            :key="catKey"
            class="category-card"
          >
            <div class="cat-header">
              <div class="cat-title-row">
                <span class="cat-icon">{{ catIcons[catKey] }}</span>
                <span class="cat-name">{{ catNames[catKey] }}</span>
                <el-tag size="small" round type="info">{{ getCategoryCount(catKey) }}</el-tag>
              </div>
            </div>
            <div class="cat-body">
              <div v-if="getCategoryDocs(catKey).length === 0" class="cat-empty">
                暂无文档
              </div>
              <div
                v-for="doc in getCategoryDocs(catKey)"
                :key="doc.id"
                class="doc-item"
                @click="onDocClick(doc)"
              >
                <div class="doc-icon-col">
                  <el-icon :size="28" :color="docTypeColors[doc.doc_type] || '#909399'">
                    <component :is="docTypeIcons[doc.doc_type] || Document" />
                  </el-icon>
                </div>
                <div class="doc-info-col">
                  <div class="doc-title">{{ doc.title }}</div>
                  <div class="doc-meta">
                    <span v-if="doc.page_count" class="meta-item">{{ doc.page_count }}页</span>
                    <span v-if="doc.file_size_str" class="meta-item">{{ doc.file_size_str }}</span>
                    <span class="meta-item">{{ doc.created_at }}</span>
                  </div>
                </div>
                <div class="doc-actions-col">
                  <el-dropdown trigger="click" @command="(cmd) => onDocAction(cmd, doc)">
                    <el-button text size="small" :icon="MoreFilled" @click.stop />
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="preview" :icon="View">预览/下载</el-dropdown-item>
                        <el-dropdown-item command="move" :icon="FolderOpened">移动分类</el-dropdown-item>
                        <el-dropdown-item command="delete" :icon="Delete" divided>删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 隐藏文件 input -->
        <input ref="fileInput" type="file" style="display:none"
          accept=".pdf,.docx,.doc,.xlsx,.xls,.txt,.csv"
          @change="onFileSelected"
        >

        <!-- 上传时选择分类弹窗 -->
        <el-dialog v-model="showUploadDialog" title="上传文档" width="480px">
          <el-form label-width="80px">
            <el-form-item label="文件">
              <el-input :model-value="uploadFileName" disabled />
            </el-form-item>
            <el-form-item label="分类">
              <el-select v-model="uploadCategory" style="width: 100%">
                <el-option v-for="(name, key) in catNames" :key="key" :label="name" :value="key" />
              </el-select>
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="uploadDesc" type="textarea" :rows="2" placeholder="可选" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showUploadDialog = false">取消</el-button>
            <el-button type="primary" :loading="uploading" @click="doUpload">确认上传</el-button>
          </template>
        </el-dialog>

        <!-- 添加链接弹窗 -->
        <el-dialog v-model="showAddLink" title="添加链接" width="480px">
          <el-form label-width="80px">
            <el-form-item label="标题" required>
              <el-input v-model="linkForm.title" placeholder="如：假期离校登记" />
            </el-form-item>
            <el-form-item label="链接" required>
              <el-input v-model="linkForm.link_url" placeholder="https://..." />
            </el-form-item>
            <el-form-item label="分类">
              <el-select v-model="linkForm.category" style="width: 100%">
                <el-option v-for="(name, key) in catNames" :key="key" :label="name" :value="key" />
              </el-select>
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="linkForm.description" type="textarea" :rows="2" placeholder="可选" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showAddLink = false">取消</el-button>
            <el-button type="primary" :loading="addingLink" @click="doAddLink">添加</el-button>
          </template>
        </el-dialog>

        <!-- 移动分类弹窗 -->
        <el-dialog v-model="showMoveDialog" title="移动分类" width="400px">
          <el-form label-width="80px">
            <el-form-item label="文档">
              <el-input :model-value="moveDoc?.title" disabled />
            </el-form-item>
            <el-form-item label="新分类">
              <el-select v-model="moveCategory" style="width: 100%">
                <el-option v-for="(name, key) in catNames" :key="key" :label="name" :value="key" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showMoveDialog = false">取消</el-button>
            <el-button type="primary" @click="doMove">确认</el-button>
          </template>
        </el-dialog>

        <!-- 文档详情/预览弹窗 -->
        <el-dialog v-model="showPreview" :title="previewDoc?.title || '文档预览'" width="90%" top="3vh"
          :close-on-click-modal="false" class="preview-dialog"
        >
          <div v-if="previewDoc" class="preview-container">
            <div class="preview-meta">
              <el-tag size="small" round>{{ catNames[previewDoc.category] }}</el-tag>
              <el-tag v-if="previewDoc.doc_type" size="small" round type="info">{{ previewDoc.doc_type.toUpperCase() }}</el-tag>
              <span v-if="previewDoc.page_count" class="meta-text">{{ previewDoc.page_count }}页</span>
              <span v-if="previewDoc.file_size_str" class="meta-text">{{ previewDoc.file_size_str }}</span>
              <span class="meta-text">{{ previewDoc.created_at }}</span>
            </div>
            <!-- PDF内嵌预览 -->
            <div v-if="previewDoc.doc_type === 'pdf'" class="preview-iframe-wrap">
              <iframe :src="docboxApi.preview(previewDoc.id)" class="preview-iframe" />
            </div>
            <!-- 链接类 -->
            <div v-else-if="previewDoc.doc_type === 'link'" class="preview-link">
              <el-link type="primary" :href="previewDoc.link_url" target="_blank" :icon="Link">
                {{ previewDoc.link_url }}
              </el-link>
              <p class="link-hint">点击链接在新窗口打开</p>
            </div>
            <!-- 其他类型：显示全文 + 下载按钮 -->
            <div v-else class="preview-text">
              <el-scrollbar max-height="60vh">
                <pre class="doc-full-text">{{ previewDoc.full_text || '（无法提取文本内容，请下载查看）' }}</pre>
              </el-scrollbar>
            </div>
            <div class="preview-footer">
              <el-button v-if="previewDoc.doc_type !== 'link'" type="primary" @click="downloadDoc(previewDoc)">
                <el-icon><Download /></el-icon> 下载文件
              </el-button>
            </div>
          </div>
        </el-dialog>
      </el-tab-pane>

      <!-- ========== Tab 2: AI 文档助手 ========== -->
      <el-tab-pane label="AI 文档助手" name="ai">
        <div class="page-header">
          <h2>AI 文档助手</h2>
          <div class="header-actions">
            <el-tag :type="llmConfigured ? 'success' : 'warning'" effect="plain" round>
              <el-icon v-if="llmConfigured" style="vertical-align:-2px;margin-right:4px"><CircleCheck /></el-icon>
              <el-icon v-else style="vertical-align:-2px;margin-right:4px"><Warning /></el-icon>
              {{ llmConfigured ? 'AI 已接入' : '未配置 AI' }}
            </el-tag>
            <el-button text type="primary" @click="showLlmTip = true">如何配置？</el-button>
          </div>
        </div>

        <div class="ai-layout">
          <!-- 左侧：AI对话 -->
          <div class="ai-chat-panel">
            <div class="col-head">
              <span class="col-title">AI 对话</span>
              <div class="col-head-actions">
                <el-tag v-if="aiChatList.length" size="small" round type="info">
                  {{ aiChatList.filter(m => m.role === 'user').length }} 轮
                </el-tag>
                <el-button size="small" text @click="aiChatList = []">清空</el-button>
              </div>
            </div>

            <div v-loading="aiChatLoading" class="chat-area" ref="chatAreaRef">
              <div v-if="aiChatList.length === 0" class="chat-empty">
                <div class="empty-icon-big">🤖</div>
                <div class="empty-title">AI 文档助手</div>
                <div class="empty-desc">基于完整文档回答，引用具体章节</div>
                <div class="empty-suggests">
                  <div class="empty-suggest" v-for="q in aiSuggestions" :key="q" @click="onAiAsk(q)">
                    <span class="suggest-icon">💡</span>
                    <span>{{ q }}</span>
                  </div>
                </div>
              </div>
              <div v-for="(m, i) in aiChatList" :key="i" class="chat-msg" :class="m.role">
                <div class="msg-avatar">
                  <span v-if="m.role === 'user'">👤</span>
                  <span v-else>🤖</span>
                </div>
                <div class="msg-body">
                  <div class="msg-text" v-html="formatMsg(m.content)"></div>
                  <div v-if="m.sources?.length" class="msg-sources">
                    <div class="src-label">📎 引用来源：</div>
                    <div v-for="(s, si) in m.sources" :key="si" class="src-item" @click="onSourceClick(s)">
                      <span class="src-icon">📄</span>
                      <span class="src-title">{{ s.doc_title }}</span>
                      <el-tag size="small" round type="info">{{ s.category_name }}</el-tag>
                    </div>
                  </div>
                  <div class="msg-time">{{ m.time || '' }}</div>
                </div>
              </div>
              <div v-if="aiChatLoading" class="chat-msg assistant typing">
                <div class="msg-avatar"><span>🤖</span></div>
                <div class="msg-body">
                  <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-text">AI 思考中...</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="chat-input">
              <el-input
                v-model="aiQuestion"
                type="textarea"
                :autosize="{ minRows: 1, maxRows: 4 }"
                placeholder="基于文档内容提问…（Enter 发送）"
                :disabled="aiChatLoading"
                @keydown="onAiKey"
              />
              <el-button type="primary" :loading="aiChatLoading" :disabled="!aiQuestion.trim() || aiChatLoading" @click="onAiSend">
                发送
              </el-button>
            </div>
          </div>

          <!-- 右侧：文档列表速览 -->
          <div class="ai-docs-panel">
            <div class="col-head">
              <span class="col-title">文档库</span>
              <el-tag size="small" round type="info">{{ totalDocs }}</el-tag>
            </div>
            <div class="quick-doc-list">
              <div
                v-for="catKey in categoryOrder"
                :key="catKey"
                class="quick-cat"
              >
                <div class="quick-cat-title">
                  {{ catIcons[catKey] }} {{ catNames[catKey] }}
                </div>
                <div
                  v-for="doc in getCategoryDocs(catKey).slice(0, 5)"
                  :key="doc.id"
                  class="quick-doc-item"
                  @click="onDocClick(doc)"
                >
                  <el-icon :size="16" :color="docTypeColors[doc.doc_type] || '#909399'">
                    <component :is="docTypeIcons[doc.doc_type] || Document" />
                  </el-icon>
                  <span class="quick-doc-title">{{ doc.title }}</span>
                </div>
                <div v-if="getCategoryDocs(catKey).length > 5" class="quick-more">
                  还有 {{ getCategoryDocs(catKey).length - 5 }} 个…
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- LLM 配置提示弹窗 -->
        <el-dialog v-model="showLlmTip" title="AI 能力配置" width="520px">
          <div class="llm-tip">
            <div>1. 打开 <b>系统设置</b> 页面</div>
            <div>2. 找到「AI 配置」区块</div>
            <div>3. 填入：</div>
            <div class="tip-field">· API Key（DeepSeek 的 sk-xxx）</div>
            <div class="tip-field">· Base URL：<code>https://api.deepseek.com</code>（默认）</div>
            <div class="tip-field">· Model：<code>deepseek-chat</code>（默认）</div>
            <div style="margin-top:12px">
              <el-button type="primary" @click="showLlmTip = false; $router.push('/system')">去配置</el-button>
            </div>
            <div class="tip-warn">
              没配 AI 也能正常使用文档管理，只是「AI 问答」会提示未配置
            </div>
          </div>
        </el-dialog>
      </el-tab-pane>

      <!-- ========== Tab 3: FAQ ========== -->
      <el-tab-pane label="FAQ" name="faq">
        <div class="page-header">
          <h2>FAQ 管理</h2>
          <div class="header-actions">
            <el-select v-model="categoryFilter" placeholder="分类筛选" clearable style="width:120px">
              <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
            </el-select>
            <el-select v-model="publishFilter" style="width:100px">
              <el-option label="全部" value="all" />
              <el-option label="已发布" value="published" />
              <el-option label="草稿" value="draft" />
            </el-select>
            <el-button type="primary" :icon="Plus" @click="onFaqCreate">新建</el-button>
            <el-dropdown @command="onFaqExport">
              <el-button :icon="Download">导出<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="xlsx">Excel</el-dropdown-item>
                  <el-dropdown-item command="json">JSON</el-dropdown-item>
                  <el-dropdown-item command="csv">CSV</el-dropdown-item>
                  <el-dropdown-item command="md">Markdown</el-dropdown-item>
                  <el-dropdown-item command="docx">Word</el-dropdown-item>
                  <el-dropdown-item command="pdf">PDF</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <div class="hint-bar">
          沉淀学生常问的问题，让答疑话术可复用。发布后可用于自动回复参考。
        </div>

        <el-empty v-if="!faqLoading && faqFilteredList.length === 0" description="还没有 FAQ 条目，点右上角新建" />

        <el-collapse v-model="faqActiveIds" v-loading="faqLoading" class="faq-collapse">
          <el-collapse-item v-for="f in faqFilteredList" :key="f.id" :name="String(f.id)">
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
              <el-button link type="primary" @click="onFaqEdit(f)">编辑</el-button>
              <el-button link :type="f.is_published ? 'warning' : 'primary'" @click="onFaqTogglePublish(f)">
                {{ f.is_published ? '撤回草稿' : '发布' }}
              </el-button>
              <el-button link type="danger" @click="onFaqDelete(f)">删除</el-button>
            </div>
          </el-collapse-item>
        </el-collapse>

        <el-dialog v-model="faqDialogVisible" :title="faqForm.id ? '编辑 FAQ' : '新建 FAQ'" width="720px">
          <el-form :model="faqForm" label-width="80px">
            <el-form-item label="分类">
              <el-select v-model="faqForm.category" allow-create filterable placeholder="选择或新增" style="width:100%">
                <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
            <el-form-item label="问题" required>
              <el-input v-model="faqForm.question" placeholder="学生常问的问题" />
            </el-form-item>
            <el-form-item label="答案" required>
              <el-input v-model="faqForm.answer" type="textarea" :rows="8" placeholder="标准回答话术" />
            </el-form-item>
            <el-form-item label="发布">
              <el-switch v-model="faqForm.is_published" active-text="已发布" inactive-text="草稿" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="faqDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="faqSaving" @click="onFaqSave">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, Download, Document, CircleCheck, Warning, ArrowDown, Plus,
  Search, Link, View, Delete, MoreFilled, FolderOpened,
  Files, Notebook, Tickets, DataBoard, Memo
} from '@element-plus/icons-vue'
import { docboxApi, knowledgeApi, chatApi, llmApi, faqsApi } from '@/api/knowledge.js'

// ===== Tab =====
const activeTab = ref('docbox')

// ===== 文档工具箱 =====
const loading = ref(false)
const categories = ref({})
const totalDocs = ref(0)
const searchText = ref('')
const fileInput = ref(null)

// 分类定义
const categoryOrder = ['policy', 'form', 'student_collect', 'other']
const catNames = {
  policy: '政策文件',
  form: '常用表格',
  student_collect: '学生端收集',
  other: '其他文档',
}
const catIcons = {
  policy: '📋',
  form: '📊',
  student_collect: '📝',
  other: '📁',
}
const docTypeIcons = {
  pdf: 'Document',
  docx: 'Notebook',
  doc: 'Notebook',
  xlsx: 'Tickets',
  xls: 'Tickets',
  txt: 'Memo',
  link: 'Link',
}
const docTypeColors = {
  pdf: '#E6A23C',
  docx: '#409EFF',
  doc: '#409EFF',
  xlsx: '#67C23A',
  xls: '#67C23A',
  txt: '#909399',
  link: '#9B59B6',
}

// 上传
const showUploadDialog = ref(false)
const uploadFile = ref(null)
const uploadFileName = ref('')
const uploadCategory = ref('other')
const uploadDesc = ref('')
const uploading = ref(false)

// 添加链接
const showAddLink = ref(false)
const linkForm = ref({ title: '', link_url: '', category: 'student_collect', description: '' })
const addingLink = ref(false)

// 移动分类
const showMoveDialog = ref(false)
const moveDoc = ref(null)
const moveCategory = ref('other')

// 预览
const showPreview = ref(false)
const previewDoc = ref(null)

function getCategoryDocs(catKey) {
  return categories.value[catKey]?.items || []
}
function getCategoryCount(catKey) {
  return categories.value[catKey]?.count || 0
}

async function loadDocs() {
  loading.value = true
  try {
    const res = await docboxApi.list({ search: searchText.value })
    categories.value = res.categories || {}
    totalDocs.value = res.total || 0
  } catch (e) {
    categories.value = {}
    totalDocs.value = 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  loadDocs()
}

function triggerUpload() {
  fileInput.value.value = ''
  fileInput.value.click()
}

function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploadFile.value = file
  uploadFileName.value = file.name
  uploadCategory.value = 'other'
  uploadDesc.value = ''
  showUploadDialog.value = true
}

async function doUpload() {
  if (!uploadFile.value) return
  uploading.value = true
  const fd = new FormData()
  fd.append('file', uploadFile.value)
  fd.append('category', uploadCategory.value)
  fd.append('description', uploadDesc.value)
  try {
    const res = await docboxApi.upload(fd)
    ElMessage.success(`${res.title} 上传成功`)
    showUploadDialog.value = false
    await loadDocs()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function doAddLink() {
  if (!linkForm.value.title || !linkForm.value.link_url) {
    ElMessage.warning('标题和链接不能为空')
    return
  }
  addingLink.value = true
  try {
    await docboxApi.addLink(linkForm.value)
    ElMessage.success('链接已添加')
    showAddLink.value = false
    linkForm.value = { title: '', link_url: '', category: 'student_collect', description: '' }
    await loadDocs()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '添加失败')
  } finally {
    addingLink.value = false
  }
}

function onDocClick(doc) {
  if (doc.doc_type === 'link') {
    window.open(doc.link_url, '_blank')
    return
  }
  openPreview(doc)
}

async function openPreview(doc) {
  try {
    const detail = await docboxApi.get(doc.id)
    previewDoc.value = detail
    showPreview.value = true
  } catch (e) {
    ElMessage.error('获取文档详情失败')
  }
}

function downloadDoc(doc) {
  const url = docboxApi.preview(doc.id)
  const a = document.createElement('a')
  a.href = url
  a.download = doc.title
  a.target = '_blank'
  a.click()
}

function onDocAction(cmd, doc) {
  if (cmd === 'preview') {
    if (doc.doc_type === 'link') {
      window.open(doc.link_url, '_blank')
    } else {
      openPreview(doc)
    }
  } else if (cmd === 'move') {
    moveDoc.value = doc
    moveCategory.value = doc.category
    showMoveDialog.value = true
  } else if (cmd === 'delete') {
    onDeleteDoc(doc)
  }
}

async function doMove() {
  if (!moveDoc.value) return
  try {
    await docboxApi.update(moveDoc.value.id, { category: moveCategory.value })
    ElMessage.success('已移动分类')
    showMoveDialog.value = false
    await loadDocs()
  } catch (e) {
    ElMessage.error('移动失败')
  }
}

async function onDeleteDoc(doc) {
  try {
    await ElMessageBox.confirm(`确认删除「${doc.title}」？`, '确认', { type: 'warning' })
    await docboxApi.remove(doc.id)
    ElMessage.success('已删除')
    await loadDocs()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// ===== AI 文档助手 =====
const aiQuestion = ref('')
const aiChatList = ref([])
const aiChatLoading = ref(false)
const chatAreaRef = ref(null)
const llmConfigured = ref(false)
const showLlmTip = ref(false)

const aiSuggestions = [
  '奖学金评定有哪些政策要点？',
  '学生请假审批流程是什么？',
  '心理危机干预的流程和注意事项',
  '考勤周汇总表怎么填？',
]

async function loadLlmStatus() {
  try {
    const r = await llmApi.get()
    llmConfigured.value = !!r?.configured
  } catch {
    llmConfigured.value = false
  }
}

function formatMsg(text) {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
  return html
}

function getTimeStr() {
  const now = new Date()
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
}

function onAiKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onAiSend()
  }
}

async function onAiAsk(q) {
  aiQuestion.value = q
  await onAiSend()
}

async function onAiSend() {
  const q = aiQuestion.value.trim()
  if (!q) return
  aiChatList.value.push({ role: 'user', content: q, time: getTimeStr() })
  aiQuestion.value = ''
  aiChatLoading.value = true
  await nextTick()
  scrollChatBottom()
  try {
    const res = await docboxApi.chat(q)
    aiChatList.value.push({
      role: 'assistant',
      content: res.answer || '(AI 未返回回答)',
      sources: res.sources || [],
      time: getTimeStr(),
    })
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '问答失败'
    aiChatList.value.push({ role: 'assistant', content: `❌ ${msg}`, time: getTimeStr() })
  } finally {
    aiChatLoading.value = false
    await nextTick()
    scrollChatBottom()
  }
}

function scrollChatBottom() {
  const area = document.querySelector('.chat-area')
  if (area) area.scrollTop = area.scrollHeight
}

function onSourceClick(s) {
  if (s.doc_id) {
    const doc = {
      id: s.doc_id,
      title: s.doc_title,
      category: s.category,
      doc_type: s.doc_type,
    }
    openPreview(doc)
  }
}

// ===== FAQ Tab =====
const faqList = ref([])
const faqLoading = ref(false)
const faqSaving = ref(false)
const categoryFilter = ref('')
const publishFilter = ref('all')
const faqActiveIds = ref([])
const categoryOptions = ['奖学金', '助学金', '宿舍', '选课', '毕业', '就业', '心理', '党团', '其他']
const faqDialogVisible = ref(false)
const faqForm = ref({ id: null, category: '', question: '', answer: '', is_published: true })

const faqFilteredList = computed(() => {
  let arr = faqList.value
  if (categoryFilter.value) arr = arr.filter(f => f.category === categoryFilter.value)
  if (publishFilter.value === 'published') arr = arr.filter(f => f.is_published)
  else if (publishFilter.value === 'draft') arr = arr.filter(f => !f.is_published)
  return arr
})

async function loadFaqs() {
  faqLoading.value = true
  try {
    faqList.value = await faqsApi.list() || []
  } catch (e) {
    faqList.value = []
  }
  faqLoading.value = false
}

function onFaqCreate() {
  faqForm.value = { id: null, category: '', question: '', answer: '', is_published: true }
  faqDialogVisible.value = true
}

function onFaqEdit(f) {
  faqForm.value = { id: f.id, category: f.category || '', question: f.question, answer: f.answer, is_published: !!f.is_published }
  faqDialogVisible.value = true
}

async function onFaqSave() {
  if (!faqForm.value.question?.trim() || !faqForm.value.answer?.trim()) {
    ElMessage.warning('问题和答案不能为空')
    return
  }
  faqSaving.value = true
  try {
    const payload = {
      category: faqForm.value.category || '其他',
      question: faqForm.value.question,
      answer: faqForm.value.answer,
      is_published: !!faqForm.value.is_published,
    }
    if (faqForm.value.id) {
      await faqsApi.update(faqForm.value.id, payload)
    } else {
      await faqsApi.create(payload)
    }
    ElMessage.success('已保存')
    faqDialogVisible.value = false
    await loadFaqs()
  } catch (e) {
    ElMessage.error('保存失败')
  }
  faqSaving.value = false
}

async function onFaqTogglePublish(f) {
  try {
    await faqsApi.update(f.id, { is_published: !f.is_published })
    ElMessage.success(f.is_published ? '已撤回为草稿' : '已发布')
    await loadFaqs()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function onFaqDelete(f) {
  try {
    await ElMessageBox.confirm(`确认删除该 FAQ？`, '确认', { type: 'warning' })
    await faqsApi.remove(f.id)
    ElMessage.success('已删除')
    await loadFaqs()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function onFaqExport(format) {
  const url = `/api/faqs/export?format=${format}`
  if (format === 'json') {
    fetch(url).then(r => r.json()).then(data => {
      const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'})
      const u = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = u; a.download = `FAQ导出_${new Date().toISOString().slice(0,10)}.json`; a.click()
      URL.revokeObjectURL(u)
    })
  } else {
    window.open(url, '_blank')
  }
}

onMounted(() => {
  loadDocs()
  loadLlmStatus()
  loadFaqs()
})
</script>

<style scoped>
.kb-page { padding: 20px; height: 100%; box-sizing: border-box; }
.kb-tabs { height: 100%; }
.kb-tabs :deep(.el-tabs__content) { overflow: visible; }
.page-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
}
.page-header h2 { margin: 0; color: #303133; }
.header-actions { display: flex; gap: 8px; align-items: center; }

/* ===== 文档工具箱 - 分类卡片 ===== */
.categories-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.category-card {
  background: #fff;
  border: 1px solid #E4E7ED;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
}
.category-card:hover {
  box-shadow: 0 4px 16px rgba(91, 146, 229, 0.1);
  border-color: rgba(91, 146, 229, 0.3);
}
.cat-header {
  padding: 14px 18px;
  background: linear-gradient(135deg, #F0F7FF, #F6FBFF);
  border-bottom: 1px solid #EBEEF5;
}
.cat-title-row {
  display: flex; align-items: center; gap: 8px;
}
.cat-icon { font-size: 20px; }
.cat-name { font-weight: 600; font-size: 15px; color: #2E5A7F; flex: 1; }
.cat-body { padding: 8px; max-height: 320px; overflow-y: auto; }
.cat-empty {
  padding: 24px; text-align: center; color: #C0C4CC; font-size: 13px;
}

/* 文档项 */
.doc-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px;
  border-radius: 8px; cursor: pointer;
  transition: all 0.18s;
  margin-bottom: 4px;
}
.doc-item:hover {
  background: linear-gradient(135deg, #F0F7FF, #F6F9FD);
}
.doc-icon-col { flex-shrink: 0; }
.doc-info-col { flex: 1; min-width: 0; }
.doc-title {
  font-weight: 500; font-size: 13.5px; color: #303133;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.doc-meta {
  display: flex; gap: 8px; margin-top: 3px; font-size: 11px; color: #909399;
}
.meta-item { white-space: nowrap; }
.doc-actions-col { flex-shrink: 0; }

/* ===== AI 布局 ===== */
.ai-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 14px;
  height: calc(100vh - 180px);
  min-height: 480px;
}
.ai-layout > div {
  background: #fff;
  border: 1px solid #E4E7ED;
  border-radius: 10px;
  display: flex; flex-direction: column;
  overflow: hidden;
}

/* 通用列头 */
.col-head {
  padding: 12px 14px;
  border-bottom: 1px solid #EBEEF5;
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, #F6F9FD, #fff);
}
.col-title { font-weight: 600; color: #303133; font-size: 14px; }
.col-head-actions { display: flex; align-items: center; gap: 6px; }

/* AI对话区 */
.chat-area { flex: 1; overflow-y: auto; padding: 14px; background: #FAFBFC; }
.chat-empty { text-align: center; padding: 30px 16px; color: var(--text-muted); }
.empty-icon-big { font-size: 48px; margin-bottom: 10px; }
.empty-title { font-size: 16px; font-weight: 700; color: #2E5A7F; margin-bottom: 4px; }
.empty-desc { font-size: 12px; color: #95A5A6; margin-bottom: 16px; }
.empty-suggests { display: flex; flex-direction: column; gap: 8px; }
.empty-suggest {
  padding: 10px 14px;
  background: #fff; border: 1px solid #E4E7ED; border-radius: 10px;
  cursor: pointer; font-size: 13px;
  transition: all .18s;
  display: flex; align-items: center; gap: 8px; text-align: left;
}
.empty-suggest:hover {
  border-color: var(--color-primary); color: var(--color-primary); background: #EEF4FD;
  transform: translateY(-1px); box-shadow: 0 2px 8px rgba(91, 146, 229, 0.1);
}
.suggest-icon { flex-shrink: 0; }

/* 对话消息 */
.chat-msg { display: flex; gap: 10px; margin-bottom: 14px; animation: msgFadeIn 0.3s ease; }
@keyframes msgFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.chat-msg.user { flex-direction: row-reverse; }
.msg-avatar {
  flex-shrink: 0; width: 36px; height: 36px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 18px; background: linear-gradient(135deg, #EEF4FD, #E8F7F3);
  border: 1px solid rgba(91, 146, 229, 0.15);
}
.chat-msg.user .msg-avatar { background: linear-gradient(135deg, #EEF4FD, #F0E8FD); }
.msg-body {
  max-width: 78%; padding: 10px 14px; border-radius: 12px;
  font-size: 14px; line-height: 1.7;
}
.chat-msg.user .msg-body {
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  color: #fff; border-bottom-right-radius: 4px;
}
.chat-msg.assistant .msg-body {
  background: #fff; border: 1px solid #E4E7ED; color: #303133;
  border-bottom-left-radius: 4px;
}
.msg-text { white-space: pre-wrap; word-break: break-word; }
.msg-text :deep(code) { background: rgba(91, 146, 229, 0.08); padding: 1px 5px; border-radius: 4px; font-size: 12px; font-family: 'SF Mono', Menlo, monospace; }
.msg-text :deep(strong) { color: #2E5A7F; }
.msg-sources { margin-top: 8px; padding-top: 8px; border-top: 1px dashed #E4E7ED; font-size: 12px; }
.src-label { color: var(--text-muted); margin-bottom: 4px; }
.src-item {
  padding: 5px 10px; margin: 3px 0; background: #F6F9FD; border-radius: 6px;
  cursor: pointer; color: var(--color-primary);
  display: flex; align-items: center; gap: 6px; transition: background .15s;
}
.src-item:hover { background: #EEF4FD; }
.src-icon { flex-shrink: 0; font-size: 12px; }
.src-title { font-weight: 500; white-space: nowrap; }
.msg-time { font-size: 10px; color: #C0C4CC; margin-top: 4px; text-align: right; }
.chat-msg.user .msg-time { color: rgba(255,255,255,0.6); }

/* 打字动画 */
.typing-indicator { display: flex; align-items: center; gap: 4px; }
.typing-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--color-primary);
  animation: typingBounce 1.2s infinite ease-in-out;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
.typing-text { margin-left: 6px; color: var(--text-muted); font-size: 12px; }

.chat-input {
  padding: 10px; border-top: 1px solid #EBEEF5;
  display: flex; gap: 8px; align-items: flex-end; background: #fff;
}
.chat-input .el-textarea { flex: 1; }

/* 右侧文档速览 */
.quick-doc-list { flex: 1; overflow-y: auto; padding: 10px; }
.quick-cat { margin-bottom: 12px; }
.quick-cat-title {
  font-size: 12px; font-weight: 600; color: #909399; padding: 4px 8px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.quick-doc-item {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px; border-radius: 6px; cursor: pointer;
  font-size: 13px; transition: all 0.15s;
}
.quick-doc-item:hover { background: #F0F7FF; }
.quick-doc-title {
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  color: #303133;
}
.quick-more { padding: 4px 10px; font-size: 11px; color: #C0C4CC; }

/* ===== 预览弹窗 ===== */
.preview-container { }
.preview-meta {
  display: flex; gap: 8px; align-items: center; margin-bottom: 16px; flex-wrap: wrap;
}
.meta-text { font-size: 12px; color: #909399; }
.preview-iframe-wrap {
  border: 1px solid #EBEEF5; border-radius: 8px; overflow: hidden;
  height: 70vh;
}
.preview-iframe { width: 100%; height: 100%; border: none; }
.preview-link { padding: 20px; text-align: center; }
.link-hint { margin-top: 8px; color: #909399; font-size: 12px; }
.preview-text { border: 1px solid #EBEEF5; border-radius: 8px; }
.doc-full-text {
  padding: 16px; font-size: 13px; line-height: 1.8; color: #303133;
  white-space: pre-wrap; word-break: break-word; margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.preview-footer { margin-top: 16px; display: flex; justify-content: flex-end; }

/* LLM 提示 */
.llm-tip { line-height: 1.9; font-size: 14px; }
.tip-field { padding-left: 12px; color: var(--text-secondary); font-size: 13px; }
.tip-field code { background: #F5F7FA; padding: 2px 6px; border-radius: 3px; font-family: Consolas, monospace; font-size: 12px; }
.tip-warn { margin-top: 16px; padding: 10px; background: #FDF6EC; border-radius: 6px; font-size: 12px; color: #E6A23C; }

/* FAQ 样式 */
.hint-bar {
  background: #EEF3F5; color: #5C7A87; padding: 8px 14px;
  border-radius: var(--radius-sm); font-size: 13px; margin-bottom: 16px;
}
.faq-collapse { background: #fff; border-radius: 10px; padding: 4px 16px; }
.faq-title-row { display: flex; gap: 8px; align-items: center; flex: 1; }
.faq-q { font-weight: 500; color: #303133; }
.faq-answer {
  white-space: pre-wrap; line-height: 1.75; color: var(--text-secondary);
  background: #FAFBFC; border-radius: 6px; padding: 12px; margin-bottom: 12px;
}
.faq-actions { display: flex; gap: 8px; padding-top: 4px; }
</style>
