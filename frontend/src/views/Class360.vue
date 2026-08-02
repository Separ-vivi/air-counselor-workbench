<template>
  <div class="c360-wrap">
    <div class="inline-back-bar">
      <el-button link @click="inlineGoBack" class="back-inline-btn">
        <el-icon><component :is="_InlineArrowLeft" /></el-icon>
        <span style="margin-left:4px;font-weight:500">返回</span>
      </el-button>
      <span class="inline-title">班级 360</span>
    </div>
    <div v-if="loadingHeader" class="empty-hint">
      <div class="icon">...</div>
      <div>加载班级数据中…</div>
    </div>

    <template v-else-if="classInfo">
      <!-- 顶部 sticky 卡 -->
      <div class="student-header-card">
        <div class="avatar" style="font-size:24px;color:#5B92E5">班</div>
        <div class="info">
          <div class="name">{{ classInfo.class_name || classInfo.name || '班级 #' + cid }}</div>
          <div class="meta">
            <span><b>{{ classInfo.major_name || '—' }}</b></span>
            <span>{{ classInfo.grade_name || '—' }}</span>
            <span>总人数 {{ classInfo.student_count ?? students.length ?? '—' }}</span>
            <br>
            <span>班主任：{{ classInfo.class_teacher || '未指定' }}</span>
            <span>班长：{{ classInfo.monitor || '未指定' }}</span>
            <span>团支书：{{ classInfo.league_secretary || '未指定' }}</span>
          </div>
          <div class="status-lights">
            <el-button size="small" type="primary" :loading="exporting" @click="onExport" style="margin-right: 8px">
              导出班级 360
            </el-button>
            <span class="status-chip">挂科率 {{ fmtPct(summary?.fail_rate) }}</span>
            <span class="status-chip red">红灯 {{ summary?.warning_red_count ?? 0 }}</span>
            <span class="status-chip yellow">黄灯 {{ summary?.warning_yellow_count ?? 0 }}</span>
            <span class="status-chip">党员 {{ summary?.party_member_count ?? 0 }}</span>
            <span class="status-chip">困难生 {{ summary?.hardship_count ?? 0 }}</span>
            <span class="status-chip">已签约 {{ summary?.employed_count ?? 0 }}</span>
          </div>
          <div v-if="summaryErr" style="margin-top:8px">
            <el-alert
              type="warning"
              :closable="false"
              show-icon
              title="班级 summary 接口返回 500 · 已用兜底数据显示（后端待修复，详见 backend_fix/README.md）"
              size="small"
            />
          </div>
        </div>
      </div>

      <!-- 内联视图：概览 & 花名册 -->
      <div v-if="inlineTab" class="c360-inline-view">
        <div class="inline-tab-bar">
          <el-button size="small" @click="inlineTab = null">
            <el-icon><component :is="_InlineArrowLeft" /></el-icon>
            返回卡片视图
          </el-button>
          <span class="inline-tab-title">{{ tabs.find(t => t.key === inlineTab)?.label || '' }}</span>
        </div>
        <div class="inline-tab-content">
          <ClassSummary  v-if="inlineTab==='summary'"  :cid="cid" :class-info="classInfo" :summary="summary" />
          <ClassStudents v-if="inlineTab==='students'" :cid="cid" :class-info="classInfo" :summary="summary" />
        </div>
      </div>

      <!-- 卡片网格 -->
      <div v-else class="c360-card-grid">
        <DimensionCard
          v-for="card in cardList"
          :key="card.key"
          :icon="card.icon"
          :title="card.label"
          :stats="card.stats"
          :badge="card.badge"
          :badge-class="card.badgeClass"
          :accent="card.accent"
          @click="card.navigate ? $router.push(card.navigate) : (card.inline ? (inlineTab = card.key) : openDialog(card.key))"
        />
      </div>

      <!-- 弹窗详情 -->
      <el-dialog
        v-model="dialogVisible"
        :title="dialogTitle"
        width="960px"
        destroy-on-close
        :close-on-click-modal="true"
        top="5vh"
        class="c360-detail-dialog"
      >
        <div v-if="dialogKey" class="c360-dialog-body">
          <ClassGrades             v-if="dialogKey==='grades'"     :cid="cid" :class-info="classInfo" :summary="summary" />
          <ClassParty              v-else-if="dialogKey==='party'"      :cid="cid" :class-info="classInfo" :summary="summary" />
          <ClassPsychology         v-else-if="dialogKey==='psychology'" :cid="cid" :class-info="classInfo" :summary="summary" :class-student-count="classStudentCount" />
          <ClassFunding            v-else-if="dialogKey==='funding'"    :cid="cid" :class-info="classInfo" :summary="summary" />
          <ClassActivities         v-else-if="dialogKey==='activities'" :cid="cid" :class-info="classInfo" :summary="summary" />
          <ClassFeaturedActivities v-else-if="dialogKey==='featured'"   :cid="cid" :class-info="classInfo" :summary="summary" />
          <ClassPartyBranch        v-else-if="dialogKey==='branch'"     :cid="cid" :class-info="classInfo" :summary="summary" />
          <ClassDaily              v-else-if="dialogKey==='daily'"      :cid="cid" :class-info="classInfo" :summary="summary" />
        </div>
      </el-dialog>
    </template>

    <div v-else class="empty-hint">
      <div class="icon" style="color:#909399">!</div><div>班级不存在或已被删除</div>
    </div>
  </div>
