/**
 * 学生 360 · 主档案页所有子资源 API
 * 严格对齐后端 openapi.json：
 *   /api/student360/{sid}/basic         GET / PUT
 *   /api/student360/{sid}/summary       GET
 *   /api/student360/{sid}/timeline      GET
 *   /api/student360/{sid}/{resource}    GET / POST / PUT / DELETE
 *
 * 20 个子资源：
 *   grades, party, psychology, family, cadres, activities, employment,
 *   hardship, grants, scholarships, loans, work-study, honors,
 *   dorm-visits, leaves, disciplines, dorm-chats, attendance,
 *   status-changes, projects
 */
import http from './index.js'

/** 顶部信息卡 */
export const getBasic  = (sid) => http.get(`/student360/${sid}/basic`)
export const updateBasic = (sid, data) => http.put(`/student360/${sid}/basic`, data)

/** 概览（含状态灯统计） */
export const getSummary  = (sid) => http.get(`/student360/${sid}/summary`)

/** 跨维度时间线 */
export const getTimeline = (sid, limit = 50) =>
  http.get(`/student360/${sid}/timeline`, { params: { limit } })

/** 成长轨迹雷达图 */
export const getRadar = (sid) =>
  http.get(`/student360/${sid}/radar`)

/**
 * 通用子资源工厂：对每个子资源生成 4 个 CRUD 方法
 * 用法：const api = resource('party'); api.list(sid); api.create(sid, data); …
 */
export function resource(name) {
  const base = (sid) => `/student360/${sid}/${name}`
  return {
    list: (sid) => http.get(base(sid)),
    create: (sid, data) => http.post(base(sid), data),
    update: (sid, rid, data) => http.put(`${base(sid)}/${rid}`, data),
    remove: (sid, rid) => http.delete(`${base(sid)}/${rid}`)
  }
}

/** 20 个子资源实例 */
export const s360 = {
  grades:        resource('grades'),
  party:         resource('party'),
  psychology:    resource('psychology'),
  family:        resource('family'),
  cadres:        resource('cadres'),
  activities:    resource('activities'),   // 只有 GET/POST/DELETE，无 PUT
  employment:    resource('employment'),
  hardship:      resource('hardship'),
  grants:        resource('grants'),
  scholarships:  resource('scholarships'),
  loans:         resource('loans'),
  workStudy:     resource('work-study'),
  honors:        resource('honors'),
  dormVisits:    resource('dorm-visits'),
  leaves:        resource('leaves'),
  disciplines:   resource('disciplines'),
  dormChats:     resource('dorm-chats'),
  attendance:    resource('attendance'),
  statusChanges: resource('status-changes'),
  projects:      resource('projects')
}
