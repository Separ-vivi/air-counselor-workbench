<template>
  <div>
    <div class="panel-head">
      <div><span class="title">🎯 本班党团发展进度</span></div>
      <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
    </div>

    <!-- 6 阶段人数分布卡片 -->
    <el-row :gutter="12" class="mb-16">
      <el-col v-for="s in stages" :key="s.key" :span="4">
        <div class="stage-card" :style="{ background: s.bg }">
          <div class="stage-label">{{ s.label }}</div>
          <div class="stage-value" :style="{ color: s.color }">{{ stageCounts[s.key] || 0 }}</div>
          <div class="stage-hint">人</div>
        </div>
      </el-col>
    </el-row>

    <!-- 全班总体进度条（横向 stepper 汇总视图，展示各阶段人数占比） -->
    <el-card shadow="never" class="overall-card" v-if="rows.length">
      <template #header><span style="font-weight:600">📈 班级党团发展总体分布</span></template>
      <el-steps :active="activeIdx" finish-status="success" align-center>
        <el-step v-for="(s, idx) in stages" :key="s.key"
                 :title="s.label"
                 :description="`${stageCounts[s.key] || 0} 人 · ${percent(s.key)}%`" />
      </el-steps>
    </el-card>

    <!-- 明细表：可展开查看单个学生 stepper 轨迹 -->
    <el-table v-loading="loading" :data="rows" border stripe size="small" height="500"
              empty-text="暂无本班党团数据" style="margin-top:12px">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-block">
            <div style="margin-bottom:8px; font-weight:600; color:#4A7A8C">
              🌱 {{ row.name }} 的党团发展轨迹
            </div>
            <el-steps v-if="row.history && row.history.length"
                      :active="row.history.length - 1"
                      finish-status="success" align-center>
              <el-step v-for="(h, i) in row.history" :key="i"
                       :title="h.stage"
                       :description="h.stage_date + (h.contact_person ? ' · 联系人 ' + h.contact_person : '')" />
            </el-steps>
            <el-empty v-else :image-size="60" description="暂无发展记录（仅政治面貌为 群众/团员）" />
            <div v-if="row.history && row.history.length" style="margin-top:8px; color:#909399; font-size:12px">
              共 {{ row.history.length }} 条阶段变更 · 最后更新 {{ row.stage_date || '—' }}
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="student_no" label="学号" width="120" />
      <el-table-column prop="name" label="姓名" width="90">
        <template #default="{ row }">
          <router-link v-if="row.student_id" :to="`/students/${row.student_id}`" class="link">{{ row.name }}</router-link>
          <span v-else>{{ row.name || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="political_status" label="政治面貌" width="120">
        <template #default="{ row }">
          <el-tag :type="stageTag(row.stage)" size="small" effect="light">
            {{ row.political_status || row.stage || '—' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="stage" label="当前发展阶段" width="120">
        <template #default="{ row }">
          <el-tag :type="stageTag(row.stage)" size="small">{{ row.stage || '—' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="join_league_date" label="入团时间" width="120">
        <template #default="{ row }">{{ row.join_league_date || '—' }}</template>
      </el-table-column>
      <el-table-column prop="join_party_date" label="入党时间" width="120">
        <template #default="{ row }">{{ row.join_party_date || '—' }}</template>
      </el-table-column>
      <el-table-column prop="stage_date" label="最近阶段日期" width="130">
        <template #default="{ row }">{{ row.stage_date || row.join_date || '—' }}</template>
      </el-table-column>
      <el-table-column prop="contact_person" label="联系人" width="110" />
      <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
    </el-table>
    <div v-if="rows.length" class="tip">
      💡 点击左侧箭头展开可查看该学生完整发展轨迹（stepper）
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getClassParty } from '@/api/class360.js'

const props = defineProps({ cid: { type: Number, required: true } })
const rows = ref([])
const loading = ref(false)

// v3j-B: 6 阶段体系（与后端 _norm_stage 保持一致）
const stages = [
  { key: '群众',       label: '群众',       bg: '#F4F4F5', color: '#909399' },
  { key: '入党申请人', label: '入党申请人', bg: '#ECF5FF', color: '#409EFF' },
  { key: '积极分子',   label: '积极分子',   bg: '#F0F9EB', color: '#67C23A' },
  { key: '发展对象',   label: '发展对象',   bg: '#FDF6EC', color: '#E6A23C' },
  { key: '预备党员',   label: '预备党员',   bg: '#FEF0F0', color: '#F56C6C' },
  { key: '正式党员',   label: '正式党员',   bg: '#FCE7E7', color: '#C45656' }
]

const stageCounts = computed(() => {
  const map = {}
  rows.value.forEach(r => {
    const s = r.stage || '群众'
    map[s] = (map[s] || 0) + 1
  })
  return map
})

// 总体进度条 active：取有人数的最靠后阶段
const activeIdx = computed(() => {
  let maxIdx = 0
  stages.forEach((s, i) => {
    if ((stageCounts.value[s.key] || 0) > 0) maxIdx = Math.max(maxIdx, i)
  })
  return maxIdx
})

function percent(key) {
  if (!rows.value.length) return 0
  return (((stageCounts.value[key] || 0) * 100) / rows.value.length).toFixed(1)
}

function stageTag(s) {
  if (s === '正式党员') return 'danger'
  if (s === '预备党员') return 'warning'
  if (s === '发展对象') return 'warning'
  if (s === '积极分子') return 'success'
  if (s === '入党申请人') return 'primary'
  return 'info'
}

async function load() {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    rows.value = (await getClassParty(props.cid)) || []
  } finally { loading.value = false }
}
watch(() => props.cid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.panel-head { display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px; }
.panel-head .title { font-weight: 600; color: #4A7A8C; font-size: 15px; }
.stage-card {
  border-radius: 12px;
  padding: 12px 8px;
  text-align: center;
  border: 1px solid rgba(0,0,0,0.04);
}
.stage-label { color: #4A7A8C; font-size: 12px; }
.stage-value { font-size: 22px; font-weight: 700; }
.stage-hint { color: #909399; font-size: 11px; }
.overall-card { margin-top: 4px; }
.expand-block { padding: 12px 24px; background: #FAFCFE; border-radius: 8px; }
.link { color: #4A7A8C; text-decoration: none; }
.link:hover { text-decoration: underline; }
.tip { margin-top: 8px; color: #909399; font-size: 12px; }
</style>
