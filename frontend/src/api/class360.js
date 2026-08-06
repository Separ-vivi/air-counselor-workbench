/**
 * 班级 360 · 8 条只读路由 API
 * /api/class360/{cid}/{summary|students|activities|daily|funding|grades|party|psychology}
 */
import http from './index.js'

export const getClassSummary    = (cid) => http.get(`/class360/${cid}/summary`)
export const getClassStudents   = (cid) => http.get(`/class360/${cid}/students`)
export const getClassGrades     = (cid) => http.get(`/class360/${cid}/grades`)
export const getClassParty      = (cid) => http.get(`/class360/${cid}/party`)
export const getClassPsychology = (cid) => http.get(`/class360/${cid}/psychology`)
export const getClassFunding    = (cid) => http.get(`/class360/${cid}/funding`)
export const getClassActivities = (cid) => http.get(`/class360/${cid}/activities`)
export const getClassDaily      = (cid) => http.get(`/class360/${cid}/daily`)
// V3-A 追加 - 联系方式 + 党团支部 + 特色活动
export const getClassContacts           = (cid) => http.get(`/class360/${cid}/contacts`)
export const getClassPartyBranch        = (cid) => http.get(`/class360/${cid}/party-branch`)
export const getClassFeaturedActivities = (cid) => http.get(`/class360/${cid}/featured-activities`)
// v3j-D · D3: 班级档案编辑 + 班级360 导出
export const updateClassInfo = (cid, data) => http.patch(`/class360/${cid}/info`, data)
export const exportClass360  = (cid) => http.get(`/class360/${cid}/export`, { responseType: 'blob' })
