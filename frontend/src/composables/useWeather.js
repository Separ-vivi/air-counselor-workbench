/* V4-hotfix10 (air 2026-07-18): Dashboard Hero 天气组件
 * 数据源: wttr.in (免 key, 支持 IP 自动定位 + 中文, 本地部署可用)
 * 兜底: 自动定位失败 → 福州; 全失败 → 显示占位不阻塞主界面
 * 缓存: localStorage 1 小时, 避免频繁调用外网
 */
import { ref, onMounted } from 'vue'

const CACHE_KEY = 'air_weather_cache_v1'
const CACHE_TTL = 60 * 60 * 1000 // 1 hour

// 中文天气描述 → emoji 图标
const ICON_MAP = [
  ['雷', '⛈️'], ['暴雨', '🌧️'], ['大雨', '🌧️'], ['中雨', '🌧️'],
  ['小雨', '🌦️'], ['阵雨', '🌦️'], ['雨', '🌧️'],
  ['雪', '❄️'], ['雾', '🌫️'], ['霾', '🌫️'],
  ['多云', '⛅'], ['阴', '☁️'], ['晴', '☀️'], ['风', '💨']
]
function pickIcon(desc) {
  if (!desc) return '🌤️'
  for (const [k, v] of ICON_MAP) {
    if (desc.includes(k)) return v
  }
  return '🌤️'
}

async function fetchWithTimeout(url, timeout = 4500) {
  const ctl = new AbortController()
  const t = setTimeout(() => ctl.abort(), timeout)
  try {
    const r = await fetch(url, { signal: ctl.signal, mode: 'cors' })
    if (!r.ok) return null
    return await r.json()
  } catch (e) {
    return null
  } finally {
    clearTimeout(t)
  }
}

function parseWttr(data) {
  if (!data || !data.current_condition || !data.current_condition[0]) return null
  const cur = data.current_condition[0]
  const area = data.nearest_area && data.nearest_area[0]
  const city =
    area?.areaName?.[0]?.value ||
    area?.region?.[0]?.value ||
    '福州'
  let desc = ''
  if (Array.isArray(cur.lang_zh) && cur.lang_zh[0]?.value) desc = cur.lang_zh[0].value
  else if (cur.weatherDesc && cur.weatherDesc[0]?.value) desc = cur.weatherDesc[0].value
  return {
    city,
    desc,
    icon: pickIcon(desc),
    tempC: cur.temp_C || '--',
    loaded: true
  }
}

export function useWeather() {
  const weather = ref({
    city: '福州',
    icon: '🌤️',
    desc: '',
    tempC: '',
    loaded: false
  })

  const load = async () => {
    // 命中 1 小时缓存
    try {
      const s = localStorage.getItem(CACHE_KEY)
      if (s) {
        const c = JSON.parse(s)
        if (c && c.ts && Date.now() - c.ts < CACHE_TTL && c.data) {
          weather.value = { ...c.data, loaded: true }
          return
        }
      }
    } catch (e) {}

    // 1. wttr.in 自动 IP 定位
    let d = await fetchWithTimeout('https://wttr.in/?format=j1&lang=zh')
    let parsed = parseWttr(d)
    // 2. 兜底福州
    if (!parsed) {
      d = await fetchWithTimeout('https://wttr.in/Fuzhou?format=j1&lang=zh')
      parsed = parseWttr(d)
    }
    if (parsed) {
      weather.value = parsed
      try {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), data: parsed }))
      } catch (e) {}
    }
  }

  onMounted(load)
  return { weather, refresh: load }
}
