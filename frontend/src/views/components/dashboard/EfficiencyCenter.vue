<template>
  <div>
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
                <span v-if="prodStats.todo_overdue > 0" class="prod-overdue">{{ prodStats.todo_overdue }}</span>
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

    <!-- 抽屉: 待办中 -->
    <el-drawer v-model="drawerTodoOpen" title="待办中" size="480px" :with-header="true">
      <div v-loading="drawerLoading" class="dash-drawer">
        <template v-if="drawerTodos.length === 0">
          <el-empty description="暂无待办" />
        </template>
        <template v-else>
          <div v-if="todoGroups.overdue.length" class="dg-block">
            <div class="dg-title overdue">已过期 · {{ todoGroups.overdue.length }}</div>
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

    <!-- 抽屉: 一周内到期 -->
    <el-drawer v-model="drawerUrgentOpen" title="一周内到期" size="480px" :with-header="true">
      <div v-loading="drawerLoading" class="dash-drawer">
        <template v-if="drawerUrgent.length === 0">
          <el-empty description="一周内无到期待办" />
        </template>
        <template v-else>
          <div v-if="urgentGroups.today.length" class="dg-block">
            <div class="dg-title today">今天 · {{ urgentGroups.today.length }}</div>
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

    <!-- 抽屉: 进行中项目 -->
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
import { ref, computed } from 'vue'
import { notesApi, projectsApi, productivityDashboard } from '@/api/productivity'

defineProps({
  prodStats: {
    type: Object,
    default: () => ({ todo_active: 0, todo_urgent_week: 0, todo_overdue: 0, projects_active: 0 })
  }
})

// ---- 抽屉状态 ----
const drawerTodoOpen = ref(false)
const drawerUrgentOpen = ref(false)
const drawerProjectsOpen = ref(false)
const drawerLoading = ref(false)
const drawerTodos = ref([])
const drawerUrgent = ref([])
const drawerProjects = ref([])

const _todayStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

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
  const byDate = (a, b) => (a.due_date || '9999').localeCompare(b.due_date || '9999')
  g.overdue.sort(byDate); g.week.sort(byDate); g.later.sort(byDate)
  return g
})

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
    drawerTodos.value = drawerTodos.value.filter(x => x.id !== t.id)
    drawerUrgent.value = drawerUrgent.value.filter(x => x.id !== t.id)
    await productivityDashboard()
  } catch(e) { ElMessage?.error?.('操作失败') }
}
</script>

<style scoped>
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
.prod-row { display: flex; gap: 12px; align-items: stretch; }
.prod-item {
  flex: 1;
  text-align: center;
  padding: 22px 8px;
  border-radius: var(--radius-lg);
  background: linear-gradient(180deg, #FFFFFF 0%, #F3F8FE 100%);
  border: 1px solid var(--shadow-sm);
  cursor: pointer;
  transition: transform .25s cubic-bezier(.4,0,.2,1), box-shadow .25s;
}
.prod-item:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}
.prod-num { position: relative; display: inline-flex; align-items: baseline; gap: 6px; font-size: 36px; font-weight: 800; color: #2E5A7F; letter-spacing: 0.5px; font-family: -apple-system, 'SF Pro Display', 'PingFang SC', sans-serif; }
.prod-num.warning { color: var(--color-primary); }
.prod-num.danger  { color: var(--color-secondary); }
.prod-num.success { color: var(--color-accent); }
.prod-label { color: rgba(91, 146, 229, 0.65); font-size: 12px; margin-top: 6px; letter-spacing: 0.3px; font-weight: 500; }
.prod-overdue {
  font-size: 12px; font-weight: 600; color: #E74C3C;
  background: rgba(231, 76, 60, 0.10); padding: 2px 6px; border-radius: 10px;
  line-height: 1.2; letter-spacing: 0.3px;
}
/* 抽屉样式 */
.dash-drawer { padding: 0 4px 60px; }
.dash-drawer .dg-block { margin-bottom: 20px; }
.dash-drawer .dg-title {
  font-size: 13px; font-weight: 600; color: var(--color-primary);
  padding: 4px 0 8px; border-bottom: 1px dashed rgba(91,146,229,0.20);
  margin-bottom: 8px; letter-spacing: 0.3px;
}
.dash-drawer .dg-title.overdue { color: #E74C3C; border-bottom-color: rgba(231,76,60,0.25); }
.dash-drawer .dg-title.today   { color: var(--color-secondary); }
.dash-drawer .dg-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 10px; border-radius: 6px; transition: background var(--transition-fast);
}
.dash-drawer .dg-item:hover { background: var(--color-primary-light); }
.dash-drawer .dg-body { flex: 1; min-width: 0; }
.dash-drawer .dg-content { font-size: 14px; color: #2E4257; line-height: 1.5; word-break: break-word; }
.dash-drawer .dg-meta { font-size: 12px; color: #8DA0B5; margin-top: 3px; }
.dash-drawer .dg-meta.overdue-txt { color: #E74C3C; font-weight: 500; }
.dash-drawer .dg-footer {
  position: sticky; bottom: 0; background: #fff;
  padding: 12px 0 8px; margin-top: 20px; text-align: center;
  border-top: 1px solid var(--shadow-md);
}
.dash-drawer .dp-card {
  padding: 12px 14px; border: 1px solid var(--color-primary-light);
  border-radius: var(--radius-sm); margin-bottom: 10px; cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.dash-drawer .dp-card:hover { border-color: var(--color-mint); box-shadow: 0 2px 8px var(--color-primary-light); }
.dash-drawer .dp-head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.dash-drawer .dp-name { font-size: 14px; font-weight: 600; color: #2E4257; }
.dash-drawer .dp-prog { font-size: 13px; color: var(--color-primary); font-weight: 600; }
.dash-drawer .dp-meta { font-size: 12px; color: #8DA0B5; margin-top: 6px; }
</style>
