import request from '@/api/index'

export default {
  semesters() {
    return request.get('/semester-report/semesters')
  },
  summary() {
    return request.get('/semester-report/summary')
  },
  academics(semester) {
    return semester ? request.get('/semester-report/academics', { params: { semester } }) : request.get('/semester-report/academics')
  },
  partyDevelopment() {
    return request.get('/semester-report/party-development')
  },
  employment() {
    return request.get('/semester-report/employment')
  },
  activities() {
    return request.get('/semester-report/activities')
  },
  export(semester) {
    return semester ? request.get('/semester-report/export', { params: { semester }, responseType: 'blob' }) : request.get('/semester-report/export', { responseType: 'blob' })
  },
  compare(semester) {
    return semester ? request.get('/semester-report/compare', { params: { semester } }) : request.get('/semester-report/compare')
  }
}
