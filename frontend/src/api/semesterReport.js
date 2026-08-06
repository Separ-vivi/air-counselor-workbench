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
  partyDevelopment(semester) {
    return semester ? request.get('/semester-report/party-development', { params: { semester } }) : request.get('/semester-report/party-development')
  },
  employment(semester) {
    return semester ? request.get('/semester-report/employment', { params: { semester } }) : request.get('/semester-report/employment')
  },
  activities(semester) {
    return semester ? request.get('/semester-report/activities', { params: { semester } }) : request.get('/semester-report/activities')
  },
  export(semester) {
    return semester ? request.get('/semester-report/export', { params: { semester }, responseType: 'blob' }) : request.get('/semester-report/export', { responseType: 'blob' })
  },
  compare(semester) {
    return semester ? request.get('/semester-report/compare', { params: { semester } }) : request.get('/semester-report/compare')
  },
  attendance(semester) {
    return semester ? request.get('/semester-report/attendance', { params: { semester } }) : request.get('/semester-report/attendance')
  },
  psychology(semester) {
    return semester ? request.get('/semester-report/psychology', { params: { semester } }) : request.get('/semester-report/psychology')
  },
  discipline(semester) {
    return semester ? request.get('/semester-report/discipline', { params: { semester } }) : request.get('/semester-report/discipline')
  },
  financialAid(semester) {
    return semester ? request.get('/semester-report/financial-aid', { params: { semester } }) : request.get('/semester-report/financial-aid')
  },
  honors(semester) {
    return semester ? request.get('/semester-report/honors', { params: { semester } }) : request.get('/semester-report/honors')
  },
  interviews(semester) {
    return semester ? request.get('/semester-report/interviews', { params: { semester } }) : request.get('/semester-report/interviews')
  },
  dormitory(semester) {
    return semester ? request.get('/semester-report/dormitory', { params: { semester } }) : request.get('/semester-report/dormitory')
  }
}
