<template>
  <div v-if="visible" class="gs-overlay" @click.self="close">
    <div class="gs-modal">
      <!-- 搜索输入区 -->
      <div class="gs-input-wrap">
        <el-icon class="gs-input-icon"><Search /></el-icon>
        <input
          ref="inputRef"
          v-model="keyword"
          class="gs-input"
          placeholder="搜索学生、班级、FAQ、模板…"
          @input="onSearch"
          @keydown.down.prevent="moveActive(1)"
          @keydown.up.prevent="moveActive(-1)"
          @keydown.enter.prevent="onEnter"
          @keydown.escape="close"
        />
        <kbd class="gs-kbd">ESC</kbd>
      </div>

      <!-- 搜索结果 -->
      <div class="gs-results">
        <div v-if="loading" class="gs-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>搜索中…</span>
        </div>

        <template v-else-if="hasResults">
          <div v-for="group in groupedResults" :key="group.category" class="gs-group">
            <div class="gs-group-header">
              <span class="gs-group-icon">{{ group.icon }}</span>
              <span>{{ group.label }}</span>
              <span class="gs-group-count">{{ group.items.length }}</span>
            </div>
            <div
              v-for="item in group.items"
              :key="`${group.category}-${item.id}`"
              class="gs-result-item"
              :class="{ active: getItemKey(group.category, item.id) === activeKey }"
              @mouseenter="activeKey = getItemKey(group.category, item.id)"
              @click="pick(group.category, item)"
            >
              <div class="gs-result-main">
                <span class="gs-result-name">{{ item.name }}</span>
                <span class="gs-result-sub" v-if="item.sub">{{ item.sub }}</span>
              </div>
              <el-icon class="gs-result-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </template>

        <div v-else-if="keyword && !loading" class="gs-empty">
          <div class="gs-empty-icon">🔍</div>
          <div>没有找到匹配的结果</div>
          <div class="gs-empty-hint">试试其他关键词，或检查拼写</div>
        </div>

        <div v-else class="gs-empty">
          <div class="gs-empty-icon">💡</div>
          <div>输入关键词开始搜索</div>
          <div class="gs-empty-hint">支持搜索：学生 · 班级 · FAQ · 模板</div>
        </div>
      </div>

      <!-- 底部提示 -->
      <div class="gs-footer">
        <span><kbd>↑↓</kbd> 选择</span>
        <span><kbd>↵</kbd> 打开</span>
        <span><kbd>esc</kbd> 关闭</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/api/index.js'
import mitt from '@/utils/eventBus.js'

const router = useRouter()
const visible = ref(false)
const keyword = ref('')
const results = ref({ students: [], classes: [], faqs: [], templates: [] })
const loading = ref(false)
const activeKey = ref(null)
const inputRef = ref()

let debounceTimer = null

// 分类配置
const categoryConfig = {
  students:  { label: '学生', icon: '🎓', route: (item) => `/students/${item.id}` },
  classes:   { label: '班级', icon: '🏫', route: (item) => `/classes/${item.id}` },
  faqs:      { label: 'FAQ',  icon: '❓', route: () => '/faqs' },
  templates: { label: '模板', icon: '📄', route: () => '/templates' },
}

// 将结果按类别分组
const groupedResults = computed(() => {
  const groups = []
  for (const [cat, config] of Object.entries(categoryConfig)) {
    const items = (results.value[cat] || []).slice(0, 5)
    if (items.length) {
      groups.push({ category: cat, ...config, items })
    }
  }
  return groups
})

const hasResults = computed(() =>
  Object.values(results.value).some(arr => arr.length > 0)
)

// 扁平化所有结果项（用于键盘导航）
const allFlatItems = computed(() => {
  const list = []
  for (const group of groupedResults.value) {
    for (const item of group.items) {
      list.push({ category: group.category, item, key: getItemKey(group.category, item.id) })
    }
  }
  return list
})

function getItemKey(category, id) {
  return `${category}:${id}`
}

function open() {
  visible.value = true
  keyword.value = ''
  results.value = { students: [], classes: [], faqs: [], templates: [] }
  activeKey.value = null
  nextTick(() => inputRef.value?.focus())
}

function close() {
  visible.value = false
  if (debounceTimer) clearTimeout(debounceTimer)
}

