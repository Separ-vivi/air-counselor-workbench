<template>
  <div class="ai-warning-card">
    <div class="awc-header">
      <span class="ch-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#5B92E5" stroke-width="2" style="vertical-align: -2px; margin-right: 4px;">
          <path d="M12 9v4m0 4h.01M12 2L2 20h20L12 2z"/>
        </svg>
        AI 智能预警
      </span>
      <div class="awc-actions">
        <el-tag v-if="llmEnhanced" type="success" size="small" effect="plain" round>AI 增强</el-tag>
        <el-button text type="primary" size="small" @click="refreshWarnings" :loading="loading">
          {{ loading ? '分析中...' : '刷新' }}
        </el-button>
        <el-button text type="primary" size="small" @click="$router.push('/ai-warnings')">
          查看详情 →
        </el-button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading && !totalCount" class="ai-loading">
      <div class="ai-loading-dots"><span></span><span></span><span></span></div>
      <span>AI 正在分析学生数据...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="ai-error">
      <span>⚠️ {{ error }}</span>
      <el-button text size="small" @click="refreshWarnings">重试</el-button>
    </div>

    <!-- Empty -->
    <div v-else-if="!totalCount" class="ai-empty">
      <span class="empty-icon">✅</span>
      <span>暂无预警，所有学生状态良好</span>
    </div>

    <!-- Summary Stats -->
    <template v-else>
      <!-- AI Advice -->
      <div v-if="aiAdvice" class="ai-advice">
        <span class="ai-advice-icon">💡</span>
        <span class="ai-advice-text">{{ aiAdvice }}</span>
      </div>

      <!-- Stats Grid -->
      <div class="awc-stats">
        <div class="awc-stat-item high" @click="$router.push('/ai-warnings')">
          <span class="awc-stat-dot">🔴</span>
          <span class="awc-stat-num">{{ highCount }}</span>
          <span class="awc-stat-label">高风险</span>
        </div>
        <div class="awc-stat-item medium" @click="$router.push('/ai-warnings')">
          <span class="awc-stat-dot">🟡</span>
          <span class="awc-stat-num">{{ mediumCount }}</span>
          <span class="awc-stat-label">中风险</span>
        </div>
        <div class="awc-stat-item low" @click="$router.push('/ai-warnings')">
          <span class="awc-stat-dot">🟢</span>
          <span class="awc-stat-num">{{ lowCount }}</span>
          <span class="awc-stat-label">低风险</span>
        </div>
        <div class="awc-stat-item total" @click="$router.push('/ai-warnings')">
          <span class="awc-stat-dot">📋</span>
          <span class="awc-stat-num">{{ totalCount }}</span>
          <span class="awc-stat-label">需关注</span>
        </div>
      </div>

      <!-- Top 3 Preview -->
      <div v-if="topWarnings.length" class="awc-preview">
        <div class="awc-preview-title">重点关注</div>
        <div v-for="w in topWarnings" :key="w.student_id + w.warning_type" class="awc-preview-item" @click="goStudent(w.student_id)">
          <span class="awc-pi-sev" :class="w.severity">{{ w.severity === 'high' ? '高' : w.severity === 'medium' ? '中' : '低' }}</span>
          <span class="awc-pi-name">{{ w.name }}</span>
          <span class="awc-pi-reason">{{ w.reason }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { aiWarnings } from '@/api/modules'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const warnings = ref([])
const highCount = ref(0)
const mediumCount = ref(0)
const lowCount = ref(0)
const totalCount = ref(0)
const llmEnhanced = ref(false)
const aiAdvice = ref('')

const topWarnings = computed(() => {
  return warnings.value.filter(w => w.severity === 'high').slice(0, 3)
})

const goStudent = (sid) => {
  if (sid) router.push(`/students/${sid}`)
}

const refreshWarnings = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await aiWarnings()
    warnings.value = res?.warnings || []
    highCount.value = res?.high_count || 0
    mediumCount.value = res?.medium_count || 0
    lowCount.value = res?.low_count || 0
    totalCount.value = res?.total || 0
    llmEnhanced.value = res?.llm_enhanced || false
    aiAdvice.value = res?.ai_advice || ''
  } catch (e) {
    error.value = 'AI 预警服务暂时不可用'
    warnings.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshWarnings()
})

