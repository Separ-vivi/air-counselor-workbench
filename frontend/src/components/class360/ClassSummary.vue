<template>
  <div>
    <h3 style="margin-top:0">📊 班级概览</h3>
    <el-row :gutter="12">
      <el-col :span="6">
        <div class="stat-card" :style="cardStyle('blue')">
          <div class="stat-label">总人数</div>
          <div class="stat-value">{{ summary?.student_count ?? '—' }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" :style="cardStyle('green')">
          <div class="stat-label">党员数</div>
          <div class="stat-value">{{ summary?.party_member_count ?? 0 }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" :style="cardStyle('orange')">
          <div class="stat-label">困难生数</div>
          <div class="stat-value">{{ summary?.hardship_count ?? 0 }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" :style="cardStyle('red')">
          <div class="stat-label">预警人数</div>
          <div class="stat-value">{{ (summary?.warning_red_count || 0) + (summary?.warning_yellow_count || 0) }}</div>
        </div>
      </el-col>
    </el-row>

    <el-divider />

    <el-row :gutter="12">
      <el-col :span="12">
        <div class="macaron-card">
          <h3>班干部</h3>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="班主任">{{ classInfo?.class_teacher || '未指定' }}</el-descriptions-item>
            <el-descriptions-item label="班长">{{ classInfo?.monitor || '未指定' }}</el-descriptions-item>
            <el-descriptions-item label="团支书">{{ classInfo?.league_secretary || '未指定' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="macaron-card">
          <h3>关键指标</h3>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="挂科率">{{ fmtPct(summary?.fail_rate) }}</el-descriptions-item>
            <el-descriptions-item label="已就业签约数">{{ summary?.employed_count ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="心理关注人数">{{ summary?.psych_attention_count ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="奖学金累计金额">{{ fmtMoney(summary?.scholarship_total) }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
defineProps({
  cid: { type: Number, required: true },
  classInfo: { type: Object, default: null },
  summary: { type: Object, default: null }
})

function fmtPct(v) {
  if (v == null) return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return '—'
  return (n > 1 ? n : n * 100).toFixed(1) + '%'
}
function fmtMoney(v) {
  if (v == null) return '—'
  return '¥ ' + Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const colorMap = {
  blue:   '#B7D8E4',
  green:  '#B7E4C7',
  orange: '#F5C7A0',
  red:    '#F8B4B4'
}
function cardStyle(color) {
  const c = colorMap[color] || '#B7D8E4'
  return {
    background: c + '22',
    borderColor: c
  }
}
</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: 14px 12px;
  border-radius: 12px;
  border: 1px solid;
  margin-bottom: 12px;
}
.stat-label { color: #4A7A8C; font-size: 13px; }
.stat-value { font-size: 28px; font-weight: 700; color: #3B6A7C; margin-top: 4px; }
</style>
