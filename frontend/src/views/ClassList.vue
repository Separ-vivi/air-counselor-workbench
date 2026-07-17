<template>
  <div class="class-list">
    <div class="page-header">
      <h2>🎓 班级管理</h2>
      <div>
        <el-button :icon="Refresh" @click="reload">刷新组织树</el-button>
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
      </el-form>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Setting } from '@element-plus/icons-vue'
import { useOrgStore } from '@/stores/org'

const router = useRouter()
const orgStore = useOrgStore()

const filter = reactive({ gradeId: null, majorId: null, keyword: '' })

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
  return list
})

const goClass = (id) => router.push(`/classes/${id}`)
const reload = () => orgStore.loadTree(true)

onMounted(() => {
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
