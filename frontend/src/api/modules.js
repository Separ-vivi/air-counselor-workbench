/**
 * 10 个业务模块列表页 API 封装
 * - 每个模块都提供 list / create / update / remove 四个方法
 * - 严格对齐 openapi.json 中的路径与参数
 */
import http from './index.js'

/** 成绩 & 预警 */
export const grades = {
  studentGrades: (sid) => http.get(`/grades/student/${sid}`),
  warnings: (params = {}) => http.get('/grades/warnings', { params }),
  exportWarnings: () => http.get('/grades/warnings/export', { responseType: 'blob' }),
  /** v3j-B-b03 · 按 ID 列表批量导出预警 */
  exportWarningsByIds: (ids) => http.post('/grades/warnings/export/by-ids', { ids }, { responseType: 'blob' }),
  semesters: () => http.get('/grades/semesters'),
  recalculateWarnings: () => http.post('/grades/recalculate'),
  /** v3j-D · D1: 切换预警已提醒状态 */
  toggleWarningReminded: (id) => http.patch(`/grades/warnings/${id}/toggle-reminded`),
  batchMarkWarningReminded: (ids, reminded = true) => http.post('/grades/warnings/batch-mark-reminded', { ids, reminded }),
  exportAll: () => http.get('/grades/export', { responseType: 'blob' }),
  /** v3j-B-b02 · 按 ID 列表批量导出成绩记录 */
  exportByIds: (ids) => http.post('/grades/export', { ids }, { responseType: 'blob' }),
  byClass: (cid, params = {}) => http.get(`/grades/by-class/${cid}`, { params })
}

/** 党团发展进程 */
export const party = {
  list: (params = {}) => http.get('/party-progress', { params }),
  create: (data) => http.post('/party-progress', data),
  update: (pid, data) => http.put(`/party-progress/${pid}`, data),
  remove: (pid) => http.delete(`/party-progress/${pid}`),
  overview: () => http.get('/party-progress/overview'),
  detail: (sid) => http.get(`/party-progress/detail/${sid}`),
  exportExcel: () => http.get('/party-progress/export', { responseType: 'blob' }),
  /** v3j-B-b03 · 按当前搜索导出全部 */
  exportAll: (params = {}) => http.get('/party-progress/export', { params, responseType: 'blob' }),
  /** v3j-B-b03 · 按 ID 列表批量导出 */
  exportByIds: (ids) => http.post('/party-progress/export-by-ids', { ids }, { responseType: 'blob' })
}

/** 党团学习记录 */
export const partyStudy = {
  list: () => http.get('/party-study'),
  create: (data) => http.post('/party-study', data),
  update: (pid, data) => http.put(`/party-study/${pid}`, data),
  remove: (pid) => http.delete(`/party-study/${pid}`)
}

/** 心理关怀 */
export const psychology = {
  /** v3j-B-b03 · 支持 search / sort_by / order 参数 */
  list: (params = {}) => http.get('/psychology', { params }),
  create: (data) => http.post('/psychology', data),
  update: (rid, data) => http.put(`/psychology/${rid}`, data),
  remove: (rid) => http.delete(`/psychology/${rid}`),
  reminders: () => http.get('/psychology/reminders'),
  /** v3j-B-b03 · 按 ID 列表批量导出 */
  exportByIds: (ids) => http.post('/psychology/export', { ids }, { responseType: 'blob' }),
  /** v3j-B-b03 · 按当前搜索导出全部 */
  exportAll: (params = {}) => http.get('/psychology/export/all', { params, responseType: 'blob' }),
  toggleReminded: (id) => http.patch(`/psychology/${id}/toggle-reminded`),
  batchMarkReminded: (ids, reminded = true) => http.post('/psychology/batch-mark-reminded', { ids, reminded })
}

/** 家庭联络 */
export const family = {
  list: (params = {}) => http.get('/family-contacts', { params }),
  create: (data) => http.post('/family-contacts', data),
  update: (cid, data) => http.put(`/family-contacts/${cid}`, data),
  remove: (cid) => http.delete(`/family-contacts/${cid}`)
}

/** 学生干部 */
export const cadres = {
  /** v3j-B-b03 · 支持 search / sort_by / order 参数 */
  list: (params = {}) => http.get('/cadres', { params }),
  directory: () => http.get('/cadres/directory'),
  create: (data) => http.post('/cadres', data),
  update: (cid, data) => http.put(`/cadres/${cid}`, data),
  remove: (cid) => http.delete(`/cadres/${cid}`),
  /** v3j-B-b03 · 按 ID 列表批量导出 */
  exportByIds: (ids) => http.post('/cadres/export', { ids }, { responseType: 'blob' }),
  /** v3j-B-b03 · 按当前搜索导出全部 */
  exportAll: (params = {}) => http.get('/cadres/export/all', { params, responseType: 'blob' })
}

