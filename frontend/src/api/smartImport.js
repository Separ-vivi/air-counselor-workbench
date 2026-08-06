/**
 * 智能导入 API
 * openapi.json 有两组接口，均支持：
 *   POST /api/smart-import/preview   （JSON 请求）
 *   POST /api/smart-import/execute   （JSON 请求）
 *   POST /api/import/detect          （multipart/form-data, file 字段）
 *   POST /api/import/confirm         （JSON: {data_type, mapping[], conflict_strategy, import_id?}）
 *
 * 前端采用组合：
 *   1. detect（上传文件 → 拿 mapping 建议 + import_id）
 *   2. confirm（用户确认后带 mapping 提交 → 后端执行入库）
 */
import http from './index.js'

/** 上传文件、AI 自动识别列 → 返回 mapping 建议 */
export const detectFile = (formData) =>
  http.post('/import/detect', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

/** 确认导入 */
export const confirmImport = (payload) => http.post('/import/confirm', payload)

/** 备用：老接口 smart-import */
export const smartImportPreview = (payload) => http.post('/smart-import/preview', payload)
export const smartImportExecute = (payload) => http.post('/smart-import/execute', payload)

/** 花名册直接导入（旧路径，仍保留） */
export const importStudents = (formData) =>
  http.post('/students/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

/** 成绩单直接导入（旧路径，仍保留） */
export const importGrades = (formData) =>
  http.post('/grades/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
