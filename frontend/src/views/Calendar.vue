<template>
  <div class="calendar-page">
    <div class="page-header">
      <h2>📅 校历 & 倒计时</h2>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="onCreateCd">新建倒计时</el-button>
        <el-button :icon="MagicStick" @click="onSeedHolidays">一键灌入法定节假日</el-button>
      </div>
    </div>

    <!-- 倒计时区 -->
    <div class="cd-section" v-loading="loadingCd">
      <el-empty v-if="!loadingCd && countdowns.length === 0" description="暂无倒计时，点击「新建倒计时」添加" :image-size="80" />
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

    <el-divider>📆 校历日历</el-divider>

    <!-- 日历视图 -->
    <div class="calendar-wrap" v-loading="loadingAct">
      <el-calendar v-model="currentDate">
        <template #date-cell="{ data }">
          <div class="day-cell" @click="onDayClick(data.day)">
            <div class="day-num">{{ data.day.split('-')[2] }}</div>
            <div class="day-events">
              <span
                v-for="ev in eventsByDay[data.day] || []"
                :key="`${ev.type}-${ev.id}`"
                class="event-dot"
                :class="[`type-${ev.type}`, ev.subtype ? `sub-${ev.subtype}` : '']"
                :title="`${activityIcon(ev.subtype)} ${ev.title}`"
              >
                <span class="dot-icon">{{ activityIcon(ev.subtype || ev.type) }}</span>
                {{ ev.title.slice(0, 6) }}
              </span>
            </div>
          </div>
        </template>
      </el-calendar>
    </div>

    <!-- 当日详情 drawer -->
    <el-drawer v-model="dayDrawer" :title="`${selectedDay || ''} 当日事项`" size="380px">
      <el-empty v-if="dayEvents.length === 0" description="当日无安排" />
      <div v-for="ev in dayEvents" :key="`${ev.type}-${ev.id}`" class="day-item">
        <div class="day-item-header">
          <el-tag :type="ev.type === 'countdown' ? 'warning' : 'primary'" size="small">
            {{ ev.type === 'countdown' ? '倒计时' : '活动' }}
          </el-tag>
          <span class="day-item-title">{{ ev.title }}</span>
        </div>
        <div v-if="ev.desc" class="day-item-desc">{{ ev.desc }}</div>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Top } from '@element-plus/icons-vue'
import { countdownsApi } from '@/api/productivity.js'
import http from '@/api/index.js'

const countdowns = ref([])
const activities = ref([])
const loadingCd = ref(false)
const loadingAct = ref(false)

const currentDate = ref(new Date())
const selectedDay = ref('')
const dayDrawer = ref(false)

const cdDialog = ref(false)
const savingCd = ref(false)
const cdForm = ref({
  id: null, title: '', target_date: '', category: 'general',
  color: 'blue', description: '', pinned: false,
})

// 加载倒计时
async function loadCd() {
  loadingCd.value = true
  try {
    const { data } = await countdownsApi.list({ include_past: false })
    countdowns.value = data || []
  } finally { loadingCd.value = false }
}

// 加载活动（用于日历标点）
async function loadAct() {
  loadingAct.value = true
  try {
    const { data } = await http.get('/activities')
    activities.value = data || []
  } catch {} finally { loadingAct.value = false }
}

// 计算每天事件（活动 + 倒计时）
const eventsByDay = computed(() => {
  const map = {}
  for (const a of activities.value) {
    const d = a.activity_date || a.date || ''
    if (!d) continue
    if (!map[d]) map[d] = []
    map[d].push({
      id: a.id,
      type: 'activity',
      subtype: a.activity_type || 'general',
      title: a.title || '活动',
    })
  }
  for (const c of countdowns.value) {
    const d = c.target_date
    if (!d) continue
    if (!map[d]) map[d] = []
    map[d].push({ id: c.id, type: 'countdown', title: c.title || '倒计时' })
  }
  return map
})

const dayEvents = computed(() => {
  if (!selectedDay.value) return []
  const list = []
  for (const a of activities.value) {
    if ((a.activity_date || a.date) === selectedDay.value) {
      list.push({ id: a.id, type: 'activity', title: a.title, desc: a.location || a.activity_type || '' })
    }
  }
  for (const c of countdowns.value) {
    if (c.target_date === selectedDay.value) {
      list.push({ id: c.id, type: 'countdown', title: c.title, desc: c.description })
    }
  }
  return list
})

function onDayClick(day) {
  selectedDay.value = day
  dayDrawer.value = true
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

function activityIcon(sub) {
  const map = {
    party:  '🚩',
    class:  '📚',
    college:'🏫',
    school: '🎓',
    countdown: '⏳',
    activity:  '📌',
    general: '📌',
    exam: '📝',
    holiday: '🌸',
    event: '📌',
    deadline: '⚡',
  }
  return map[sub] || '·'
}

function onCreateCd() {
  cdForm.value = { id: null, title: '', target_date: '', category: 'general', color: 'blue', description: '', pinned: false }
  cdDialog.value = true
}

function onEditCd(c) {
  cdForm.value = { ...c }
  cdDialog.value = true
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
  } catch (e) {
    ElMessage.error('灌入失败：' + (e?.response?.data?.detail || e.message))
  }
}

function onSaveCd() {
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
    loadCd()
  } finally { savingCd.value = false }
}

async function onDeleteCd(c) {
  try {
    await ElMessageBox.confirm(`确认删除「${c.title}」？`, '提示', { type: 'warning' })
    await countdownsApi.remove(c.id)
    ElMessage.success('已删除')
    loadCd()
  } catch {}
}

onMounted(() => { loadCd(); loadAct() })
</script>

<style scoped>
.calendar-page { padding: 20px; }
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { margin: 0; }

.cd-section { margin-bottom: 20px; min-height: 100px; }
.cd-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}
.cd-card {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid transparent;
  box-shadow: 0 2px 8px rgba(74,122,140,.06);
  display: flex; flex-direction: column; gap: 6px;
  position: relative;
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
.cd-days { display: flex; align-items: baseline; gap: 4px; margin-top: 4px; }
.cd-days .num { font-size: 34px; font-weight: 700; color: #4A7A8C; line-height: 1; }
.cd-days .unit { font-size: 13px; color: #7B7B7B; }
.cd-meta { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #7B7B7B; }
.cd-actions { position: absolute; right: 8px; top: 8px; }
.cd-actions .el-button { padding: 3px; }

/* 日历 */
.calendar-wrap :deep(.el-calendar-day) { height: 90px !important; padding: 4px !important; }
.day-cell { height: 100%; display: flex; flex-direction: column; cursor: pointer; }
.day-num { font-size: 13px; font-weight: 600; color: #3A3A3A; }
.day-events { flex: 1; display: flex; flex-direction: column; gap: 2px; overflow: hidden; margin-top: 2px; }
.event-dot {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 4px;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.event-dot.type-activity  { background: #4A7A8C; }
.event-dot.type-countdown { background: #E58B3E; }
.event-dot.sub-party  { background: #C9635B; }
.event-dot.sub-class  { background: #4A7A8C; }
.event-dot.sub-college{ background: #7A6BAF; }
.event-dot.sub-school { background: #2E7D6B; }
.dot-icon { margin-right: 2px; font-size: 10px; }

.day-item { padding: 12px 0; border-bottom: 1px dashed #eee; }
.day-item-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.day-item-title { font-weight: 600; }
.day-item-desc { font-size: 12px; color: #7B7B7B; margin-left: 60px; }
</style>
