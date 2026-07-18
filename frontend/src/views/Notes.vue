<template>
  <div class="notes-page">
    <div class="ios-hero">
      <div class="hero-row">
        <div class="hero-title">
          <div class="hero-main">记事本</div>
          <div class="hero-sub">{{ list.length }} 条记录 · 让灵感和待办一目了然</div>
        </div>
        <div class="header-actions">
          <el-input
            v-model="keyword"
            placeholder="搜索"
            clearable
            :prefix-icon="Search"
            class="ios-search"
            @keyup.enter="load"
            @clear="load"
          />
          <el-button type="primary" :icon="Plus" @click="onCreate" round>新建</el-button>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange" class="cat-tabs">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="待办" name="todo" />
      <el-tab-pane label="备忘" name="memo" />
      <el-tab-pane label="想法" name="idea" />
      <el-tab-pane label="归档" name="archived" />
    </el-tabs>

    <div v-if="activeTab === 'todo'" class="filter-row">
      <el-radio-group v-model="statusFilter" size="small" @change="load">
        <el-radio-button label="active">未完成</el-radio-button>
        <el-radio-button label="done">已完成</el-radio-button>
        <el-radio-button label="">全部</el-radio-button>
      </el-radio-group>
    </div>

    <el-empty v-if="!loading && list.length === 0" description="还没有内容，点右上角新建一条" />

    <div class="note-grid" v-loading="loading">
      <div
        v-for="n in list"
        :key="n.id"
        class="note-card"
        :class="[`color-${n.color}`, { done: n.status === 'done', pinned: n.pinned }]"
        @click.self="onEdit(n)"
      >
        <div class="note-topbar">
          <span class="cat-dot" :class="`cat-${n.category}`">
            {{ n.category === 'todo' ? '☑️' : n.category === 'idea' ? '💡' : '📄' }}
          </span>
          <span class="cat-label">{{ catLabel(n.category) }}</span>
          <el-tag v-if="n.status === 'archived'" size="small" type="info" effect="light" round style="margin-left:6px">已归档</el-tag>
          <span class="cat-flex"></span>
          <el-icon v-if="n.pinned" class="pin-icon" title="已置顶"><Top /></el-icon>
        </div>

        <!-- Todo：checkbox + 标题 一行显示，点 checkbox 直接切换完成 -->
        <div v-if="n.category === 'todo'" class="todo-row" @click.stop>
          <el-checkbox
            :model-value="n.status === 'done'"
            @change="onToggle(n)"
            size="large"
            class="todo-check"
          />
          <div class="todo-title-wrap" @click="onEdit(n)">
            <div class="note-title todo-title">{{ n.title || '（无标题待办）' }}</div>
            <div v-if="n.content" class="note-body todo-body">{{ n.content }}</div>
          </div>
        </div>

        <!-- Memo / Idea：普通标题 + 正文 -->
        <template v-else>
          <div class="note-title" @click="onEdit(n)">{{ n.title || '（无标题）' }}</div>
          <div class="note-body" @click="onEdit(n)">{{ n.content || '（点击编辑内容）' }}</div>
        </template>

        <div class="note-meta">
          <el-tag v-if="n.category === 'todo' && n.priority === 2" type="danger" size="small" effect="light" round>🔥 高优先</el-tag>
          <el-tag v-else-if="n.category === 'todo' && n.priority === 1" type="warning" size="small" effect="light" round>中优先</el-tag>
          <el-tag v-if="n.category === 'todo' && n.due_date" size="small" effect="plain" round :type="dueTagType(n.due_date, n.status)">
            <el-icon><Calendar /></el-icon>&nbsp;{{ formatDue(n.due_date) }}
          </el-tag>
          <el-tag v-if="n.remind_at" size="small" effect="plain" round type="warning">
            🔔 {{ formatRemind(n.remind_at) }}
          </el-tag>
          <span v-if="n.tags" class="tag-list">#{{ n.tags }}</span>
        </div>

        <div class="note-footer">
          <span class="note-time">{{ formatTime(n.updated_at || n.created_at) }}</span>
          <div class="note-actions" @click.stop>
            <!-- Idea 专属：转项目 -->
            <el-tooltip v-if="n.category === 'idea' && n.status !== 'archived'" content="扩展为项目">
              <el-button link @click="onToProject(n)"><el-icon><Promotion /></el-icon></el-button>
            </el-tooltip>
            <!-- Idea 专属：归档 -->
            <el-tooltip v-if="n.category === 'idea'" :content="n.status === 'archived' ? '取消归档' : '归档'">
              <el-button link @click="onArchive(n)"><el-icon><FolderOpened /></el-icon></el-button>
            </el-tooltip>
            <el-tooltip :content="n.pinned ? '取消置顶' : '置顶'">
              <el-button link :icon="Top" :class="{ 'active-pin': n.pinned }" @click="onTogglePin(n)" />
            </el-tooltip>
            <el-tooltip content="编辑">
              <el-button link :icon="Edit" @click="onEdit(n)" />
            </el-tooltip>
            <el-tooltip content="删除">
              <el-button link :icon="Delete" @click="onDelete(n)" />
            </el-tooltip>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑记事' : '新建记事'"
      width="560px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="标题" maxlength="200" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.category">
            <el-radio-button label="todo">☑️ 待办</el-radio-button>
            <el-radio-button label="memo">📄 备忘</el-radio-button>
            <el-radio-button label="idea">💡 想法</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="5" placeholder="内容" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-radio-group v-model="form.color" class="color-picker">
            <el-radio label="yellow" border><span class="dot-yellow" />黄</el-radio>
            <el-radio label="pink" border><span class="dot-pink" />粉</el-radio>
            <el-radio label="blue" border><span class="dot-blue" />蓝</el-radio>
            <el-radio label="green" border><span class="dot-green" />绿</el-radio>
            <el-radio label="purple" border><span class="dot-purple" />紫</el-radio>
            <el-radio label="orange" border><span class="dot-orange" />橙</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="优先级" v-if="form.category === 'todo'">
          <el-radio-group v-model="form.priority">
            <el-radio-button :label="0">低</el-radio-button>
            <el-radio-button :label="1">中</el-radio-button>
            <el-radio-button :label="2">高</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="截止" v-if="form.category === 'todo'">
          <el-date-picker
            v-model="form.due_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择截止日期"
          />
        </el-form-item>
        <el-form-item label="提醒">
          <el-date-picker
            v-model="form.remind_at"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm"
            format="YYYY-MM-DD HH:mm"
            placeholder="选择提醒时间（会显示在日历）"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="逗号分隔，如：期末,重要" />
        </el-form-item>
        <el-form-item label="置顶">
          <el-switch v-model="form.pinned" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import {
  Plus, Search, Edit, Delete, Top, Check, Calendar, RefreshLeft,
  Promotion, FolderOpened
} from '@element-plus/icons-vue'
import { notesApi, projectsApi } from '@/api/productivity.js'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const keyword = ref('')
const activeTab = ref('')
const statusFilter = ref('active')

