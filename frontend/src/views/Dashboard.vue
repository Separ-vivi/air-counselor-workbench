<template>
  <div class="dashboard">
    <div class="hero-card">
      <div class="hero-left">
        <div class="hero-greeting">{{ greeting }}，老师 👋</div>
        <div class="hero-date">
          <span class="hero-date-main">{{ dateStr }}</span>
          <span class="hero-date-week">{{ weekdayStr }}</span>
        </div>
        <div class="hero-sub">辅导员工作台 · 一切从容如常</div>
      </div>
      <div class="hero-right">
        <div class="hero-time">{{ timeStr }}</div>
        <div class="hero-time-label">当前时间</div>
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


    <!-- ============ 可视化图表区（air 要求：类多维表格样式，不要冷冰冰数字） ============ -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="8">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>🎯 预警灯分布</span>
              <span class="chart-sub">全体 {{ dash.total_students }} 人</span>
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
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>🎓 专业人数分布</span>
              <span class="chart-sub">{{ dash.total_majors }} 个专业</span>
            </div>
          </template>
          <div ref="majorPieRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>🏷️ 学生标签 Top</span>
              <span class="chart-sub">热度前 8</span>
            </div>
          </template>
          <div ref="tagBarRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="24">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>📊 各班学生人数对比</span>
              <span class="chart-sub">{{ dash.total_classes }} 个班级 · 点击柱状图跳转班级 360</span>
            </div>
          </template>
          <div ref="classBarRef" class="chart-box-wide"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>⚠️ 关注学生 (预警灯)</span>
              <el-button text type="primary" size="small" @click="goWarning">查看全部</el-button>
            </div>
          </template>
          <el-empty v-if="!warnings.length" description="暂无预警学生" :image-size="80" />
          <el-table v-else :data="warnings.slice(0, 10)" size="small">
            <el-table-column label="学生" prop="name" width="100">
              <template #default="{ row }">
                <el-link type="primary" @click="goStudent(row.id)">{{ row.name }}</el-link>
              </template>
            </el-table-column>
            <el-table-column label="学号" prop="student_no" width="130" />
            <el-table-column label="班级" prop="class_name" show-overflow-tooltip />
            <el-table-column label="预警" prop="warning_reason" show-overflow-tooltip>
              <template #default="{ row }">
                <el-tag size="small" type="danger">{{ row.warning_reason || row.reason || '需关注' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>📅 近期动态</span>
            </div>
          </template>
          <el-empty v-if="!recentActivities.length" description="暂无近期动态" :image-size="80" />
          <el-timeline v-else style="max-height: 340px; overflow: auto">
            <el-timeline-item
              v-for="(item, idx) in recentActivities.slice(0, 12)"
              :key="idx"
              :timestamp="item.activity_date || item.time || item.date || item.created_at || '未标注日期'"
              placement="top"
              :type="idx === 0 ? 'primary' : 'success'"
              :hollow="idx > 0"
            >
              <div class="timeline-title">{{ item.title || item.desc || item.content || '未命名' }}</div>
              <div v-if="item.location || item.activity_type" class="timeline-meta">
                <el-tag v-if="item.activity_type" size="small" effect="light">{{ item.activity_type }}</el-tag>
                <span v-if="item.location" style="margin-left:6px;color:#909399">📍 {{ item.location }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>📌 待办中心</span>
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
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>⏳ 校历倒计时</span>
              <el-button text type="primary" size="small" @click="$router.push('/calendar')">打开校历</el-button>
            </div>
          </template>
          <el-empty v-if="!prodStats.countdowns_top || !prodStats.countdowns_top.length" description="暂无倒计时事件" :image-size="60" />
          <div v-else class="cd-row">
            <div v-for="cd in prodStats.countdowns_top" :key="cd.id" class="cd-card" :style="{ borderColor: cd.color || '#4A7A8C' }">
              <div class="cd-title">{{ cd.title }}</div>
              <div class="cd-date">{{ cd.target_date }}</div>
              <div class="cd-days" :class="daysClass(cd.days_left)">
                {{ cd.days_left >= 0 ? `还有 ${cd.days_left} 天` : `已过 ${-cd.days_left} 天` }}
              </div>
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
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useRouter } from 'vue-router'
import { dashboard as getDashboard } from '@/api/modules'
import { productivityDashboard } from '@/api/productivity'

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
const tagBarRef = ref(null)
const classBarRef = ref(null)
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

  // ---- 标签 TOP 横向柱状 ----
  if (tagBarRef.value) {
    const c3 = echarts.init(tagBarRef.value)
    const td = (dash.value.tag_distribution || []).slice(0, 8).reverse()
    c3.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 8, right: 30, top: 12, bottom: 8, containLabel: true },
      xAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#E4E7ED' } }, axisLabel: { color: '#909399', fontSize: 11 } },
      yAxis: { type: 'category', data: td.map(x => x.name), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#606266', fontSize: 12 } },
      series: [{
        type: 'bar', barWidth: 14, data: td.map((x, i) => ({ value: x.value, itemStyle: { color: x.color || macaronColors[i % macaronColors.length], borderRadius: [0, 6, 6, 0] } })),
        label: { show: true, position: 'right', color: '#606266', fontSize: 11 }
      }]
    })
    charts.push(c3)
  }

  // ---- 班级人数柱状 ----
  if (classBarRef.value) {
    const c4 = echarts.init(classBarRef.value)
    const cd = dash.value.class_distribution || []
    c4.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 8, right: 12, top: 20, bottom: 40, containLabel: true },
      xAxis: { type: 'category', data: cd.map(x => x.name), axisLine: { lineStyle: { color: '#DCDFE6' } }, axisLabel: { color: '#606266', fontSize: 11, rotate: cd.length > 8 ? 20 : 0, interval: 0 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#E4E7ED' } }, axisLabel: { color: '#909399', fontSize: 11 } },
      series: [{
        type: 'bar', barWidth: '46%',
        data: cd.map((x, i) => ({ value: x.value, itemStyle: { color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: macaronColors[i % macaronColors.length] },
            { offset: 1, color: '#FFFFFF' }
          ]
        }, borderRadius: [8, 8, 0, 0] } })),
        label: { show: true, position: 'top', color: '#606266', fontSize: 11, fontWeight: 500 }
      }]
    })
    c4.on('click', (params) => {
      const name = params?.name
      if (!name) return
      // 跳到班级 360（用 class_name query）
      router.push({ path: '/class360', query: { class_name: name } })
    })
    charts.push(c4)
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

