/**
 * V5-B 知识库 API：文档库 + AI 问答 + LLM 配置
 */
import http from './index.js'

// ---------- 文档库（旧 CRUD 兼容 + 新增） ----------
export const knowledgeApi = {
  list:   ()          => http.get('/knowledge/enhanced'),
  get:    (id)        => http.get(`/knowledge/${id}`),
  chunks: (id)        => http.get(`/knowledge/${id}/chunks`),
  remove: (id)        => http.delete(`/knowledge/${id}/full`),
  upload: (form, onProgress) => http.post('/knowledge/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
    timeout: 120000,
  }),
}

// ---------- AI 问答 ----------
export const chatApi = {
  ask:     (question)  => http.post('/knowledge/chat', { question }, { timeout: 60000 }),
  history: (limit = 20) => http.get('/knowledge/chat/history', { params: { limit } }),
}

// ---------- LLM 配置 ----------
export const llmApi = {
  get:    ()        => http.get('/system/llm-settings'),
  update: (payload) => http.post('/system/llm-settings', payload),
}

// ---------- FAQ / 模板 / 文书（保留） ----------
export const faqsApi = {
  list:   (params = {}) => http.get('/faqs', { params }),
  get:    (id)        => http.get(`/faqs/${id}`),
  create: (data)      => http.post('/faqs', data),
  update: (id, data)  => http.put(`/faqs/${id}`, data),
  remove: (id)        => http.delete(`/faqs/${id}`),
}

export const templatesApi = {
  list:   ()     => http.get('/document-templates'),
  create: (data) => http.post('/document-templates', data),
}

export const documentsApi = {
  list:     (params = {}) => http.get('/documents', { params }),
  get:      (id)          => http.get(`/documents/${id}`),
  generate: (data)        => http.post('/documents/generate', data),
  update:   (id, data)    => http.put(`/documents/${id}`, data),
  remove:   (id)          => http.delete(`/documents/${id}`),
}
