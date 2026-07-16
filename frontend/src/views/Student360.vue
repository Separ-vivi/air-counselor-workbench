<template>
  <div class="s360-wrap">
    <div v-if="loading" class="empty-hint">
      <div class="icon">⏳</div>
      <div>加载学生 360 数据中…</div>
    </div>

    <template v-else-if="student">
      <!-- 顶部 sticky 信息卡 -->
      <div class="student-header-card">
        <div class="avatar">{{ student.name?.slice(0, 1) || '?' }}</div>
        <div class="info">
          <div class="name">
            {{ student.name }}
            <el-tag size="small" style="margin-left:8px" round>{{ student.gender || '—' }}</el-tag>
            <el-button link @click="editBasic" style="margin-left:12px">
              <el-icon><Edit /></el-icon>&nbsp;编辑基础信息
            </el-button>
          </div>
          <div class="meta">
            <span>🎓 <b>{{ student.student_no }}</b></span>
            <span>🏫
              <router-link v-if="student.class_id" :to="`/classes/${student.class_id}`">
                {{ student.class_name || '—' }}
              </router-link>
              <template v-else>{{ student.class_name || '—' }}</template>
            </span>
            <span>📚 {{ student.major_name || '—' }}</span>
            <span>📅 {{ student.grade_name || '—' }}</span>
            <br>
            <span>🎖️ {{ student.political_status || '—' }}</span>
            <span>📱 {{ student.phone || '—' }}</span>
            <span>👨‍👩‍👧 家长电话 {{ student.parent_phone || '—' }}</span>
            <span>📍 生源地 {{ student.birth_source || '—' }}</span>
          </div>
          <div class="status-lights">
            <span class="status-chip" :class="warningClass">
              <span class="status-dot" :class="warningClass" /> 学业预警 · {{ warningLabel }}
            </span>
            <span class="status-chip">🎯 党团 · {{ summary?.stats?.party_stage || '群众' }}</span>
            <span class="status-chip" :class="summary?.psych_status === 'attention' ? 'yellow' : 'green'">
              💚 心理 · {{ summary?.psych_status === 'attention' ? '需关注' : '正常' }}
            </span>
            <span class="status-chip">💼 就业 · {{ summary?.stats?.employment_status || '未登记' }}</span>
            <span class="status-chip" :class="hardshipClass">
              💰 资助 · {{ summary?.stats?.hardship_level || '无' }}
            </span>
            <span class="status-chip">🏨 宿舍 · 在校</span>
          </div>
        </div>
      </div>

      <!-- Tab 区 -->
      <div class="s360-body">
        <div class="side-tabs">
          <div
            v-for="tab in tabs"
            :key="tab.key"
            class="side-tab-item"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.icon }} {{ tab.label }}
          </div>
        </div>

        <div class="tab-main">
          <keep-alive>
            <component :is="currentTabComponent" :sid="sid" :student="student" :summary="summary" @refresh-header="loadHeader" />
          </keep-alive>
        </div>
      </div>
    </template>

    <div v-else class="empty-hint">
      <div class="icon">😢</div>
      <div>学生不存在或已被删除</div>
    </div>

    <!-- 编辑基础信息弹窗 -->
    <el-dialog v-model="basicDialog" title="编辑基础信息" width="640px" destroy-on-close>
      <el-form :model="basicForm" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="学号"><el-input v-model="basicForm.student_no" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="姓名"><el-input v-model="basicForm.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="性别">
            <el-select v-model="basicForm.gender" clearable>
              <el-option label="男" value="男" /><el-option label="女" value="女" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="政治面貌">
            <el-select v-model="basicForm.political_status" clearable>
              <el-option v-for="s in politicalOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="出生日期">
            <el-date-picker v-model="basicForm.birth_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="生源地"><el-input v-model="basicForm.birth_source" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="联系电话"><el-input v-model="basicForm.phone" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="家长电话"><el-input v-model="basicForm.parent_phone" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="邮箱"><el-input v-model="basicForm.email" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="所属班级">
            <el-select v-model="basicForm.class_id" filterable clearable style="width:100%">
              <el-option
                v-for="c in orgStore.classes"
                :key="c.id"
                :label="`${c.name} · ${c.major_name}`"
                :value="c.id"
              />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注">
            <el-input v-model="basicForm.notes" type="textarea" :rows="2" />
          </el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="basicDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingBasic" @click="saveBasic">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getBasic, getSummary, updateBasic } from '@/api/student360.js'
import { useOrgStore } from '@/stores/org.js'

