<template>
  <div>
    <el-tabs v-model="activeSub" class="daily-subtabs">
      <el-tab-pane label="宿舍走访" name="dormVisits" />
      <el-tab-pane label="请假记录" name="leaves" />
      <el-tab-pane label="违纪处分" name="disciplines" />
      <el-tab-pane label="寝谈记录" name="dormChats" />
      <el-tab-pane label="考勤异常" name="attendance" />
    </el-tabs>

    <!-- 宿舍走访 -->
    <CrudPanel
      v-if="activeSub === 'dormVisits'"
      title="宿舍走访"
      :columns="dvCols" :fields="dvFields" :rows="dormVisits" :loading="loading.dormVisits"
      :default-form="{ visit_date: today }"
      :on-reload="() => load('dormVisits')"
      :on-create="p => s360.dormVisits.create(sid, p)"
      :on-update="(id, p) => s360.dormVisits.update(sid, id, p)"
      :on-delete="id => s360.dormVisits.remove(sid, id)"
    />

    <!-- 请假记录 -->
    <CrudPanel
      v-else-if="activeSub === 'leaves'"
      title="请假记录"
      :columns="lvCols" :fields="lvFields" :rows="leaves" :loading="loading.leaves"
      :default-form="{ approval_status: '待审批' }"
      :on-reload="() => load('leaves')"
      :on-create="p => s360.leaves.create(sid, p)"
      :on-update="(id, p) => s360.leaves.update(sid, id, p)"
      :on-delete="id => s360.leaves.remove(sid, id)"
    />

    <!-- 违纪处分 -->
    <CrudPanel
      v-else-if="activeSub === 'disciplines'"
      title="违纪处分"
      :columns="dcCols" :fields="dcFields" :rows="disciplines" :loading="loading.disciplines"
      :default-form="{ discipline_date: today }"
      :on-reload="() => load('disciplines')"
      :on-create="p => s360.disciplines.create(sid, p)"
      :on-update="(id, p) => s360.disciplines.update(sid, id, p)"
      :on-delete="id => s360.disciplines.remove(sid, id)"
    />

    <!-- 寝谈 -->
    <CrudPanel
      v-else-if="activeSub === 'dormChats'"
      title="寝谈记录"
      :columns="chatCols" :fields="chatFields" :rows="dormChats" :loading="loading.dormChats"
      :default-form="{ chat_date: today }"
      :on-reload="() => load('dormChats')"
      :on-create="p => s360.dormChats.create(sid, p)"
      :on-update="(id, p) => s360.dormChats.update(sid, id, p)"
      :on-delete="id => s360.dormChats.remove(sid, id)"
    />

    <!-- 考勤异常 -->
    <CrudPanel
      v-else-if="activeSub === 'attendance'"
      title="考勤异常"
      :columns="atCols" :fields="atFields" :rows="attendance" :loading="loading.attendance"
      :default-form="{ exception_date: today, exception_type: '旷课' }"
      :on-reload="() => load('attendance')"
      :on-create="p => s360.attendance.create(sid, p)"
      :on-update="(id, p) => s360.attendance.update(sid, id, p)"
      :on-delete="id => s360.attendance.remove(sid, id)"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import CrudPanel from '@/components/CrudPanel.vue'
import { s360 as s360Api } from '@/api/student360.js'

const props = defineProps({ sid: { type: Number, required: true } })
const sid = computed(() => props.sid)
const s360 = s360Api

const today = new Date().toISOString().slice(0, 10)
const activeSub = ref('dormVisits')

const dormVisits  = ref([])
const leaves      = ref([])
const disciplines = ref([])
const dormChats   = ref([])
const attendance  = ref([])
const loading = ref({
  dormVisits: false, leaves: false, disciplines: false,
  dormChats: false, attendance: false
})

