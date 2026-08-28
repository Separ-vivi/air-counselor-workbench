<template>
  <div class="tab-party">
    <div class="party-summary">
      <div class="party-stat" v-for="(stat, idx) in stats" :key="stat.label">
        <div class="p-val" :style="{color: colors[idx % colors.length]}">{{ stat.value }}</div>
        <div class="p-lbl">{{ stat.label }}</div>
      </div>
    </div>

    <el-timeline v-if="rows.length" class="party-timeline">
      <el-timeline-item
        v-for="r in sortedRows"
        :key="r.id"
        :timestamp="r.stage_date || '日期未填'"
        placement="top"
        :color="stageColor(r.stage)"
      >
        <el-card shadow="never" class="stage-card">
          <div class="stage-head">
            <span class="stage-name">{{ r.stage }}</span>
            <el-button link type="danger" size="small" @click="onDelete(r)" style="margin-left:auto">删除</el-button>
          </div>
          <div v-if="r.contact_person" class="stage-meta">联系人：{{ r.contact_person }}</div>
          <div v-if="r.notes" class="stage-notes">{{ r.notes }}</div>
        </el-card>
      </el-timeline-item>
    </el-timeline>

    <el-empty v-else description="暂无党团发展记录" :image-size="60" />

    <div class="party-add">
      <el-button type="primary" size="small" @click="showAdd = true" :icon="Plus">添加党团记录</el-button>
    </div>

    <el-dialog v-model="showAdd" title="添加党团发展记录" width="460px" append-to-body>
      <el-form :model="form" label-width="80px">
        <el-form-item label="阶段">
          <el-select v-model="form.stage" style="width:100%">
            <el-option v-for="s in stageOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="form.stage_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact_person" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { s360 } from '@/api/student360.js'

const props = defineProps({ sid: { type: Number, required: true } })
const rows = ref([])
const showAdd = ref(false)
const colors = ['#5B92E5', '#4FC3B8', '#8FA9E5']
const stageOptions = ['入党申请人', '积极分子', '发展对象', '中共预备党员', '中共党员']
const form = ref({ stage: '入党申请人', stage_date: '', contact_person: '', notes: '' })

const sortedRows = computed(() =>
  [...rows.value].sort((a,b) => (b.stage_date||'').localeCompare(a.stage_date||''))
)

const nextStageMap = { '入党申请人':'积极分子','积极分子':'发展对象','发展对象':'中共预备党员','中共预备党员':'中共党员','中共党员':null }

const stats = computed(() => {
  if (!rows.value.length) return [
    { label: '当前阶段', value: '无' }, { label: '下一阶段', value: '无' }, { label: '记录数', value: 0 }
  ]
  const current = sortedRows.value[0]?.stage || '无'
  const next = nextStageMap[current] || '无'
  return [
    { label: '当前阶段', value: current },
    { label: '下一阶段', value: next },
    { label: '记录数', value: rows.value.length }
  ]
})

function stageColor(stage) {
  const map = { '入党申请人':'#909399','积极分子':'#E6A23C','发展对象':'#5B92E5','中共预备党员':'#67C23A','中共党员':'#F56C6C' }
  return map[stage] || '#5B92E5'
}

async function load() {
  try { rows.value = await s360.party.list(props.sid) || [] } catch { rows.value = [] }
}

async function onSave() {
  if (!form.value.stage) { ElMessage.warning('请选择阶段'); return }
  try {
    await s360.party.create(props.sid, form.value)
    ElMessage.success('已添加')
    showAdd.value = false
    form.value = { stage: '入党申请人', stage_date: '', contact_person: '', notes: '' }
    await load()
  } catch { ElMessage.error('保存失败') }
}

async function onDelete(r) {
  try {
    await ElMessageBox.confirm('确认删除该条党团记录？', '确认', { type: 'warning' })
    await s360.party.remove(props.sid, r.id)
    ElMessage.success('已删除')
    await load()
  } catch {}
}

watch(() => props.sid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.tab-party { padding: 4px 0; }
.party-summary { display:flex; gap:12px; margin-bottom:16px; }
.party-stat { flex:1; background:rgba(91,146,229,0.05); border:1px solid rgba(91,146,229,0.12); border-radius:10px; padding:14px; text-align:center; }
.p-val { font-size:22px; font-weight:700; line-height:1.2; }
.p-lbl { font-size:12px; color:#6B7B8D; margin-top:4px; }
.party-timeline { padding: 4px 0 0 4px; max-height: 320px; overflow-y: auto; }
.stage-card { border-radius: 10px; }
.stage-head { display:flex; align-items:center; margin-bottom:6px; }
.stage-name { font-weight:600; color:#2C3E50; }
.stage-meta { font-size:12px; color:#909399; }
.stage-notes { font-size:13px; color:#606266; margin-top:4px; }
.party-add { margin-top: 12px; }
</style>
