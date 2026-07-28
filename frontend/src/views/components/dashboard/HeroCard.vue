<template>
  <div class="hero-card">
    <div class="hero-left">
      <div class="hero-greeting">{{ greeting }}，老师</div>
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
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWeather } from '@/composables/useWeather'

defineProps({
  heroCountdowns: { type: Array, default: () => [] }
})

const { weather } = useWeather()

// 实时时钟
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
</script>

<style scoped>
.hero-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  margin-bottom: 20px;
  border-radius: 20px;
  background: linear-gradient(160deg, #FFFFFF 0%, #E8F1FB 100%);
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
.hero-weather {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 4px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--shadow-sm) 0%, rgba(79, 195, 184, 0.10) 100%);
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
.hero-cd-row {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.hero-cd-chip {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  min-width: 100px;
  text-align: center;
}
.hero-cd-title { font-size: 12px; color: #4A5A6A; font-weight: 500; }
.hero-cd-days { font-size: 13px; margin-top: 3px; color: #3B6A7C; font-weight: 600; }
.hero-cd-days.warning { color: #E6A23C; }
.hero-cd-days.danger { color: #F56C6C; }
</style>
