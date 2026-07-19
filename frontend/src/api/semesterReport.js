import request from '@/api/index'

export default {
  // 获取学期列表
  semesters() {
    return request.get('/api/semester-report/semesters')
  },
  // 学期总览
  summary() {
    return request.get('/api/semester-report/summary')
  },
  // 学业数据
  academics(semester) {
    return semester ? request.get('/api/semester-report/academics', { params: { semester } }) : request.get('/api/semester-report/academics')
  },
  // 党团发展
  partyDevelopment() {
    return request.get('/api/semester-report/party-development')
  },
  // 就业跟踪
  employment() {
    return request.get('/api/semester-report/employment')
  },
  // 学生活动
  activities() {
    return request.get('/api/semester-report/activities')
  },
  // 导出报表
  export(semester) {
    return semester ? request.get('/api/semester-report/export', { params: { semester }, responseType: 'blob' }) : request.get('/api/semester-report/export', { responseType: 'blob' })
  },
  // 学期对比
  compare(semester) {
    return semester ? request.get('/api/semester-report/compare', { params: { semester } }) : request.get('/api/semester-report/compare')
  }
}
