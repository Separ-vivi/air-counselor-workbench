/**
 * 学生管理 API
 * - 严格对齐后端 openapi.json
 */
import http from './index.js'

/** 列表（分页 + 搜索 + 筛选 + 排序） */
export const listStudents = (params = {}) => http.get('/students', { params })

/** 单个学生详情 */
export const getStudent = (id) => http.get(`/students/${id}`)

/** 新增学生 */
export const createStudent = (data) => http.post('/students', data)

/** 更新学生 */
export const updateStudent = (id, data) => http.put(`/students/${id}`, data)

/** 删除学生 */
export const deleteStudent = (id) => http.delete(`/students/${id}`)

/** 学生远程搜索（用于下拉选择器，禁止缓存） */
export const searchStudents = (q, limit = 50) =>
  http.get('/students/search', { params: { q, limit } })

/** 学生筛选选项 */
export const getStudentFilters = () => http.get('/students/filters')

/** 班级列表（旧接口） */
export const listStudentClasses = () => http.get('/students/classes')

/** 导出学生 Excel */
export const exportStudents = (params = {}) =>
  http.get('/students/export', { params, responseType: 'blob' })

/** 学生信息完整度检查 */
export const getStudentCompleteness = (id) => http.get(`/students/${id}/completeness`)
