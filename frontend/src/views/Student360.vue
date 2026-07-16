<template>
  <div class="s360-wrap">
    <div class="inline-back-bar">
      <el-button link @click="inlineGoBack" class="back-inline-btn">
        <el-icon><component :is="_InlineArrowLeft" /></el-icon>
        <span style="margin-left:4px;font-weight:500">返回</span>
      </el-button>
      <span class="inline-title">学生 360</span>
    </div>
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
            <el-button link @click="onOpenPdf" style="margin-left:8px" class="action-btn-edit">
              <span>📄 导出 PDF</span>
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
            <br>
            <span>🪪 身份证 <b>{{ maskedIdCard }}</b></span>
            <span v-if="student.is_off_campus">🏠 <el-tag size="small" type="warning">外宿</el-tag> {{ student.off_campus_address || '—' }}</span>
            <span v-else>🛏️ 宿舍 {{ student.campus || '—' }}·{{ student.dorm_building || '—' }}·{{ student.dorm_room || '—' }}</span>
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
                v-for="c in orgStore.allClasses"
                :key="c.id"
                :label="`${c.name} · ${c.major_name}`"
                :value="c.id"
              />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="身份证号">
            <el-input v-model="basicForm.id_card" placeholder="18位身份证" maxlength="18" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="校区">
            <el-select v-model="basicForm.campus" clearable placeholder="选择校区" style="width:100%">
              <el-option label="铜盘校区" value="铜盘校区" />
              <el-option label="旗山校区" value="旗山校区" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="宿舍楼">
            <el-input v-model="basicForm.dorm_building" placeholder="如 3号楼" :disabled="basicForm.is_off_campus" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="房间号">
            <el-input v-model="basicForm.dorm_room" placeholder="如 401" :disabled="basicForm.is_off_campus" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="外宿">
            <el-switch v-model="basicForm.is_off_campus" active-text="外宿" inactive-text="住校" />
          </el-form-item></el-col>
          <el-col :span="24" v-if="basicForm.is_off_campus"><el-form-item label="外宿地址">
            <el-input v-model="basicForm.off_campus_address" placeholder="详细地址" />
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

    <!-- PDF 导出弹窗 -->
    <el-dialog v-model="pdfDialog" title="导出 PDF · 选择字段" width="720px">
      <el-form label-width="90px">
        <el-form-item label="包含字段">
          <el-checkbox-group v-model="pdfFields">
            <el-checkbox label="basic">A 基本信息</el-checkbox>
            <el-checkbox label="academic">B 学业总览</el-checkbox>
            <el-checkbox label="party">C 党团进度</el-checkbox>
            <el-checkbox label="psych">D 心理等级</el-checkbox>
            <el-checkbox label="aid">E 资助情况</el-checkbox>
            <el-checkbox label="family">F 家庭联络</el-checkbox>
            <el-checkbox label="employment">G 就业意向</el-checkbox>
            <el-checkbox label="status">H 学籍异动</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="脱敏">
          <el-switch v-model="pdfMask" active-text="身份证/电话中段脱敏" />
        </el-form-item>
      </el-form>
      <div class="pdf-preview-hint">提示：确认后弹出浏览器打印窗口，可选择「另存为 PDF」</div>
      <template #footer>
        <el-button @click="pdfDialog = false">取消</el-button>
        <el-button type="primary" @click="onDoPrint">打印 / 保存 PDF</el-button>
      </template>
    </el-dialog>

    <!-- 隐藏的 A4 打印区，只在打印时显示 -->
    <div id="s360-print-area" v-if="student">
      <h1>{{ student.name }} · 学生 360 一页汇总</h1>
      <p class="print-meta">学号 {{ student.student_no }} · {{ student.class_name }} · 生成于 {{ nowStr }}</p>

      <section v-if="pdfFields.includes('basic')">
        <h2>A 基本信息</h2>
        <dl>
          <dt>姓名</dt><dd>{{ student.name }}</dd>
          <dt>性别</dt><dd>{{ student.gender || '—' }}</dd>
          <dt>学号</dt><dd>{{ student.student_no }}</dd>
          <dt>班级</dt><dd>{{ student.class_name || '—' }}</dd>
          <dt>专业/年级</dt><dd>{{ student.major_name || '—' }} · {{ student.grade_name || '—' }}</dd>
          <dt>政治面貌</dt><dd>{{ student.political_status || '—' }}</dd>
          <dt>身份证</dt><dd>{{ printIdCard }}</dd>
          <dt>电话</dt><dd>{{ printPhone }}</dd>
          <dt>生源地</dt><dd>{{ student.birth_source || '—' }}</dd>
          <dt>校区/宿舍</dt><dd>{{ student.campus || '—' }} · {{ student.dorm_building || '—' }} · {{ student.dorm_room || '—' }}</dd>
        </dl>
      </section>

      <section v-if="pdfFields.includes('academic')">
        <h2>B 学业总览</h2>
        <p>预警状态：<b>{{ warningLabel }}</b></p>
        <p v-if="summary?.stats?.gpa">GPA / 平均分：{{ summary.stats.gpa }}</p>
        <p v-else>成绩数据待完善</p>
      </section>

      <section v-if="pdfFields.includes('party')">
        <h2>C 党团进度</h2>
        <p>当前阶段：<b>{{ summary?.party_stage || student.political_status || '—' }}</b></p>
      </section>

      <section v-if="pdfFields.includes('psych')">
        <h2>D 心理等级</h2>
        <p>{{ summary?.psych_status === 'attention' ? '有谈心/关注记录' : '暂无关注记录' }}</p>
      </section>

      <section v-if="pdfFields.includes('aid')">
        <h2>E 资助情况</h2>
        <p>困难等级：{{ summary?.hardship_level || '无' }}</p>
      </section>

      <section v-if="pdfFields.includes('family')">
        <h2>F 家庭联络</h2>
        <p>家长电话：{{ printParent }}</p>
      </section>

      <section v-if="pdfFields.includes('employment')">
        <h2>G 就业意向</h2>
        <p>就业状态：{{ summary?.employment_status || '未登记' }}</p>
      </section>

      <section v-if="pdfFields.includes('status')">
        <h2>H 学籍异动</h2>
        <p>完整时间线请查看学生 360 · 时间线标签</p>
      </section>

      <footer class="print-footer">辅导员工作平台 · 由 air 生成</footer>
    </div>

  </div>
