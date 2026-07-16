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
      <div class="icon">⏳</div>
      <div>加载班级数据中…</div>
    </div>

    <template v-else-if="classInfo">
      <!-- 顶部 sticky 卡 -->
      <div class="student-header-card">
        <div class="avatar">🏫</div>
        <div class="info">
          <div class="name">{{ classInfo.class_name || classInfo.name || '班级 #' + cid }}</div>
          <div class="meta">
            <span>📚 <b>{{ classInfo.major_name || '—' }}</b></span>
            <span>📅 {{ classInfo.grade_name || '—' }}</span>
            <span>👥 总人数 {{ classInfo.student_count ?? students.length ?? '—' }}</span>
            <br>
            <span>🧑‍🏫 班主任：{{ classInfo.class_teacher || '未指定' }}</span>
            <span>👑 班长：{{ classInfo.monitor || '未指定' }}</span>
            <span>🎗️ 团支书：{{ classInfo.league_secretary || '未指定' }}</span>
          </div>
          <div class="status-lights">
            <span class="status-chip">📊 挂科率 {{ fmtPct(summary?.fail_rate) }}</span>
            <span class="status-chip red">🚦 红灯 {{ summary?.warning_red_count ?? 0 }}</span>
            <span class="status-chip yellow">🚦 黄灯 {{ summary?.warning_yellow_count ?? 0 }}</span>
            <span class="status-chip">🎯 党员 {{ summary?.party_member_count ?? 0 }}</span>
            <span class="status-chip">💰 困难生 {{ summary?.hardship_count ?? 0 }}</span>
            <span class="status-chip">💼 已签约 {{ summary?.employed_count ?? 0 }}</span>
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

      <!-- 8 Tab -->
      <div class="c360-body">
        <div class="side-tabs">
          <div
            v-for="tab in tabs"
            :key="tab.key"
            class="side-tab-item"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.icon }} {{ tab.label }}
          </div>
        </div>

        <div class="tab-main">
          <keep-alive>
            <component v-if="!Number.isNaN(cid)" :is="currentTabComponent" :cid="cid" :class-info="classInfo" :summary="summary" />
          </keep-alive>
        </div>
      </div>
    </template>

    <div v-else class="empty-hint">
      <div class="icon">😢</div><div>班级不存在或已被删除</div>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getClassSummary, getClassStudents } from '@/api/class360.js'
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
const activeTab = ref('summary')

const tabs = [
  { key: 'summary',    label: '概览',       icon: '📊', comp: ClassSummary },
  { key: 'students',   label: '班级花名册', icon: '📋', comp: ClassStudents },
  { key: 'grades',     label: '学业统计',   icon: '📈', comp: ClassGrades },
  { key: 'party',      label: '党团进度',   icon: '🎯', comp: ClassParty },
  { key: 'psychology', label: '心理关注',   icon: '💚', comp: ClassPsychology },
  { key: 'funding',    label: '资助分布',   icon: '💰', comp: ClassFunding },
  { key: 'activities', label: '活动参与',   icon: '🎨', comp: ClassActivities },
  { key: 'featured',   label: '特色活动',   icon: '🌟', comp: ClassFeaturedActivities },
  { key: 'branch',     label: '党团支部',   icon: '🚩', comp: ClassPartyBranch },
  { key: 'daily',      label: '班级大事记', icon: '📅', comp: ClassDaily }
]
const currentTabComponent = computed(() => tabs.find(t => t.key === activeTab.value)?.comp)

function fmtPct(v) {
  if (v == null) return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return '—'
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
    // 保证 orgTree 已加载（用于兜底）
    if (!orgStore.orgTree.length) await orgStore.loadTree().catch(() => {})

    // 尝试 class summary（已知会 500，捕获后走兜底）
    let s = null
    try {
      s = await getClassSummary(cid.value)
      summary.value = s
    } catch (e) {
      summaryErr.value = true
      summary.value = null
    }

    // classInfo 优先来自 summary，其次 fallback / org 详情
    if (s && (s.class_name || s.name)) {
      classInfo.value = s
    } else {
      // 再试 /api/org/classes/{cid}
      try {
        const c = await getClass(cid.value)
        classInfo.value = c
      } catch {
        classInfo.value = buildFallback(cid.value)
      }
    }

    // students 兜底用
    try {
      students.value = await getClassStudents(cid.value) || []
    } catch { students.value = [] }
  } finally {
    loadingHeader.value = false
  }
}
watch(cid, loadHeader, { immediate: false })
onMounted(loadHeader)
</script>

<style scoped>
.c360-body { display: flex; gap: 16px; align-items: flex-start; }
.tab-main {
  flex: 1;
  min-width: 0;
  background: var(--color-card-bg);
  border: 1px solid var(--color-card-border);
  border-radius: var(--radius-card);
  padding: 16px;
  box-shadow: var(--shadow-card);
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
