<template>
  <el-dialog
    v-model="visible"
    class="global-search-dialog"
    :show-close="false"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
    top="12vh"
    width="560px"
    @open="onOpen"
  >
    <template #header>
      <div style="display:flex;align-items:center;gap:8px;">
        <el-icon><Search /></el-icon>
        <span>全局搜索 · 学生（学号/姓名/拼音/班级名，均实时无缓存）</span>
      </div>
    </template>
    <div class="global-search-panel">
      <el-input
        ref="inputRef"
        v-model="keyword"
        placeholder="输入学号 / 姓名 / 拼音首字母（示例：张、20250502、zyt、网安）"
        clearable
        @input="onSearch"
        @keydown.down.prevent="moveActive(1)"
        @keydown.up.prevent="moveActive(-1)"
        @keydown.enter.prevent="onEnter"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>

      <div class="global-search-results">
        <div v-if="loading" class="empty-hint">搜索中…</div>
        <template v-else-if="results.length">
          <div
            v-for="(item, i) in results"
            :key="item.id"
            class="global-search-item"
            :class="{ active: i === activeIdx }"
            @mouseenter="activeIdx = i"
            @click="pick(item)"
          >
            <div>
              <span class="name">{{ item.name }}</span>
              <span class="sub" style="margin-left:8px">
                {{ item.student_no }} · {{ item.class_name || '—' }} · {{ item.major || '' }}
              </span>
            </div>
            <el-icon><ArrowRight /></el-icon>
          </div>
        </template>
        <div v-else-if="keyword" class="empty-hint">
          <div class="icon">🔍</div>
          <div>没有找到匹配的学生</div>
          <div class="text-muted" style="font-size:12px;margin-top:4px;">
            试试：改为姓氏、学号前缀、班级名（如"网安2501"）、拼音首字母（如"zyt"）
          </div>
        </div>
        <div v-else class="empty-hint">
          <div class="icon">💡</div>
          <div>请输入关键词开始搜索</div>
          <div class="text-muted" style="font-size:12px;margin-top:6px;">
            回车 / 点击 = 进入学生 360；↑↓ 键选择；Esc 关闭
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { searchStudents } from '@/api/students.js'
import mitt from '@/utils/eventBus.js'

const router = useRouter()
const visible = ref(false)
const keyword = ref('')
const results = ref([])
const loading = ref(false)
const activeIdx = ref(0)
const inputRef = ref()

let debounceTimer = null

function open() {
  visible.value = true
  keyword.value = ''
  results.value = []
  activeIdx.value = 0
}

function onOpen() {
  nextTick(() => inputRef.value?.focus())
}

function onSearch() {
  activeIdx.value = 0
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    if (!keyword.value?.trim()) {
      results.value = []
      return
    }
    loading.value = true
    try {
      // ⚠️ 无缓存：每次都发新请求（axios 拦截器已加 _t 时间戳）
      const data = await searchStudents(keyword.value.trim(), 50)
      results.value = Array.isArray(data) ? data : (data?.items || [])
    } catch {
      results.value = []
    } finally {
      loading.value = false
    }
  }, 300)  // 300ms debounce（air 硬要求）
}

function moveActive(delta) {
  if (!results.value.length) return
  activeIdx.value = (activeIdx.value + delta + results.value.length) % results.value.length
}

function onEnter() {
  if (!results.value.length) return
  pick(results.value[activeIdx.value])
}

function pick(item) {
  visible.value = false
  router.push(`/students/${item.id}`)
}

mitt.on('global-search:open', open)
onBeforeUnmount(() => mitt.off('global-search:open', open))
</script>