// --- 宿舍走访 ---
const dvCols = [
  { prop: 'visit_date', label: '走访日期', width: 120 },
  { prop: 'dorm_room', label: '寝室号', width: 120 },
  { prop: 'visitor', label: '走访人', width: 100 },
  { prop: 'situation', label: '寝室情况', minWidth: 200 },
  { prop: 'notes', label: '备注', minWidth: 140 }
]
const dvFields = [
  { prop: 'visit_date', label: '走访日期', type: 'date' },
  { prop: 'dorm_room', label: '寝室号', placeholder: '例：C-6-306' },
  { prop: 'visitor', label: '走访人' },
  { prop: 'situation', label: '寝室情况', type: 'textarea' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

// --- 请假记录 ---
const lvCols = [
  { prop: 'leave_type', label: '类型', width: 100 },
  { prop: 'start_date', label: '开始', width: 110 },
  { prop: 'end_date', label: '结束', width: 110 },
  { prop: 'destination', label: '去向', minWidth: 140 },
  { prop: 'approval_status', label: '审批状态', width: 110, type: 'tag',
    tagType: (r) => r.approval_status === '已批准' ? 'success' :
      r.approval_status === '未批准' ? 'danger' : 'warning' },
  { prop: 'approver', label: '审批人', width: 100 },
  { prop: 'notes', label: '备注', minWidth: 140 }
]
const lvFields = [
  {
    prop: 'leave_type', label: '请假类型', type: 'select',
    options: ['事假', '病假', '公假', '其他']
  },
  { prop: 'start_date', label: '开始日期', type: 'date' },
  { prop: 'end_date',   label: '结束日期', type: 'date' },
  { prop: 'destination', label: '去向', placeholder: '例：北京市 / 家中' },
  {
    prop: 'approval_status', label: '审批状态', type: 'select',
    options: ['待审批', '已批准', '未批准', '销假']
  },
  { prop: 'approver', label: '审批人' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

// --- 违纪 ---
const dcCols = [
  { prop: 'discipline_date', label: '违纪日期', width: 120 },
  { prop: 'discipline_type', label: '违纪类型', minWidth: 140 },
  { prop: 'level', label: '处分等级', width: 110, type: 'tag',
    tagType: (r) =>
      /留校察看|开除/.test(r.level || '') ? 'danger' :
      /记过|记大过/.test(r.level || '') ? 'warning' :
      r.level ? 'primary' : '' },
  { prop: 'reason', label: '原因', minWidth: 180 },
  { prop: 'attachment', label: '附件', minWidth: 120 },
  { prop: 'notes', label: '备注', minWidth: 140 }
]
const dcFields = [
  { prop: 'discipline_date', label: '违纪日期', type: 'date' },
  {
    prop: 'discipline_type', label: '违纪类型',
    placeholder: '例：夜不归寝 / 考试违纪 / 打架斗殴'
  },
  {
    prop: 'level', label: '处分等级', type: 'select',
    options: ['警告', '严重警告', '记过', '记大过', '留校察看', '开除学籍']
  },
  { prop: 'reason', label: '违纪原因', type: 'textarea' },
  { prop: 'attachment', label: '附件 URL' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

// --- 寝谈 ---
const chatCols = [
  { prop: 'chat_date', label: '谈话日期', width: 120 },
  { prop: 'topic', label: '话题', minWidth: 140 },
  { prop: 'key_points', label: '要点', minWidth: 220 },
  { prop: 'follow_up', label: '跟进', minWidth: 180 }
]
const chatFields = [
  { prop: 'chat_date', label: '谈话日期', type: 'date' },
  { prop: 'topic', label: '话题' },
  { prop: 'key_points', label: '要点', type: 'textarea' },
  { prop: 'follow_up', label: '跟进计划', type: 'textarea' }
]

// --- 考勤异常 ---
const atCols = [
  { prop: 'exception_date', label: '异常日期', width: 120 },
  { prop: 'course_name', label: '课程', minWidth: 160 },
  { prop: 'exception_type', label: '异常类型', width: 100, type: 'tag',
    tagType: (r) => r.exception_type === '旷课' ? 'danger' :
      r.exception_type === '早退' ? 'warning' :
      r.exception_type === '迟到' ? 'warning' : '' },
  { prop: 'notes', label: '备注', minWidth: 180 }
]
const atFields = [
  { prop: 'exception_date', label: '异常日期', type: 'date' },
  { prop: 'course_name', label: '课程名称' },
  {
    prop: 'exception_type', label: '异常类型', type: 'select',
    options: ['旷课', '迟到', '早退', '其他']
  },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

async function load(sub) {
  const store = {
    dormVisits, leaves, disciplines, dormChats, attendance
  }[sub]
  const api = s360[sub]
  loading.value[sub] = true
  try {
    store.value = (await api.list(sid.value)) || []
  } finally {
    loading.value[sub] = false
  }
}
watch(activeSub, (v) => load(v))
watch(sid, () => load(activeSub.value))
onMounted(() => load(activeSub.value))
</script>

<style scoped>
.daily-subtabs { margin-bottom: 12px; }
</style>
