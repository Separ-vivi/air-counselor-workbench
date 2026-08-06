<template>
  <el-row :gutter="16" style="margin-bottom: 16px">
    <el-col :span="8">
      <el-card shadow="never" class="chart-card triple-card">
        <template #header>
          <div class="card-header">
            <span class="ch-title">预警灯分布</span>
            <el-button text type="primary" size="small" @click="$emit('goWarning')">查看学业预警</el-button>
          </div>
        </template>
        <div ref="warningPieRef" class="chart-box"></div>
        <div class="chart-legend">
          <span class="lg-dot" style="background:#F5B7B7"></span>红牌 {{ dash.redCount }}
          <span class="lg-dot" style="background:#F5D78A; margin-left:12px"></span>黄牌 {{ dash.yellowCount }}
          <span class="lg-dot" style="background:#8FD5C4; margin-left:12px"></span>正常 {{ dash.normalCount }}
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
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  dash: {
    type: Object,
    required: true,
    default: () => ({
      total_students: 0, total_classes: 0, total_majors: 0,
      red_count: 0, yellow_count: 0, normal_count: 0,
      major_distribution: [], class_distribution: [], tag_distribution: []
    })
  },
  weekEvents: { type: Array, default: () => [] }
})

defineEmits(['goWarning'])

// ---- 响应式别名（供模板使用） ----
const dash = computed(() => ({
  redCount: props.dash.red_count,
  yellowCount: props.dash.yellow_count,
  normalCount: props.dash.normal_count
}))

// ---- 迷你日历逻辑 ----
const now = ref(new Date())
let clockTimer = null
onMounted(() => { clockTimer = setInterval(() => { now.value = new Date() }, 60000) })
onUnmounted(() => { if (clockTimer) clearInterval(clockTimer) })

const todayStrKey = computed(() => {
  const n = now.value
  const p = (x) => String(x).padStart(2, '0')
  return `${n.getFullYear()}-${p(n.getMonth()+1)}-${p(n.getDate())}`
})

const weekEventsByDay = computed(() => {
  const n = now.value
  const start = new Date(n)
  start.setDate(n.getDate() - ((n.getDay() + 6) % 7))
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
  for (const ev of props.weekEvents) {
    if (map[ev.date]) map[ev.date].items.push(ev)
  }
  return days
})

const evBarColor = (c) => {
  const m = {
    blue: '#7BB6D6', orange: '#F5A76E', yellow: '#E8C86A', pink: '#F1A6B7',
    green: '#8CC9A1', cyan: '#7EC4C0', purple: '#B29AC9', red: '#E88686',
  }
  return m[c] || '#909399'
}

// ---- ECharts 逻辑 ----
const warningPieRef = ref(null)
const majorPieRef = ref(null)
let charts = []
const iceMintColors = ['#5B92E5','#7BCFCB','#8FA9E5','#4FC3B8','#B7D5E4','#C7CEEA','#A8E6CF','#93C4E8','#B7E4E0','#DAE8F7','#6EAECF','#94D2C8']

function renderCharts() {
  charts.forEach(c => { try { c.dispose() } catch(e){} })
  charts = []

  if (warningPieRef.value) {
    const c1 = echarts.init(warningPieRef.value)
    c1.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { show: false },
      series: [{
        type: 'pie', radius: ['55%', '78%'], center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#FFFFFF', borderWidth: 2 },
        label: { show: true, position: 'center', formatter: () => `{a|${props.dash.total_students}}\n{b|全体学生}`, rich: { a:{fontSize:28,fontWeight:700,color:'#2E5A7F'}, b:{fontSize:12,color:'#8FA9E5',padding:[4,0,0,0]} } },
        labelLine: { show: false },
        data: [
          { value: props.dash.red_count,    name: '红牌', itemStyle: { color: '#F5B7B7' } },
          { value: props.dash.yellow_count, name: '黄牌', itemStyle: { color: '#F5D78A' } },
          { value: props.dash.normal_count, name: '正常', itemStyle: { color: '#8FD5C4' } }
        ]
      }]
    })
    charts.push(c1)
  }

  if (majorPieRef.value) {
    const c2 = echarts.init(majorPieRef.value)
    const md = props.dash.major_distribution || []
    c2.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)' },
      legend: { bottom: 4, textStyle: { fontSize: 11, color: '#5B92E5' }, itemWidth: 10, itemHeight: 10 },
      series: [{
        type: 'pie', radius: ['55%', '78%'], center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#FFFFFF', borderWidth: 2 },
        label: { show: true, position: 'center', formatter: () => `{a|${md.length}}\n{b|专业数}`, rich: { a:{fontSize:28,fontWeight:700,color:'#2E5A7F'}, b:{fontSize:12,color:'#8FA9E5',padding:[4,0,0,0]} } },
        labelLine: { show: false },
        data: md.map((x, i) => ({ value: x.value, name: x.name, itemStyle: { color: iceMintColors[i % iceMintColors.length] } }))
      }]
    })
    charts.push(c2)
  }
}

function resizeCharts() { charts.forEach(c => { try { c.resize() } catch(e){} }) }

onMounted(() => {
  window.addEventListener('resize', resizeCharts)
})
onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  charts.forEach(c => { try { c.dispose() } catch(e){} })
})

// 监听 dash 变化，重新渲染图表
watch(() => props.dash, () => {
  nextTick(() => renderCharts())
}, { deep: true })

// 暴露 renderCharts 供父组件调用
defineExpose({ renderCharts })
</script>

<style scoped>
.chart-card :deep(.el-card__header) {
  padding: 12px 18px;
  background: transparent;
  border-bottom: 1px solid rgba(220, 226, 232, 0.5);
}
.chart-box {
  width: 100%;
  height: 220px;
}
.chart-legend {
  display: flex;
  justify-content: center;
  font-size: 12px;
  color: var(--color-primary);
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ch-title {
  font-weight: 600;
  font-size: 14px;
  color: #2E5A7F;
  letter-spacing: 0.4px;
}
.triple-card { height: 100%; }
.triple-card :deep(.el-card__body) { padding: 12px 16px; }

.mini-week-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 6px 2px;
}
.mini-day {
  position: relative;
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
  background: linear-gradient(135deg, #A6D5DE 0%, var(--color-mint) 55%, var(--color-accent) 100%);
  border-color: rgba(255, 255, 255, 0.92);
  box-shadow: 0 4px 14px rgba(91, 146, 229, 0.24), inset 0 1px 0 rgba(255,255,255,0.85);
}
.mini-day.is-today .mini-mmdd { color: #FFFFFF; text-shadow: 0 1px 2px rgba(46, 90, 127, 0.35); }
.mini-day.is-today .mini-week { color: rgba(255,255,255,0.92); text-shadow: 0 1px 2px rgba(46, 90, 127, 0.35); }
.mini-day.is-today .mini-empty { color: rgba(255,255,255,0.88); font-style: normal; font-weight: 500; }
.mini-day.is-today .mini-badge { background: rgba(255,255,255,0.95); color: var(--color-primary); }
.mini-week { font-size: 11px; color: var(--color-primary); font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; }
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
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(91,146,229,0.30);
}
.mini-empty { color: rgba(79, 195, 184, 0.65); font-size: 11px; margin-top: auto; font-style: italic; letter-spacing: 0.3px; }
</style>
