<template>
  <div>
    <div class="panel-head">
      <div><span class="title">🚩 党团支部（{{ data?.class_name || '' }}）</span></div>
      <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="5">
        <el-card shadow="never" class="stat-card"><div class="stat-lbl">总人数</div>
          <div class="stat-val" style="color:#409EFF">{{ data?.total ?? 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card shadow="never" class="stat-card"><div class="stat-lbl">党员 / 预备党员</div>
          <div class="stat-val" style="color:#F56C6C">{{ (data?.party_members?.length || 0) + (data?.reserved_members?.length || 0) }}</div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card shadow="never" class="stat-card"><div class="stat-lbl">积极分子</div>
          <div class="stat-val" style="color:#E6A23C">{{ data?.activists?.length || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card shadow="never" class="stat-card"><div class="stat-lbl">团员</div>
          <div class="stat-val" style="color:#67C23A">{{ data?.league_members?.length || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="never" class="stat-card"><div class="stat-lbl">群众</div>
          <div class="stat-val" style="color:#909399">{{ data?.masses?.length || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-bottom:12px" v-if="data?.monitor || data?.league_secretary">
      <div style="display:flex;gap:18px;flex-wrap:wrap;font-size:13px">
        <span v-if="data.monitor"><el-tag type="primary" effect="dark" size="small">班长</el-tag> <b>{{ data.monitor }}</b></span>
        <span v-if="data.league_secretary"><el-tag type="warning" effect="dark" size="small">团支书</el-tag> <b>{{ data.league_secretary }}</b></span>
      </div>
    </el-card>

    <el-tabs v-model="activeGroup" v-loading="loading">
      <el-tab-pane
        v-for="g in groups"
        :key="g.name"
        :label="`${g.title} (${(data?.[g.key]||[]).length})`"
        :name="g.name"
      >
        <el-table :data="data?.[g.key] || []" stripe border size="small" max-height="460">
          <el-table-column type="index" width="55" label="#" />
          <el-table-column prop="student_no" label="学号" width="140" sortable />
          <el-table-column prop="name" label="姓名" min-width="100" sortable />
          <el-table-column prop="political_status" label="政治面貌" min-width="140" sortable />
          <el-table-column prop="phone" label="联系电话" min-width="140" sortable />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getClassPartyBranch } from '@/api/class360.js'

const props = defineProps({ cid: { type: Number, required: true } })
const data = ref(null)
const loading = ref(false)
const activeGroup = ref('party')

async function load() {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    data.value = await getClassPartyBranch(props.cid)
  } catch (e) {
    data.value = null
  } finally { loading.value = false }
}

watch(() => props.cid, load, { immediate: false })
onMounted(load)

// 5 个成员分组（对应后端返回的 5 组名单字段）
const groups = [
  { name: 'party',     key: 'party_members',    title: '党员' },
  { name: 'reserved',  key: 'reserved_members', title: '预备党员' },
  { name: 'activists', key: 'activists',        title: '积极分子' },
  { name: 'league',    key: 'league_members',   title: '团员' },
  { name: 'masses',    key: 'masses',           title: '群众' },
]
</script>

<style scoped>
.panel-head { display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px; }
.panel-head .title { font-weight: 600; color: #4A7A8C; font-size: 15px; }
.stat-card { border-radius: 12px; text-align: center; }
.stat-lbl { color: #909399; font-size: 12px; margin-bottom: 6px; }
.stat-val { font-size: 22px; font-weight: 600; }
</style>
