<template>
  <div class="crud-panel">
    <div class="panel-header">
      <div>
        <span class="title">{{ title }}</span>
        <span class="count text-muted">&nbsp;共 {{ filteredRows.length }} 条</span>
      </div>
      <div class="panel-actions">
        <el-input
          v-if="searchable"
          v-model="filterKw"
          size="small"
          placeholder="过滤本表..."
          clearable
          style="width:180px"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button size="small" @click="onReload">
          <el-icon><Refresh /></el-icon>&nbsp;刷新
        </el-button>
        <el-button v-if="!readonly && onCreate" type="primary" size="small" @click="openCreate">
          <el-icon><Plus /></el-icon>&nbsp;新增
        </el-button>
      </div>
    </div>

    <el-table
      v-loading="loading"
      :data="pagedRows"
      stripe
      border
      empty-text="暂无记录"
      style="width:100%"
      size="small"
    >
      <el-table-column
        v-for="col in columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth || 100"
        :show-overflow-tooltip="true"
      >
        <template #default="{ row }">
          <span v-if="col.formatter">{{ col.formatter(row[col.prop], row) }}</span>
          <el-tag v-else-if="col.type === 'tag'" size="small" :type="col.tagType?.(row) || ''">
            {{ row[col.prop] || '—' }}
          </el-tag>
          <span v-else>{{ formatCell(col, row) }}</span>
        </template>
      </el-table-column>
      <el-table-column v-if="!readonly && (onUpdate || onDelete)" label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button v-if="onUpdate" link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm v-if="onDelete" title="确认删除该条记录？" @confirm="doDelete(row)">
            <template #reference>
              <el-button link type="danger" size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="filteredRows.length > pageSize"
      class="pagination"
      :current-page="page"
      :page-size="pageSize"
      :total="filteredRows.length"
      layout="prev, pager, next, total"
      @current-change="p => page = p"
    />

    <!-- CRUD 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑 · ' + title : '新增 · ' + title"
      :width="dialogWidth"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="110px"
        label-position="right"
      >
        <slot name="form" :form="form" :editing="editing">
          <el-form-item
            v-for="f in fields"
            :key="f.prop"
            :label="f.label"
            :prop="f.prop"
          >
            <el-input
              v-if="!f.type || f.type === 'text'"
              v-model="form[f.prop]"
              :placeholder="f.placeholder || `请输入${f.label}`"
              clearable
            />
            <el-input
              v-else-if="f.type === 'textarea'"
              v-model="form[f.prop]"
              type="textarea"
              :rows="3"
              :placeholder="f.placeholder || ''"
            />
            <el-input-number
              v-else-if="f.type === 'number'"
              v-model="form[f.prop]"
              :min="f.min"
              :max="f.max"
              :step="f.step || 1"
              :precision="f.precision"
              style="width:100%"
            />
            <el-select
              v-else-if="f.type === 'select'"
              v-model="form[f.prop]"
              :placeholder="`请选择${f.label}`"
              clearable
              style="width:100%"
            >
              <el-option
                v-for="opt in (f.options || [])"
                :key="opt.value ?? opt"
                :label="opt.label ?? opt"
                :value="opt.value ?? opt"
              />
            </el-select>
            <el-date-picker
              v-else-if="f.type === 'date'"
              v-model="form[f.prop]"
              type="date"
              value-format="YYYY-MM-DD"
              style="width:100%"
            />
            <el-switch v-else-if="f.type === 'switch'" v-model="form[f.prop]" />
          </el-form-item>
        </slot>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  title: { type: String, required: true },
  columns: { type: Array, required: true },
  fields:  { type: Array, default: () => [] },
  rows:    { type: Array, default: () => [] },
  rules:   { type: Object, default: () => ({}) },
  defaultForm: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
  searchable: { type: Boolean, default: true },
  pageSize: { type: Number, default: 15 },
  dialogWidth: { type: String, default: '640px' },
  onReload: { type: Function, default: () => {} },
  onCreate: { type: Function, default: null },  // async (payload) => {}
  onUpdate: { type: Function, default: null },  // async (id, payload) => {}
  onDelete: { type: Function, default: null }   // async (id) => {}
})

const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({})
const saving = ref(false)
const formRef = ref()
const filterKw = ref('')
const page = ref(1)

watch(filterKw, () => (page.value = 1))
watch(() => props.rows, () => {
  const maxPage = Math.max(1, Math.ceil(props.rows.length / props.pageSize))
  if (page.value > maxPage) page.value = maxPage
})

const filteredRows = computed(() => {
  if (!filterKw.value) return props.rows
  const k = filterKw.value.toLowerCase()
  return props.rows.filter(r =>
    Object.values(r).some(v => v != null && String(v).toLowerCase().includes(k))
  )
})
const pagedRows = computed(() => {
  const s = (page.value - 1) * props.pageSize
  return filteredRows.value.slice(s, s + props.pageSize)
})

function formatCell(col, row) {
  const v = row[col.prop]
  if (v === null || v === undefined || v === '') return '—'
  return v
}

function openCreate() {
  editing.value = null
  form.value = { ...(props.defaultForm || {}) }
  dialogVisible.value = true
}
function openEdit(row) {
  editing.value = row
  // 拷贝已有字段（只带 fields 中定义的 + 保留 id）
  const clone = { ...(props.defaultForm || {}) }
  props.fields.forEach(f => {
    if (row[f.prop] !== undefined) clone[f.prop] = row[f.prop]
  })
  form.value = clone
  dialogVisible.value = true
}
async function onSave() {
  if (formRef.value) {
    try { await formRef.value.validate() } catch { return }
  }
  // 只提交 fields 中定义过的字段
  const payload = {}
  for (const f of props.fields) {
    payload[f.prop] = form.value[f.prop] ?? null
  }
  saving.value = true
  try {
    if (editing.value) {
      if (!props.onUpdate) return
      await props.onUpdate(editing.value.id ?? editing.value.record_id, payload)
      ElMessage.success('更新成功')
    } else {
      if (!props.onCreate) return
      await props.onCreate(payload)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    props.onReload?.()
  } catch (e) {
    // 拦截器已提示，这里只保底
  } finally {
    saving.value = false
  }
}

async function doDelete(row) {
  if (!props.onDelete) return
  try {
    await props.onDelete(row.id ?? row.record_id)
    ElMessage.success('删除成功')
    props.onReload?.()
  } catch {/* handled */}
}

defineExpose({ openCreate, openEdit })
</script>

<style scoped>
.crud-panel { }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.panel-header .title { font-weight: 600; color: var(--color-sidebar-active); font-size: 15px; }
.panel-header .count { margin-left: 8px; font-size: 12px; }
.panel-actions { display: flex; gap: 8px; align-items: center; }
.pagination { margin-top: 12px; justify-content: end; }
</style>
