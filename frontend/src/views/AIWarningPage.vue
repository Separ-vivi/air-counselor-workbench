<template>
  <div class="ai-warning-page">
    <div class="page-header">
      <div class="header-left">
        <h2>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#5B92E5" stroke-width="2" style="vertical-align: -4px; margin-right: 6px;">
            <path d="M12 9v4m0 4h.01M12 2L2 20h20L12 2z"/>
          </svg>
          AI 智能预警
        </h2>
        <el-tag v-if="llmEnhanced" type="success" size="small" effect="plain" round>AI 增强分析</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="refreshWarnings(true)" :loading="loading" :icon="Refresh">刷新分析</el-button>
        <el-button type="primary" :icon="Download" @click="exportCSV" :disabled="!filteredWarnings.length">导出 CSV</el-button>
      </div>
    </div>

    <!-- AI Advice Banner -->
    <div v-if="aiAdvice" class="ai-advice-banner">
      <span class="advice-icon">💡</span>
      <div class="advice-body">
        <div class="advice-label">AI 工作建议</div>
        <div class="advice-text">{{ aiAdvice }}</div>
      </div>
      <div v-if="topPriority.length" class="advice-priority">
        <span class="priority-label">重点关注：</span>
        <el-tag v-for="name in topPriority" :key="name" type="danger" size="small" effect="plain" round style="margin-right: 4px;">{{ name }}</el-tag>
      </div>
    </div>

    <!-- Stats Overview -->
    <div class="stats-overview">
      <div class="stat-card high" @click="filterSeverity = filterSeverity === 'high' ? '' : 'high'">
        <div class="sc-icon">🔴</div>
        <div class="sc-num">{{ highCount }}</div>
        <div class="sc-label">高风险</div>
        <div class="sc-bar" :class="{ active: filterSeverity === 'high' }"></div>
      </div>
      <div class="stat-card medium" @click="filterSeverity = filterSeverity === 'medium' ? '' : 'medium'">
        <div class="sc-icon">🟡</div>
        <div class="sc-num">{{ mediumCount }}</div>
        <div class="sc-label">中风险</div>
        <div class="sc-bar" :class="{ active: filterSeverity === 'medium' }"></div>
      </div>
      <div class="stat-card low" @click="filterSeverity = filterSeverity === 'low' ? '' : 'low'">
        <div class="sc-icon">🟢</div>
        <div class="sc-num">{{ lowCount }}</div>
        <div class="sc-label">低风险</div>
        <div class="sc-bar" :class="{ active: filterSeverity === 'low' }"></div>
      </div>
      <div class="stat-card total">
        <div class="sc-icon">📋</div>
        <div class="sc-num">{{ totalCount }}</div>
        <div class="sc-label">总计需关注</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-input v-model="searchText" placeholder="搜索姓名 / 学号" :prefix-icon="Search" clearable style="width: 220px" />
      <el-select v-model="filterSeverity" placeholder="风险等级" clearable style="width: 140px">
        <el-option label="🔴 高风险" value="high" />
        <el-option label="🟡 中风险" value="medium" />
        <el-option label="🟢 低风险" value="low" />
      </el-select>
      <el-select v-model="filterType" placeholder="预警类型" clearable style="width: 140px">
        <el-option v-for="t in warningTypes" :key="t" :label="t" :value="t" />
      </el-select>
      <el-select v-model="sortBy" style="width: 140px">
        <el-option label="按风险等级" value="severity" />
        <el-option label="按学号" value="student_no" />
        <el-option label="按姓名" value="name" />
        <el-option label="按预警类型" value="warning_type" />
      </el-select>
      <el-button :icon="filterSeverity || searchText || filterType ? Refresh : undefined" @click="resetFilters" text>
        {{ filterSeverity || searchText || filterType ? '重置筛选' : '' }}
      </el-button>
      <span class="filter-result-count">
        共 {{ filteredWarnings.length }} 条
        <span v-if="selectedRows.length">| 已选 {{ selectedRows.length }} 条</span>
        <span v-if="filteredWarnings.length !== totalCount">（已筛选）</span>
      </span>
    </div>

    <!-- Loading -->
    <div v-if="loading && !warnings.length" class="page-loading">
      <div class="ai-loading-dots"><span></span><span></span><span></span></div>
      <span>AI 正在分析学生数据，请稍候...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="page-error">
      <el-empty :description="error">
        <el-button type="primary" @click="refreshWarnings">重试</el-button>
      </el-empty>
    </div>

    <!-- Empty -->
    <div v-else-if="!filteredWarnings.length" class="page-empty">
      <el-empty :description="totalCount ? '没有符合筛选条件的预警' : '暂无预警，所有学生状态良好 ✅'">
        <el-button v-if="filterSeverity || searchText || filterType" @click="resetFilters">重置筛选</el-button>
      </el-empty>
    </div>

    <!-- V6.14: Warning Table - 支持多选、分页、排序 -->
    <div v-else class="warning-table">
      <!-- 批量操作栏 -->
      <div v-if="selectedRows.length" class="batch-actions">
        <span>已选 {{ selectedRows.length }} 条</span>
        <el-button size="small" type="primary" text @click="exportSelectedCSV">导出选中</el-button>
        <el-button size="small" type="danger" text @click="selectedRows = []">取消选择</el-button>
      </div>

      <el-table
        :data="paginatedWarnings"
        stripe
        @selection-change="handleSelectionChange"
        @sort-change="handleSortChange"
        :default-sort="{ prop: 'severity', order: 'ascending' }"
        row-key="rowKey"
      >
        <!-- V6.14: 多选 checkbox -->
        <el-table-column type="selection" width="45" fixed="left" />
        <el-table-column label="风险" width="70" sortable="custom" prop="severity" align="center">
          <template #default="{ row }">
            <span class="sev-badge" :class="row.severity">
              {{ row.severity === 'high' ? '高' : row.severity === 'medium' ? '中' : '低' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="学生" min-width="150" sortable="custom" prop="name">
          <template #default="{ row }">
            <div class="cell-student-info">
              <el-link type="primary" @click="goStudent(row.student_id)" class="cell-student-name">{{ row.name }}</el-link>
              <span class="cell-student-no">{{ row.student_no }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="班级" prop="class_name" min-width="130" show-overflow-tooltip sortable="custom" />
        <el-table-column label="预警类型" prop="warning_type" width="110" sortable="custom">
          <template #default="{ row }">
            <el-tag :type="getWarningTypeTag(row.warning_type)" size="small" effect="plain" round>{{ row.warning_type }}</el-tag>
          </template>
        </el-table-column>
        <!-- V6.14: 详细信息列 - 显示具体日期、课程等 -->
        <el-table-column label="详细原因" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="cell-detail">
              <div class="cell-detail-main">{{ row.reason }}</div>
              <div v-if="row.details && row.details.length" class="cell-detail-extra">
                <el-popover placement="bottom" :width="360" trigger="click">
                  <template #reference>
                    <el-button text size="small" type="primary">查看详情 ({{ row.details.length }})</el-button>
                  </template>
                  <div class="detail-popover">
                    <div v-for="(d, i) in row.details" :key="i" class="detail-item">
                      <span v-if="d.date" class="detail-date">{{ d.date }}</span>
                      <span v-if="d.course" class="detail-course">{{ d.course }}</span>
                      <span v-if="d.type" class="detail-type">{{ d.type }}</span>
                      <span v-if="d.info" class="detail-info">{{ d.info }}</span>
                    </div>
                  </div>
                </el-popover>
              </div>
            </div>
          </template>
        </el-table-column>
        <!-- V6.15: 操作列 - 发起谈心谈话，联动访谈页面 -->
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="startInterview(row)">发起谈话</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- V6.14: 分页 -->
      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredWarnings.length"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          small
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
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
const topPriority = ref([])

// V6.14: 分页
const currentPage = ref(1)
const pageSize = ref(20)
// V6.14: 多选
const selectedRows = ref([])

// Filters
const searchText = ref('')
const filterSeverity = ref('')
const filterType = ref('')
const sortBy = ref('severity')
const sortOrder = ref('ascending')

const warningTypes = computed(() => {
  const types = new Set(warnings.value.map(w => w.warning_type))
  return [...types]
})

const filteredWarnings = computed(() => {
  let list = [...warnings.value]
  
  if (filterSeverity.value) {
    list = list.filter(w => w.severity === filterSeverity.value)
  }
  if (filterType.value) {
    list = list.filter(w => w.warning_type === filterType.value)
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(w =>
      (w.name || '').toLowerCase().includes(q) ||
      (w.student_no || '').toLowerCase().includes(q) ||
      (w.class_name || '').toLowerCase().includes(q)
    )
  }
  
  // Sort
  const severityOrder = { high: 0, medium: 1, low: 2 }
  const dir = sortOrder.value === 'descending' ? -1 : 1
  list.sort((a, b) => {
    let va, vb
    switch (sortBy.value) {
      case 'severity':
        va = severityOrder[a.severity] ?? 3
        vb = severityOrder[b.severity] ?? 3
        break
      case 'name':
        va = (a.name || '').localeCompare(b.name || '')
        return va * dir
      case 'student_no':
        va = a.student_no || ''
        vb = b.student_no || ''
        return va.localeCompare(vb) * dir
      case 'warning_type':
        va = a.warning_type || ''
        vb = b.warning_type || ''
        return va.localeCompare(vb) * dir
      default:
        va = severityOrder[a.severity] ?? 3
        vb = severityOrder[b.severity] ?? 3
    }
    return (va - vb) * dir
  })
  
  return list
})

// V6.14: 分页数据
const paginatedWarnings = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredWarnings.value.slice(start, start + pageSize.value)
})

const handleSortChange = ({ prop, order }) => {
  if (prop) {
    sortBy.value = prop
    sortOrder.value = order || 'ascending'
  }
}

// V6.14: 多选处理
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const resetFilters = () => {
  searchText.value = ''
  filterSeverity.value = ''
  filterType.value = ''
  sortBy.value = 'severity'
  sortOrder.value = 'ascending'
  currentPage.value = 1
}

const getWarningTypeTag = (type) => {
  const map = {
    '成绩预警': 'danger',
    '缺勤过多': 'warning',
    '心理关注': 'danger',
    '纪律处分': 'warning',
    '访谈待跟进': 'info'
  }
  return map[type] || ''
}

const goStudent = (sid) => {
  if (sid) router.push(`/students/${sid}`)
}

// V6.15: 发起谈心谈话 - 跳转到访谈页面并携带预警上下文
const startInterview = (row) => {
  // 序列化预警详情
  const warningDetails = row.details && row.details.length
    ? row.details.map(d => [d.date, d.course, d.type, d.info].filter(Boolean).join(' ')).join('; ')
    : ''
  router.push({
    path: '/module/interview',
    query: {
      warning_student_id: row.student_id || '',
      warning_student_name: row.name || '',
      warning_student_no: row.student_no || '',
      warning_class_name: row.class_name || '',
      warning_type: row.warning_type || '',
      warning_reason: row.reason || '',
      warning_severity: row.severity || '',
      warning_details: warningDetails
    }
  })
}

const refreshWarnings = async (force = false) => {
  loading.value = true
  error.value = ''
  try {
    const res = await aiWarnings(force)
    const data = res?.warnings && !Array.isArray(res.warnings) ? res.warnings : res
    const rawWarnings = Array.isArray(data?.warnings) ? data.warnings : []
    // V6.14: 为每行添加唯一key
    warnings.value = rawWarnings.map((w, i) => ({
      ...w,
      rowKey: `${w.student_id}-${w.warning_type}-${i}`
    }))
    highCount.value = data?.high_count || 0
    mediumCount.value = data?.medium_count || 0
    lowCount.value = data?.low_count || 0
    totalCount.value = data?.total || 0
    llmEnhanced.value = data?.llm_enhanced || false
    aiAdvice.value = data?.ai_advice || ''
    topPriority.value = data?.top_priority || []
  } catch (e) {
    error.value = 'AI 预警服务暂时不可用'
    warnings.value = []
  } finally {
    loading.value = false
  }
}

const exportCSV = () => {
  const headers = ['风险等级', '姓名', '学号', '班级', '预警类型', '原因']
  const severityLabel = { high: '高风险', medium: '中风险', low: '低风险' }
  const rows = filteredWarnings.value.map(w => [
    severityLabel[w.severity] || w.severity,
    w.name,
    w.student_no,
    w.class_name,
    w.warning_type,
    w.reason
  ])
  downloadCSV(rows, headers, 'AI智能预警')
}

// V6.14: 导出选中
const exportSelectedCSV = () => {
  const headers = ['风险等级', '姓名', '学号', '班级', '预警类型', '原因']
  const severityLabel = { high: '高风险', medium: '中风险', low: '低风险' }
  const rows = selectedRows.value.map(w => [
    severityLabel[w.severity] || w.severity,
    w.name,
    w.student_no,
    w.class_name,
    w.warning_type,
    w.reason
  ])
  downloadCSV(rows, headers, 'AI智能预警_选中')
}

const downloadCSV = (rows, headers, filename) => {
  const BOM = '\uFEFF'
  const csv = BOM + [headers, ...rows].map(r => r.map(c => `"${(c || '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${filename}_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  refreshWarnings(true)
})
</script>

<style scoped>
.ai-warning-page {
  padding: 4px;
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 22px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-right {
  display: flex;
  gap: 8px;
}

/* AI Advice Banner */
.ai-advice-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 18px;
  background: linear-gradient(135deg, rgba(91, 146, 229, 0.06), rgba(123, 207, 203, 0.08));
  border: 1px solid rgba(91, 146, 229, 0.15);
  border-radius: 12px;
  margin-bottom: 16px;
}
.advice-icon { font-size: 22px; flex-shrink: 0; }
.advice-body { flex: 1; }
.advice-label { font-size: 12px; color: #5B92E5; font-weight: 600; margin-bottom: 2px; }
.advice-text { font-size: 13px; color: #2E5A7F; line-height: 1.6; }
.advice-priority {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.priority-label { font-size: 12px; color: #E74C3C; font-weight: 600; }

/* Stats Overview */
.stats-overview {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  flex: 1;
  text-align: center;
  padding: 16px 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(200, 215, 235, 0.5);
  background: linear-gradient(180deg, #FFFFFF 0%, #F3F8FE 100%);
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(91, 146, 229, 0.12);
}
.stat-card.high { border-left: 3px solid #F56C6C; }
.stat-card.medium { border-left: 3px solid #E6A23C; }
.stat-card.low { border-left: 3px solid #67C23A; }
.stat-card.total { border-left: 3px solid #5B92E5; }
.sc-icon { font-size: 18px; margin-bottom: 4px; }
.sc-num {
  font-size: 28px;
  font-weight: 800;
  line-height: 1.2;
  font-family: -apple-system, 'SF Pro Display', 'PingFang SC', sans-serif;
}
.stat-card.high .sc-num { color: #F56C6C; }
.stat-card.medium .sc-num { color: #E6A23C; }
.stat-card.low .sc-num { color: #67C23A; }
.stat-card.total .sc-num { color: #5B92E5; }
.sc-label { font-size: 12px; color: #7F8C8D; margin-top: 2px; font-weight: 500; }
.sc-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: transparent;
  transition: background 0.2s;
}
.sc-bar.active { background: #5B92E5; }

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.filter-result-count {
  font-size: 13px;
  color: #7F8C8D;
  margin-left: auto;
}

/* V6.14: 批量操作栏 */
.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(91, 146, 229, 0.06);
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid rgba(91, 146, 229, 0.15);
  font-size: 13px;
  color: #2E5A7F;
}

/* Loading / Error / Empty */
.page-loading {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  padding: 60px 20px;
  color: #5B92E5;
  font-size: 14px;
}
.ai-loading-dots {
  display: flex;
  gap: 4px;
}
.ai-loading-dots span {
  width: 6px;
  height: 6px;
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
.page-empty, .page-error { padding: 40px 0; }

/* Severity Badge */
.sev-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}
.sev-badge.high { background: linear-gradient(135deg, #F56C6C, #E88686); }
.sev-badge.medium { background: linear-gradient(135deg, #E6A23C, #F5A76E); }
.sev-badge.low { background: linear-gradient(135deg, #67C23A, #85CE61); }

/* Cell styles */
.cell-student-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.cell-student-name {
  font-size: 14px;
  font-weight: 500;
}
.cell-student-no {
  font-size: 12px;
  color: #909399;
  font-family: 'SF Mono', 'Menlo', monospace;
  letter-spacing: 0.3px;
}

/* V6.14: 详细信息样式 */
.cell-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.cell-detail-main {
  color: #2C3E50;
  font-size: 13px;
}
.cell-detail-extra {
  display: flex;
  align-items: center;
}

/* 详情弹窗 */
.detail-popover {
  max-height: 300px;
  overflow-y: auto;
}
.detail-item {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px dashed rgba(200, 215, 235, 0.4);
  font-size: 12px;
  align-items: center;
}
.detail-item:last-child { border-bottom: none; }
.detail-date {
  color: #5B92E5;
  font-weight: 500;
  white-space: nowrap;
}
.detail-course {
  color: #2C3E50;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.detail-type {
  color: #E6A23C;
  font-weight: 500;
  white-space: nowrap;
}
.detail-info {
  color: #7F8C8D;
  font-size: 11px;
}

/* Table */
.warning-table {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(200, 215, 235, 0.5);
}
.warning-table :deep(.el-table) {
  border-radius: 12px;
}
.warning-table :deep(.el-table th) {
  background: linear-gradient(180deg, #F7FAFE 0%, #EEF3F9 100%);
  color: #2E5A7F;
  font-weight: 600;
  font-size: 13px;
}

/* V6.14: 分页栏 */
.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  background: linear-gradient(180deg, #F9FBFD 0%, #FFFFFF 100%);
  border-top: 1px solid rgba(200, 215, 235, 0.3);
}
</style>
