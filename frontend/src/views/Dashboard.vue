<template>
  <div class="dashboard">
    <div class="hero-card">
      <div class="hero-left">
        <div class="hero-greeting">{{ greeting }}，老师 👋</div>
        <div class="hero-date">
          <span class="hero-date-main">{{ dateStr }}</span>
          <span class="hero-date-week">{{ weekdayStr }}</span>
        </div>
        <div class="hero-weather" v-if="weather.loaded">
          <span class="hero-weather-icon">{{ weather.icon }}</span>
          <span class="hero-weather-city">{{ weather.city }}</span>
          <span class="hero-weather-dot">·</span>
          <span class="hero-weather-temp">{{ weather.tempC }}°C</span>
          <span v-if="weather.desc" class="hero-weather-desc">{{ weather.desc }}</span>
        </div>
        <div class="hero-sub">辅导员工作台 · 一切从容如常</div>
      </div>
      <div class="hero-right">
        <div class="hero-time">{{ timeStr }}</div>
        <div class="hero-time-label">当前时间</div>
        <div v-if="heroCountdowns.length" class="hero-cd-row">
          <div
            v-for="cd in heroCountdowns"
            :key="cd.id"
            class="hero-cd-chip"
            :style="{ background: cdChipBg(cd.color) }"
          >
            <div class="hero-cd-title">{{ cd.title }}</div>
            <div class="hero-cd-days" :class="daysClass(cd.days_left)">
              {{ cd.days_left >= 0 ? `还有 ${cd.days_left} 天` : `已过 ${-cd.days_left} 天` }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6" v-for="stat in statCards" :key="stat.label">
        <el-card shadow="hover" class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-icon" :style="{ background: stat.bg, color: stat.color }"><el-icon :size="26"><component :is="stat.icon" /></el-icon></div>
          <div class="stat-body">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value">{{ stat.value }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>


    <!-- v3h-hotfix1: 三格并排（预警灯 / 专业分布 / 本周待办中心） -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="8">
        <el-card shadow="never" class="chart-card triple-card">
          <template #header>
            <div class="card-header">
              <span class="ch-title">预警灯分布</span>
              <el-button text type="primary" size="small" @click="goWarning">查看学业预警</el-button>
            </div>
          </template>
          <div ref="warningPieRef" class="chart-box"></div>
          <div class="chart-legend">
            <span class="lg-dot" style="background:#F5B7B7"></span>红牌 {{ dash.red_count }}
            <span class="lg-dot" style="background:#F5D78A; margin-left:12px"></span>黄牌 {{ dash.yellow_count }}
            <span class="lg-dot" style="background:#8FD5C4; margin-left:12px"></span>正常 {{ dash.normal_count }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="chart-card triple-card">
          <template #header>
            <div class="card-header">
              <span class="ch-title">专业人数分布</span>
              <el-button text type="primary" size="small" @click="$router.push('/classes')">查看班级</el-button>
            </div>
          </template>
          <div ref="majorPieRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="triple-card">
          <template #header>
            <div class="card-header">
              <span class="ch-title">本周待办</span>
              <el-button text type="primary" size="small" @click="$router.push('/calendar')">打开日历</el-button>
            </div>
          </template>
          <!-- v4: 7 天迷你日历，只显示日期数字 + 事件圆点标记，不显示事件详情 -->
          <div class="mini-week-grid">
            <div
              v-for="grp in weekEventsByDay"
              :key="grp.date"
              class="mini-day"
              :class="{ 'is-today': grp.date === todayStrKey }"
              :title="grp.items.length ? grp.items.map(x=>x.title).join('\n') : '无事项'"
              @click="$router.push('/calendar')"
            >
              <div class="mini-week">{{ grp.weekdayCn }}</div>
              <div class="mini-mmdd">{{ grp.mmdd }}</div>
              <div v-if="grp.items.length" class="mini-dots">
                <span
                  v-for="(ev, di) in grp.items.slice(0, 5)"
                  :key="di"
                  class="mini-dot"
                  :style="{ background: evBarColor(ev.color) }"
                ></span>
                <span v-if="grp.items.length > 5" class="mini-more">+{{ grp.items.length - 5 }}</span>
              </div>
              <div v-else class="mini-empty">无事项</div>
              <span v-if="grp.items.length" class="mini-badge">{{ grp.items.length }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="24">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span class="ch-title">效率中心统计</span>
              <el-button text type="primary" size="small" @click="$router.push('/notes')">查看便签</el-button>
            </div>
          </template>
          <div class="prod-row">
            <div class="prod-item" @click="openTodoDrawer">
              <div class="prod-num warning">
                {{ prodStats.todo_active }}
                <span v-if="prodStats.todo_overdue > 0" class="prod-overdue">⚠{{ prodStats.todo_overdue }}</span>
              </div>
              <div class="prod-label">待办中</div>
            </div>
            <div class="prod-item" @click="openUrgentDrawer">
              <div class="prod-num danger">{{ prodStats.todo_urgent_week }}</div>
              <div class="prod-label">一周内到期</div>
            </div>
            <div class="prod-item" @click="openProjectsDrawer">
              <div class="prod-num success">{{ prodStats.projects_active }}</div>
              <div class="prod-label">进行中项目</div>
            </div>
          </div>
        </el-card>
      </el-col>

    </el-row>

    <el-card shadow="never">
      <template #header>
        <span class="ch-title">快捷入口</span>
      </template>
      <div class="shortcuts">
        <div class="sc-item" v-for="s in shortcuts" :key="s.to" @click="$router.push(s.to)">
          <div class="sc-icon" :style="{ background: s.bg, color: s.color }"><el-icon :size="22"><component :is="s.icon" /></el-icon></div>
          <div class="sc-label">{{ s.label }}</div>
        </div>
      </div>
    </el-card>

    <!-- ============ Dashboard 抽屉 · 效率中心 3 数字点击详情 ============ -->
    <el-drawer v-model="drawerTodoOpen" title="待办中" size="480px" :with-header="true">
      <div v-loading="drawerLoading" class="dash-drawer">
        <template v-if="drawerTodos.length === 0">
          <el-empty description="暂无待办" />
        </template>
        <template v-else>
          <div v-if="todoGroups.overdue.length" class="dg-block">
            <div class="dg-title overdue">⚠ 已过期 · {{ todoGroups.overdue.length }}</div>
            <div v-for="t in todoGroups.overdue" :key="t.id" class="dg-item">
              <el-checkbox :model-value="false" @change="handleTodoToggle(t)" />
              <div class="dg-body">
                <div class="dg-content">{{ t.title || t.content }}</div>
                <div class="dg-meta overdue-txt">截止 {{ t.due_date }}</div>
              </div>
            </div>
          </div>
          <div v-if="todoGroups.week.length" class="dg-block">
            <div class="dg-title">本周内 · {{ todoGroups.week.length }}</div>
            <div v-for="t in todoGroups.week" :key="t.id" class="dg-item">
              <el-checkbox :model-value="false" @change="handleTodoToggle(t)" />
              <div class="dg-body">
                <div class="dg-content">{{ t.title || t.content }}</div>
                <div class="dg-meta">截止 {{ t.due_date }}</div>
              </div>
            </div>
          </div>
          <div v-if="todoGroups.later.length" class="dg-block">
            <div class="dg-title">一周之后 · {{ todoGroups.later.length }}</div>
            <div v-for="t in todoGroups.later" :key="t.id" class="dg-item">
              <el-checkbox :model-value="false" @change="handleTodoToggle(t)" />
              <div class="dg-body">
                <div class="dg-content">{{ t.title || t.content }}</div>
                <div class="dg-meta">截止 {{ t.due_date }}</div>
              </div>
            </div>
          </div>
          <div v-if="todoGroups.nodate.length" class="dg-block">
            <div class="dg-title">无截止日 · {{ todoGroups.nodate.length }}</div>
            <div v-for="t in todoGroups.nodate" :key="t.id" class="dg-item">
              <el-checkbox :model-value="false" @change="handleTodoToggle(t)" />
              <div class="dg-body">
                <div class="dg-content">{{ t.title || t.content }}</div>
                <div class="dg-meta">—</div>
              </div>
            </div>
          </div>
        </template>
        <div class="dg-footer">
          <el-button type="primary" plain @click="$router.push('/notes')">打开记事本 →</el-button>
        </div>
      </div>
    </el-drawer>

    <el-drawer v-model="drawerUrgentOpen" title="一周内到期" size="480px" :with-header="true">
      <div v-loading="drawerLoading" class="dash-drawer">
        <template v-if="drawerUrgent.length === 0">
          <el-empty description="一周内无到期待办" />
        </template>
        <template v-else>
          <div v-if="urgentGroups.today.length" class="dg-block">
            <div class="dg-title today">🔥 今天 · {{ urgentGroups.today.length }}</div>
            <div v-for="t in urgentGroups.today" :key="t.id" class="dg-item">
              <el-checkbox :model-value="false" @change="handleTodoToggle(t)" />
              <div class="dg-body">
                <div class="dg-content">{{ t.title || t.content }}</div>
                <div class="dg-meta">今天 {{ t.due_date }}</div>
              </div>
            </div>
          </div>
          <div v-if="urgentGroups.tomorrow.length" class="dg-block">
            <div class="dg-title">明天 · {{ urgentGroups.tomorrow.length }}</div>
            <div v-for="t in urgentGroups.tomorrow" :key="t.id" class="dg-item">
              <el-checkbox :model-value="false" @change="handleTodoToggle(t)" />
              <div class="dg-body">
                <div class="dg-content">{{ t.title || t.content }}</div>
                <div class="dg-meta">明天 {{ t.due_date }}</div>
              </div>
            </div>
          </div>
          <div v-if="urgentGroups.rest.length" class="dg-block">
            <div class="dg-title">3-7 天内 · {{ urgentGroups.rest.length }}</div>
            <div v-for="t in urgentGroups.rest" :key="t.id" class="dg-item">
              <el-checkbox :model-value="false" @change="handleTodoToggle(t)" />
              <div class="dg-body">
                <div class="dg-content">{{ t.title || t.content }}</div>
                <div class="dg-meta">{{ t.due_date }}</div>
              </div>
            </div>
          </div>
        </template>
        <div class="dg-footer">
          <el-button type="primary" plain @click="$router.push('/notes')">打开记事本 →</el-button>
        </div>
      </div>
    </el-drawer>

    <el-drawer v-model="drawerProjectsOpen" title="进行中项目" size="520px" :with-header="true">
      <div v-loading="drawerLoading" class="dash-drawer">
        <template v-if="drawerProjects.length === 0">
          <el-empty description="暂无进行中项目" />
        </template>
        <template v-else>
          <div v-for="p in drawerProjects" :key="p.id" class="dp-card" @click="$router.push('/projects')">
            <div class="dp-head">
              <span class="dp-name">{{ p.name }}</span>
              <span class="dp-prog">{{ p.progress ?? 0 }}%</span>
            </div>
            <el-progress :percentage="p.progress ?? 0" :stroke-width="6" :show-text="false" />
            <div class="dp-meta">
              <span v-if="p.deadline">截止 {{ p.deadline }}</span>
              <span v-if="p.priority">· 优先级 {{ p.priority }}</span>
            </div>
          </div>
        </template>
        <div class="dg-footer">
          <el-button type="primary" plain @click="$router.push('/projects')">打开项目管理页 →</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { useWeather } from '@/composables/useWeather'
const { weather } = useWeather()

import { ref, onMounted, onUnmounted, computed, nextTick, markRaw } from 'vue'
import {
  UserFilled, Reading, Flag, Trophy,
  Document, School, OfficeBuilding, UploadFilled,
  DataAnalysis, Warning, Medal, Sunny
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useRouter } from 'vue-router'
import { dashboard as getDashboard } from '@/api/modules'
import { productivityDashboard, eventsApi, countdownsApi, notesApi, projectsApi } from '@/api/productivity'

const router = useRouter()
const warnings = ref([])
const recentActivities = ref([])
const prodStats = ref({ todo_active: 0, todo_urgent_week: 0, todo_overdue: 0, projects_active: 0, countdowns_top: [] })

// ============ Dashboard 抽屉：3 个数字点击展开详情 ============
const drawerTodoOpen = ref(false)
const drawerUrgentOpen = ref(false)
const drawerProjectsOpen = ref(false)
const drawerLoading = ref(false)
const drawerTodos = ref([])       // 待办抽屉：全量 active 待办
const drawerUrgent = ref([])      // 快到期抽屉：一周内到期
const drawerProjects = ref([])    // 项目抽屉：active 项目

const _todayStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

// 分组：待办抽屉 → 已过期 / 本周 / 一周之后 / 无截止日
const todoGroups = computed(() => {
  const today = _todayStr()
  const weekLater = (() => {
    const d = new Date(); d.setDate(d.getDate()+7)
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
  })()
  const g = { overdue: [], week: [], later: [], nodate: [] }
  for (const t of drawerTodos.value) {
    const dd = t.due_date || ''
    if (!dd) g.nodate.push(t)
    else if (dd < today) g.overdue.push(t)
    else if (dd <= weekLater) g.week.push(t)
    else g.later.push(t)
  }
  // 每组按 due_date 升序（无日期归尾）
  const byDate = (a, b) => (a.due_date || '9999').localeCompare(b.due_date || '9999')
  g.overdue.sort(byDate); g.week.sort(byDate); g.later.sort(byDate)
  return g
})

// 分组：快到期抽屉 → 今天 / 明天 / 后天-7天
const urgentGroups = computed(() => {
  const today = new Date(); today.setHours(0,0,0,0)
  const fmt = (d) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
  const todayStr = fmt(today)
  const tmr = new Date(today); tmr.setDate(tmr.getDate()+1); const tmrStr = fmt(tmr)
  const g = { today: [], tomorrow: [], rest: [] }
  for (const t of drawerUrgent.value) {
    const dd = t.due_date || ''
    if (dd === todayStr) g.today.push(t)
    else if (dd === tmrStr) g.tomorrow.push(t)
    else g.rest.push(t)
  }
  const byDate = (a, b) => (a.due_date || '').localeCompare(b.due_date || '')
  g.today.sort(byDate); g.tomorrow.sort(byDate); g.rest.sort(byDate)
  return g
})

async function loadDashProd() {
  try {
    const pd = await productivityDashboard()
    if (pd) prodStats.value = { ...prodStats.value, ...pd }
  } catch(e) { console.error('reload prodStats failed', e) }
}

async function openTodoDrawer() {
  drawerTodoOpen.value = true
  drawerLoading.value = true
  try {
    const rows = await notesApi.list({ category: 'todo', status: 'active', size: 500 })
    drawerTodos.value = Array.isArray(rows) ? rows : (rows?.items || rows?.data || [])
  } catch(e) { drawerTodos.value = [] }
  finally { drawerLoading.value = false }
}

async function openUrgentDrawer() {
  drawerUrgentOpen.value = true
  drawerLoading.value = true
  try {
    const today = _todayStr()
    const wl = (() => { const d = new Date(); d.setDate(d.getDate()+7); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` })()
    const rows = await notesApi.list({ category: 'todo', status: 'active', due_start: today, due_end: wl, size: 500 })
    let list = Array.isArray(rows) ? rows : (rows?.items || rows?.data || [])
    // 前端兜底过滤（后端未支持 due_start/end 时）
    list = list.filter(r => r.due_date && r.due_date >= today && r.due_date <= wl)
    drawerUrgent.value = list
  } catch(e) { drawerUrgent.value = [] }
  finally { drawerLoading.value = false }
}

async function openProjectsDrawer() {
  drawerProjectsOpen.value = true
  drawerLoading.value = true
  try {
    const rows = await projectsApi.list({ status: 'active', size: 200 })
    drawerProjects.value = Array.isArray(rows) ? rows : (rows?.items || rows?.data || [])
  } catch(e) { drawerProjects.value = [] }
  finally { drawerLoading.value = false }
}

async function handleTodoToggle(t) {
  try {
    await notesApi.toggle(t.id)
    // 抽屉内本地移除（因为切成 done 后不再是 active）
    drawerTodos.value = drawerTodos.value.filter(x => x.id !== t.id)
    drawerUrgent.value = drawerUrgent.value.filter(x => x.id !== t.id)
    await loadDashProd()
  } catch(e) { ElMessage?.error?.('操作失败') }
}

// ============ 可视化 echarts refs ============
const dash = ref({
  total_students: 0, total_classes: 0, total_majors: 0,
  red_count: 0, yellow_count: 0, normal_count: 0,
  major_distribution: [], class_distribution: [], tag_distribution: []
})
const warningPieRef = ref(null)
const majorPieRef = ref(null)
let charts = []

const iceMintColors = ['#5B92E5','#7BCFCB','#8FA9E5','#4FC3B8','#B7D8E4','#C7CEEA','#A8E6CF','#93C4E8','#B7E4E0','#DAE8F7','#6EAECF','#94D2C8']

function renderCharts() {
  // 销毁旧实例
  charts.forEach(c => { try { c.dispose() } catch(e){} })
  charts = []

  // ---- 预警灯环形 ----
  if (warningPieRef.value) {
    const c1 = echarts.init(warningPieRef.value)
    c1.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { show: false },
      series: [{
        type: 'pie', radius: ['55%', '78%'], center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#FFFFFF', borderWidth: 2 },
        label: { show: true, position: 'center', formatter: () => `{a|${dash.value.total_students}}\n{b|全体学生}`, rich: { a:{fontSize:28,fontWeight:700,color:'#2E5A7F'}, b:{fontSize:12,color:'#8FA9E5',padding:[4,0,0,0]} } },
        labelLine: { show: false },
        data: [
          { value: dash.value.red_count,    name: '红牌', itemStyle: { color: '#F5B7B7' } },
          { value: dash.value.yellow_count, name: '黄牌', itemStyle: { color: '#F5D78A' } },
          { value: dash.value.normal_count, name: '正常', itemStyle: { color: '#8FD5C4' } }
        ]
      }]
    })
    charts.push(c1)
  }

  // ---- 专业分布环形 ----
  if (majorPieRef.value) {
    const c2 = echarts.init(majorPieRef.value)
    const md = dash.value.major_distribution || []
    c2.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)' },
      legend: { bottom: 4, textStyle: { fontSize: 11, color: '#5B92E5' }, itemWidth: 10, itemHeight: 10 },
      series: [{
        type: 'pie', radius: ['55%', '78%'], center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#FFFFFF', borderWidth: 2 },
        label: { show: true, position: 'center', formatter: () => `{a|${md.length}}\n{b|专业数}`, rich: { a:{fontSize:28,fontWeight:700,color:'#2E5A7F'}, b:{fontSize:12,color:'#8FA9E5',padding:[4,0,0,0]} } },
        labelLine: { show: false },
        data: md.map((x, i) => ({ value: x.value, name: x.name, itemStyle: { color: iceMintColors[i % iceMintColors.length] } }))
      }]
    })
    charts.push(c2)
  }

}

function resizeCharts() { charts.forEach(c => { try { c.resize() } catch(e){} }) }

onMounted(() => { window.addEventListener('resize', resizeCharts) })
onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  charts.forEach(c => { try { c.dispose() } catch(e){} })
})


// ============ 实时时钟 ============
const now = ref(new Date())
let clockTimer = null
onMounted(() => { clockTimer = setInterval(() => { now.value = new Date() }, 1000) })
onUnmounted(() => { if (clockTimer) clearInterval(clockTimer) })

const timeStr = computed(() => {
  const n = now.value
  const p = x => x.toString().padStart(2, '0')
  return `${p(n.getHours())}:${p(n.getMinutes())}:${p(n.getSeconds())}`
})
const dateStr = computed(() => {
  const n = now.value
  return `${n.getFullYear()}年${n.getMonth()+1}月${n.getDate()}日`
})
const weekdayStr = computed(() => {
  return ['周日','周一','周二','周三','周四','周五','周六'][now.value.getDay()]
})
const greeting = computed(() => {
  const h = now.value.getHours()
  if (h < 6)  return '夜深了'
  if (h < 9)  return '早上好'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  if (h < 22) return '晚上好'
  return '夜深了'
})

// v3h A: 本周事件 + hero 倒计时
const weekEvents = ref([])
const heroCountdowns = ref([])

const todayStrKey = computed(() => {
  const n = now.value
  const p = (x) => String(x).padStart(2, '0')
  return `${n.getFullYear()}-${p(n.getMonth()+1)}-${p(n.getDate())}`
})

const weekEventsByDay = computed(() => {
  const n = now.value
  const start = new Date(n)
  start.setDate(n.getDate() - ((n.getDay() + 6) % 7))  // 本周一
  start.setHours(0,0,0,0)
  const days = []
  const wkCn = ['一','二','三','四','五','六','日']
  for (let i = 0; i < 7; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    const p = (x) => String(x).padStart(2, '0')
    const key = `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`
    days.push({
      date: key,
      mmdd: `${d.getMonth()+1}/${d.getDate()}`,
      weekdayCn: '周' + wkCn[i],
      items: [],
    })
  }
  const map = Object.fromEntries(days.map(d => [d.date, d]))
  for (const ev of weekEvents.value) {
    if (map[ev.date]) map[ev.date].items.push(ev)
  }
  return days
})

// v3h-hotfix1: 待办中心竖列（本周未过期事件按日期升序）
const weekTodoList = computed(() => {
  const arr = [...weekEvents.value]
  arr.sort((a, b) => (a.date || '').localeCompare(b.date || ''))
  // 优先未完成 + 未过期
  const today = todayStrKey.value
  return arr.filter(ev => !ev.done && (ev.date || '') >= today).slice(0, 12)
})

function tvDateLabel(d) {
  if (!d) return '—'
  const today = todayStrKey.value
  if (d === today) return '今天'
  const nt = new Date(today)
  const nd = new Date(d)
  const diff = Math.round((nd - nt) / 86400000)
  if (diff === 1) return '明天'
  if (diff === 2) return '后天'
  const [y, m, dd] = d.split('-')
  return `${parseInt(m)}/${parseInt(dd)}`
}

const evBarColor = (c) => {
  const m = {
    blue: '#7BB6D6', orange: '#F5A76E', yellow: '#E8C86A', pink: '#F1A6B7',
    green: '#8CC9A1', cyan: '#7EC4C0', purple: '#B29AC9', red: '#E88686',
  }
  return m[c] || '#909399'
}
const cdChipBg = (c) => {
  const m = {
    blue: 'rgba(123,182,214,0.16)', orange: 'rgba(245,167,110,0.16)',
    yellow: 'rgba(232,200,106,0.18)', pink: 'rgba(241,166,183,0.18)',
    green: 'rgba(140,201,161,0.18)', red: 'rgba(232,134,134,0.18)',
    purple: 'rgba(178,154,201,0.18)',
  }
  return m[c] || 'rgba(150,170,190,0.15)'
}

const daysClass = (d) => {
  if (d === undefined || d === null) return ''
  if (d <= 3) return 'danger'
  if (d <= 7) return 'warning'
  return ''
}

const statCards = ref([
  // v4-hotfix11: 冰蓝薄荷主题, el-icon SVG + 主题色底
  { label: '在校学生',       value: 0, icon: markRaw(UserFilled), bg: 'rgba(91, 146, 229, 0.14)',  color: '#5B92E5' },
  { label: '班级数量',       value: 0, icon: markRaw(Reading),    bg: 'rgba(79, 195, 184, 0.14)',  color: '#4FC3B8' },
  { label: '党员/发展对象', value: 0, icon: markRaw(Flag),       bg: 'rgba(143, 169, 229, 0.14)', color: '#7B92D6' },
  { label: '本月活动',       value: 0, icon: markRaw(Trophy),     bg: 'rgba(123, 207, 203, 0.16)', color: '#5FB8AC' }
])

const shortcuts = [
  // v4-hotfix11: 冰蓝薄荷 4 色轮播, 保持视觉区分度
  { icon: markRaw(UserFilled),     label: '学生管理', to: '/students',        bg: 'rgba(91, 146, 229, 0.10)',  color: '#5B92E5' },
  { icon: markRaw(School),         label: '班级管理', to: '/classes',         bg: 'rgba(79, 195, 184, 0.12)',  color: '#4FC3B8' },
  { icon: markRaw(OfficeBuilding), label: '组织架构', to: '/org',             bg: 'rgba(143, 169, 229, 0.12)', color: '#7B92D6' },
  { icon: markRaw(UploadFilled),   label: '智能导入', to: '/smart-import',    bg: 'rgba(123, 207, 203, 0.14)', color: '#5FB8AC' },
  { icon: markRaw(DataAnalysis),   label: '成绩管理', to: '/module/grades',   bg: 'rgba(91, 146, 229, 0.10)',  color: '#5B92E5' },
  { icon: markRaw(Warning),        label: '预警管理', to: '/module/warnings', bg: 'rgba(79, 195, 184, 0.12)',  color: '#4FC3B8' },
  { icon: markRaw(Flag),           label: '党团发展', to: '/module/party',    bg: 'rgba(143, 169, 229, 0.12)', color: '#7B92D6' },
  { icon: markRaw(Sunny),          label: '心理档案', to: '/module/psychology', bg: 'rgba(123, 207, 203, 0.14)', color: '#5FB8AC' }
]

const goStudent = (id) => router.push(`/students/${id}`)
const goWarning = () => router.push('/module/warnings')

onMounted(async () => {
  try {
    const res = await getDashboard()
    const d = res || {}
    dash.value = {
      total_students: d.total_students ?? d.student_count ?? 0,
      total_classes: d.total_classes ?? d.class_count ?? 0,
      total_majors: d.total_majors ?? 0,
      red_count: d.red_count ?? 0,
      yellow_count: d.yellow_count ?? 0,
      normal_count: d.normal_count ?? Math.max(0, (d.total_students ?? 0) - (d.red_count ?? 0) - (d.yellow_count ?? 0)),
      major_distribution: d.major_distribution || [],
      class_distribution: d.class_distribution || [],
      tag_distribution: d.tag_distribution || []
    }
    statCards.value[0].value = dash.value.total_students
    statCards.value[1].value = dash.value.total_classes
    statCards.value[2].value = d.party_count ?? d.total_party ?? 0
    statCards.value[3].value = d.month_activities ?? d.activity_count ?? 0
    warnings.value = d.warnings || d.warning_students || []
    recentActivities.value = d.recent || d.recent_activities || d.timeline || []
    await nextTick()
    renderCharts()
  } catch (e) {
    // 拦截器已提示，页面用空态展示
  }
  try {
    const pd = await productivityDashboard()
    if (pd) prodStats.value = pd
  } catch (e) {
    // 空态
  }
  // v3h A: 本周事件
  try {
    const we = await eventsApi.week(0)
    weekEvents.value = we?.events || []
  } catch (e) { weekEvents.value = [] }
  // v3h A: hero 倒计时（取最近 3 条）
  try {
    heroCountdowns.value = (prodStats.value.countdowns_top || []).slice(0, 3)
  } catch (e) { heroCountdowns.value = [] }
})
</script>

<style scoped>
/* ============ 全局：马卡龙渐变背景 ============ */
.dashboard {
  padding: 8px;
  min-height: calc(100vh - 100px);
  background: transparent;
  /* V4-hotfix10: 主区 ⑤ 冰蓝薄荷同色系, 底色由父容器决定, 此处保持透明避免叠色冲突 */
}

/* ============ 顶部 hero 时钟卡片 ============ */
.hero-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  margin-bottom: 20px;
  border-radius: 20px;
  /* v4-hotfix5: 清新极简 hero，浅蓝白作视觉焦点 */
  background: linear-gradient(160deg, #FFFFFF 0%, #E8F1FB 100%);
  /* V4-hotfix10: Hero 保浅色, 深字, 与深蓝侧栏形成明暗对比 */
  border: 1px solid rgba(200, 215, 235, 0.6);
  box-shadow:
    0 2px 12px rgba(90, 130, 180, 0.08),
    0 8px 28px rgba(90, 130, 180, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}
.hero-left { flex: 1; }
.hero-greeting {
  font-size: 24px;
  font-weight: 600;
  color: #3A4A5A;
  letter-spacing: 0.5px;
}
.hero-date {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin-top: 12px;
}
.hero-date-main {
  font-size: 18px;
  color: #4A5A6A;
  font-weight: 500;
}
.hero-date-week {
  font-size: 15px;
  color: #7A8A9A;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(180, 200, 220, 0.25);
}
.hero-sub {
  color: #909BA6;
  font-size: 13px;
  margin-top: 8px;
}
/* V4-hotfix10: 日期下加一行天气小字 - air 20:15 定案位置 */
.hero-weather {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 4px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(91, 146, 229, 0.08) 0%, rgba(79, 195, 184, 0.10) 100%);
  font-size: 13px;
  color: #4A6A82;
}
.hero-weather-icon { font-size: 15px; line-height: 1; }
.hero-weather-city { font-weight: 500; color: #2E5A7F; }
.hero-weather-dot { color: #A0B4C4; margin: 0 2px; }
.hero-weather-temp {
  font-weight: 600;
  color: #1B4166;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  letter-spacing: 0.3px;
}
.hero-weather-desc { color: #6B84A0; margin-left: 4px; }
.hero-right { text-align: right; }
.hero-time {
  font-size: 42px;
  font-weight: 300;
  color: #2E5A7F;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  letter-spacing: 2px;
  line-height: 1;
}
.hero-time-label {
  color: #A0AAB4;
  font-size: 12px;
  margin-top: 6px;
  letter-spacing: 1px;
}

/* ============ 卡片高度对齐 + 毛玻璃 ============ */
.dashboard :deep(.el-row) { display: flex; flex-wrap: wrap; }
.dashboard :deep(.el-col) { display: flex; }
.dashboard :deep(.el-col > .el-card) {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 16px !important;
  /* v4-hotfix5: 清新蓝白极简 · air 拒绝奶油 → 浅蓝白 + 淡蓝描边 */
  background: linear-gradient(180deg, #FFFFFF 0%, #F3F8FE 100%) !important;
  border: 1px solid rgba(200, 215, 235, 0.55) !important;
  box-shadow:
    0 2px 10px rgba(90, 130, 180, 0.06),
    0 6px 22px rgba(90, 130, 180, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}
.dashboard :deep(.el-col > .el-card:hover) {
  transform: translateY(-2px);
  box-shadow:
    0 4px 14px rgba(90, 130, 180, 0.12),
    0 12px 28px rgba(90, 130, 180, 0.10);
  border-color: rgba(160, 195, 225, 0.75) !important;
}
.dashboard :deep(.el-col > .el-card > .el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stat-card {
  border-radius: 12px;
  border: none;
}
.stat-card :deep(.el-card__body) {
  /* v4-hotfix1: air 要数字文字全居中，不要左对齐 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
  padding: 18px 12px !important;
}
.stat-icon {
  /* v4-hotfix11: el-icon SVG 版, 尺寸由 :size 控制, color 走 stat.color 主题色 */
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .2s ease;
}
.stat-card:hover .stat-icon { transform: scale(1.05); }
.stat-body { text-align: center; width: 100%; }
.stat-body .stat-label {
  color: #7B8B9C;
  font-size: 13px;
  text-align: center;
}
.stat-body .stat-value {
  color: #1E3A56;
  font-size: 24px;
  font-weight: 700;
  margin-top: 4px;
  text-align: center;
  letter-spacing: 0.5px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.shortcuts {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 12px;
}
.sc-item {
  padding: 14px 6px;
  text-align: center;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.sc-item:hover { background: rgba(91, 146, 229, 0.06); }
.sc-icon {
  /* v4-hotfix11: el-icon SVG, 主题色底 */
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  transition: transform .2s ease;
}
.sc-item:hover .sc-icon { transform: scale(1.06); }
.sc-label {
  font-size: 13px;
  color: #303133;
}
.prod-row { display: flex; gap: 12px; align-items: stretch; }
.prod-item { cursor: pointer; transition: background 0.2s, transform 0.1s; }
.prod-item:hover { background: rgba(91, 146, 229, 0.06); transform: translateY(-1px); }
.prod-num { position: relative; display: inline-flex; align-items: baseline; gap: 6px; }
.prod-overdue {
  font-size: 12px; font-weight: 600; color: #E74C3C;
  background: rgba(231, 76, 60, 0.10); padding: 2px 6px; border-radius: 10px;
  line-height: 1.2; letter-spacing: 0.3px;
}
/* ============ Dashboard 抽屉样式 ============ */
.dash-drawer { padding: 0 4px 60px; }
.dash-drawer .dg-block { margin-bottom: 20px; }
.dash-drawer .dg-title {
  font-size: 13px; font-weight: 600; color: #5B92E5;
  padding: 4px 0 8px; border-bottom: 1px dashed rgba(91,146,229,0.20);
  margin-bottom: 8px; letter-spacing: 0.3px;
}
.dash-drawer .dg-title.overdue { color: #E74C3C; border-bottom-color: rgba(231,76,60,0.25); }
.dash-drawer .dg-title.today   { color: #4FC3B8; }
.dash-drawer .dg-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 10px; border-radius: 6px; transition: background 0.15s;
}
.dash-drawer .dg-item:hover { background: rgba(91,146,229,0.05); }
.dash-drawer .dg-body { flex: 1; min-width: 0; }
.dash-drawer .dg-content { font-size: 14px; color: #2E4257; line-height: 1.5; word-break: break-word; }
.dash-drawer .dg-meta { font-size: 12px; color: #8DA0B5; margin-top: 3px; }
.dash-drawer .dg-meta.overdue-txt { color: #E74C3C; font-weight: 500; }
.dash-drawer .dg-footer {
  position: sticky; bottom: 0; background: #fff;
  padding: 12px 0 8px; margin-top: 20px; text-align: center;
  border-top: 1px solid rgba(91,146,229,0.10);
}
.dash-drawer .dp-card {
  padding: 12px 14px; border: 1px solid rgba(91,146,229,0.15);
  border-radius: 8px; margin-bottom: 10px; cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.dash-drawer .dp-card:hover { border-color: #7BCFCB; box-shadow: 0 2px 8px rgba(91,146,229,0.12); }
.dash-drawer .dp-head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.dash-drawer .dp-name { font-size: 14px; font-weight: 600; color: #2E4257; }
.dash-drawer .dp-prog { font-size: 13px; color: #5B92E5; font-weight: 600; }
.dash-drawer .dp-meta { font-size: 12px; color: #8DA0B5; margin-top: 6px; }
/* v4-hotfix5: ⑩ 效率中心与全站清新蓝白统一，去除冷灰+纯黑 */
.prod-item {
  flex: 1;
  text-align: center;
  padding: 20px 8px;
  border-radius: 14px;
  background: linear-gradient(180deg, #FFFFFF 0%, #F3F8FE 100%);
  border: 1px solid rgba(91, 146, 229, 0.10);
  transition: transform .2s ease, box-shadow .2s ease;
}
.prod-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(91, 146, 229, 0.10);
}
.prod-num { font-size: 32px; font-weight: 700; color: #2E5A7F; letter-spacing: 0.5px; }
.prod-num.warning { color: #5B92E5; }
.prod-num.danger { color: #4FC3B8; }
.prod-num.success { color: #8FA9E5; }
.prod-label { color: rgba(91, 146, 229, 0.70); font-size: 12px; margin-top: 6px; letter-spacing: 0.3px; font-weight: 500; }
.cd-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.cd-card {
  border-left: 4px solid #4A7A8C;
  background: #F5F7FA;
  padding: 14px 12px;
  border-radius: 8px;
}
.cd-title { font-size: 14px; font-weight: 600; color: #303133; }
.cd-date { color: #909399; font-size: 12px; margin-top: 4px; }
.cd-days { margin-top: 8px; font-size: 13px; font-weight: 600; color: #4A7A8C; }
.cd-days.warning { color: #E6A23C; }
.cd-days.danger { color: #F56C6C; }


/* ============ 可视化图表卡片 ============ */
.chart-card :deep(.el-card__header) {
  padding: 12px 18px;
  background: transparent;
  border-bottom: 1px solid rgba(220, 226, 232, 0.5);
}
.chart-sub {
  color: #909BA6;
  font-size: 12px;
  font-weight: normal;
}
.chart-box {
  width: 100%;
  height: 220px;
}
.chart-box-wide {
  width: 100%;
  height: 260px;
}
.chart-legend {
  display: flex;
  justify-content: center;
  font-size: 12px;
  color: #5B92E5;
  padding: 4px 0 2px;
  font-weight: 500;
}
.lg-dot {
  display: inline-block;
  width: 10px; height: 10px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}

.timeline-title { font-size: 13px; color: #303133; font-weight: 500; line-height: 1.5; }
.timeline-meta { margin-top: 4px; font-size: 12px; }
.timeline-meta :deep(.el-tag) { border-radius: 6px; }

/* v3h A · hero 右侧倒计时 chip */
.hero-cd-row {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.hero-cd-chip {
  padding: 8px 12px;
  border-radius: 12px;
  min-width: 100px;
  text-align: center;
}
.hero-cd-title { font-size: 12px; color: #4A5A6A; font-weight: 500; }
.hero-cd-days { font-size: 13px; margin-top: 3px; color: #3B6A7C; font-weight: 600; }
.hero-cd-days.warning { color: #E6A23C; }
.hero-cd-days.danger { color: #F56C6C; }

/* v4 · 三格并排 + 待办中心 7 天迷你日历 */
.triple-card { height: 100%; }
.triple-card :deep(.el-card__body) { padding: 12px 16px; }

.mini-week-grid {
  /* v4-hotfix2: iOS 大数字风，4+3 布局，每格更大更精致 */
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 6px 2px;
}
.mini-day {
  position: relative;
  /* v4-hotfix11: 冰蓝薄荷主题描边, 与整体色调呼应 */
  background: linear-gradient(160deg, #FFFFFF 0%, #F3F8FE 100%);
  border: 1px solid rgba(91, 146, 229, 0.14);
  border-radius: 14px;
  padding: 12px 10px 10px;
  min-height: 108px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.4,0,.2,1), box-shadow .2s, border-color .2s;
  box-shadow:
    0 1px 4px rgba(90, 130, 180, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}
.mini-day:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 22px rgba(90,130,170,0.22), inset 0 1px 0 rgba(255,255,255,1);
  border-color: rgba(180, 215, 240, 1);
}
.mini-day.is-today {
  /* v4-hotfix11: 冰蓝薄荷主题渐变（跟侧栏同色系呼应）*/
  background: linear-gradient(135deg, #A6D5DE 0%, #7BCFCB 55%, #8FA9E5 100%);
  border-color: rgba(255, 255, 255, 0.92);
  box-shadow: 0 4px 14px rgba(91, 146, 229, 0.24), inset 0 1px 0 rgba(255,255,255,0.85);
}
/* v4-hotfix6: 今日格背景已改浅蓝双色，文字改深色避免白字糊 */
.mini-day.is-today .mini-mmdd { color: #FFFFFF; text-shadow: 0 1px 2px rgba(46, 90, 127, 0.35); }
.mini-day.is-today .mini-week { color: rgba(255,255,255,0.92); text-shadow: 0 1px 2px rgba(46, 90, 127, 0.35); }
.mini-day.is-today .mini-empty { color: rgba(255,255,255,0.88); font-style: normal; font-weight: 500; }
.mini-day.is-today .mini-badge { background: rgba(255,255,255,0.95); color: #5B92E5; }
.mini-week { font-size: 11px; color: #5B92E5; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; }
.mini-mmdd { font-size: 22px; color: #1E3A56; font-weight: 800; margin: 4px 0 auto; letter-spacing: -0.5px; line-height: 1; font-family: -apple-system, "SF Pro Display", "PingFang SC", sans-serif; }
.mini-dots {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: flex-start;
  align-items: center;
  margin-top: 6px;
  width: 100%;
}
.mini-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 1px 2px rgba(0,0,0,0.10);
}
.mini-more {
  font-size: 10px;
  color: #7B8B9C;
  margin-left: 2px;
  font-weight: 600;
}

.mini-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: linear-gradient(135deg, #5B92E5 0%, #4FC3B8 100%);
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(91,146,229,0.30);
}
.mini-empty { color: rgba(79, 195, 184, 0.65); font-size: 11px; margin-top: auto; font-style: italic; letter-spacing: 0.3px; }

/* v4-hotfix11: 卡片头标题统一（去 emoji 后的纯文字样式）*/
.ch-title {
  font-weight: 600;
  font-size: 14px;
  color: #2E5A7F;
  letter-spacing: 0.4px;
}
</style>
