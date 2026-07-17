/**
 * V3-B 效率中心 API 封装
 * 涵盖 记事本 / 倒计时 / 项目追踪 / 周汇总
 */
import http from './index.js'

// ---------- 记事本 ----------
export const notesApi = {
  list:   (params = {}) => http.get('/notes', { params }),
  get:    (id)          => http.get(`/notes/${id}`),
  create: (data)        => http.post('/notes', data),
  update: (id, data)    => http.put(`/notes/${id}`, data),
  toggle: (id)          => http.post(`/notes/${id}/toggle`),
  remove: (id)          => http.delete(`/notes/${id}`),
}

// ---------- 倒计时 ----------
export const countdownsApi = {
  list:   (params = {}) => http.get('/countdowns', { params }),
  create: (data)        => http.post('/countdowns', data),
  update: (id, data)    => http.put(`/countdowns/${id}`, data),
  remove: (id)          => http.delete(`/countdowns/${id}`),
}

// ---------- 项目追踪 ----------
export const projectsApi = {
  list:   (params = {}) => http.get('/projects', { params }),
  get:    (id)          => http.get(`/projects/${id}`),
  create: (data)        => http.post('/projects', data),
  update: (id, data)    => http.put(`/projects/${id}`, data),
  remove: (id)          => http.delete(`/projects/${id}`),
  addMember:    (pid, data)      => http.post(`/projects/${pid}/members`, data),
  updateMember: (pid, mid, data) => http.put(`/projects/${pid}/members/${mid}`, data),
  removeMember: (pid, mid)       => http.delete(`/projects/${pid}/members/${mid}`),
}

// ---------- 周汇总（复用 knowledge_modules 已有接口） ----------
export const summariesApi = {
  list:     (params = {}) => http.get('/weekly-summaries', { params }),
  get:      (id)          => http.get(`/weekly-summaries/${id}`),
  generate: (data = {})   => http.post('/weekly-summaries/generate', data),
  update:   (id, data)    => http.put(`/weekly-summaries/${id}`, data),
  remove:   (id)          => http.delete(`/weekly-summaries/${id}`),
}

// ---------- 效率中心汇总 ----------
export const productivityDashboard = () => http.get('/productivity/dashboard')

// ---------- v3h · 统一事件聚合（日历/驾驶舱本周待办用） ----------
export const eventsApi = {
  list:  (start, end) => http.get('/events', { params: { start, end } }),
  week:  (offset = 0) => http.get('/events/week', { params: { offset } }),
}