</template>

<script setup>
import { ArrowLeft as _InlineArrowLeft } from '@element-plus/icons-vue'
import { useRouter as _useRouterInline } from 'vue-router'
const _routerInline = _useRouterInline()
function inlineGoBack() {
  if (window.history.length > 1) _routerInline.back()
  else _routerInline.push('/dashboard')
}

// D3: 班级360 导出
import { ref as _refExp } from 'vue'
import { ElMessage as _ElMsgExp } from 'element-plus'
import { triggerDownload as _triggerDl, stampedName as _stamp } from '@/utils/download'
const exporting = _refExp(false)
async function onExport() {
  const _cid = cid.value
  const _cn = classInfo.value?.class_name || classInfo.value?.name || '班级'
  if (!_cid || Number.isNaN(Number(_cid))) { _ElMsgExp.warning('班级 ID 无效'); return }
  exporting.value = true
  try {
    const blob = await exportClass360(_cid)
    _triggerDl(blob, _stamp(`班级360_${_cn}`))
    _ElMsgExp.success('导出成功')
  } catch (e) {
    _ElMsgExp.error('导出失败: ' + (e?.message || '未知错误'))
  } finally {
    exporting.value = false
  }
}
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getClassSummary, getClassStudents, exportClass360 } from '@/api/class360.js'
import { getClass } from '@/api/org.js'
import { useOrgStore } from '@/stores/org.js'

import ClassSummary    from '@/components/class360/ClassSummary.vue'
import ClassStudents   from '@/components/class360/ClassStudents.vue'
import ClassGrades     from '@/components/class360/ClassGrades.vue'
import ClassParty      from '@/components/class360/ClassParty.vue'
import ClassPsychology from '@/components/class360/ClassPsychology.vue'
import ClassFunding    from '@/components/class360/ClassFunding.vue'
import ClassActivities from '@/components/class360/ClassActivities.vue'
import ClassDaily      from '@/components/class360/ClassDaily.vue'
import ClassFeaturedActivities from '@/components/class360/ClassFeaturedActivities.vue'
import ClassPartyBranch        from '@/components/class360/ClassPartyBranch.vue'
import DimensionCard   from '@/components/common/DimensionCard.vue'

const route = useRoute()
const orgStore = useOrgStore()

const cid = computed(() => {
  const raw = route.params.id
  if (raw === undefined || raw === null || raw === 'undefined' || raw === '') return NaN
  const n = Number(raw)
  return Number.isNaN(n) ? NaN : n
})
const classInfo = ref(null)
const summary = ref(null)
const summaryErr = ref(false)
const students = ref([])
const loadingHeader = ref(false)
const inlineTab = ref(null)