/** 活动 */
export const activities = {
  /** v3j-B-b02 · 支持 search / sort_by / order 参数 */
  list: (params = {}) => http.get('/activities', { params }),
  create: (data) => http.post('/activities', data),
  update: (aid, data) => http.put(`/activities/${aid}`, data),
  remove: (aid) => http.delete(`/activities/${aid}`),
  /** v3j-B-b02 · 按 ID 列表批量导出 */
  exportByIds: (ids) => http.post('/activities/export', { ids }, { responseType: 'blob' }),
  /** v3j-B-b02 · 按当前搜索导出全部 */
  exportAll: (params = {}) => http.get('/activities/export', { params, responseType: 'blob' }),
  listSignups: (aid) => http.get(`/activities/${aid}/signups`),
  createSignup: (aid, data) => http.post(`/activities/${aid}/signups`, data),
  updateSignup: (aid, sid, data) => http.put(`/activities/${aid}/signups/${sid}`, data)
}

/** 就业信息 */
export const employment = {
  /** v3j-B-b03 · 支持 search / sort_by / order 参数 */
  list: (params = {}) => http.get('/employment', { params }),
  create: (data) => http.post('/employment', data),
  update: (eid, data) => http.put(`/employment/${eid}`, data),
  remove: (eid) => http.delete(`/employment/${eid}`),
  /** v3j-B-b03 · 按 ID 列表批量导出 */
  exportByIds: (ids) => http.post('/employment/export', { ids }, { responseType: 'blob' }),
  /** v3j-B-b03 · 按当前搜索导出全部 */
  exportAll: (params = {}) => http.get('/employment/export/all', { params, responseType: 'blob' })
}

/** 班会 */
export const classMeetings = {
  /** v3j-B-b03 · 支持 search / sort_by / order 参数 */
  list: (params = {}) => http.get('/class-meetings', { params }),
  create: (data) => http.post('/class-meetings', data),
  update: (mid, data) => http.put(`/class-meetings/${mid}`, data),
  remove: (mid) => http.delete(`/class-meetings/${mid}`),
  /** v3j-B-b03 · 按 ID 列表批量导出 */
  exportByIds: (ids) => http.post('/class-meetings/export', { ids }, { responseType: 'blob' }),
  /** v3j-B-b03 · 按当前搜索导出全部 */
  exportAll: (params = {}) => http.get('/class-meetings/export/all', { params, responseType: 'blob' })
}

/** 班主任 */
export const classTeachers = {
  /** v3j-B-b03 · 支持 search / sort_by / order 参数 */
  list: (params = {}) => http.get('/class-teachers', { params }),
  create: (data) => http.post('/class-teachers', data),
  update: (tid, data) => http.put(`/class-teachers/${tid}`, data),
  remove: (tid) => http.delete(`/class-teachers/${tid}`),
  /** v3j-B-b03 · 按 ID 列表批量导出 */
  exportByIds: (ids) => http.post('/class-teachers/export', { ids }, { responseType: 'blob' }),
  /** v3j-B-b03 · 按当前搜索导出全部 */
  exportAll: (params = {}) => http.get('/class-teachers/export/all', { params, responseType: 'blob' })
}

/** 驾驶舱 */
export const dashboard = () => http.get('/dashboard')

/** 全局设置 */
export const settings = {
  get: () => http.get('/settings'),
  update: (data) => http.put('/settings', data),
  reset: () => http.delete('/settings/reset')
}

/** 标签 */
export const tags = {
  list: () => http.get('/tags'),
  groups: () => http.get('/tags/groups'),
  create: (data) => http.post('/tags', data),
  update: (id, data) => http.put(`/tags/${id}`, data),
  remove: (id) => http.delete(`/tags/${id}`),
  addToStudent: (tagId, sid) => http.post(`/tags/${tagId}/students/${sid}`),
  removeFromStudent: (tagId, sid) => http.delete(`/tags/${tagId}/students/${sid}`)
}

/** 系统数据管理（V3-A 新增） */
export const system = {
  health: () => http.get('/system/health'),
  reinit: () => http.post('/system/reinit'),
  seedLarge: (force = false) => http.post('/system/seed-large', null, { params: { force } }),
  backupUrl: () => '/api/system/backup',
  restore: (formData) => http.post('/system/restore', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  clearBusiness: () => http.delete('/system/clear-business'),
  // V5-B: AI 配置
  llmGet:    ()        => http.get('/system/llm-settings'),
  llmUpdate: (payload) => http.post('/system/llm-settings', payload),
  llmTest:   ()        => http.post('/system/llm-test', null, { timeout: 30000 }),
}

/** 查课考勤 */
export const attendance = {
  list: (params = {}) => http.get('/attendance/', { params }),
  create: (data) => http.post('/attendance/', data),
  update: (id, data) => http.put(`/attendance/${id}`, data),
  remove: (id) => http.delete(`/attendance/${id}`),
  stats: () => http.get('/attendance/stats'),
  topStudents: (params = {}) => http.get('/attendance/top-students', { params }),
  topCourses: (params = {}) => http.get('/attendance/top-courses', { params }),
  monthlyTrend: () => http.get('/attendance/monthly-trend'),
  exportExcel: (params = {}) => http.get('/attendance/export', { params, responseType: 'blob' })
}