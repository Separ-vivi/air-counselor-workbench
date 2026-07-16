<template>
  <div>
    <div class="panel-head">
      <div>
        <span class="title">📅 全维度时间线</span>
        <span class="text-muted count">&nbsp;共 {{ items.length }} 条</span>
      </div>
      <div>
        <el-select v-model="filterType" size="small" clearable placeholder="按类型过滤" style="width:160px">
          <el-option v-for="opt in typeOptions" :key="opt" :label="opt" :value="opt" />
        </el-select>
        <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </div>
    </div>

    <div v-if="loading" class="empty-hint"><div class="icon">⏳</div><div>加载中…</div></div>
    <div v-else-if="!filteredItems.length" class="empty-hint">
      <div class="icon">📅</div>
      <div>暂无时间线记录</div>
      <div class="text-muted" style="font-size:12px;margin-top:4px">
        新增学业/党团/心理/家庭等记录后，会自动汇集到这里
      </div>
    </div>

    <div v-else class="timeline-list">
      <div
        v-for="(item, i) in filteredItems"
        :key="i"
        class="timeline-item"
      >
        <div class="time">{{ item.date || item.event_date || item.time || '—' }}
          <el-tag size="small" style="margin-left:8px">{{ item.type || item.category || '事件' }}</el-tag>
        </div>
        <div class="title">{{ item.title || item.summary || item.event || '—' }}</div>
        <div v-if="item.detail || item.description || item.notes" class="desc">
          {{ item.detail || item.description || item.notes }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getTimeline } from '@/api/student360.js'

const props = defineProps({ sid: { type: Number, required: true } })
const items = ref([])
const loading = ref(false)
const filterType = ref('')

const typeOptions = computed(() => {
  const set = new Set()
  items.value.forEach(x => {
    if (x.type) set.add(x.type)
    else if (x.category) set.add(x.category)
  })
  return Array.from(set)
})
const filteredItems = computed(() => {
  if (!filterType.value) return items.value
  return items.value.filter(x => (x.type === filterType.value) || (x.category === filterType.value))
})

async function load() {
  loading.value = true
  try {
    const data = await getTimeline(props.sid, 100)
    items.value = Array.isArray(data) ? data : (data?.items || [])
  } finally { loading.value = false }
}

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.panel-head .title { font-weight: 600; color: var(--color-sidebar-active); font-size: 15px; }
.panel-head .count { font-size: 12px; }
.panel-head > div:last-child { display: flex; gap: 8px; align-items: center; }
.timeline-list { max-height: 600px; overflow-y: auto; padding-right: 6px; }
</style>