</template>

<script setup>
import { ArrowLeft as _InlineArrowLeft } from '@element-plus/icons-vue'
import { useRouter as _useRouterInline } from 'vue-router'
const _routerInline = _useRouterInline()
function inlineGoBack() {
  if (window.history.length > 1) _routerInline.back()
  else _routerInline.push('/dashboard')
}
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

const sid = computed(() => {
  const raw = route.params.id
  if (raw === undefined || raw === null || raw === 'undefined' || raw === '') return NaN
  const n = Number(raw)
  return Number.isNaN(n) ? NaN : n
})
const student = ref(null)
const summary = ref(null)
const loading = ref(false)
const activeTab = ref('basic')
const pdfDialog = ref(false)
const pdfFields = ref(['basic','academic','party','psych','aid','family','employment','status'])
const pdfMask = ref(true)
const nowStr = new Date().toLocaleString()

const maskCenter = (str, keepStart = 3, keepEnd = 4) => {
  if (!str) return '—'
  if (!pdfMask.value) return str
  if (str.length <= keepStart + keepEnd) return str
  return str.slice(0, keepStart) + '*'.repeat(str.length - keepStart - keepEnd) + str.slice(-keepEnd)
}
const printIdCard = computed(() => maskCenter(student.value?.id_card, 6, 4))
const printPhone  = computed(() => maskCenter(student.value?.phone, 3, 4))
const printParent = computed(() => maskCenter(student.value?.parent_phone, 3, 4))

function onOpenPdf() {
  pdfDialog.value = true
}

function onDoPrint() {
  pdfDialog.value = false
  // 等 DOM 更新完再打印
  setTimeout(() => {
    document.body.classList.add('printing-s360')
    window.print()
    document.body.classList.remove('printing-s360')
  }, 150)
}

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

const maskedIdCard = computed(() => {
  const v = student.value?.id_card || ''
  if (!v || v.length < 10) return '—'
  return v.slice(0, 6) + '********' + v.slice(-4)
})
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

// ---- 信息完整度 ----
const completeness = ref(null)
const completenessDialog = ref(false)
const completenessClass = computed(() => {
  const lv = completeness.value?.level
  if (lv === 'excellent') return 'green'
  if (lv === 'good') return 'green'
  if (lv === 'warning') return 'yellow'
  if (lv === 'poor') return 'red'
  return 'gray'
})
async function loadCompleteness() {
  try {
    completeness.value = await getStudentCompleteness(sid.value)
  } catch (e) {
    completeness.value = null
  }
}

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
    loadCompleteness()
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
    // StudentUpdate schema 支持的字段
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
      id_card: basicForm.value.id_card || '',
      campus: basicForm.value.campus || '',
      dorm_building: basicForm.value.dorm_building || '',
      dorm_room: basicForm.value.dorm_room || '',
      is_off_campus: !!basicForm.value.is_off_campus,
      off_campus_address: basicForm.value.off_campus_address || '',
      notes: basicForm.value.notes
    }
    await updateBasic(sid.value, payload)
    ElMessage.success('保存成功')
    basicDialog.value = false
    await loadHeader()
    await loadCompleteness()
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

.inline-back-bar {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 4px 6px 4px;
  border-bottom: 1px dashed rgba(74, 122, 140, .18);
  margin-bottom: 12px;
}
.back-inline-btn {
  color: #4A7A8C;
  padding: 4px 12px;
  border-radius: 8px;
  background: rgba(74, 122, 140, .08);
  font-size: 14px;
}
.back-inline-btn:hover { background: rgba(74, 122, 140, .18); }
.inline-title { color: #666; font-size: 13px; }

#s360-print-area { display: none; }
@media print {
  body.printing-s360 * { visibility: hidden !important; }
  body.printing-s360 #s360-print-area,
  body.printing-s360 #s360-print-area * { visibility: visible !important; }
  #s360-print-area {
    display: block !important;
    position: absolute; left: 0; top: 0; width: 100%;
    padding: 24mm 18mm; background: #fff; color: #000;
    font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', sans-serif;
  }
  #s360-print-area h1 { font-size: 20px; margin: 0 0 6px; }
  #s360-print-area h2 { font-size: 14px; margin: 14px 0 6px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
  #s360-print-area .print-meta { color: #666; font-size: 12px; margin-bottom: 12px; }
  #s360-print-area dl { display: grid; grid-template-columns: 90px 1fr 90px 1fr; row-gap: 4px; column-gap: 12px; font-size: 12px; }
  #s360-print-area dt { color: #666; }
  #s360-print-area dd { margin: 0; color: #000; }
  #s360-print-area section { margin-bottom: 8px; }
  #s360-print-area p { font-size: 12px; margin: 4px 0; }
  #s360-print-area .print-footer { position: fixed; bottom: 10mm; left: 18mm; right: 18mm; text-align: center; color: #999; font-size: 10px; }
  @page { size: A4; margin: 0; }
}
.pdf-preview-hint { color: #909399; font-size: 12px; margin-top: -8px; margin-bottom: 8px; }
</style>
