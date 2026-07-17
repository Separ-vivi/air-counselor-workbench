<template>
  <div class="class-list">
    <div class="page-header">
      <h2>🎓 班级管理</h2>
      <div>
        <el-button :icon="Refresh" @click="reload">刷新组织树</el-button>
        <el-button :icon="Download" @click="exportAll">导出全部</el-button>
        <el-button type="primary" :icon="Setting" @click="$router.push('/org')">管理组织架构</el-button>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="年级">
          <el-select v-model="filter.gradeId" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="g in orgStore.grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="filter.majorId" placeholder="全部" clearable filterable style="width: 200px">
            <el-option v-for="m in majorOptions" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字">
          <el-input v-model="filter.keyword" placeholder="班级名 / 班主任 / 班长" clearable style="width: 220px" />
        </el-form-item>
        <el-form-item label="排序">
          <el-select v-model="filter.sortBy" style="width: 160px">
            <el-option label="默认（年级/专业）" value="" />
            <el-option label="班级名（升）" value="name_asc" />
            <el-option label="班级名（降）" value="name_desc" />
            <el-option label="人数（多→少）" value="count_desc" />
            <el-option label="人数（少→多）" value="count_asc" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- v3h A: 班级人数柱状图（从驾驶舱挪来） -->
    <el-card shadow="never" style="margin-bottom: 16px" v-if="filteredClasses.length">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>📊 各班学生人数对比</span>
          <span style="font-size:12px;color:#909399">共 {{ filteredClasses.length }} 个班级 · 点击柱形跳转班级 360</span>
        </div>
      </template>
      <div ref="classBarRef" style="width: 100%; height: 260px"></div>
    </el-card>

    <el-row :gutter="16">
      <el-col v-for="c in filteredClasses" :key="c.id" :span="8" style="margin-bottom: 16px">
        <el-card shadow="hover" class="class-card" @click.stop="goClass(c.id)">
          <div class="cc-top">
            <div class="cc-name">🏫 {{ c.name }}</div>
            <el-tag size="small" type="info">{{ c.grade_name }}</el-tag>
          </div>
          <div class="cc-major">{{ c.major_name }}</div>
          <div class="cc-count">
            <span class="cc-num">{{ c.student_count ?? '-' }}</span>
            <span class="cc-unit">名学生</span>
          </div>
          <div class="cc-footer">
            <el-button type="primary" text size="small" @click.stop="goClass(c.id)">查看班级 360</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col v-if="!filteredClasses.length" :span="24">
        <el-empty description="没有符合条件的班级" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useRouter } from 'vue-router'
