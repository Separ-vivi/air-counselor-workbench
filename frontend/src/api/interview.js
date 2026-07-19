import request from '@/api/index'

export default {
  list(params) {
    return request.get('/api/interview/', { params })
  },
  types() {
    return request.get('/api/interview/types')
  },
  statistics() {
    return request.get('/api/interview/statistics')
  },
  get(id) {
    return request.get(`/api/interview/${id}`)
  },
  create(data) {
    return request.post('/api/interview/', data)
  },
  update(id, data) {
    return request.put(`/api/interview/${id}`, data)
  },
  delete(id) {
    return request.delete(`/api/interview/${id}`)
  }
}
