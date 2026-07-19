import http from './index.js'

export const tagsApi = {
  list: () => http.get('/tags'),
  create: (data) => http.post('/tags', data),
  remove: (id) => http.delete(`/tags/${id}`),
  getStudentTags: (sid) => http.get(`/students/${sid}/tags`),
  addStudentTag: (sid, tagId) => http.post(`/students/${sid}/tags`, { tag_id: tagId }),
  removeStudentTag: (sid, tagId) => http.delete(`/students/${sid}/tags/${tagId}`),
}