import { Refresh, Setting, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { exportClassesAll } from '@/api/org'
import { triggerDownload, stampedName } from '@/utils/download'
import { useOrgStore } from '@/stores/org'

const router = useRouter()
const orgStore = useOrgStore()

const filter = reactive({ gradeId: null, majorId: null, keyword: '', sortBy: '' })

const majorOptions = computed(() => {
  // 用 allMajors 全量，避免和组织切换器耦合
  const all = orgStore.allMajors
  return filter.gradeId ? all.filter((m) => m.grade_id === filter.gradeId) : all
})

const filteredClasses = computed(() => {
  // 用 allClasses（不受顶端组织切换器影响），只按本页 filter 过滤
  let list = orgStore.allClasses
  if (filter.gradeId) list = list.filter((c) => c.grade_id === filter.gradeId)
  if (filter.majorId) list = list.filter((c) => c.major_id === filter.majorId)
  const kw = filter.keyword.trim()
  if (kw) {
    list = list.filter(
      (c) =>
        (c.name || '').includes(kw) ||
        (c.class_teacher || '').includes(kw) ||
        (c.monitor || '').includes(kw)
    )
  }
  // v3j-B-b02 · 前端排序（班级列表数据量小，全量已加载）
  const sb = filter.sortBy
  if (sb) {
    const arr = [...list]
    if (sb === 'name_asc')  arr.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    if (sb === 'name_desc') arr.sort((a, b) => (b.name || '').localeCompare(a.name || ''))
    if (sb === 'count_desc') arr.sort((a, b) => (b.student_count || 0) - (a.student_count || 0))
    if (sb === 'count_asc')  arr.sort((a, b) => (a.student_count || 0) - (b.student_count || 0))
    return arr
  }
  return list
})

const goClass = (id) => router.push(`/classes/${id}`)
// v3h A: 班级人数柱状图
const classBarRef = ref(null)
let classBarChart = null
const macaronColors = ['#F8B4B4','#F9E79F','#B7E4C7','#B7D8E4','#D5B7E4','#F5C7A0','#FCB69F','#A8E6CF','#FFD3B6','#FF8B94','#C7CEEA','#FEC8D8']

function renderClassBar() {
  if (!classBarRef.value) return
  const cd = filteredClasses.value.map(c => ({ name: c.name, value: c.student_count || 0, id: c.id }))
  if (!classBarChart) classBarChart = echarts.init(classBarRef.value)
  classBarChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 12, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: 'category', data: cd.map(x => x.name), axisLine: { lineStyle: { color: '#DCDFE6' } }, axisLabel: { color: '#606266', fontSize: 11, rotate: cd.length > 8 ? 20 : 0, interval: 0 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#E4E7ED' } }, axisLabel: { color: '#909399', fontSize: 11 } },
    series: [{
      type: 'bar', barWidth: '46%',
      data: cd.map((x, i) => ({ value: x.value, name: x.name, itemStyle: { color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: macaronColors[i % macaronColors.length] },
          { offset: 1, color: '#FFFFFF' }
        ]
      }, borderRadius: [8, 8, 0, 0] } })),
      label: { show: true, position: 'top', color: '#606266', fontSize: 11, fontWeight: 500 }
    }]
  })
  classBarChart.off('click')
  classBarChart.on('click', (params) => {
    const idx = params?.dataIndex
    const cls = filteredClasses.value[idx]
    if (cls?.id) router.push({ path: `/class360/${cls.id}` })
  })
}

const resizeClassBar = () => { try { classBarChart?.resize() } catch(e) {} }
watch(filteredClasses, () => { nextTick(renderClassBar) })
onUnmounted(() => {
  window.removeEventListener('resize', resizeClassBar)
  try { classBarChart?.dispose() } catch(e) {}
})

const reload = () => orgStore.loadTree(true)

// v3j-B-b02 · 导出全部班级
const exportAll = async () => {
  try {
    const params = {}
    if (filter.gradeId) params.grade_id = filter.gradeId
    if (filter.majorId) params.major_id = filter.majorId
    if (filter.keyword.trim()) params.search = filter.keyword.trim()
    const blob = await exportClassesAll(params)
    triggerDownload(blob, stampedName('班级列表'))
    ElMessage.success('已导出班级列表')
  } catch (e) { ElMessage.error('导出失败') }
}

onMounted(() => {
  window.addEventListener('resize', resizeClassBar)
  nextTick(renderClassBar)
  if (!orgStore.orgTree.length) orgStore.loadTree()
  // reinit 后自动刷新组织树（数据库被重建，班级列表要重新拉）
  window.addEventListener('system-reinit-done', () => orgStore.loadTree(true))
})
</script>

<style scoped>
.class-list { padding: 4px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { margin: 0; font-size: 22px; color: #303133; }
.class-card {
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.class-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}
.cc-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cc-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.cc-major {
  color: #606266;
  font-size: 13px;
  margin: 8px 0;
}
.cc-count {
  padding: 8px 0;
  border-top: 1px dashed #EBEEF5;
  border-bottom: 1px dashed #EBEEF5;
  margin: 8px 0;
}
.cc-num {
  color: #4A7A8C;
  font-size: 26px;
  font-weight: 700;
}
.cc-unit {
  color: #909399;
  margin-left: 6px;
  font-size: 13px;
}
.cc-footer {
  text-align: right;
}
</style>
