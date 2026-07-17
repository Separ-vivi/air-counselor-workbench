<template>
  <div class="calendar-page">
    <div class="page-header">
      <h2>📅 统一日程本</h2>
      <div class="header-actions">
        <el-radio-group v-model="viewMode" size="default" @change="onViewChange">
          <el-radio-button label="month">月视图</el-radio-button>
          <el-radio-button label="week">周视图</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :icon="Plus" @click="onCreateCd">新建倒计时</el-button>
        <el-button :icon="MagicStick" @click="onSeedHolidays">灌入法定节假日</el-button>
      </div>
    </div>

    <!-- 图例（v3h-hotfix1: 颜色对齐后端 event.color） -->
    <div class="legend-row">
      <span class="lg-tag lg-blue">📚 校历倒计时</span>
      <span class="lg-tag lg-orange">☑️ 待办截止</span>
      <span class="lg-tag lg-yellow">🔔 记事提醒</span>
      <span class="lg-tag lg-purple">🎯 项目节点</span>
      <span class="lg-tag lg-pink">📌 活动</span>
      <span class="lg-tag lg-green">🏫 班会</span>
      <span class="lg-tag lg-cyan">👨‍👩‍👧 家校沟通</span>
    </div>

    <!-- 倒计时 chip 区（保留） -->
    <div class="cd-section" v-loading="loadingCd">
      <el-empty v-if="!loadingCd && countdowns.length === 0" description="暂无倒计时，点右上「新建倒计时」" :image-size="60" />
      <div class="cd-grid" v-else>
        <div
          v-for="c in countdowns"
          :key="c.id"
          class="cd-card"
          :class="[`color-${c.color}`, cdUrgencyClass(c)]"
        >
          <div class="cd-title">{{ c.title }} <el-icon v-if="c.pinned" class="pin"><Top /></el-icon></div>
          <div class="cd-days">
            <span class="num">{{ Math.max(c.days_left, 0) }}</span>
            <span class="unit">{{ c.days_left <= 0 ? '今天' : '天' }}</span>
          </div>
          <div class="cd-meta">
            <el-tag size="small" effect="plain">{{ categoryLabel(c.category) }}</el-tag>
            <span class="date">{{ c.target_date }}</span>
          </div>
          <div class="cd-actions">
            <el-button link :icon="Edit" size="small" @click="onEditCd(c)" />
            <el-button link :icon="Delete" size="small" @click="onDeleteCd(c)" />
          </div>
        </div>
      </div>
    </div>

    <el-divider>📆 {{ viewMode === 'month' ? '月视图' : '周视图' }}</el-divider>

    <!-- 月视图：el-calendar -->
    <div v-if="viewMode === 'month'" class="calendar-wrap" v-loading="loadingEvents">
      <el-calendar v-model="currentDate">
        <template #date-cell="{ data }">
          <div class="day-cell" @click="onDayClick(data.day)">
            <div class="day-num">{{ data.day.split('-')[2] }}</div>
            <div class="day-events">
              <span
                v-for="ev in (eventsByDay[data.day] || []).slice(0, 3)"
                :key="`${ev.type}-${ev.id}`"
                class="event-dot"
                :style="{ background: evBg(ev) }"
                :title="ev.title"
              >
                <span class="dot-icon">{{ evIcon(ev.type) }}</span>
                {{ (ev.title || '').slice(0, 6) }}
              </span>
              <span v-if="(eventsByDay[data.day] || []).length > 3" class="more-hint">
                +{{ eventsByDay[data.day].length - 3 }}
              </span>
            </div>
          </div>
        </template>
      </el-calendar>
    </div>

    <!-- 周视图：横向 7 列 -->
    <div v-else class="week-view" v-loading="loadingEvents">
      <div class="week-nav">
        <el-button link @click="shiftWeek(-1)">← 上一周</el-button>
        <span class="week-range">{{ weekRangeLabel }}</span>
        <el-button link @click="shiftWeek(1)">下一周 →</el-button>
        <el-button link @click="goThisWeek">回到本周</el-button>
      </div>
      <div class="week-grid">
        <div
          v-for="(d, idx) in weekDays"
          :key="d.dateKey"
          class="week-day"
          :class="{ today: d.isToday, weekend: idx >= 5 }"
          @click="onDayClick(d.dateKey)"
        >
          <div class="week-day-head">
            <span class="wd-name">{{ ['一','二','三','四','五','六','日'][idx] }}</span>
            <span class="wd-num">{{ d.dateKey.slice(5).replace('-', '/') }}</span>
          </div>
          <div class="week-day-body">
            <div
              v-if="(eventsByDay[d.dateKey] || []).length === 0"
              class="week-empty"
            >—</div>
            <div
              v-for="ev in eventsByDay[d.dateKey] || []"
              :key="`${ev.type}-${ev.id}`"
              class="week-ev"
              :style="{ borderLeftColor: evBg(ev) }"
              @click.stop="onEventClick(ev, d.dateKey)"
            >
              <span class="wev-icon">{{ evIcon(ev.type) }}</span>
              <span class="wev-title">{{ ev.title }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 当日详情 drawer -->
    <el-drawer v-model="dayDrawer" :title="`${selectedDay || ''} 当日事项`" size="420px">
      <div class="drawer-actions">
        <el-button size="small" :icon="Plus" @click="onQuickCd">新建倒计时</el-button>
        <el-button size="small" @click="onGoNotes">去记事本新建提醒</el-button>
      </div>
      <el-empty v-if="dayEvents.length === 0" description="当日无安排" />
      <div v-for="ev in dayEvents" :key="`${ev.type}-${ev.id}`" class="day-item">
        <div class="day-item-header">
          <span class="ev-badge" :style="{ background: evBg(ev) }">{{ evIcon(ev.type) }} {{ typeLabel(ev.type) }}</span>
          <span class="day-item-title">{{ ev.title }}</span>
        </div>
        <div v-if="ev.description" class="day-item-desc">{{ ev.description }}</div>
        <div v-if="ev.meta" class="day-item-meta">
          <template v-for="(v, k) in ev.meta" :key="k">
            <el-tag v-if="v" size="small" effect="plain" round>{{ metaLabel(k) }}: {{ v }}</el-tag>
          </template>
        </div>
        <div v-if="ev.link" class="day-item-link">
          <el-button link type="primary" @click="onGoLink(ev.link)">前往查看 →</el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 倒计时编辑弹窗 -->
    <el-dialog v-model="cdDialog" :title="cdForm.id ? '编辑倒计时' : '新建倒计时'" width="480px">
      <el-form :model="cdForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="cdForm.title" placeholder="例：期末考试 / 就业签约截止" maxlength="200" />
        </el-form-item>
        <el-form-item label="目标日期" required>
          <el-date-picker v-model="cdForm.target_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="cdForm.category" style="width:100%">
            <el-option value="general" label="一般" />
            <el-option value="exam" label="考试" />
            <el-option value="deadline" label="截止" />
            <el-option value="event" label="活动" />
            <el-option value="holiday" label="节假日" />
          </el-select>
        </el-form-item>
        <el-form-item label="颜色">
          <el-radio-group v-model="cdForm.color">
            <el-radio label="blue">蓝</el-radio>
            <el-radio label="pink">粉</el-radio>
            <el-radio label="green">绿</el-radio>
            <el-radio label="yellow">黄</el-radio>
            <el-radio label="purple">紫</el-radio>
            <el-radio label="orange">橙</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="cdForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="置顶">
          <el-switch v-model="cdForm.pinned" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cdDialog = false">取消</el-button>
        <el-button type="primary" @click="onSaveCd" :loading="savingCd">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Top, MagicStick } from '@element-plus/icons-vue'
