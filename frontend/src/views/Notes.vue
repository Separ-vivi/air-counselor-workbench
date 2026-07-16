<template>
  <div class="notes-page">
    <div class="page-header">
      <h2>📝 记事本</h2>
      <div class="header-actions">
        <el-input
          v-model="keyword"
          placeholder="搜索标题/内容/标签"
          clearable
          :prefix-icon="Search"
          style="width: 260px"
          @keyup.enter="load"
          @clear="load"
        />
        <el-button type="primary" :icon="Plus" @click="onCreate">新建</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" @tab-change="load" class="cat-tabs">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="📌 待办 Todo" name="todo" />
      <el-tab-pane label="📄 备忘 Memo" name="memo" />
      <el-tab-pane label="💡 想法 Idea" name="idea" />
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
      >
        <div class="note-header">
          <span class="note-title" @click="onEdit(n)">{{ n.title || '(无标题)' }}</span>
          <el-icon v-if="n.pinned" class="pin-icon"><Top /></el-icon>
        </div>
        <div class="note-body" @click="onEdit(n)">{{ n.content || '(空)' }}</div>
        <div class="note-meta">
          <el-tag v-if="n.priority === 2" type="danger" size="small" effect="light">高</el-tag>
          <el-tag v-else-if="n.priority === 1" type="warning" size="small" effect="light">中</el-tag>
          <el-tag v-if="n.due_date" size="small" effect="plain">
            <el-icon><Calendar /></el-icon>&nbsp;{{ n.due_date }}
          </el-tag>
          <span v-if="n.tags" class="tag-list">{{ n.tags }}</span>
        </div>
        <div class="note-actions">
          <el-tooltip :content="n.status === 'done' ? '标记未完成' : '标记完成'" v-if="n.category === 'todo'">
            <el-button link :icon="n.status === 'done' ? RefreshLeft : Check" @click="onToggle(n)" />
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
            <el-radio-button label="memo">📄 备忘</el-radio-button>
            <el-radio-button label="todo">📌 待办</el-radio-button>
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
import {
  Plus, Search, Edit, Delete, Top, Check, Calendar, RefreshLeft
} from '@element-plus/icons-vue'
import { notesApi } from '@/api/productivity.js'

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
  priority: 0, due_date: '', tags: '', pinned: false, color: 'yellow',
})

async function load() {
  loading.value = true
  try {
    const params = {}
    if (activeTab.value) params.category = activeTab.value
    if (activeTab.value === 'todo' && statusFilter.value) params.status = statusFilter.value
    if (keyword.value) params.keyword = keyword.value
    const { data } = await notesApi.list(params)
    list.value = data || []
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function onCreate() {
  form.value = {
    id: null,
    title: '', content: '',
    category: activeTab.value || 'memo',
    status: 'active', priority: 0, due_date: '', tags: '',
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

onMounted(load)
</script>

<style scoped>
.notes-page { padding: 20px; }
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 12px; }
.cat-tabs { margin-bottom: 12px; }
.filter-row { margin-bottom: 12px; }

.note-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.note-card {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid transparent;
  box-shadow: 0 2px 8px rgba(74,122,140,.06);
  display: flex; flex-direction: column; gap: 8px;
  transition: transform .12s, box-shadow .12s;
  min-height: 140px;
}
.note-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(74,122,140,.14); }
.note-card.done { opacity: .55; }
.note-card.done .note-title { text-decoration: line-through; }
.note-card.pinned { border-color: rgba(74,122,140,.35); }
.note-card.color-yellow { background: #FDF3C9; }
.note-card.color-pink   { background: #FADBDB; }
.note-card.color-blue   { background: #DBEAF3; }
.note-card.color-green  { background: #DCF0DE; }
.note-card.color-purple { background: #E6D9F0; }
.note-card.color-orange { background: #FCE4CA; }

.note-header { display: flex; justify-content: space-between; align-items: center; }
.note-title { font-weight: 600; font-size: 15px; color: #3A3A3A; cursor: pointer; word-break: break-all; }
.note-title:hover { color: #4A7A8C; }
.pin-icon { color: #E58B3E; }
.note-body {
  flex: 1;
  font-size: 13px; color: #4a4a4a; line-height: 1.6;
  white-space: pre-wrap; word-break: break-all;
  max-height: 96px; overflow: hidden;
  cursor: pointer;
}
.note-meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.tag-list { font-size: 12px; color: #7B7B7B; }
.note-actions {
  display: flex; justify-content: flex-end; gap: 4px;
  border-top: 1px dashed rgba(0,0,0,.08); padding-top: 6px;
}
.note-actions .el-button { padding: 4px; }
.note-actions .active-pin { color: #E58B3E; }

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
