/**
 * 班级 store · 缓存班级 360 数据
 */
import { defineStore } from 'pinia'
import * as class360Api from '@/api/class360.js'

export const useClassStore = defineStore('class', {
  state: () => ({
    current: null,             // {cid, class_name, ...} 简单存 summary
    currentCid: null,
    summary: null,
    students: [],
    grades: [],
    party: [],
    psychology: [],
    funding: null,
    activities: [],
    daily: null,
    loading: false,
    error: null
  }),
  actions: {
    async loadSummary(cid) {
      this.currentCid = cid
      this.loading = true
      this.error = null
      try {
        this.summary = await class360Api.getClassSummary(cid)
      } catch (e) {
        // class360/summary 已知会 500，做兜底：从 org 树拿基本信息 + students 数拼装
        this.error = e
        this.summary = null
      } finally {
        this.loading = false
      }
    },
    async loadTab(tab, cid) {
      switch (tab) {
        case 'students':   this.students   = await class360Api.getClassStudents(cid);   break
        case 'grades':     this.grades     = await class360Api.getClassGrades(cid);     break
        case 'party':      this.party      = await class360Api.getClassParty(cid);      break
        case 'psychology': this.psychology = await class360Api.getClassPsychology(cid); break
        case 'funding':    this.funding    = await class360Api.getClassFunding(cid);    break
        case 'activities': this.activities = await class360Api.getClassActivities(cid); break
        case 'daily':      this.daily      = await class360Api.getClassDaily(cid);      break
      }
    },
    clear() {
      this.currentCid = null
      this.summary = null
      this.students = []
      this.grades = []
      this.party = []
      this.psychology = []
      this.funding = null
      this.activities = []
      this.daily = null
    }
  }
})
