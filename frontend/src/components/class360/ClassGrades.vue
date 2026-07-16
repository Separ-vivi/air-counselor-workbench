<template>
  <div>
    <div class="panel-head">
      <div><span class="title">📈 本班学业统计</span><span class="text-muted count">&nbsp;共 {{ rows.length }} 条成绩</span></div>
      <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
    </div>

    <el-row v-if="stats" :gutter="12" class="mb-16">
      <el-col :span="6">
        <div class="mini-stat"><div class="label">平均分</div><div class="value">{{ stats.avg }}</div></div>
      </el-col>
      <el-col :span="6">
        <div class="mini-stat"><div class="label">及格率</div><div class="value">{{ stats.passRate }}%</div></div>
      </el-col>
      <el-col :span="6">
        <div class="mini-stat"><div class="label">优秀率(≥85)</div><div class="value">{{ stats.excellentRate }}%</div></div>
      </el-col>
      <el-col :span="6">
        <div class="mini-stat"><div class="label">挂科条数</div><div class="value red">{{ stats.failCount }}</div></div>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="rows" border stripe size="small" height="480" empty-text="暂无本班成绩记录">
      <el-table-column prop="student_no" label="学号" width="130" />
      <el-table-column prop="name" label="姓名" width="100">
        <template #default="{ row }">
          <router-link v-if="row.student_id" :to="`/students/${row.student_id}`" class="link">{{ row.name }}</router-link>
          <span v-else>{{ row.name || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="semester" label="学期" width="120" />
      <el-table-column prop="course_name" label="课程" min-width="180" />
      <el-table-column prop="score" label="成绩" width="90">
        <template #default="{ row }">
          <span :class="{ 'text-danger': row.score != null && row.score < 60 }">
            {{ row.score != null ? Number(row.score).toFixed(1) : '—' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="gpa" label="绩点" width="80"
        :formatter="(r) => r.gpa != null ? Number(r.gpa).toFixed(2) : '—'" />
      <el-table-column prop="credit" label="学分" width="80" />
      <el-table-column prop="is_repair" label="重修" width="80"
        :formatter="(r) => r.is_repair ? '是' : ''" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getClassGrades } from '@/api/class360.js'

const props = defineProps({ cid: { type: Number, required: true } })
const rows = ref([])
const loading = ref(false)

const stats = computed(() => {
  if (!rows.value.length) return null
  const scored = rows.value.filter(r => r.score != null)
  if (!scored.length) return null
  const avg = scored.reduce((s, r) => s + Number(r.score), 0) / scored.length
  const pass = scored.filter(r => r.score >= 60).length
  const excel = scored.filter(r => r.score >= 85).length
  const fail = scored.filter(r => r.score < 60).length
  return {
    avg: avg.toFixed(1),
    passRate: ((pass / scored.length) * 100).toFixed(1),
    excellentRate: ((excel / scored.length) * 100).toFixed(1),
    failCount: fail
  }
})

async function load() {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    rows.value = await getClassGrades(props.cid) || []
  } finally { loading.value = false }
}
watch(() => props.cid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.panel-head { display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px; }
.panel-head .title { font-weight: 600; color: var(--color-sidebar-active); font-size: 15px; }
.panel-head .count { font-size: 12px; }
.mini-stat {
  background: var(--color-macaron-blue);
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}
.mini-stat .label { color: var(--color-sidebar-active); font-size: 12px; }
.mini-stat .value { font-size: 22px; font-weight: 700; color: var(--color-sidebar-active); }
.mini-stat .value.red { color: #c1443f; }
.text-danger { color: #c1443f; font-weight: 600; }
.link { color: var(--color-sidebar); }
</style>
