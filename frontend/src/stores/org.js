/**
 * 组织树 store · 顶栏切换器共享 + 三级架构管理页
 * - orgTree: 完整的年级→专业→班级树
 * - 顶栏切换器过滤状态：filterGradeId / filterMajorId / filterClassId
 * - 状态存 localStorage，跨页面保持（V3-A 硬要求 § 6.1）
 */
import { defineStore } from 'pinia'
import * as orgApi from '@/api/org.js'

const LS_KEY = 'v3a.orgFilter'

function loadFilter() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export const useOrgStore = defineStore('org', {
  state: () => ({
    orgTree: [],                 // [{id, grade_name, majors:[{id, major_name, classes:[{id, class_name, student_count}]}]}]
    treeLoading: false,
    treeLoadedAt: 0,
    filterGradeId: loadFilter().gradeId || null,
    filterMajorId: loadFilter().majorId || null,
    filterClassId: loadFilter().classId || null
  }),
  getters: {
    /** 扁平年级列表 */
    grades: (state) => state.orgTree.map(g => ({ id: g.id, name: g.grade_name })),
    /** 当前 filterGradeId 下的专业列表 */
    majors: (state) => {
      const g = state.orgTree.find(x => x.id === state.filterGradeId)
      const src = g ? g.majors : state.orgTree.flatMap(x => x.majors || [])
      return (src || []).map(m => ({ id: m.id, name: m.major_name, grade_id: m.grade_id || g?.id }))
    },
    /** 当前筛选下的班级列表 */
    classes: (state) => {
      let src = []
      state.orgTree.forEach(g => {
        (g.majors || []).forEach(m => {
          (m.classes || []).forEach(c => {
            src.push({
              id: c.id,
              name: c.class_name,
              student_count: c.student_count,
              class_teacher: c.class_teacher,
              monitor: c.monitor,
              league_secretary: c.league_secretary,
              major_id: m.id,
              major_name: m.major_name,
              grade_id: g.id,
              grade_name: g.grade_name
            })
          })
        })
      })
      if (state.filterMajorId) src = src.filter(c => c.major_id === state.filterMajorId)
      else if (state.filterGradeId) src = src.filter(c => c.grade_id === state.filterGradeId)
      return src
    },
    /** 【新增】不受组织切换器影响的全量班级列表（供筛选下拉用） */
    allClasses: (state) => {
      const src = []
      state.orgTree.forEach(g => {
        (g.majors || []).forEach(m => {
          (m.classes || []).forEach(c => {
            src.push({
              id: c.id,
              name: c.class_name,
              student_count: c.student_count,
              class_teacher: c.class_teacher,
              monitor: c.monitor,
              league_secretary: c.league_secretary,
              major_id: m.id,
              major_name: m.major_name,
              grade_id: g.id,
              grade_name: g.grade_name
            })
          })
        })
      })
      return src
    },
    /** 【新增】不受组织切换器影响的全量专业列表 */
    allMajors: (state) => {
      const src = []
      state.orgTree.forEach(g => {
        (g.majors || []).forEach(m => {
          src.push({
            id: m.id,
            name: m.major_name,
            grade_id: g.id,
            grade_name: g.grade_name
          })
        })
      })
      return src
    },
    /** 找班级名 */
    getClassName: (state) => (cid) => {
      for (const g of state.orgTree) {
        for (const m of (g.majors || [])) {
          for (const c of (m.classes || [])) {
            if (c.id === cid) return c.class_name
          }
        }
      }
      return ''
    }
  },
  actions: {
    persist() {
      localStorage.setItem(LS_KEY, JSON.stringify({
        gradeId: this.filterGradeId,
        majorId: this.filterMajorId,
        classId: this.filterClassId
      }))
    },
    /** 加载组织树（force=true 时无视缓存） */
    async loadTree(force = false) {
      if (!force && this.orgTree.length && Date.now() - this.treeLoadedAt < 60_000) {
        return this.orgTree
      }
      this.treeLoading = true
      try {
        const data = await orgApi.getOrgTree()
        this.orgTree = Array.isArray(data) ? data : []
        this.treeLoadedAt = Date.now()
      } finally {
        this.treeLoading = false
      }
      return this.orgTree
    },
    /** 顶栏切换器改变 */
    setFilter({ gradeId = null, majorId = null, classId = null } = {}) {
      this.filterGradeId = gradeId
      this.filterMajorId = majorId
      this.filterClassId = classId
      this.persist()
    },
    resetFilter() {
      this.filterGradeId = null
      this.filterMajorId = null
      this.filterClassId = null
      this.persist()
    }
  }
})
