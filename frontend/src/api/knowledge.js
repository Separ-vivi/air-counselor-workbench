/**
 * V3-C 辅助工具 API 封装：知识库 / FAQ / 文档模板 / 生成文书
 * 后端路由：backend/routers/knowledge_modules.py
 */
import http from './index.js'

// ---------- 知识库 ----------
export const knowledgeApi = {
  list:   ()          => http.get('/knowledge'),
  get:    (id)        => http.get(`/knowledge/${id}`),
  create: (data)      => http.post('/knowledge', data),
  remove: (id)        => http.delete(`/knowledge/${id}`),
}

// ---------- FAQ ----------
export const faqsApi = {
  list:   (params = {}) => http.get('/faqs', { params }),
  get:    (id)          => http.get(`/faqs/${id}`),
  create: (data)        => http.post('/faqs', data),
  update: (id, data)    => http.put(`/faqs/${id}`, data),
  remove: (id)          => http.delete(`/faqs/${id}`),
}

// ---------- 文档模板 ----------
export const templatesApi = {
  list:   ()     => http.get('/document-templates'),
  create: (data) => http.post('/document-templates', data),
}

// ---------- 生成文书 ----------
export const documentsApi = {
  list:     (params = {}) => http.get('/documents', { params }),
  get:      (id)          => http.get(`/documents/${id}`),
  generate: (data)        => http.post('/documents/generate', data),
  update:   (id, data)    => http.put(`/documents/${id}`, data),
  remove:   (id)          => http.delete(`/documents/${id}`),
}
