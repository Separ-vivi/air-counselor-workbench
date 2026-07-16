<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>🏠 工作台总览</h2>
      <p class="sub">高校辅导员工作平台 · V3-A</p>
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
              :timestamp="item.time || item.date"
              placement="top"
            >
              <div>{{ item.title || item.desc || item.content }}</div>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dashboard as getDashboard } from '@/api/modules'
import { productivityDashboard } from '@/api/productivity'

const router = useRouter()
const warnings = ref([])
const recentActivities = ref([])
const prodStats = ref({ todo_active: 0, todo_urgent_week: 0, projects_active: 0, countdowns_top: [] })

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
    statCards.value[0].value = d.total_students ?? d.student_count ?? 0
    statCards.value[1].value = d.total_classes ?? d.class_count ?? 0
    statCards.value[2].value = d.party_count ?? d.total_party ?? 0
    statCards.value[3].value = d.month_activities ?? d.activity_count ?? 0
    warnings.value = d.warnings || d.warning_students || []
    recentActivities.value = d.recent || d.recent_activities || d.timeline || []
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
.dashboard { padding: 4px; }
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0; color: #303133; font-size: 22px; }
.page-header .sub { color: #909399; margin: 4px 0 0; font-size: 13px; }

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
</style>
