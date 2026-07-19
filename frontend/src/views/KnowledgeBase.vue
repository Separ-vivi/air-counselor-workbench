<template>
  <div class="kb-page">
    <el-tabs v-model="activeTab" class="kb-tabs">
      <el-tab-pane label="AI 知识库" name="knowledge">
        <div class="page-header">
          <h2>知识库 · AI 助手</h2>
          <div class="header-actions">
            <el-tag :type="llmConfigured ? 'success' : 'warning'" effect="plain" round>
              <el-icon v-if="llmConfigured" style="vertical-align:-2px;margin-right:4px"><CircleCheck /></el-icon>
              <el-icon v-else style="vertical-align:-2px;margin-right:4px"><Warning /></el-icon>
              {{ llmConfigured ? 'AI 已接入' : '未配置 AI（仅上传不问答）' }}
            </el-tag>
            <el-button text type="primary" @click="showLlmTip = true">如何配置？</el-button>
          </div>
        </div>

        <div class="kb-layout">
          <!-- ============ 左栏：文档库 ============ -->
          <div class="col-docs">
            <div class="col-head">
              <span class="col-title">📚 文档库</span>
              <el-button size="small" type="primary" :icon="Upload" @click="triggerUpload">上传</el-button>
            </div>
            <div v-if="docs.length === 0 && !docsLoading" class="col-empty">
              暂无文档<br>
              <span class="hint">点右上角「上传」开始</span>
            </div>
            <div v-loading="docsLoading" class="doc-list">
              <div
                v-for="d in docs"
                :key="d.id"
                class="doc-item"
                :class="{ active: selectedDoc?.id === d.id }"
                @click="onSelectDoc(d)"
              >
                <div class="doc-row1">
                  <el-icon><Document /></el-icon>
                  <span class="doc-title">{{ d.title }}</span>
                </div>
                <div class="doc-row2">
                  <el-tag size="small" round effect="plain">{{ d.doc_type || '未分类' }}</el-tag>
                  <span class="doc-chunks">{{ d.chunk_count }} chunks</span>
                </div>
                <div class="doc-row3">
                  <span class="doc-time">{{ formatDate(d.created_at) }}</span>
                  <el-button link type="danger" size="small" @click.stop="onDeleteDoc(d)">删除</el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- ============ 中栏：AI 对话 ============ -->
          <div class="col-chat">
            <div class="col-head">
              <span class="col-title">💬 AI 助手</span>
              <el-button size="small" text @click="chatList = []">清空</el-button>
            </div>

            <div v-loading="chatLoading" class="chat-area">
              <div v-if="chatList.length === 0" class="chat-empty">
                <div class="empty-icon">💡</div>
                <div>试试提问：</div>
                <div class="empty-suggest" v-for="q in suggestions" :key="q" @click="onAsk(q)">"{{ q }}"</div>
              </div>
              <div v-for="(m, i) in chatList" :key="i" class="chat-msg" :class="m.role">
                <div class="msg-role">{{ m.role === 'user' ? '你' : 'AI' }}</div>
                <div class="msg-body">
                  <div class="msg-text">{{ m.content }}</div>
                  <div v-if="m.sources?.length" class="msg-sources">
                    <div class="src-label">📎 引用来源：</div>
                    <div v-for="(s, si) in m.sources" :key="si" class="src-item" @click="jumpToChunk(s)">
                      · {{ s.doc_title }} <span class="src-snippet">…{{ s.snippet?.slice(0, 60) }}…</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="chatLoading" class="chat-msg assistant typing">
                <div class="msg-role">AI</div>
                <div class="msg-body"><span class="typing-dots">思考中...</span></div>
              </div>
            </div>

            <div class="chat-input">
              <el-input
                v-model="question"
                type="textarea"
                :autosize="{ minRows: 1, maxRows: 4 }"
                placeholder="基于文档库内容提问…（Enter 发送，Shift+Enter 换行）"
                :disabled="chatLoading"
                @keydown="onKey"
              />
              <el-button type="primary" :loading="chatLoading" :disabled="!question.trim() || chatLoading" @click="onSend">
                发送
              </el-button>
            </div>
          </div>

          <!-- ============ 右栏：来源预览 ============ -->
          <div class="col-chunks">
            <div class="col-head">
              <span class="col-title">📎 来源预览</span>
              <span v-if="chunks.length" class="chunk-count">{{ chunks.length }} 块</span>
            </div>
            <div v-if="!selectedDoc && !highlightChunk" class="col-empty">
              点击左栏文档查看分块<br>
              或点击聊天中引用的来源
            </div>
            <div v-else class="chunk-list">
              <template v-if="highlightChunk">
                <div class="chunk-item highlight">
                  <div class="chunk-head">
                    <el-tag size="small" type="warning" round>引用</el-tag>
                    <span class="chunk-src">{{ highlightChunk.doc_title }}</span>
                  </div>
                  <div class="chunk-body">{{ highlightChunk.snippet }}</div>
                </div>
                <el-divider />
                <div class="chunk-hint">该文档其他分块：</div>
              </template>
              <div v-for="c in chunks" :key="c.id" class="chunk-item" @click="toggleChunkExpand(c.id)">
                <div class="chunk-head">
                  <el-tag size="small" round>#{{ c.chunk_index + 1 }}</el-tag>
                  <span class="chunk-chars">{{ c.content.length }}字</span>
                  <el-icon class="expand-icon" :class="{ expanded: expandedChunks.has(c.id) }"><ArrowDown /></el-icon>
                </div>
                <div class="chunk-body" :class="{ collapsed: !expandedChunks.has(c.id) }">{{ c.content }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 隐藏文件 input -->
        <input ref="fileInput" type="file" style="display:none" accept=".docx,.doc,.pdf,.txt" @change="onFileSelected">

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
              💡 没配 AI 也能正常使用文档上传/查看/分块，只是「问答」会提示未配置
            </div>
          </div>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="FAQ 常见问题" name="faq">
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
            <el-button type="primary" :icon="Plus" @click="onFaqCreate">新建 FAQ</el-button>
            <el-dropdown @command="onFaqExport" style="margin-left:8px">
              <el-button :icon="Download">导出</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="excel">导出 Excel</el-dropdown-item>
                  <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
                  <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
                  <el-dropdown-item command="pdf">导出 PDF</el-dropdown-item>
                  <el-dropdown-item command="docx">导出 Word</el-dropdown-item>
                  <el-dropdown-item command="md">导出 Markdown</el-dropdown-item>
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
              <el-button link type="primary" @click="onFaqEdit(f)">✏️ 编辑</el-button>
              <el-button link :type="f.is_published ? 'warning' : 'primary'" @click="onFaqTogglePublish(f)">
                {{ f.is_published ? '⬇️ 撤回草稿' : '⬆️ 发布' }}
              </el-button>
              <el-button link type="danger" @click="onFaqDelete(f)">🗑️ 删除</el-button>
            </div>
          </el-collapse-item>
        </el-collapse>

        <!-- FAQ 新建/编辑对话框 -->
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
import { Upload, Document, CircleCheck, Warning, ArrowDown, Plus, Download } from '@element-plus/icons-vue'
import { knowledgeApi, chatApi, llmApi, faqsApi } from '@/api/knowledge.js'

// ===== Tab 切换 =====
const activeTab = ref('knowledge')

// ===== AI 知识库 Tab =====
const docs = ref([])
const docsLoading = ref(false)
const selectedDoc = ref(null)
const chunks = ref([])
const fileInput = ref(null)

const question = ref('')
const chatList = ref([])
const chatLoading = ref(false)
const highlightChunk = ref(null)
const expandedChunks = ref(new Set())

function toggleChunkExpand(id) {
  const s = new Set(expandedChunks.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  expandedChunks.value = s
}

const llmConfigured = ref(false)
const showLlmTip = ref(false)

const suggestions = [
  '奖学金评定办法有哪些要点？',
  '请假审批流程怎么走？',
  '学生心理危机干预怎么做？',
]

async function loadDocs() {
  docsLoading.value = true
  try {
    const res = await knowledgeApi.list()
    docs.value = Array.isArray(res) ? res : []
  } catch (e) {
    docs.value = []
    ElMessage.error('加载文档失败')
  } finally {
    docsLoading.value = false
  }
}

async function loadLlmStatus() {
  try {
    const r = await llmApi.get()
    llmConfigured.value = !!r?.configured
  } catch {
    llmConfigured.value = false
  }
}

function triggerUpload() {
  fileInput.value.value = ''
  fileInput.value.click()
}

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  fd.append('title', file.name.replace(/\.[^.]+$/, ''))
  ElMessage.info(`正在上传 ${file.name}，解析中…`)
  try {
    const res = await knowledgeApi.upload(fd)
    ElMessage.success(`✅ 已解析为 ${res.chunk_count} 个分块`)
    await loadDocs()
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '上传失败'
    ElMessage.error(msg)
  }
}

async function onSelectDoc(d) {
  selectedDoc.value = d
  highlightChunk.value = null
  expandedChunks.value = new Set()
  try {
    const res = await knowledgeApi.chunks(d.id)
    chunks.value = Array.isArray(res) ? res : []
  } catch {
    chunks.value = []
  }
}

async function onDeleteDoc(d) {
  try {
    await ElMessageBox.confirm(`确认删除「${d.title}」？\n关联的分块和 AI 问答记录也会一并删除。`, '确认', { type: 'warning' })
    await knowledgeApi.remove(d.id)
    ElMessage.success('已删除')
    if (selectedDoc.value?.id === d.id) {
      selectedDoc.value = null
      chunks.value = []
    }
    await loadDocs()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function onKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}

async function onAsk(q) {
  question.value = q
  await onSend()
}

async function onSend() {
  const q = question.value.trim()
  if (!q) return
  chatList.value.push({ role: 'user', content: q })
  question.value = ''
  chatLoading.value = true
  try {
    const res = await chatApi.ask(q)
    chatList.value.push({
      role: 'assistant',
      content: res.answer || '(AI 未返回回答)',
      sources: res.sources || [],
    })
    await nextTick()
    scrollChatBottom()
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '问答失败'
    chatList.value.push({ role: 'assistant', content: `❌ ${msg}` })
  } finally {
    chatLoading.value = false
    await nextTick()
    scrollChatBottom()
  }
}

function scrollChatBottom() {
  const area = document.querySelector('.chat-area')
  if (area) area.scrollTop = area.scrollHeight
}

function jumpToChunk(s) {
  highlightChunk.value = s
  if (s.doc_id) {
    const d = docs.value.find(x => x.id === s.doc_id)
    if (d) {
      selectedDoc.value = d
      knowledgeApi.chunks(d.id).then(r => { chunks.value = Array.isArray(r) ? r : [] })
    }
  }
}

function formatDate(s) {
  if (!s) return ''
  return String(s).slice(0, 10)
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
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;
}
.page-header h2 { margin: 0; color: #303133; }
.header-actions { display: flex; gap: 8px; align-items: center; }

/* 三栏布局 */
.kb-layout {
  display: grid;
  grid-template-columns: 260px 1fr 300px;
  gap: 14px;
  height: calc(100vh - 200px);
  min-height: 500px;
}
.kb-layout > div {
  background: #fff;
  border: 1px solid #E4E7ED;
  border-radius: 10px;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.col-head {
  padding: 12px 14px;
  border-bottom: 1px solid #EBEEF5;
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, #F6F9FD, #fff);
}
.col-title { font-weight: 600; color: #303133; font-size: 14px; }
.col-empty {
  padding: 40px 20px; text-align: center; color: #909399; font-size: 13px; line-height: 1.8;
}
.col-empty .hint { font-size: 12px; color: #C0C4CC; }

/* 左：文档列表 */
.doc-list { flex: 1; overflow-y: auto; padding: 8px; }
.doc-item {
  padding: 10px; margin-bottom: 6px;
  border-radius: 8px; cursor: pointer;
  border: 1px solid transparent;
  transition: all .18s;
}
.doc-item:hover { background: #F6F9FD; border-color: #E4E7ED; }
.doc-item.active {
  background: linear-gradient(135deg, #EEF4FD, #E8F7F3);
  border-color: #5B92E5;
}
.doc-row1 { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.doc-row1 .el-icon { color: #5B92E5; }
.doc-title { font-weight: 500; font-size: 13px; color: #303133;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.doc-row2 { display: flex; gap: 6px; align-items: center; margin-bottom: 4px; }
.doc-chunks { font-size: 11px; color: #909399; }
.doc-row3 { display: flex; justify-content: space-between; align-items: center; }
.doc-time { font-size: 11px; color: #C0C4CC; }

/* 中：对话 */
.chat-area { flex: 1; overflow-y: auto; padding: 14px; background: #FAFBFC; }
.chat-empty {
  text-align: center; padding: 40px 20px; color: #909399;
}
.empty-icon { font-size: 40px; margin-bottom: 10px; }
.empty-suggest {
  margin-top: 8px; padding: 8px 12px;
  background: #fff; border: 1px solid #E4E7ED; border-radius: 8px;
  cursor: pointer; font-size: 13px;
  transition: all .18s;
}
.empty-suggest:hover {
  border-color: #5B92E5; color: #5B92E5; background: #EEF4FD;
}
.chat-msg {
  display: flex; gap: 10px; margin-bottom: 14px;
}
.chat-msg.user { flex-direction: row-reverse; }
.msg-role {
  flex-shrink: 0; width: 32px; height: 32px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; color: #fff;
  background: linear-gradient(135deg, #5B92E5, #7BCFCB);
}
.chat-msg.user .msg-role { background: linear-gradient(135deg, #8FA9E5, #4FC3B8); }
.msg-body {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px; line-height: 1.7;
}
.chat-msg.user .msg-body {
  background: linear-gradient(135deg, #5B92E5, #4FC3B8);
  color: #fff;
}
.chat-msg.assistant .msg-body {
  background: #fff;
  border: 1px solid #E4E7ED;
  color: #303133;
}
.msg-text { white-space: pre-wrap; word-break: break-word; }
.msg-sources {
  margin-top: 8px; padding-top: 8px; border-top: 1px dashed #E4E7ED;
  font-size: 12px;
}
.src-label { color: #909399; margin-bottom: 4px; }
.src-item {
  padding: 4px 8px; margin: 3px 0;
  background: #F6F9FD; border-radius: 4px;
  cursor: pointer; color: #5B92E5;
}
.src-item:hover { background: #EEF4FD; }
.src-snippet { color: #909399; margin-left: 4px; }
.typing-dots { color: #909399; font-style: italic; }
.chat-input {
  padding: 10px; border-top: 1px solid #EBEEF5;
  display: flex; gap: 8px; align-items: flex-end;
  background: #fff;
}
.chat-input .el-textarea { flex: 1; }

/* 右：分块 */
.chunk-list { flex: 1; overflow-y: auto; padding: 10px; background: #FAFBFC; }
.chunk-count { font-size: 12px; color: #909399; }
.chunk-hint { padding: 0 10px 8px; font-size: 12px; color: #909399; }
.chunk-item {
  background: #fff; border: 1px solid #E4E7ED; border-radius: 8px;
  padding: 10px; margin-bottom: 8px; cursor: pointer; transition: border-color .18s;
}
.chunk-item:hover { border-color: #5B92E5; }
.chunk-item.highlight {
  border-color: #E6A23C; background: #FDF6EC; cursor: default;
}
.chunk-head {
  display: flex; align-items: center; gap: 6px; margin-bottom: 6px;
  font-size: 12px;
}
.chunk-chars { color: #C0C4CC; font-size: 11px; }
.expand-icon {
  margin-left: auto; transition: transform .2s; color: #C0C4CC; font-size: 14px;
}
.expand-icon.expanded { transform: rotate(180deg); }
.chunk-body {
  font-size: 13px; line-height: 1.6; color: #303133;
  white-space: pre-wrap; word-break: break-word;
}
.chunk-body.collapsed {
  max-height: 72px; overflow: hidden;
  mask-image: linear-gradient(to bottom, #000 50%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, #000 50%, transparent 100%);
}

/* LLM 提示 */
.llm-tip { line-height: 1.9; font-size: 14px; }
.tip-field {
  padding-left: 12px; color: #606266; font-size: 13px;
}
.tip-field code {
  background: #F5F7FA; padding: 2px 6px; border-radius: 3px;
  font-family: Consolas, monospace; font-size: 12px;
}
.tip-warn {
  margin-top: 16px; padding: 10px; background: #FDF6EC;
  border-radius: 6px; font-size: 12px; color: #E6A23C;
}

/* FAQ 样式 */
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
