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
          <div class="stat-icon" :style="{ background: stat.bg }">{{ stat.icon }}</div>
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
              <span>🎯 预警灯分布</span>
              <el-button text type="primary" size="small" @click="goWarning">查看学业预警</el-button>
            </div>
          </template>
          <div ref="warningPieRef" class="chart-box"></div>
          <div class="chart-legend">
            <span class="lg-dot" style="background:#F8B4B4"></span>红牌 {{ dash.red_count }}
            <span class="lg-dot" style="background:#F9E79F; margin-left:12px"></span>黄牌 {{ dash.yellow_count }}
            <span class="lg-dot" style="background:#B7E4C7; margin-left:12px"></span>正常 {{ dash.normal_count }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="chart-card triple-card">
          <template #header>
            <div class="card-header">
              <span>🎓 专业人数分布</span>
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
              <span>🗓️ 本周待办</span>
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
              <span>📌 效率中心统计</span>
              <el-button text type="primary" size="small" @click="$router.push('/notes')">查看便签</el-button>
            </div>
          </template>
          <div class="prod-row">
            <div class="prod-item">
              <div class="prod-num warning">{{ prodStats.todo_active }}</div>
              <div class="prod-label">待办中</div>
            </div>
            <div class="prod-item">
              <div class="prod-num danger">{{ prodStats.todo_urgent_week }}</div>
              <div class="prod-label">一周内到期</div>
            </div>
            <div class="prod-item">
              <div class="prod-num success">{{ prodStats.projects_active }}</div>
              <div class="prod-label">进行中项目</div>
            </div>
          </div>
        </el-card>
      </el-col>

    </el-row>

    <el-card shadow="never">
      <template #header>
        <span>⚡ 快捷入口</span>
      </template>
      <div class="shortcuts">
        <div class="sc-item" v-for="s in shortcuts" :key="s.to" @click="$router.push(s.to)">
          <div class="sc-icon" :style="{ background: s.bg }">{{ s.icon }}</div>
          <div class="sc-label">{{ s.label }}</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { useWeather } from '@/composables/useWeather'
const { weather } = useWeather()

import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useRouter } from 'vue-router'
import { dashboard as getDashboard } from '@/api/modules'
import { productivityDashboard, eventsApi, countdownsApi } from '@/api/productivity'

const router = useRouter()
const warnings = ref([])
const recentActivities = ref([])
const prodStats = ref({ todo_active: 0, todo_urgent_week: 0, projects_active: 0, countdowns_top: [] })

// ============ 可视化 echarts refs ============
const dash = ref({
  total_students: 0, total_classes: 0, total_majors: 0,
  red_count: 0, yellow_count: 0, normal_count: 0,
  major_distribution: [], class_distribution: [], tag_distribution: []
})
const warningPieRef = ref(null)
const majorPieRef = ref(null)
let charts = []

const macaronColors = ['#F8B4B4','#F9E79F','#B7E4C7','#B7D8E4','#D5B7E4','#F5C7A0','#FCB69F','#A8E6CF','#FFD3B6','#FF8B94','#C7CEEA','#FEC8D8']

