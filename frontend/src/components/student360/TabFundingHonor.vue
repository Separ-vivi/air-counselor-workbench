<template>
  <div>
    <el-tabs v-model="activeSub" class="funding-subtabs">
      <el-tab-pane label="困难认定" name="hardship" />
      <el-tab-pane label="助学金" name="grants" />
      <el-tab-pane label="奖学金" name="scholarships" />
      <el-tab-pane label="助学贷款" name="loans" />
      <el-tab-pane label="勤工助学" name="workStudy" />
      <el-tab-pane label="评优评先" name="honors" />
    </el-tabs>

    <!-- 困难认定 -->
    <CrudPanel
      v-if="activeSub === 'hardship'"
      title="困难认定记录"
      :columns="hardshipCols"
      :fields="hardshipFields"
      :rows="hardship"
      :loading="loading.hardship"
      :default-form="{ hardship_level: '一般' }"
      :on-reload="() => load('hardship')"
      :on-create="p => s360.hardship.create(sid, p)"
      :on-update="(id, p) => s360.hardship.update(sid, id, p)"
      :on-delete="id => s360.hardship.remove(sid, id)"
    />

    <!-- 助学金 -->
    <CrudPanel
      v-else-if="activeSub === 'grants'"
      title="助学金"
      :columns="grantCols"
      :fields="grantFields"
      :rows="grants"
      :loading="loading.grants"
      :on-reload="() => load('grants')"
      :on-create="p => s360.grants.create(sid, p)"
      :on-update="(id, p) => s360.grants.update(sid, id, p)"
      :on-delete="id => s360.grants.remove(sid, id)"
    />

    <!-- 奖学金 -->
    <CrudPanel
      v-else-if="activeSub === 'scholarships'"
      title="奖学金"
      :columns="scholarshipCols"
      :fields="scholarshipFields"
      :rows="scholarships"
      :loading="loading.scholarships"
      :on-reload="() => load('scholarships')"
      :on-create="p => s360.scholarships.create(sid, p)"
      :on-update="(id, p) => s360.scholarships.update(sid, id, p)"
      :on-delete="id => s360.scholarships.remove(sid, id)"
    />

    <!-- 助学贷款 -->
    <CrudPanel
      v-else-if="activeSub === 'loans'"
      title="助学贷款"
      :columns="loanCols"
      :fields="loanFields"
      :rows="loans"
      :loading="loading.loans"
      :on-reload="() => load('loans')"
      :on-create="p => s360.loans.create(sid, p)"
      :on-update="(id, p) => s360.loans.update(sid, id, p)"
      :on-delete="id => s360.loans.remove(sid, id)"
    />

    <!-- 勤工助学 -->
    <CrudPanel
      v-else-if="activeSub === 'workStudy'"
      title="勤工助学"
      :columns="workCols"
      :fields="workFields"
      :rows="workStudy"
      :loading="loading.workStudy"
      :on-reload="() => load('workStudy')"
      :on-create="p => s360.workStudy.create(sid, p)"
      :on-update="(id, p) => s360.workStudy.update(sid, id, p)"
      :on-delete="id => s360.workStudy.remove(sid, id)"
    />

    <!-- 评优评先 -->
    <CrudPanel
      v-else-if="activeSub === 'honors'"
      title="评优评先"
      :columns="honorCols"
      :fields="honorFields"
      :rows="honors"
      :loading="loading.honors"
      :on-reload="() => load('honors')"
      :on-create="p => s360.honors.create(sid, p)"
      :on-update="(id, p) => s360.honors.update(sid, id, p)"
      :on-delete="id => s360.honors.remove(sid, id)"
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
const activeSub = ref('hardship')

const hardship     = ref([])
const grants       = ref([])
const scholarships = ref([])
const loans        = ref([])
const workStudy    = ref([])
const honors       = ref([])
const loading = ref({
  hardship: false, grants: false, scholarships: false,
  loans: false, workStudy: false, honors: false
})

