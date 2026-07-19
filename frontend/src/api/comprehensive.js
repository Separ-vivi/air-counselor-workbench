import request from '@/api/index'

export default {
  list(params) {
    return request.get('/api/comprehensive/', { params })
  },
  semesters() {
    return request.get('/api/comprehensive/semesters')
  },
  statistics(params) {
    return request.get('/api/comprehensive/statistics', { params })
  },
  get(id) {
    return request.get(`/api/comprehensive/${id}`)
  },
  create(data) {
    return request.post('/api/comprehensive/', data)
  },
  update(id, data) {
    return request.put(`/api/comprehensive/${id}`, data)
  },
  delete(id) {
    return request.delete(`/api/comprehensive/${id}`)
  }
}
