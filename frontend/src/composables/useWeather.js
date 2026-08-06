/* V4-hotfix11 (air 2026-07-18): Dashboard Hero 天气组件
 * 数据源: wttr.in Fuzhou 硬编端点（air 开 VPN 常态, 自动 IP 定位不可靠, 直接锁福州）
 * 描述: weatherCode 数字码 → 中文映射（不依赖 wttr.in 的 lang 翻译, VPN 下常返回英文）
 * 缓存: localStorage 1 小时, 避免频繁调用外网
 */
import { ref, onMounted } from 'vue'

const CACHE_KEY = 'air_weather_cache_v2'
const CACHE_TTL = 60 * 60 * 1000 // 1 hour

// wttr.in / WWO weatherCode → 中文描述 + emoji
// 参考: https://github.com/chubin/wttr.in/blob/master/lib/constants.py
const CODE_MAP = {
  '113': ['晴', '☀️'],
  '116': ['多云', '⛅'],
  '119': ['阴', '☁️'],
  '122': ['阴', '☁️'],
  '143': ['雾', '🌫️'],
  '176': ['局部小雨', '🌦️'],
  '179': ['局部小雪', '🌨️'],
  '182': ['局部雨夹雪', '🌨️'],
  '185': ['局部冻雨', '🌨️'],
  '200': ['雷阵雨', '⛈️'],
  '227': ['小雪', '🌨️'],
  '230': ['暴雪', '❄️'],
  '248': ['雾', '🌫️'],
  '260': ['冻雾', '🌫️'],
  '263': ['小阵雨', '🌦️'],
  '266': ['小雨', '🌦️'],
  '281': ['冻雨', '🌧️'],
  '284': ['大冻雨', '🌧️'],
  '293': ['小雨', '🌦️'],
  '296': ['小雨', '🌦️'],
  '299': ['中雨', '🌧️'],
  '302': ['中雨', '🌧️'],
  '305': ['大雨', '🌧️'],
  '308': ['暴雨', '🌧️'],
  '311': ['冻雨', '🌧️'],
  '314': ['大冻雨', '🌧️'],
  '317': ['雨夹雪', '🌨️'],
  '320': ['雨夹雪', '🌨️'],
  '323': ['小雪', '🌨️'],
  '326': ['小雪', '🌨️'],
  '329': ['中雪', '❄️'],
  '332': ['中雪', '❄️'],
  '335': ['大雪', '❄️'],
  '338': ['暴雪', '❄️'],
  '350': ['冰雹', '🌨️'],
  '353': ['小阵雨', '🌦️'],
  '356': ['中阵雨', '🌧️'],
  '359': ['大阵雨', '🌧️'],
  '362': ['阵雨夹雪', '🌨️'],
  '365': ['阵雨夹雪', '🌨️'],
  '368': ['阵雪', '🌨️'],
  '371': ['大阵雪', '❄️'],
  '374': ['小冰雹', '🌨️'],
  '377': ['冰雹', '🌨️'],
  '386': ['雷阵雨', '⛈️'],
  '389': ['强雷阵雨', '⛈️'],
  '392': ['雷阵雪', '⛈️'],
  '395': ['强雷阵雪', '⛈️']
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
  const code = cur.weatherCode || ''
  const [desc, icon] = CODE_MAP[code] || ['—', '🌤️']
  return {
    city: '福州',
    desc,
    icon,
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

    // 硬编福州, 不做自动 IP 定位（air 开 VPN 常态）
    const d = await fetchWithTimeout('https://wttr.in/Fuzhou?format=j1')
    const parsed = parseWttr(d)
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
