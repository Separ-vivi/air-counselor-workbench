<template>
  <div>
    <div class="panel-head">
      <div><span class="title">📋 班级花名册</span><span class="text-muted count">&nbsp;共 {{ rows.length }} 人</span></div>
      <div>
        <el-input v-model="kw" size="small" placeholder="按姓名/学号/电话过滤..." clearable style="width:220px">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="filtered" border stripe size="small" height="520">
      <el-table-column type="index" width="55" label="#" />
      <el-table-column prop="student_no" label="学号" width="130" />
      <el-table-column prop="name" label="姓名" min-width="100">
        <template #default="{ row }">
          <router-link :to="`/students/${row.id}`" class="link">{{ row.name }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="gender" label="性别" width="70" />
      <el-table-column prop="political_status" label="政治面貌" min-width="120" />
      <el-table-column prop="phone" label="联系电话" min-width="130" />
      <el-table-column prop="warning_status" label="学业预警" width="100">
        <template #default="{ row }">
          <span class="status-chip" :class="row.warning_status">
            <span class="status-dot" :class="row.warning_status" />
            {{ warnLabel(row.warning_status) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="$router.push(`/students/${row.id}`)">
            360
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getClassStudents } from '@/api/class360.js'

const props = defineProps({ cid: { type: Number, required: true } })
const rows = ref([])
const loading = ref(false)
const kw = ref('')

const filtered = computed(() => {
  if (!kw.value) return rows.value
  const k = kw.value.toLowerCase()
  return rows.value.filter(r =>
    (r.name || '').toLowerCase().includes(k) ||
    (r.student_no || '').includes(k) ||
    (r.phone || '').includes(k)
  )
})

function warnLabel(s) {
  if (s === 'red') return '红灯'
  if (s === 'yellow') return '黄灯'
  return '绿灯'
}

async function load() {
  loading.value = true
  try {
    rows.value = await getClassStudents(props.cid) || []
  } finally { loading.value = false }
}

watch(() => props.cid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.panel-head { display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px; }
.panel-head .title { font-weight: 600; color: var(--color-sidebar-active); font-size: 15px; }
.panel-head .count { font-size: 12px; }
.panel-head > div:last-child { display:flex; gap: 8px; }
.link { color: var(--color-sidebar); font-weight: 500; }
</style>