import TabBasic       from '@/components/student360/TabBasic.vue'
import TabGrades      from '@/components/student360/TabGrades.vue'
import TabParty       from '@/components/student360/TabParty.vue'
import TabPsychology  from '@/components/student360/TabPsychology.vue'
import TabFamily      from '@/components/student360/TabFamily.vue'
import TabCadres      from '@/components/student360/TabCadres.vue'
import TabActivities  from '@/components/student360/TabActivities.vue'
import TabEmployment  from '@/components/student360/TabEmployment.vue'
import TabFundingHonor from '@/components/student360/TabFundingHonor.vue'
import TabDaily       from '@/components/student360/TabDaily.vue'
import TabProjects    from '@/components/student360/TabProjects.vue'
import TabTimeline    from '@/components/student360/TabTimeline.vue'

const route = useRoute()
const orgStore = useOrgStore()

const sid = computed(() => Number(route.params.id))
const student = ref(null)
const summary = ref(null)
const loading = ref(false)
const activeTab = ref('basic')

const tabs = [
  { key: 'basic',      label: '基础信息 · 学籍异动', icon: '📋', comp: TabBasic },
  { key: 'grades',     label: '学业情况',           icon: '📊', comp: TabGrades },
  { key: 'party',      label: '党团发展',           icon: '🎯', comp: TabParty },
  { key: 'psychology', label: '心理档案',           icon: '💚', comp: TabPsychology },
  { key: 'family',     label: '家庭联络',           icon: '🏠', comp: TabFamily },
  { key: 'cadres',     label: '学生工作',           icon: '👥', comp: TabCadres },
  { key: 'activities', label: '活动参与',           icon: '🎨', comp: TabActivities },
  { key: 'employment', label: '就业信息',           icon: '💼', comp: TabEmployment },
  { key: 'funding',    label: '资助与荣誉',         icon: '💰', comp: TabFundingHonor },
  { key: 'daily',      label: '日常管理',           icon: '🏨', comp: TabDaily },
  { key: 'projects',   label: '专项工作',           icon: '📎', comp: TabProjects },
  { key: 'timeline',   label: '时间线',             icon: '📅', comp: TabTimeline }
]

const currentTabComponent = computed(() => tabs.find(t => t.key === activeTab.value)?.comp)

const warningClass = computed(() =>
  summary.value?.warning_status === 'red' ? 'red' :
  summary.value?.warning_status === 'yellow' ? 'yellow' : 'green'
)
const warningLabel = computed(() =>
  summary.value?.warning_status === 'red' ? '红灯' :
  summary.value?.warning_status === 'yellow' ? '黄灯' : '绿灯'
)
const hardshipClass = computed(() => {
  const lv = summary.value?.stats?.hardship_level
  if (!lv || lv === '无') return 'gray'
  if (lv.includes('特殊') || lv.includes('建档')) return 'red'
  return 'yellow'
})

const politicalOptions = ['群众', '共青团员', '中共预备党员', '中共党员']

async function loadHeader() {
  loading.value = true
  try {
    const [b, s] = await Promise.all([
      getBasic(sid.value),
      getSummary(sid.value).catch(() => null)
    ])
    student.value = b
    summary.value = s
  } catch (e) {
    student.value = null
  } finally {
    loading.value = false
  }
}
watch(sid, loadHeader, { immediate: false })
onMounted(async () => {
  await loadHeader()
  if (!orgStore.orgTree.length) orgStore.loadTree()
})

// 编辑基础信息
const basicDialog = ref(false)
const basicForm = ref({})
const savingBasic = ref(false)
function editBasic() {
  basicForm.value = { ...(student.value || {}) }
  basicDialog.value = true
}
async function saveBasic() {
  savingBasic.value = true
  try {
    // StudentBase schema 只接受一小组字段
    const payload = {
      student_no: basicForm.value.student_no,
      name: basicForm.value.name,
      gender: basicForm.value.gender,
      class_id: basicForm.value.class_id ?? null,
      birth_date: basicForm.value.birth_date || null,
      political_status: basicForm.value.political_status,
      phone: basicForm.value.phone,
      email: basicForm.value.email,
      parent_phone: basicForm.value.parent_phone,
      birth_source: basicForm.value.birth_source,
      notes: basicForm.value.notes
    }
    await updateBasic(sid.value, payload)
    ElMessage.success('保存成功')
    basicDialog.value = false
    await loadHeader()
  } catch {} finally { savingBasic.value = false }
}
</script>

<style scoped>
.s360-wrap { }
.s360-body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.tab-main {
  flex: 1;
  min-width: 0;
  background: var(--color-card-bg);
  border: 1px solid var(--color-card-border);
  border-radius: var(--radius-card);
  padding: 16px;
  box-shadow: var(--shadow-card);
}
</style>
