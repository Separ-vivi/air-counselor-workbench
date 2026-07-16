<template>
  <div class="topbar-root">
    <!-- 左：返回按钮（深入页显示） + 三级架构切换器 -->
    <div class="left-side">
      <el-tooltip content="返回上一页">
        <el-button
          v-if="showBack"
          link
          class="back-btn"
          @click="goBack"
        >
          <el-icon><ArrowLeft /></el-icon>
          <span style="margin-left:4px">返回</span>
        </el-button>
      </el-tooltip>
      <OrgSelector />
    </div>

    <!-- 中：全局搜索 -->
    <div class="mid-side">
      <div class="search-trigger" @click="openSearch">
        <el-icon><Search /></el-icon>
        <span class="hint-text">搜学号 / 姓名 / 拼音（支持"张""20250502""zyt""网安"）</span>
        <span class="hotkey">Ctrl + K</span>
      </div>
    </div>

    <!-- 右：辅助操作 -->
    <div class="right-side">
      <el-tooltip content="刷新组织树">
        <el-button link @click="reloadOrg">
          <el-icon :class="{ spinning: orgLoading }"><Refresh /></el-icon>
        </el-button>
      </el-tooltip>
      <el-tooltip content="设置">
        <el-button link @click="$router.push('/org')">
          <el-icon><Setting /></el-icon>
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Search, Refresh, Setting } from '@element-plus/icons-vue'
import { useOrgStore } from '@/stores/org.js'
import OrgSelector from './OrgSelector.vue'
import mitt from '@/utils/eventBus.js'

const route = useRoute()
const router = useRouter()

// 判断当前是不是深入页（学生 360 / 班级 360 等），有 :id 参数即认为需要返回按钮
const showBack = computed(() => {
  const p = route.path || ''
  // 顶级主菜单页不显示返回；其他所有深入页都显示
  const topLevel = new Set([
    '/', '/dashboard', '/students', '/classes', '/org', '/smart-import',
    '/system', '/notes', '/calendar', '/projects', '/summary',
  ])
  if (topLevel.has(p)) return false
  // /module/xxx 顶级模块页也不显示
  if (/^\/module\/[^/]+$/.test(p)) return false
  return true
})

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/dashboard')
  }
}

const orgStore = useOrgStore()
const orgLoading = computed(() => orgStore.treeLoading)

function openSearch() {
  mitt.emit('global-search:open')
}

async function reloadOrg() {
  try {
    await orgStore.loadTree(true)
  } catch {/* handled in http interceptor */}
}

/** Ctrl+K / ⌘+K 快捷键 */
function onKeydown(e) {
  const isK = e.key === 'k' || e.key === 'K'
  if (isK && (e.ctrlKey || e.metaKey)) {
    e.preventDefault()
    openSearch()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.topbar-root {
  height: 60px;
  background: var(--color-topbar);
  border-bottom: 1px solid var(--color-card-border);
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 20px;
  flex-shrink: 0;
}
.left-side { flex-shrink: 0; display: flex; align-items: center; gap: 8px; }
.back-btn {
  color: #4A7A8C;
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(74, 122, 140, 0.06);
  transition: background .15s;
}
.back-btn:hover { background: rgba(74, 122, 140, 0.14); }
.mid-side { flex: 1; display: flex; justify-content: center; }
.right-side { display: flex; gap: 8px; align-items: center; }

.search-trigger {
  width: 100%;
  max-width: 560px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #EDF1F4;
  border: 1px solid var(--color-card-border);
  padding: 8px 14px;
  border-radius: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all .18s;
}
.search-trigger:hover {
  background: #DDE4EA;
  border-color: var(--color-macaron-blue);
}
.search-trigger .hint-text {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.search-trigger .hotkey {
  background: rgba(74, 122, 140, .12);
  color: var(--color-sidebar-active);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-family: monospace;
}
.spinning { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