defineExpose({ refreshWarnings })
</script>

<style scoped>
.ai-warning-card {
  border-radius: var(--radius-lg) !important;
  border: 1px solid rgba(200, 215, 235, 0.55) !important;
  background: linear-gradient(180deg, #FFFFFF 0%, #F3F8FE 100%) !important;
  padding: 0;
}
.awc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  border-bottom: 1px solid rgba(220, 226, 232, 0.5);
}
.awc-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.ch-title {
  font-weight: 600;
  font-size: 14px;
  color: #2E5A7F;
  letter-spacing: 0.4px;
}

/* Loading */
.ai-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 30px 18px;
  justify-content: center;
  color: #5B92E5;
  font-size: 13px;
}
.ai-loading-dots {
  display: flex;
  gap: 4px;
}
.ai-loading-dots span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #5B92E5;
  animation: aiDotPulse 1.2s infinite ease-in-out;
}
.ai-loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.ai-loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes aiDotPulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.2); }
}

/* Error & Empty */
.ai-error, .ai-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 30px 18px;
  color: #7F8C8D;
  font-size: 13px;
  justify-content: center;
}
.empty-icon { font-size: 24px; }

/* AI Advice */
.ai-advice {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 18px;
  background: linear-gradient(135deg, rgba(91, 146, 229, 0.05), rgba(123, 207, 203, 0.06));
  font-size: 12px;
  color: #2E5A7F;
  line-height: 1.5;
}
.ai-advice-icon { flex-shrink: 0; }

/* Stats Grid */
.awc-stats {
  display: flex;
  gap: 8px;
  padding: 14px 18px;
}
.awc-stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 6px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(91, 146, 229, 0.03);
  border: 1px solid rgba(200, 215, 235, 0.4);
}
.awc-stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(91, 146, 229, 0.12);
  border-color: rgba(160, 195, 225, 0.6);
}
.awc-stat-item.high { background: rgba(245, 108, 108, 0.05); }
.awc-stat-item.medium { background: rgba(230, 162, 60, 0.05); }
.awc-stat-item.low { background: rgba(103, 194, 58, 0.05); }
.awc-stat-item.total { background: rgba(91, 146, 229, 0.06); border-color: rgba(91, 146, 229, 0.2); }
.awc-stat-dot { font-size: 14px; margin-bottom: 2px; }
.awc-stat-num {
  font-size: 24px;
  font-weight: 800;
  line-height: 1.2;
  font-family: -apple-system, 'SF Pro Display', 'PingFang SC', sans-serif;
}
.awc-stat-item.high .awc-stat-num { color: #F56C6C; }
.awc-stat-item.medium .awc-stat-num { color: #E6A23C; }
.awc-stat-item.low .awc-stat-num { color: #67C23A; }
.awc-stat-item.total .awc-stat-num { color: #5B92E5; }
.awc-stat-label {
  font-size: 11px;
  color: #7F8C8D;
  margin-top: 2px;
  font-weight: 500;
}

/* Preview */
.awc-preview {
  padding: 0 18px 14px;
}
.awc-preview-title {
  font-size: 12px;
  font-weight: 600;
  color: #2E5A7F;
  margin-bottom: 6px;
  letter-spacing: 0.3px;
}
.awc-preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 12px;
}
.awc-preview-item:hover {
  background: rgba(91, 146, 229, 0.06);
}
.awc-pi-sev {
  width: 20px;
  height: 20px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.awc-pi-sev.high { background: linear-gradient(135deg, #F56C6C, #E88686); }
.awc-pi-sev.medium { background: linear-gradient(135deg, #E6A23C, #F5A76E); }
.awc-pi-sev.low { background: linear-gradient(135deg, #67C23A, #85CE61); }
.awc-pi-name {
  font-weight: 600;
  color: #2C3E50;
  white-space: nowrap;
}
.awc-pi-reason {
  color: #7B8B9C;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}
</style>
