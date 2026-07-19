/**
 * Vue Router 4 · V3-A 路由表
 * 保留 V2 已有路由 + 新增 V3-A 学生 360/班级 360/三级架构/智能导入
 */
import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },

  { path: '/dashboard',        name: 'dashboard',        component: () => import('@/views/Dashboard.vue'),         meta: { title: '驾驶舱' } },
  { path: '/students',         name: 'students',         component: () => import('@/views/StudentList.vue'),       meta: { title: '学生管理' } },
  { path: '/students/:id',     name: 'student360',       component: () => import('@/views/Student360.vue'),        meta: { title: '学生 360' }, props: true },
  { path: '/classes',          name: 'classes',          component: () => import('@/views/ClassList.vue'),         meta: { title: '班级管理' } },
  { path: '/classes/:id',      name: 'class360',         component: () => import('@/views/Class360.vue'),          meta: { title: '班级 360' }, props: true },
  { path: '/org',              name: 'org',              component: () => import('@/views/OrgManagement.vue'),     meta: { title: '三级架构' } },
  { path: '/smart-import',     name: 'smartImport',      component: () => import('@/views/SmartImport.vue'),       meta: { title: '智能导入' } },

  // 10 个模块列表页
  { path: '/module/grades',     name: 'mGrades',     component: () => import('@/views/modules/GradesModule.vue'),     meta: { title: '成绩管理' } },
  { path: '/module/warnings',   name: 'mWarnings',   component: () => import('@/views/modules/WarningsModule.vue'),   meta: { title: '学业预警' } },
  { path: '/module/party',      name: 'mParty',      component: () => import('@/views/modules/PartyModule.vue'),      meta: { title: '党团进程' } },
  { path: '/module/psychology', name: 'mPsy',        component: () => import('@/views/modules/PsychologyModule.vue'), meta: { title: '心理关怀' } },
  { path: '/module/family',     name: 'mFamily',     component: () => import('@/views/modules/FamilyModule.vue'),     meta: { title: '家庭联络' } },
  { path: '/module/cadres',     name: 'mCadres',     component: () => import('@/views/modules/CadresModule.vue'),     meta: { title: '干部管理' } },
  { path: '/module/activities', name: 'mActivities', component: () => import('@/views/modules/ActivitiesModule.vue'), meta: { title: '活动管理' } },
  { path: '/module/employment', name: 'mEmployment', component: () => import('@/views/modules/EmploymentModule.vue'), meta: { title: '就业管理' } },
  { path: '/module/meetings',   name: 'mMeetings',   component: () => import('@/views/modules/MeetingsModule.vue'),   meta: { title: '班会管理' } },
  { path: '/module/teachers',   name: 'mTeachers',   component: () => import('@/views/modules/TeachersModule.vue'),   meta: { title: '班主任' } },

  // V3-B 效率中心
  { path: '/notes',            name: 'notes',            component: () => import('@/views/Notes.vue'),             meta: { title: '记事本' } },
  { path: '/calendar',         name: 'calendar',         component: () => import('@/views/Calendar.vue'),          meta: { title: '校历 · 倒计时' } },
  { path: '/projects',         name: 'projects',         component: () => import('@/views/Projects.vue'),          meta: { title: '项目追踪' } },
  { path: '/summary',          name: 'summary',          component: () => import('@/views/WeeklySummary.vue'),     meta: { title: '周汇总' } },
  // 系统设置
  { path: '/knowledge',        name: 'knowledge',        component: () => import('@/views/KnowledgeBase.vue'),      meta: { title: '知识库 · AI 助手' } },
  { path: '/faqs',             name: 'faqs',             component: () => import('@/views/Faqs.vue'),               meta: { title: 'FAQ' } },
  { path: '/templates',        name: 'templates',        component: () => import('@/views/DocumentTemplates.vue'),  meta: { title: '文档模板' } },

  { path: '/system',           name: 'system',           component: () => import('@/views/SystemSettings.vue'),     meta: { title: '系统设置' } },

  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.afterEach((to) => {
  document.title = `${to.meta?.title || '辅导员工作平台'} · V5-b`
})

export default router