// Dialog state
const dialogVisible = ref(false)
const dialogKey = ref('')
const dialogTitle = computed(() => tabs.find(t => t.key === dialogKey.value)?.label || '详情')

function openDialog(key) {
  dialogKey.value = key
  dialogVisible.value = true
}

const tabs = [
  { key: 'summary',    label: '概览',       icon: '📋' },
  { key: 'students',   label: '班级花名册', icon: '👥' },
  { key: 'grades',     label: '学业统计',   icon: '📊' },
  { key: 'party',      label: '党团进度',   icon: '🚩' },
  { key: 'psychology', label: '心理关注',   icon: '💚' },
  { key: 'funding',    label: '资助分布',   icon: '💰' },
  { key: 'activities', label: '活动参与',   icon: '🏃' },
  { key: 'featured',   label: '特色活动',   icon: '🌟' },
  { key: 'branch',     label: '党团支部',   icon: '🏛️' },
  { key: 'daily',      label: '班级大事记', icon: '📅' }
]

// Card list with summary data
const cardList = computed(() => {
  const s = summary.value
  const stuCount = students.value?.length || 0
  const maleCount = (students.value || []).filter(st => st.gender === '男').length
  const femaleCount = (students.value || []).filter(st => st.gender === '女').length
  return [
    {
      key: 'summary', label: '班级概览', icon: '📋', inline: true,
      accent: '#5B92E5',
      stats: [
        { label: '总人数', value: classInfo.value?.student_count ?? stuCount ?? 0 },
        { label: '挂科率', value: fmtPct(s?.fail_rate) }
      ]
    },
    {
      key: 'students', label: '班级花名册', icon: '👥',
      navigate: { name: 'students', query: { class_id: cid.value } },
      accent: '#8FA9E5',
      stats: [
        { label: '总人数', value: stuCount || 0 },
        { label: '男生', value: maleCount || 0 },
        { label: '女生', value: femaleCount || 0 }
      ]
    },
    {
      key: 'grades', label: '学业统计', icon: '📊',
      accent: '#5B92E5',
      badge: (s?.fail_rate && s.fail_rate > 0.1) ? '预警' : '',
      badgeClass: (s?.fail_rate && s.fail_rate > 0.1) ? 'badge-red' : '',
      stats: [
        { label: '挂科率', value: fmtPct(s?.fail_rate) },
        { label: '均分', value: s?.avg_score ? Number(s.avg_score).toFixed(1) : '无' }
      ]
    },
    {
      key: 'party', label: '党团进度', icon: '🚩',
      accent: '#e06c75',
      stats: [
        { label: '党员', value: `${s?.party_member_count ?? 0}人` },
        { label: '发展对象', value: `${s?.party_develop_count ?? 0}人` },
        { label: '团员', value: `${s?.league_member_count ?? 0}人` }
      ]
    },
    {
      key: 'psychology', label: '心理关注', icon: '💚',
      accent: '#4FC3B8',
      badge: (s?.warning_red_count > 0) ? '红灯' : '',
      badgeClass: (s?.warning_red_count > 0) ? 'badge-red' : '',
      stats: [
        { label: '红灯', value: `${s?.warning_red_count ?? 0}人` },
        { label: '黄灯', value: `${s?.warning_yellow_count ?? 0}人` },
        { label: '绿灯', value: `${s?.warning_green_count ?? (stuCount - (s?.warning_red_count ?? 0) - (s?.warning_yellow_count ?? 0))}人` }
      ]
    },
    {
      key: 'funding', label: '资助分布', icon: '💰',
      accent: '#e6a23c',
      stats: [
        { label: '困难生', value: `${s?.hardship_count ?? 0}人` },
        { label: '特殊困难', value: `${s?.special_hardship_count ?? 0}人` }
      ]
    },
    {
      key: 'activities', label: '活动参与', icon: '🏃',
      accent: '#5B92E5',
      stats: [
        { label: '活动总数', value: s?.activity_count ?? 0 },
        { label: '参与率', value: fmtPct(s?.activity_rate) }
      ]
    },
    {
      key: 'featured', label: '特色活动', icon: '🌟',
      accent: '#8FA9E5',
      stats: [
        { label: '特色项目', value: `${s?.featured_count ?? 0}项` }
      ]
    },
    {
      key: 'branch', label: '党团支部', icon: '🏛️',
      accent: '#e06c75',
      stats: [
        { label: '党支部', value: s?.party_branch_count ?? 0 },
        { label: '团支部', value: s?.league_branch_count ?? 0 }
      ]
    },
    {
      key: 'daily', label: '班级大事记', icon: '📅',
      accent: '#4FC3B8',
      stats: [
        { label: '事件数', value: s?.daily_count ?? 0 }
      ]
    }
  ]
})

