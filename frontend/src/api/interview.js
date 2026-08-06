import request from '@/api/index'

export default {
  list(params) {
    return request.get('/interview/', { params })
  },
  types() {
    return request.get('/interview/types')
  },
  statistics() {
    return request.get('/interview/statistics')
  },
  get(id) {
    return request.get(`/interview/${id}`)
  },
  create(data) {
    return request.post('/interview/', data)
  },
  update(id, data) {
    return request.put(`/interview/${id}`, data)
  },
  delete(id) {
    return request.delete(`/interview/${id}`)
  }
}
