import request from '@/api/index'

export default {
  semesters() {
    return request.get('/semester-report/semesters')
  },
  summary(semester) {
    return semester ? request.get('/semester-report/summary', { params: { semester } }) : request.get('/semester-report/summary')
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
  },
  // 新增 API
  attendance(semester) {
    return semester ? request.get('/semester-report/attendance', { params: { semester } }) : request.get('/semester-report/attendance')
  },
  psychology() {
    return request.get('/semester-report/psychology')
  },
  discipline() {
    return request.get('/semester-report/discipline')
  },
  financialAid(semester) {
    return semester ? request.get('/semester-report/financial-aid', { params: { semester } }) : request.get('/semester-report/financial-aid')
  },
  honors() {
    return request.get('/semester-report/honors')
  },
  interviews() {
    return request.get('/semester-report/interviews')
  },
  dormitory(semester) {
    return semester ? request.get('/semester-report/dormitory', { params: { semester } }) : request.get('/semester-report/dormitory')
  }
}