function renderCharts() {
  // 销毁旧实例
  charts.forEach(c => { try { c.dispose() } catch(e){} })
  charts = []

  // ---- 预警灯环形 ----
  if (warningPieRef.value) {
    const c1 = echarts.init(warningPieRef.value)
    c1.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie', radius: ['55%', '78%'], center: ['50%', '50%'],
        avoidLabelOverlap: false,
        label: { show: true, position: 'center', formatter: () => `{a|${dash.value.total_students}}\n{b|全体学生}`, rich: { a:{fontSize:26,fontWeight:600,color:'#4A6A7A'}, b:{fontSize:12,color:'#909BA6',padding:[4,0,0,0]} } },
        labelLine: { show: false },
        data: [
          { value: dash.value.red_count, name: '红牌', itemStyle: { color: '#F8B4B4' } },
          { value: dash.value.yellow_count, name: '黄牌', itemStyle: { color: '#F9E79F' } },
          { value: dash.value.normal_count, name: '正常', itemStyle: { color: '#B7E4C7' } }
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
      legend: { bottom: 4, textStyle: { fontSize: 11, color: '#606266' }, itemWidth: 10, itemHeight: 10 },
      series: [{
        type: 'pie', radius: ['40%', '68%'], center: ['50%', '42%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false }, labelLine: { show: false },
        data: md.map((x, i) => ({ value: x.value, name: x.name, itemStyle: { color: macaronColors[i % macaronColors.length] } }))
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
  // v4-hotfix5: 清新马卡龙渐变 + 活动黄→薰衣草紫（air 拒绝黄）
  { label: '在校学生', value: 0, icon: '👥', bg: 'linear-gradient(135deg, #C4E0F5 0%, #93C4E8 100%)' },
  { label: '班级数量', value: 0, icon: '🎓', bg: 'linear-gradient(135deg, #C7E9D4 0%, #92CFB0 100%)' },
  { label: '党员/发展对象', value: 0, icon: '🚩', bg: 'linear-gradient(135deg, #F5D0D8 0%, #E9A9B5 100%)' },
  { label: '本月活动', value: 0, icon: '🎨', bg: 'linear-gradient(135deg, #DDD0F0 0%, #B396E0 100%)' }
])

const shortcuts = [
  { icon: '📋', label: '学生管理', to: '/students', bg: '#E1F0FF' },
  { icon: '🎓', label: '班级管理', to: '/classes', bg: '#E8F5E9' },
  { icon: '🏛️', label: '组织架构', to: '/org', bg: '#E8E4F5' },
  { icon: '📥', label: '智能导入', to: '/smart-import', bg: '#F3E5F5' },
  { icon: '📊', label: '成绩管理', to: '/module/grades', bg: '#E0F7FA' },
  { icon: '⚠️', label: '预警管理', to: '/module/warnings', bg: '#FFEBEE' },
  { icon: '🚩', label: '党团发展', to: '/module/party', bg: '#FCE4EC' },
  { icon: '💚', label: '心理档案', to: '/module/psychology', bg: '#E8F5E9' }
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
  background: linear-gradient(135deg, rgba(91, 146, 229, 0.10) 0%, rgba(79, 195, 184, 0.12) 100%);
  border: 1px solid rgba(91, 146, 229, 0.18);
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
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  line-height: 1;                       /* v4: emoji 严格垂直居中 */
  font-family: "Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif;
}
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
.sc-item:hover { background: #F5F7FA; }
.sc-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  margin-bottom: 8px;
}
.sc-label {
  font-size: 13px;
  color: #303133;
}
.prod-row { display: flex; gap: 12px; align-items: stretch; }
/* v4-hotfix5: ⑩ 效率中心与全站清新蓝白统一，去除冷灰+纯黑 */
.prod-item {
  flex: 1;
  text-align: center;
  padding: 18px 8px;
  border-radius: 12px;
  background: linear-gradient(180deg, #F7FAFD 0%, #EDF3FA 100%);
  border: 1px solid rgba(200, 215, 235, 0.55);
}
.prod-num { font-size: 32px; font-weight: 700; color: #3A4A5A; letter-spacing: 0.5px; }
.prod-num.warning { color: #E6A23C; }
.prod-num.danger { color: #F56C6C; }
.prod-num.success { color: #67C23A; }
.prod-label { color: #8CA0B4; font-size: 12px; margin-top: 6px; letter-spacing: 0.3px; }
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
  color: #606266;
  padding: 4px 0 2px;
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
  /* v4-hotfix5: 清新蓝白，与卡片主色统一，去暖调 */
  background: linear-gradient(160deg, #FFFFFF 0%, #F1F7FC 100%);
  border: 1px solid rgba(200, 215, 235, 0.6);
  border-radius: 16px;
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
  /* v4-hotfix5: 今日格降饱和收敛为清新主色蓝，不再刺眼 */
  background: linear-gradient(160deg, #B4D4EC 0%, #8CB8DE 100%);
  border-color: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 14px rgba(90, 130, 180, 0.22), inset 0 1px 0 rgba(255,255,255,0.85);
}
/* v4-hotfix6: 今日格背景已改浅蓝双色，文字改深色避免白字糊 */
.mini-day.is-today .mini-mmdd { color: #1B3552; text-shadow: 0 1px 1px rgba(255,255,255,0.55); }
.mini-day.is-today .mini-week { color: #35597E; text-shadow: 0 1px 1px rgba(255,255,255,0.55); }
.mini-day.is-today .mini-empty { color: #4A6A88; font-style: normal; font-weight: 500; }
.mini-day.is-today .mini-badge { background: rgba(255,255,255,0.95); color: #4A85C0; }
.mini-week { font-size: 11px; color: #6B85A0; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; }
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
  background: linear-gradient(135deg, #7EB6E5 0%, #5A9CCF 100%);
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(90,140,200,0.30);
}
.mini-empty { color: #7A8FA5; font-size: 11px; margin-top: auto; font-style: italic; letter-spacing: 0.3px; }

</style>
