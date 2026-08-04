/**
 * V6.16 校历同步 API 封装
 * 从教务处官网同步校历事件
 */
import http from './index.js'

export const calendarApi = {
  /** 同步校历（从官网抓取） */
  sync: (semester = '') => http.get('/calendar/sync', { params: { semester } }),

  /** 获取校历事件列表 */
  events: (semester = '') => http.get('/calendar/events', { params: { semester } }),

  /** 获取可用学期列表 */
  semesters: () => http.get('/calendar/semesters'),
}