// --- 困难认定 ---
const hardshipCols = [
  { prop: 'hardship_level', label: '认定等级', width: 130,
    type: 'tag',
    tagType: (r) =>
      r.hardship_level?.includes('特殊') ? 'danger' :
      r.hardship_level?.includes('建档') ? 'danger' :
      r.hardship_level?.includes('普通') ? 'warning' : '' },
  { prop: 'academic_year', label: '认定学年', width: 140 },
  { prop: 'evidence', label: '佐证材料', minWidth: 200 },
  { prop: 'notes', label: '备注', minWidth: 160 }
]
const hardshipFields = [
  {
    prop: 'hardship_level', label: '认定等级', type: 'select',
    options: ['一般', '普通困难', '特殊困难', '建档立卡']
  },
  { prop: 'academic_year', label: '认定学年', placeholder: '例：2025-2026' },
  { prop: 'evidence', label: '佐证材料', type: 'textarea' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

// --- 助学金 ---
const grantCols = [
  { prop: 'grant_type', label: '助学金类型', minWidth: 160 },
  { prop: 'amount', label: '金额（元）', width: 120,
    formatter: (v) => (v == null ? '—' : Number(v).toFixed(2)) },
  { prop: 'academic_year', label: '发放学年', width: 140 },
  { prop: 'notes', label: '备注', minWidth: 180 }
]
const grantFields = [
  {
    prop: 'grant_type', label: '助学金类型', type: 'select',
    options: ['国家助学金 · 一等', '国家助学金 · 二等', '国家助学金 · 三等',
              '校助学金', '社会助学金', '其他']
  },
  { prop: 'amount', label: '金额（元）', type: 'number', min: 0, step: 100, precision: 2 },
  { prop: 'academic_year', label: '发放学年', placeholder: '例：2025-2026' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

// --- 奖学金 ---
const scholarshipCols = [
  { prop: 'scholarship_type', label: '奖学金类型', minWidth: 180 },
  { prop: 'amount', label: '金额（元）', width: 120,
    formatter: (v) => (v == null ? '—' : Number(v).toFixed(2)) },
  { prop: 'academic_year', label: '发放学年', width: 140 },
  { prop: 'notes', label: '备注', minWidth: 180 }
]
const scholarshipFields = [
  {
    prop: 'scholarship_type', label: '奖学金类型', type: 'select',
    options: ['国家奖学金', '国家励志奖学金', '校一等奖学金', '校二等奖学金',
              '校三等奖学金', '院级奖学金', '社会奖学金', '其他']
  },
  { prop: 'amount', label: '金额（元）', type: 'number', min: 0, step: 100, precision: 2 },
  { prop: 'academic_year', label: '发放学年' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

// --- 助学贷款 ---
const loanCols = [
  { prop: 'loan_type', label: '贷款类型', width: 140 },
  { prop: 'amount', label: '金额（元）', width: 120,
    formatter: (v) => (v == null ? '—' : Number(v).toFixed(2)) },
  { prop: 'duration', label: '期限', minWidth: 130 },
  { prop: 'status', label: '还款状态', width: 110, type: 'tag',
    tagType: (r) =>
      r.status === '已结清' ? 'success' :
      r.status === '还款中' ? 'primary' :
      r.status === '逾期' ? 'danger' : '' },
  { prop: 'notes', label: '备注', minWidth: 160 }
]
const loanFields = [
  {
    prop: 'loan_type', label: '贷款类型', type: 'select',
    options: ['生源地信用助学贷款', '校园地国家助学贷款', '其他']
  },
  { prop: 'amount', label: '金额（元）', type: 'number', min: 0, step: 500, precision: 2 },
  { prop: 'duration', label: '贷款期限', placeholder: '例：4 年 / 2025-2029' },
  {
    prop: 'status', label: '还款状态', type: 'select',
    options: ['在校期间', '还款中', '已结清', '逾期', '延期']
  },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

// --- 勤工助学 ---
const workCols = [
  { prop: 'position', label: '岗位', minWidth: 160 },
  { prop: 'hours', label: '时长（小时）', width: 130,
    formatter: (v) => (v == null ? '—' : Number(v)) },
  { prop: 'compensation', label: '报酬（元）', width: 130,
    formatter: (v) => (v == null ? '—' : Number(v).toFixed(2)) },
  { prop: 'academic_year', label: '学年', width: 140 },
  { prop: 'notes', label: '备注', minWidth: 160 }
]
const workFields = [
  { prop: 'position', label: '岗位', placeholder: '例：图书馆助管、实验室助理' },
  { prop: 'hours', label: '时长（小时）', type: 'number', min: 0, step: 1 },
  { prop: 'compensation', label: '报酬（元）', type: 'number', min: 0, step: 50, precision: 2 },
  { prop: 'academic_year', label: '学年' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

// --- 评优评先 ---
const honorCols = [
  { prop: 'honor_name', label: '奖项名称', minWidth: 200 },
  { prop: 'level', label: '级别', width: 100, type: 'tag' },
  { prop: 'academic_year', label: '获奖学年', width: 140 },
  { prop: 'notes', label: '备注', minWidth: 160 }
]
const honorFields = [
  {
    prop: 'honor_name', label: '奖项名称',
    placeholder: '例：三好学生 / 优秀学生干部 / 优秀团员 / 单项奖'
  },
  {
    prop: 'level', label: '级别', type: 'select',
    options: ['国家级', '省级', '市级', '校级', '院级', '班级']
  },
  { prop: 'academic_year', label: '获奖学年' },
  { prop: 'notes', label: '备注', type: 'textarea' }
]

async function load(sub) {
  const store = {
    hardship: hardship, grants: grants, scholarships: scholarships,
    loans: loans, workStudy: workStudy, honors: honors
  }[sub]
  const api = {
    hardship: s360.hardship, grants: s360.grants, scholarships: s360.scholarships,
    loans: s360.loans, workStudy: s360.workStudy, honors: s360.honors
  }[sub]
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
.funding-subtabs { margin-bottom: 12px; }
</style>
