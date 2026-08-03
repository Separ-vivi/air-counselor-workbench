<template>
  <el-card shadow="never">
    <template #header>
      <span class="ch-title">快捷入口</span>
    </template>
    <div class="shortcuts">
      <div class="sc-item" v-for="s in shortcuts" :key="s.to" @click="$router.push(s.to)">
        <div class="sc-icon" :style="{ background: s.bg, color: s.color }"><el-icon :size="20"><component :is="s.icon" /></el-icon></div>
        <div class="sc-label">{{ s.label }}</div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { markRaw } from 'vue'
import {
  UserFilled, School, UploadFilled,
  DataAnalysis, Warning, Flag, Sunny,
  ChatDotRound, Calendar, Money, Promotion
} from '@element-plus/icons-vue'

const shortcuts = [
  { icon: markRaw(UserFilled),      label: '学生管理', to: '/students',            bg: 'rgba(91, 146, 229, 0.10)',  color: '#5B92E5' },
  { icon: markRaw(School),          label: '班级管理', to: '/classes',             bg: 'rgba(79, 195, 184, 0.12)',  color: '#4FC3B8' },
  { icon: markRaw(UploadFilled),    label: '智能导入', to: '/smart-import',        bg: 'rgba(123, 207, 203, 0.14)', color: '#5FB8AC' },
  { icon: markRaw(DataAnalysis),    label: '成绩管理', to: '/module/grades',       bg: 'rgba(91, 146, 229, 0.10)',  color: '#5B92E5' },
  { icon: markRaw(Warning),         label: '学业预警', to: '/module/warnings',     bg: 'rgba(245, 108, 108, 0.10)', color: '#E74C3C' },
  { icon: markRaw(Flag),            label: '党团进程', to: '/module/party',        bg: 'rgba(143, 169, 229, 0.12)', color: '#7B92D6' },
  { icon: markRaw(Sunny),           label: '心理关怀', to: '/module/psychology',   bg: 'rgba(123, 207, 203, 0.14)', color: '#5FB8AC' },
  { icon: markRaw(ChatDotRound),    label: '学生访谈', to: '/module/interview',    bg: 'rgba(91, 146, 229, 0.10)',  color: '#5B92E5' },
  { icon: markRaw(Calendar),        label: '查课考勤', to: '/module/attendance',   bg: 'rgba(79, 195, 184, 0.12)',  color: '#4FC3B8' },
  { icon: markRaw(Money),           label: '奖助贷',   to: '/module/financial-aid', bg: 'rgba(230, 162, 60, 0.10)', color: '#E6A23C' },
  { icon: markRaw(Promotion),       label: '综测成绩', to: '/module/comprehensive', bg: 'rgba(143, 169, 229, 0.12)', color: '#7B92D6' },
  { icon: markRaw(DataAnalysis),    label: '学期报表', to: '/semester-report',     bg: 'rgba(123, 207, 203, 0.14)', color: '#5FB8AC' }
]
</script>

<style scoped>
.ch-title {
  font-weight: 600;
  font-size: 14px;
  color: #2E5A7F;
  letter-spacing: 0.4px;
}
/* V6.14: 一行显示12个，紧凑排列 */
.shortcuts {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 6px;
}
.sc-item {
  padding: 10px 4px;
  text-align: center;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
}
.sc-item:hover { background: var(--color-primary-light); }
.sc-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
  transition: transform .25s cubic-bezier(.4,0,.2,1), box-shadow .25s;
  box-shadow: 0 2px 6px var(--shadow-md);
}
.sc-item:hover .sc-icon {
  transform: scale(1.1);
  box-shadow: var(--shadow-hover);
}
.sc-label {
  font-size: 11px;
  color: #303133;
  font-weight: 500;
  white-space: nowrap;
}

/* 响应式：中屏6列，小屏4列 */
@media (max-width: 1200px) {
  .shortcuts { grid-template-columns: repeat(6, 1fr); }
}
@media (max-width: 768px) {
  .shortcuts { grid-template-columns: repeat(4, 1fr); }
}
</style>