import { countdownsApi, eventsApi } from '@/api/productivity.js'
import http from '@/api/index.js'

const router = useRouter()

const countdowns = ref([])
const events = ref([])
const loadingCd = ref(false)
const loadingEvents = ref(false)

const viewMode = ref('month')
const currentDate = ref(new Date())
const selectedDay = ref('')
const dayDrawer = ref(false)
const weekOffset = ref(0)

const cdDialog = ref(false)
const savingCd = ref(false)
const cdForm = ref({
  id: null, title: '', target_date: '', category: 'general',
  color: 'blue', description: '', pinned: false,
})

function pad(n) { return String(n).padStart(2, '0') }
function fmtDate(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` }
function mondayOf(d) {
  const dd = new Date(d)
  dd.setHours(0, 0, 0, 0)
  const day = dd.getDay()
  const diff = day === 0 ? -6 : 1 - day
  dd.setDate(dd.getDate() + diff)
  return dd
}
function addDays(d, n) { const dd = new Date(d); dd.setDate(dd.getDate() + n); return dd }

async function loadCd() {
  loadingCd.value = true
  try {
    const data = await countdownsApi.list({ include_past: false })
    countdowns.value = data || []
  } finally { loadingCd.value = false }
}

async function loadEvents() {
  loadingEvents.value = true
  try {
    let start, end
    if (viewMode.value === 'month') {
      const y = currentDate.value.getFullYear()
      const m = currentDate.value.getMonth()
      start = fmtDate(new Date(y, m - 1, 15))
      end = fmtDate(new Date(y, m + 1, 15))
    } else {
      const mon = mondayOf(addDays(new Date(), weekOffset.value * 7))
      start = fmtDate(mon)
      end = fmtDate(addDays(mon, 6))
    }
    const data = await eventsApi.list(start, end)
    events.value = data?.events || []
  } catch (e) {
    events.value = []
  } finally { loadingEvents.value = false }
}

const eventsByDay = computed(() => {
  const map = {}
  for (const ev of events.value) {
    const d = ev.date
    if (!d) continue
    if (!map[d]) map[d] = []
    map[d].push(ev)
  }
  return map
})

const weekDays = computed(() => {
  const mon = mondayOf(addDays(new Date(), weekOffset.value * 7))
  const todayKey = fmtDate(new Date())
  return Array.from({ length: 7 }).map((_, i) => {
    const d = addDays(mon, i)
    const key = fmtDate(d)
    return { dateKey: key, isToday: key === todayKey }
  })
})

const weekRangeLabel = computed(() => {
  if (weekDays.value.length === 0) return ''
  return `${weekDays.value[0].dateKey} ~ ${weekDays.value[6].dateKey}`
})

const dayEvents = computed(() => {
  if (!selectedDay.value) return []
  return eventsByDay.value[selectedDay.value] || []
})

function evBg(ev) {
  const map = {
    blue: '#4A7A8C', orange: '#E58B3E', yellow: '#D9A441',
    pink: '#C9635B', green: '#2E7D6B', cyan: '#3F8FA5',
    purple: '#7A6BAF', red: '#C0392B',
  }
  return map[ev.color] || map.blue
}
function evIcon(t) {
  return ({
    countdown: '📚', todo: '☑️', memo: '🔔',
    project: '🎯', activity: '📌', meeting: '🏫', family: '👨‍👩‍👧',
  })[t] || '·'
}
function typeLabel(t) {
  return ({
    countdown: '校历倒计时', todo: '待办截止', memo: '记事提醒',
    project: '项目节点', activity: '活动', meeting: '班会', family: '家校沟通',
  })[t] || t
}
function metaLabel(k) {
  return ({
    type: '类型', priority: '优先级', student: '学生', class_name: '班级',
    location: '地点', activity_type: '活动类型', node: '节点', time: '时间',
    contact_type: '沟通方式', teacher: '班主任',
  })[k] || k
}

function onViewChange() { loadEvents() }
function shiftWeek(n) { weekOffset.value += n; loadEvents() }
function goThisWeek() { weekOffset.value = 0; loadEvents() }
function onDayClick(day) { selectedDay.value = day; dayDrawer.value = true }
function onEventClick(ev, day) { selectedDay.value = day; dayDrawer.value = true }

function onQuickCd() {
  cdForm.value = { id: null, title: '', target_date: selectedDay.value, category: 'general', color: 'blue', description: '', pinned: false }
  cdDialog.value = true
  dayDrawer.value = false
}
function onGoNotes() {
  router.push({ path: '/notes', query: { create: 'todo', due: selectedDay.value } })
}
function onGoLink(link) {
  if (!link) return
  if (link.startsWith('/')) router.push(link)
  else window.open(link, '_blank')
}

function cdUrgencyClass(c) {
  if (c.days_left == null) return ''
  if (c.days_left <= 3) return 'urgent'
  if (c.days_left <= 7) return 'soon'
  return ''
}
function categoryLabel(cat) {
  return ({ exam: '考试', deadline: '截止', event: '活动', holiday: '节假日', general: '一般' })[cat] || '一般'
}
function onCreateCd() {
  cdForm.value = { id: null, title: '', target_date: '', category: 'general', color: 'blue', description: '', pinned: false }
  cdDialog.value = true
}
function onEditCd(c) {
  cdForm.value = { ...c }
  cdDialog.value = true
}
async function onSaveCd() {
  if (!cdForm.value.title || !cdForm.value.target_date) {
    ElMessage.warning('标题和目标日期不能为空')
    return
  }
  savingCd.value = true
  try {
    if (cdForm.value.id) {
      await countdownsApi.update(cdForm.value.id, cdForm.value)
    } else {
      await countdownsApi.create(cdForm.value)
    }
    ElMessage.success('已保存')
    cdDialog.value = false
    await loadCd()
    await loadEvents()
  } finally { savingCd.value = false }
}
async function onDeleteCd(c) {
  try {
    await ElMessageBox.confirm(`确认删除「${c.title}」？`, '提示', { type: 'warning' })
    await countdownsApi.remove(c.id)
    ElMessage.success('已删除')
    await loadCd()
    await loadEvents()
  } catch {}
}
async function onSeedHolidays() {
  try {
    await ElMessageBox.confirm(
      '将写入 2026 年全部法定节假日 + 学期关键节点（元旦/春节/清明/劳动节/端午/中秋/国庆 + 开学/期中/期末/寒假等），已存在的同名条目会被替换。是否继续？',
      '一键灌入校历',
      { confirmButtonText: '灌入', cancelButtonText: '取消', type: 'warning' }
    )
  } catch { return }
  try {
    const data = await http.post('/system/seed-holidays', null, { params: { overwrite: true } })
    ElMessage.success(`已灌入，新增 ${data?.stats?.added ?? 0} 条`)
    await loadCd()
    await loadEvents()
  } catch (e) {
    ElMessage.error('灌入失败：' + (e?.response?.data?.detail || e.message))
  }
}

watch(currentDate, () => { if (viewMode.value === 'month') loadEvents() })
onMounted(() => { loadCd(); loadEvents() })
</script>

<style scoped>
.calendar-page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 10px; align-items: center; }

.legend-row {
  display: flex; flex-wrap: wrap; gap: 8px;
  padding: 8px 12px; margin-bottom: 12px;
  background: rgba(255,255,255,0.5);
  border-radius: 8px;
  font-size: 12px;
}
.lg-tag { padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 12px; }
.lg-blue   { background: #4A7A8C; }
.lg-orange { background: #E58B3E; }
.lg-yellow { background: #D9A441; }
.lg-pink   { background: #C9635B; }
.lg-green  { background: #2E7D6B; }
.lg-cyan   { background: #3F8FA5; }
.lg-purple { background: #7A6BAF; }

.cd-section { margin-bottom: 12px; min-height: 80px; }
.cd-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.cd-card {
  padding: 12px 14px; border-radius: 12px; border: 1px solid transparent;
  box-shadow: 0 2px 8px rgba(74,122,140,.06);
  display: flex; flex-direction: column; gap: 4px; position: relative;
  transition: transform .12s;
}
.cd-card:hover { transform: translateY(-2px); }
.cd-card.color-blue   { background: #DBEAF3; }
.cd-card.color-pink   { background: #FADBDB; }
.cd-card.color-green  { background: #DCF0DE; }
.cd-card.color-yellow { background: #FDF3C9; }
.cd-card.color-purple { background: #E6D9F0; }
.cd-card.color-orange { background: #FCE4CA; }
.cd-card.urgent { border-color: #F56C6C; }
.cd-card.soon   { border-color: #E6A23C; }

.cd-title { font-weight: 600; font-size: 14px; color: #3A3A3A; display: flex; align-items: center; gap: 4px; }
.cd-title .pin { color: #E58B3E; }
.cd-days { display: flex; align-items: baseline; gap: 4px; margin-top: 2px; }
.cd-days .num { font-size: 28px; font-weight: 700; color: #4A7A8C; line-height: 1; }
.cd-days .unit { font-size: 12px; color: #7B7B7B; }
.cd-meta { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #7B7B7B; }
.cd-actions { position: absolute; right: 8px; top: 8px; }
.cd-actions .el-button { padding: 3px; }

.calendar-wrap :deep(.el-calendar-day) { height: 96px !important; padding: 4px !important; }
.day-cell { height: 100%; display: flex; flex-direction: column; cursor: pointer; }
.day-num { font-size: 13px; font-weight: 600; color: #3A3A3A; }
.day-events { flex: 1; display: flex; flex-direction: column; gap: 2px; overflow: hidden; margin-top: 2px; }
.event-dot {
  font-size: 10px; padding: 1px 4px; border-radius: 4px; color: #fff;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.dot-icon { margin-right: 2px; font-size: 10px; }
.more-hint { font-size: 10px; color: #7B7B7B; }

.week-view { background: rgba(255,255,255,0.5); border-radius: 12px; padding: 12px; }
.week-nav { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.week-range { font-weight: 600; color: #3A3A3A; }
.week-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }
.week-day {
  min-height: 220px; background: #fff; border: 1px solid #E1E7EE;
  border-radius: 10px; padding: 8px; cursor: pointer; transition: box-shadow .12s;
}
.week-day:hover { box-shadow: 0 2px 12px rgba(74,122,140,.12); }
.week-day.today { border-color: #4A7A8C; box-shadow: 0 0 0 2px rgba(74,122,140,.15); }
.week-day.weekend { background: #F7F9FC; }
.week-day-head { display: flex; justify-content: space-between; align-items: center; padding-bottom: 6px; border-bottom: 1px dashed #eee; margin-bottom: 6px; }
.wd-name { font-weight: 600; color: #3A3A3A; }
.wd-num { font-size: 12px; color: #7B7B7B; }
.week-day-body { display: flex; flex-direction: column; gap: 4px; }
.week-empty { text-align: center; color: #C0C4CC; font-size: 12px; padding: 10px 0; }
.week-ev {
  padding: 4px 6px; border-left: 3px solid #4A7A8C; background: #F5F9FC;
  border-radius: 4px; font-size: 12px; color: #3A3A3A;
  display: flex; gap: 4px; align-items: center; cursor: pointer;
}
.week-ev:hover { background: #EAF3F7; }
.wev-icon { font-size: 12px; }
.wev-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.drawer-actions { display: flex; gap: 8px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #eee; }
.day-item { padding: 12px 0; border-bottom: 1px dashed #eee; }
.day-item-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.day-item-title { font-weight: 600; color: #3A3A3A; }
.ev-badge { padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 11px; }
.day-item-desc { font-size: 13px; color: #5A5A5A; margin: 4px 0; }
.day-item-meta { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.day-item-link { margin-top: 6px; }
</style>
