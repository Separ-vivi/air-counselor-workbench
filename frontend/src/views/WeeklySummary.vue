<template>
  <div class="ws-page">
    <div class="page-header">
      <h2>📊 周汇总</h2>
      <div class="header-actions">
        <el-button type="primary" :icon="MagicStick" @click="onGenerate" :loading="generating">
          自动生成本周汇总
        </el-button>
        <el-button :icon="Plus" @click="onCreate">手写一份</el-button>
      </div>
    </div>

    <div class="ws-layout">
      <!-- 左侧列表 -->
      <div class="ws-list" v-loading="loading">
        <el-empty v-if="!loading && list.length === 0" description="暂无周汇总，点右上「自动生成」" :image-size="80" />
        <div
          v-for="s in list"
          :key="s.id"
          class="ws-item"
          :class="{ active: current?.id === s.id }"
          @click="onSelect(s)"
        >
          <div class="ws-item-title">{{ s.title || `${s.week_start} ~ ${s.week_end}` || `汇总 #${s.id}` }}</div>
          <div class="ws-item-meta">
            <el-tag size="small" :type="s.summary_type === 'auto' ? 'primary' : 'success'" effect="light">
              {{ s.summary_type === 'auto' ? '自动' : '手写' }}
            </el-tag>
            <span class="date">{{ formatTime(s.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧详情 -->
      <div class="ws-detail">
        <el-empty v-if="!current" description="选择左侧一份汇总查看" />
        <div v-else class="detail-body">
          <div class="detail-header">
            <div>
              <h3>{{ current.title || `${current.week_start} ~ ${current.week_end}` }}</h3>
              <div class="detail-sub">
                <el-tag size="small">{{ current.summary_type === 'auto' ? '自动生成' : '手写' }}</el-tag>
                <span>创建于 {{ current.created_at }}</span>
              </div>
            </div>
            <div class="detail-actions">
              <el-button :icon="Edit" @click="onEditCurrent">编辑</el-button>
              <el-button :icon="Delete" @click="onDeleteCurrent" type="danger" plain>删除</el-button>
            </div>
          </div>
          <div class="detail-content">
            <pre>{{ current.content }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialog" :title="form.id ? '编辑汇总' : '新建汇总'" width="640px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="例：第 28 周工作汇总" maxlength="200" />
        </el-form-item>
        <el-form-item label="周起">
          <el-date-picker v-model="form.week_start" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="周止">
          <el-date-picker v-model="form.week_end" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="14" placeholder="支持 Markdown 结构" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="onSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, MagicStick } from '@element-plus/icons-vue'
import { summariesApi } from '@/api/productivity.js'

const list = ref([])
const current = ref(null)
const loading = ref(false)
const generating = ref(false)
const saving = ref(false)

const editDialog = ref(false)
const form = ref({ id: null, title: '', week_start: '', week_end: '', content: '' })

async function load(keepCurrent = false) {
  loading.value = true
  try {
    const { data } = await summariesApi.list()
    list.value = data || []
    if (!keepCurrent) {
      current.value = list.value[0] || null
      if (current.value?.id) await fetchDetail(current.value.id)
    }
  } finally { loading.value = false }
}

async function fetchDetail(id) {
  try {
    const { data } = await summariesApi.get(id)
    current.value = data
  } catch {}
}

async function onSelect(s) {
  current.value = s
  await fetchDetail(s.id)
}

async function onGenerate() {
  generating.value = true
  try {
    const { data } = await summariesApi.generate({})
    ElMessage.success('已生成')
    await load()
    if (data.id) await fetchDetail(data.id)
  } finally { generating.value = false }
}

function onCreate() {
  form.value = { id: null, title: '', week_start: '', week_end: '', content: '' }
  editDialog.value = true
}

function onEditCurrent() {
  if (!current.value) return
  form.value = {
    id: current.value.id,
    title: current.value.title || '',
    week_start: current.value.week_start || '',
    week_end: current.value.week_end || '',
    content: current.value.content || '',
  }
  editDialog.value = true
}

async function onSave() {
  saving.value = true
  try {
    if (form.value.id) {
      await summariesApi.update(form.value.id, form.value)
      ElMessage.success('已更新')
    } else {
      // 后端 POST /weekly-summaries 未提供手写创建接口 → 走 update fallback：先 generate 后编辑
      // 简化：直接 PUT 一个新记录不可行；这里改用先 generate 再覆盖
      const { data: gen } = await summariesApi.generate({})
      await summariesApi.update(gen.id, form.value)
      ElMessage.success('已创建（基于自动生成模板覆盖）')
    }
    editDialog.value = false
    await load()
  } finally { saving.value = false }
}

async function onDeleteCurrent() {
  if (!current.value) return
  try {
    await ElMessageBox.confirm('确认删除此份汇总？', '提示', { type: 'warning' })
    await summariesApi.remove(current.value.id)
    ElMessage.success('已删除')
    current.value = null
    await load()
  } catch {}
}

function formatTime(t) {
  if (!t) return ''
  return t.slice(0, 10)
}

onMounted(load)
</script>

<style scoped>
.ws-page { padding: 20px; height: 100%; display: flex; flex-direction: column; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 8px; }

.ws-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  flex: 1;
  min-height: 500px;
}
.ws-list {
  border: 1px solid var(--color-card-border);
  border-radius: 12px;
  padding: 8px;
  overflow-y: auto;
  background: #fff;
}
.ws-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  margin-bottom: 6px;
  transition: background .12s;
}
.ws-item:hover { background: var(--color-page-bg); }
.ws-item.active { background: rgba(74,122,140,.10); border-color: rgba(74,122,140,.25); }
.ws-item-title { font-weight: 600; font-size: 13px; margin-bottom: 4px; }
.ws-item-meta { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #7B7B7B; }

.ws-detail {
  border: 1px solid var(--color-card-border);
  border-radius: 12px;
  background: #fff;
  padding: 20px;
  overflow-y: auto;
}
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.detail-header h3 { margin: 0 0 8px; }
.detail-sub { display: flex; gap: 8px; align-items: center; font-size: 12px; color: #7B7B7B; }
.detail-actions { display: flex; gap: 8px; }
.detail-content pre {
  background: var(--color-page-bg);
  padding: 16px;
  border-radius: 8px;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 14px;
  line-height: 1.75;
  color: #3A3A3A;
}
</style>