function fmtPct(v) {
  if (v == null) return '无'
  const n = Number(v)
  if (Number.isNaN(n)) return '无'
  return (n > 1 ? n : n * 100).toFixed(1) + '%'
}

/** 兜底：从 org 树 + students 接口拼装 classInfo（应对 summary 500） */
function buildFallback(cid) {
  for (const g of orgStore.orgTree) {
    for (const m of (g.majors || [])) {
      for (const c of (m.classes || [])) {
        if (c.id === cid) {
          return {
            id: c.id,
            class_name: c.class_name,
            major_name: m.major_name,
            grade_name: g.grade_name,
            student_count: c.student_count,
            class_teacher: c.class_teacher || '',
            monitor: c.monitor || '',
            league_secretary: c.league_secretary || ''
          }
        }
      }
    }
  }
  return null
}

async function loadHeader() {
  if (Number.isNaN(cid.value)) return
  loadingHeader.value = true
  summaryErr.value = false
  try {
    if (!orgStore.orgTree.length) await orgStore.loadTree().catch(() => {})

    let s = null
    try {
      s = await getClassSummary(cid.value)
      summary.value = s
    } catch (e) {
      summaryErr.value = true
      summary.value = null
    }

    if (s && (s.class_name || s.name)) {
      classInfo.value = s
    } else {
      try {
        const c = await getClass(cid.value)
        classInfo.value = c
      } catch {
        classInfo.value = buildFallback(cid.value)
      }
    }

    try {
      students.value = await getClassStudents(cid.value) || []
    } catch { students.value = [] }
  } finally {
    loadingHeader.value = false
  }
}

const classStudentCount = computed(() => {
  const n = classInfo.value?.student_count
  if (typeof n === 'number' && n > 0) return n
  return students.value?.length || 0
})

watch(cid, loadHeader, { immediate: false })
onMounted(() => {
  loadHeader()
  window.addEventListener('system-reinit-done', loadHeader)
})
</script>

<style scoped>
.c360-wrap { }

/* 卡片网格 */
.c360-card-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 8px;
}
@media (max-width: 1400px) {
  .c360-card-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 1100px) {
  .c360-card-grid { grid-template-columns: repeat(2, 1fr); }
}

/* 内联视图 */
.c360-inline-view {
  background: var(--bg-card, #fff);
  border: 1px solid rgba(91, 146, 229, 0.1);
  border-radius: var(--radius-md, 12px);
  padding: 16px;
  margin-top: 8px;
  box-shadow: var(--shadow-sm);
}
.inline-tab-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(91, 146, 229, 0.1);
}
.inline-tab-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #2c3e50);
}
.inline-tab-content {
  min-height: 200px;
}

/* 弹窗内容 */
.c360-dialog-body {
  max-height: 75vh;
  overflow-y: auto;
  padding: 4px 0;
}

.inline-back-bar {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 4px 6px 4px;
  border-bottom: 1px dashed rgba(74, 122, 140, .18);
  margin-bottom: 12px;
}
.back-inline-btn {
  color: #4A7A8C;
  padding: 4px 12px;
  border-radius: 8px;
  background: rgba(74, 122, 140, .08);
  font-size: 14px;
}
.back-inline-btn:hover { background: rgba(74, 122, 140, .18); }
.inline-title { color: #666; font-size: 13px; }
</style>
