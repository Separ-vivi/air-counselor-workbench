import request from '@/api/index'

export default {
  list(params) {
    return request.get('/comprehensive/', { params })
  },
  semesters() {
    return request.get('/comprehensive/semesters')
  },
  statistics(params) {
    return request.get('/comprehensive/statistics', { params })
  },
  get(id) {
    return request.get(`/comprehensive/${id}`)
  },
  create(data) {
    return request.post('/comprehensive/', data)
  },
  update(id, data) {
    return request.put(`/comprehensive/${id}`, data)
  },
  delete(id) {
    return request.delete(`/comprehensive/${id}`)
  }
}