function onSearch() {
  activeKey.value = null
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    const q = keyword.value?.trim()
    if (!q) {
      results.value = { students: [], classes: [], faqs: [], templates: [] }
      return
    }
    loading.value = true
    try {
      const data = await http.get('/search', { params: { q } })
      // 后端可能返回 { students, classes, faqs, templates } 或统一 items
      if (data && typeof data === 'object' && !Array.isArray(data)) {
        results.value = {
          students:  data.students  || [],
          classes:   data.classes   || [],
          faqs:      data.faqs      || [],
          templates: data.templates || [],
        }
      } else if (Array.isArray(data)) {
        // 兜底：全部放学生
        results.value = { students: data, classes: [], faqs: [], templates: [] }
      }
      // 设置 active 到第一项
      if (allFlatItems.value.length) {
        activeKey.value = allFlatItems.value[0].key
      }
    } catch {
      results.value = { students: [], classes: [], faqs: [], templates: [] }
    } finally {
      loading.value = false
    }
  }, 300)
}

function moveActive(delta) {
  const list = allFlatItems.value
  if (!list.length) return
  const currentIdx = list.findIndex(i => i.key === activeKey.value)
  const nextIdx = (currentIdx + delta + list.length) % list.length
  activeKey.value = list[nextIdx].key
}

function onEnter() {
  const found = allFlatItems.value.find(i => i.key === activeKey.value)
  if (found) pick(found.category, found.item)
}

function pick(category, item) {
  const config = categoryConfig[category]
  if (config) {
    visible.value = false
    router.push(config.route(item))
  }
}

// 全局快捷键 Cmd+K / Ctrl+K
function onKeyDown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    if (visible.value) close()
    else open()
  }
}

onMounted(() => {
  document.addEventListener('keydown', onKeyDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeyDown)
})

// 事件总线兼容
mitt.on('global-search:open', open)
onBeforeUnmount(() => mitt.off('global-search:open', open))
</script>

<style scoped>
.gs-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(20, 30, 50, 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 12vh;
  animation: gs-fade-in 0.15s ease;
}

@keyframes gs-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.gs-modal {
  width: 580px;
  max-height: 70vh;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(50, 80, 120, 0.3), 0 0 0 1px rgba(91, 146, 229, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: gs-slide-down 0.2s ease;
}

@keyframes gs-slide-down {
  from { transform: translateY(-16px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.gs-input-wrap {
  display: flex;
  align-items: center;
  padding: 14px 18px;
  gap: 10px;
  border-bottom: 1px solid #E8EEF5;
  background: linear-gradient(180deg, #F8FBFF 0%, #fff 100%);
}

.gs-input-icon {
  color: #5B92E5;
  font-size: 20px;
  flex-shrink: 0;
}

.gs-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 15px;
  color: #303133;
  background: transparent;
  font-family: inherit;
}

.gs-input::placeholder {
  color: #B0BAC8;
}

.gs-kbd {
  background: #F0F3F8;
  border: 1px solid #D8DFE9;
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 11px;
  color: #8896A7;
  font-family: inherit;
}

.gs-results {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
  max-height: 420px;
}

.gs-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #8896A7;
  justify-content: center;
}

.gs-group {
  margin-bottom: 4px;
}

.gs-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 8px 4px;
  font-size: 12px;
  font-weight: 600;
  color: #5B92E5;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.gs-group-icon {
  font-size: 14px;
}

.gs-group-count {
  background: #EBF2FC;
  color: #5B92E5;
  border-radius: 10px;
  padding: 0 6px;
  font-size: 11px;
  font-weight: 500;
  margin-left: auto;
}

.gs-result-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s;
}

.gs-result-item:hover,
.gs-result-item.active {
  background: #EBF2FC;
}

.gs-result-main {
  flex: 1;
  min-width: 0;
}

.gs-result-name {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.gs-result-sub {
  display: block;
  font-size: 12px;
  color: #8896A7;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gs-result-arrow {
  color: #B0BAC8;
  flex-shrink: 0;
}

.gs-empty {
  text-align: center;
  padding: 32px 20px;
  color: #8896A7;
  font-size: 13px;
}

.gs-empty-icon {
  font-size: 28px;
  margin-bottom: 8px;
  opacity: 0.5;
}

.gs-empty-hint {
  font-size: 12px;
  color: #B0BAC8;
  margin-top: 4px;
}

.gs-footer {
  display: flex;
  gap: 16px;
  padding: 10px 18px;
  border-top: 1px solid #E8EEF5;
  background: #FAFBFD;
  font-size: 12px;
  color: #8896A7;
}

.gs-footer kbd {
  background: #F0F3F8;
  border: 1px solid #D8DFE9;
  border-radius: 3px;
  padding: 0 4px;
  font-size: 11px;
  margin-right: 3px;
  font-family: inherit;
}
</style>
