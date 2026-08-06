/**
 * 学生 store · 学生列表 + 学生 360 缓存管理
 * - list: 学生列表分页缓存
 * - current: 当前打开的学生 360 数据
 * - refreshBumper: 数字累加器，用于强制响应式刷新（子组件 watch 这个值）
 *
 * ⚠️ V3-A 强验收 § 6.3.1：
 *   下拉搜索接口（searchStudents）**禁止缓存**，因此本 store 不缓存 search 结果
 *   本 store 只缓存列表分页数据 + 学生 360 详情
 *   凡是 CRUD 后必须调用 bumpRefresh() 触发所有 watcher 重新拉取
 */
import { defineStore } from 'pinia'
import * as studentApi from '@/api/students.js'
import * as s360Api from '@/api/student360.js'

export const useStudentStore = defineStore('student', {
  state: () => ({
    list: [],
    total: 0,
    page: 1,
    pageSize: 20,
    listLoading: false,

    /** 当前学生 360 主数据 */
    current: null,
    currentSummary: null,
    currentLoading: false,

    /** 响应式刷新计数器 · 任何 CRUD 后 +1，子组件 watch 触发重拉 */
    refreshBumper: 0
  }),
  actions: {
    async loadList(params = {}) {
      this.listLoading = true
      try {
        const q = { page: this.page, page_size: this.pageSize, ...params }
        const data = await studentApi.listStudents(q)
        this.list = data.items || []
        this.total = data.total || 0
      } finally {
        this.listLoading = false
      }
    },
    async loadStudent360(sid) {
      this.currentLoading = true
      try {
        const [basic, summary] = await Promise.all([
          s360Api.getBasic(sid),
          s360Api.getSummary(sid).catch(() => null)
        ])
        this.current = basic
        this.currentSummary = summary
      } finally {
        this.currentLoading = false
      }
    },
    async reloadCurrent() {
      if (this.current?.id) {
        await this.loadStudent360(this.current.id)
      }
    },
    bumpRefresh() {
      this.refreshBumper += 1
    },
    clear() {
      this.list = []
      this.current = null
      this.currentSummary = null
      this.total = 0
    }
  }
})
