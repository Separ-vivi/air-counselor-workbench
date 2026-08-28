<template>
  <div class="dimension-card" :style="cardStyle" @click="$emit('click')">
    <div class="card-icon-area">
      <div class="card-icon" :style="iconStyle">
        <el-icon v-if="iconComp" :size="22" class="card-ep-icon"><component :is="iconComp" /></el-icon>
        <span v-else class="card-emoji">{{ icon }}</span>
      </div>
      <div class="card-badge" v-if="badge">
        <span :class="badgeClass">{{ badge }}</span>
      </div>
    </div>
    <div class="card-content">
      <div class="card-title">{{ title }}</div>
      <div class="card-stats">
        <div v-for="(stat, idx) in stats" :key="idx" class="stat-item">
          <span class="stat-value" :class="{ 'stat-highlight': stat.highlight }">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
        <div v-if="!stats.length" class="stat-item">
          <span class="stat-value">无</span>
        </div>
      </div>
    </div>
    <div class="card-arrow">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 18l6-6-6-6"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: { type: [String, Object], default: '' },
  title: { type: String, required: true },
  stats: { type: Array, default: () => [] },
  badge: { type: String, default: '' },
  badgeClass: { type: String, default: 'badge-default' },
  accent: { type: String, default: '#5B92E5' }
})

defineEmits(['click'])

const isComponent = (v) => v && typeof v === 'object'
const iconComp = computed(() => isComponent(props.icon) ? props.icon : null)

const cardStyle = computed(() => ({
  '--card-accent': props.accent
}))

const iconStyle = computed(() => ({
  background: `linear-gradient(135deg, ${props.accent}22, ${props.accent}0a)`,
  color: props.accent,
  border: `1px solid ${props.accent}30`
}))
</script>

<style scoped>
.dimension-card {
  background: var(--bg-card, #fff);
  border-radius: var(--radius-md, 12px);
  border: 1px solid rgba(91, 146, 229, 0.1);
  padding: 12px 14px;
  cursor: pointer;
  transition: all var(--transition-normal, 0.25s ease);
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-sm, 0 2px 8px rgba(91,146,229,0.06));
}
.dimension-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--card-accent, #5B92E5), transparent);
  opacity: 0;
  transition: opacity var(--transition-fast, 0.15s ease);
}
.dimension-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91,146,229,0.15);
  border-color: var(--card-accent, #5B92E5);
}
.dimension-card:hover::before { opacity: 1; }
.dimension-card:active { transform: translateY(0); }

.card-icon-area { position: relative; flex-shrink: 0; }
.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-ep-icon { display: flex; align-items: center; justify-content: center; }
.card-emoji { font-size: 20px; line-height: 1; }
.card-badge { position: absolute; top: -4px; right: -4px; }
.card-badge span {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 6px;
  font-weight: 600;
  white-space: nowrap;
}
.badge-default { background: rgba(91,146,229,0.12); color: #5B92E5; }
.badge-red { background: rgba(245,108,108,0.15); color: #f56c6c; }
.badge-yellow { background: rgba(230,162,60,0.15); color: #e6a23c; }
.badge-green { background: rgba(103,194,58,0.15); color: #67c23a; }

.card-content { flex: 1; min-width: 0; }
.card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #2c3e50);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-stats { display: flex; flex-wrap: wrap; gap: 2px 10px; }
.stat-item { display: flex; align-items: baseline; gap: 3px; }
.stat-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--card-accent, #5B92E5);
}
.stat-value.stat-highlight { color: #f56c6c; }
.stat-label { font-size: 11px; color: var(--text-muted, #909399); }

.card-arrow {
  flex-shrink: 0;
  color: var(--text-muted, #909399);
  opacity: 0;
  transition: opacity var(--transition-fast, 0.15s ease);
}
.dimension-card:hover .card-arrow {
  opacity: 1;
  color: var(--card-accent, #5B92E5);
}
</style>
