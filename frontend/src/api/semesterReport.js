import http from './index.js'

export const semesterReportApi = {
  semesters: () => http.get('/semester-report/semesters'),
  summary: (semester) => http.get('/semester-report/summary', { params: semester && semester !== 'all' ? { semester } : {} }),
  academics: (semester) => http.get('/semester-report/academics', { params: semester && semester !== 'all' ? { semester } : {} }),
  partyDevelopment: (semester) => http.get('/semester-report/party-development', { params: semester && semester !== 'all' ? { semester } : {} }),
  employment: (semester) => http.get('/semester-report/employment', { params: semester && semester !== 'all' ? { semester } : {} }),
  activities: (semester) => http.get('/semester-report/activities', { params: semester && semester !== 'all' ? { semester } : {} }),
  export: (semester) => http.get('/semester-report/export', { params: semester && semester !== 'all' ? { semester } : {}, responseType: 'blob' }),
}
