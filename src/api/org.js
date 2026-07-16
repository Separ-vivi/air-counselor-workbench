/**
 * 三级组织架构 API · 年级 / 专业 / 班级
 * 严格对齐 openapi.json 的 /api/org/*
 */
import http from './index.js'

/** 组织树（顶栏切换器用） */
export const getOrgTree = () => http.get('/org/tree')

/** 年级 CRUD */
export const listGrades   = () => http.get('/org/grades')
export const createGrade  = (data) => http.post('/org/grades', data)
export const updateGrade  = (id, data) => http.put(`/org/grades/${id}`, data)
export const deleteGrade  = (id) => http.delete(`/org/grades/${id}`)

/** 专业 CRUD */
export const listMajors   = (grade_id) =>
  http.get('/org/majors', { params: grade_id ? { grade_id } : {} })
export const createMajor  = (data) => http.post('/org/majors', data)
export const updateMajor  = (id, data) => http.put(`/org/majors/${id}`, data)
export const deleteMajor  = (id) => http.delete(`/org/majors/${id}`)

/** 班级 CRUD */
export const listClasses  = (params = {}) => http.get('/org/classes', { params })
export const getClass     = (id) => http.get(`/org/classes/${id}`)
export const createClass  = (data) => http.post('/org/classes', data)
export const updateClass  = (id, data) => http.put(`/org/classes/${id}`, data)
export const deleteClass  = (id) => http.delete(`/org/classes/${id}`)