const dialogVisible = ref(false)
const form = ref({
  id: null,
  title: '', content: '', category: 'memo', status: 'active',
  priority: 0, due_date: '', remind_at: '', tags: '', pinned: false, color: 'yellow',
})

async function load() {
  loading.value = true
  try {
    const params = {}
    if (activeTab.value === 'archived') {
      params.status = 'archived'
    } else {
      if (activeTab.value) params.category = activeTab.value
      if (activeTab.value === 'todo' && statusFilter.value) params.status = statusFilter.value
    }
    if (keyword.value) params.keyword = keyword.value
    const data = await notesApi.list(params)
    // 非 archived tab 时前端再过滤一次已归档条目（后端已经支持 status 过滤但没过滤"非归档"）
    let arr = data || []
    if (activeTab.value !== 'archived' && !(activeTab.value === 'todo' && statusFilter.value)) {
      arr = arr.filter(x => x.status !== 'archived')
    }
    list.value = arr
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function onTabChange() {
  // 切到归档 tab 时不显示优先级 filter
  load()
}

function onCreate() {
  form.value = {
    id: null,
    title: '', content: '',
    category: activeTab.value || 'memo',
    status: 'active', priority: 0, due_date: '', remind_at: '', tags: '',
    pinned: false, color: 'yellow',
  }
  dialogVisible.value = true
}

function onEdit(n) {
  form.value = { ...n }
  dialogVisible.value = true
}

async function onSave() {
  saving.value = true
  try {
    if (form.value.id) {
      await notesApi.update(form.value.id, form.value)
      ElMessage.success('已更新')
    } else {
      await notesApi.create(form.value)
      ElMessage.success('已新建')
    }
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function onDelete(n) {
  try {
    await ElMessageBox.confirm(`确认删除「${n.title || '未命名'}」？`, '提示', { type: 'warning' })
    await notesApi.remove(n.id)
    ElMessage.success('已删除')
    load()
  } catch {}
}

async function onToggle(n) {
  await notesApi.toggle(n.id)
  load()
}

async function onTogglePin(n) {
  await notesApi.update(n.id, { pinned: !n.pinned })
  load()
}

const route = useRoute()
onMounted(async () => {
  // 支持 Calendar drawer 跳来自动打开新建
  const q = route.query || {}
  if (q.create) {
    activeTab.value = String(q.create)
  }
  await load()
  if (q.create) {
    form.value = {
      id: null,
      title: '',
      content: '',
      category: String(q.create),
      status: 'active',
      priority: 0,
      due_date: q.due || '',
      remind_at: q.remind || '',
      tags: '',
      pinned: false,
      color: 'yellow',
    }
    dialogVisible.value = true
  }
})

const router = useRouter()

async function onToProject(n) {
  try {
    await ElMessageBox.confirm(
      `把「${n.title || '想法'}」扩展成正式项目？\n\n项目名将以此想法为标题，描述沿用想法内容。`,
      '扩展为项目',
      { confirmButtonText: '好，创建项目', cancelButtonText: '再想想', type: 'info' }
    )
    const created = await projectsApi.create({
      name: n.title || '来自想法',
      description: n.content || '',
      status: 'active',
      progress: 0,
    })
    ElMessage.success('项目已创建，正在跳转…')
    // 顺手把想法归档
    try { await notesApi.update(n.id, { status: 'archived' }) } catch(e) {}
    router.push({ path: '/projects', query: { highlight: created?.id } })
  } catch (e) {
    // 用户取消
  }
}

async function onArchive(n) {
  const next = n.status === 'archived' ? 'active' : 'archived'
  await notesApi.update(n.id, { status: next })
  ElMessage.success(next === 'archived' ? '已归档' : '已恢复')
  await load()
}

function formatDue(d) {
  if (!d) return ''
  const today = new Date()
  today.setHours(0,0,0,0)
  const target = new Date(d)
  target.setHours(0,0,0,0)
  const diff = Math.round((target - today) / 86400000)
  if (diff === 0) return '今天到期'
  if (diff === 1) return '明天到期'
  if (diff === -1) return '昨天到期'
  if (diff > 1 && diff <= 7) return `${diff} 天后`
  if (diff < -1) return `已逾期 ${-diff} 天`
  return d
}

function dueTagType(d, st) {
  if (st === 'done') return 'success'
  if (!d) return ''
  const today = new Date(); today.setHours(0,0,0,0)
  const target = new Date(d); target.setHours(0,0,0,0)
  const diff = Math.round((target - today) / 86400000)
  if (diff < 0) return 'danger'
  if (diff <= 2) return 'warning'
  return ''
}

function formatRemind(t) {
  if (!t) return ''
  const s = String(t).replace('T', ' ')
  // 只保留 MM-DD HH:mm
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/)
  if (m) return `${m[2]}-${m[3]} ${m[4]}:${m[5]}`
  return s.slice(5, 16)
}
function catLabel(c) {
  return { todo: '待办', memo: '备忘', idea: '想法' }[c] || '备忘'
}
function formatTime(t) {
  if (!t) return '刚刚'
  const d = new Date(t)
  if (isNaN(d.getTime())) return String(t).slice(0, 16).replace('T', ' ')
  const now = new Date()
  const diffMs = now - d
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return diffMin + ' 分钟前'
  if (diffMin < 60 * 24) return Math.floor(diffMin / 60) + ' 小时前'
  if (diffMin < 60 * 24 * 7) return Math.floor(diffMin / 60 / 24) + ' 天前'
  const p = x => x.toString().padStart(2, '0')
  return `${d.getFullYear()}/${p(d.getMonth() + 1)}/${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

</script>

<style scoped>
.notes-page { padding: 24px 20px; }

/* ============ iOS 大字标题栏 ============ */
.ios-hero { margin-bottom: 20px; }
.hero-row { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; }
.hero-main {
  font-size: 32px; font-weight: 700; color: #1D1D1F;
  letter-spacing: -0.5px; line-height: 1.1;
  font-family: -apple-system, "SF Pro Display", "PingFang SC", "Helvetica Neue", sans-serif;
}
.hero-sub { font-size: 13px; color: #86868B; margin-top: 6px; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.ios-search { width: 240px; }
.ios-search :deep(.el-input__wrapper) {
  border-radius: 999px !important;
  background: rgba(120, 120, 128, 0.10) !important;
  box-shadow: none !important;
  padding-left: 14px;
}
.ios-search :deep(.el-input__wrapper.is-focus) {
  background: rgba(120, 120, 128, 0.16) !important;
}

/* ============ 分段控制器风 Tab ============ */
.cat-tabs { margin-bottom: 12px; }
.cat-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.cat-tabs :deep(.el-tabs__item) {
  font-size: 15px; font-weight: 500; color: #3A3A3A;
  padding: 0 18px; height: 36px; line-height: 36px;
}
.cat-tabs :deep(.el-tabs__active-bar) {
  height: 3px !important; border-radius: 3px;
  background: linear-gradient(90deg, #5D8FA0, #82C79A) !important;
}
.filter-row { margin-bottom: 12px; }

/* ============ 卡片网格 ============ */
.note-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  min-height: 200px;
}

/* ============ iOS 记事卡片 ============ */
.note-card {
  position: relative;
  padding: 14px 16px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(14px) saturate(160%);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 10px rgba(60, 80, 120, 0.06);
  display: flex; flex-direction: column; gap: 6px;
  transition: transform .18s cubic-bezier(.2,.9,.3,1.2), box-shadow .18s;
  min-height: 160px;
  cursor: default;
  overflow: hidden;
}
.note-card::before {
  content: '';
  position: absolute; left: 0; top: 0; bottom: 0;
  width: 4px;
  background: #C7CEEA;
  border-radius: 16px 0 0 16px;
}
.note-card.color-yellow::before { background: #F5D45C; }
.note-card.color-pink::before   { background: #F58BAA; }
.note-card.color-blue::before   { background: #6AB8E4; }
.note-card.color-green::before  { background: #67C79A; }
.note-card.color-purple::before { background: #A88BE0; }
.note-card.color-orange::before { background: #F5A25F; }
.note-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(60, 80, 120, 0.14);
}
.note-card.done { opacity: .60; }
.note-card.done .note-title { text-decoration: line-through; color: #909399; }
.note-card.pinned { box-shadow: 0 4px 16px rgba(230, 162, 60, 0.20); }
.note-card.pinned::after {
  content: ''; position: absolute; right: 10px; top: 10px;
  width: 8px; height: 8px; border-radius: 50%; background: #E6A23C;
}

/* topbar：分类圆点 + 分类文字 + 置顶 icon */
.note-topbar { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #86868B; }
.cat-dot { font-size: 14px; }
.cat-label { font-weight: 500; letter-spacing: .3px; }
.cat-flex { flex: 1; }
.pin-icon { color: #E6A23C; font-size: 14px; }

.note-title {
  font-weight: 600; font-size: 16px; color: #1D1D1F;
  letter-spacing: -0.2px; line-height: 1.35;
  cursor: pointer; word-break: break-all;
  margin-top: 2px;
}
.note-title:hover { color: #4A7A8C; }
.note-body {
  flex: 1;
  font-size: 13px; color: #4A4A4C; line-height: 1.55;
  white-space: pre-wrap; word-break: break-all;
  max-height: 88px; overflow: hidden;
  cursor: pointer;
}
.note-meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-top: 4px; }
.tag-list { font-size: 12px; color: #5D8FA0; font-weight: 500; }

.note-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding-top: 6px; margin-top: 4px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}
.note-time {
  font-size: 11px; color: #86868B; letter-spacing: .3px;
  font-variant-numeric: tabular-nums;
}
.note-actions { display: flex; gap: 2px; }
.note-actions .el-button { padding: 4px; color: #86868B; }
.note-actions .el-button:hover { color: #4A7A8C; }
.note-actions .active-pin { color: #E6A23C; }


.color-picker { display: flex; flex-wrap: wrap; gap: 6px; }
.color-picker :deep(.el-radio) { margin-right: 0 !important; }
.dot-yellow, .dot-pink, .dot-blue, .dot-green, .dot-purple, .dot-orange {
  display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; vertical-align: middle;
}
.dot-yellow { background: #FDF3C9; }
.dot-pink   { background: #FADBDB; }
.dot-blue   { background: #DBEAF3; }
.dot-green  { background: #DCF0DE; }
.dot-purple { background: #E6D9F0; }
.dot-orange { background: #FCE4CA; }
</style>
