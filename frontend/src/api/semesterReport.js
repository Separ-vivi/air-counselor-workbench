import http from './index.js'

export const semesterReportApi = {
  summary: () => http.get('/semester-report/summary'),
  academics: () => http.get('/semester-report/academics'),
  partyDevelopment: () => http.get('/semester-report/party-development'),
  employment: () => http.get('/semester-report/employment'),
  activities: () => http.get('/semester-report/activities'),
  export: () => http.get('/semester-report/export', { responseType: 'blob' }),
}