const daysClass = (d) => {
  if (d === undefined || d === null) return ''
  if (d <= 3) return 'danger'
  if (d <= 7) return 'warning'
  return ''
}

const statCards = ref([
  { label: '在校学生', value: 0, icon: '👥', bg: '#E1F0FF' },
  { label: '班级数量', value: 0, icon: '🎓', bg: '#E8F5E9' },
  { label: '党员/发展对象', value: 0, icon: '🚩', bg: '#FFEBEE' },
  { label: '本月活动', value: 0, icon: '🎨', bg: '#FFF8E1' }
])

const shortcuts = [
  { icon: '📋', label: '学生管理', to: '/students', bg: '#E1F0FF' },
  { icon: '🎓', label: '班级管理', to: '/classes', bg: '#E8F5E9' },
  { icon: '🏛️', label: '组织架构', to: '/org', bg: '#FFF3E0' },
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
})
</script>

<style scoped>
/* ============ 全局：马卡龙渐变背景 ============ */
.dashboard {
  padding: 8px;
  min-height: calc(100vh - 100px);
  background:
    radial-gradient(circle at 10% 10%, rgba(255, 210, 220, 0.35), transparent 40%),
    radial-gradient(circle at 90% 20%, rgba(200, 230, 240, 0.35), transparent 45%),
    radial-gradient(circle at 50% 100%, rgba(220, 220, 250, 0.30), transparent 50%),
    linear-gradient(180deg, #FDFCFA 0%, #F5F7FA 100%);
  border-radius: 20px;
}

/* ============ 顶部 hero 时钟卡片 ============ */
.hero-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  margin-bottom: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(180, 190, 220, 0.15);
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
.hero-right { text-align: right; }
.hero-time {
  font-size: 42px;
  font-weight: 300;
  color: #4A6A7A;
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
  background: rgba(255, 255, 255, 0.65) !important;
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.7) !important;
  box-shadow: 0 4px 16px rgba(180, 190, 220, 0.12);
  transition: transform 0.2s, box-shadow 0.2s;
}
.dashboard :deep(.el-col > .el-card:hover) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(180, 190, 220, 0.18);
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
  display: flex;
  align-items: center;
  gap: 14px;
}
.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
}
.stat-body .stat-label {
  color: #909399;
  font-size: 13px;
}
.stat-body .stat-value {
  color: #303133;
  font-size: 22px;
  font-weight: 600;
  margin-top: 4px;
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
.prod-item { flex: 1; text-align: center; padding: 18px 8px; border-radius: 10px; background: #F5F7FA; }
.prod-num { font-size: 32px; font-weight: 700; color: #303133; }
.prod-num.warning { color: #E6A23C; }
.prod-num.danger { color: #F56C6C; }
.prod-num.success { color: #67C23A; }
.prod-label { color: #909399; font-size: 12px; margin-top: 6px; }
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
</style>
