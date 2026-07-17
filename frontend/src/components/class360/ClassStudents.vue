<template>
  <div>
    <!-- 班主任 + 班干部联系方式 -->
    <el-card v-if="contacts" shadow="never" class="contact-card">
      <div class="contact-title">📞 班主任 &amp; 班干部联系方式</div>
      <div class="contact-row">
        <span class="contact-item" v-if="contacts.class_teacher?.name">
          <el-tag type="success" size="small" effect="dark">班主任</el-tag>
          <b>{{ contacts.class_teacher.name }}</b>
          <span v-if="contacts.class_teacher.phone"> · 📱 {{ contacts.class_teacher.phone }}</span>
        </span>
        <span class="contact-item" v-if="contacts.monitor?.name">
          <el-tag type="primary" size="small" effect="dark">班长</el-tag>
          <b>{{ contacts.monitor.name }}</b>
          <span v-if="contacts.monitor.phone"> · 📱 {{ contacts.monitor.phone }}</span>
        </span>
        <span class="contact-item" v-if="contacts.league_secretary?.name">
          <el-tag type="warning" size="small" effect="dark">团支书</el-tag>
          <b>{{ contacts.league_secretary.name }}</b>
          <span v-if="contacts.league_secretary.phone"> · 📱 {{ contacts.league_secretary.phone }}</span>
        </span>
        <span class="contact-item" v-for="c in otherCadres" :key="c.student_id + c.position">
          <el-tag type="info" size="small" effect="plain">{{ c.position }}</el-tag>
          <b>{{ c.name }}</b>
          <span v-if="c.phone"> · 📱 {{ c.phone }}</span>
        </span>
        <span v-if="!hasContacts" class="contact-empty">暂无班干部信息（请到"三级架构"里为班级配置班主任、班长、团支书）</span>
      </div>
    </el-card>

    <div class="panel-head">
      <div><span class="title">📋 班级花名册</span><span class="text-muted count">&nbsp;共 {{ rows.length }} 人</span></div>
      <div>
        <el-input v-model="kw" size="small" placeholder="按姓名/学号/电话过滤..." clearable style="width:220px">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="filtered" border stripe size="small" height="520">
      <el-table-column type="index" width="55" label="#" />
      <el-table-column prop="student_no" label="学号" width="130" />
      <el-table-column prop="name" label="姓名" min-width="130">
        <template #default="{ row }">
          <span v-if="cadreIcon(row)" :title="(row.cadre_positions || []).join('、')" class="cadre-icon">{{ cadreIcon(row) }}</span>
          <router-link :to="`/students/${row.id}`" class="link" :class="{ 'is-cadre': (row.cadre_positions || []).length }">{{ row.name }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="gender" label="性别" width="70" />
      <el-table-column prop="political_status" label="政治面貌" min-width="120" />
      <el-table-column label="班干部职务" min-width="180">
        <template #default="{ row }">
          <el-tag
            v-for="pos in (row.cadre_positions || [])"
            :key="pos"
            :type="cadreTagType(pos)"
            size="small"
            effect="dark"
            round
            style="margin:0 4px 2px 0; font-weight:600"
          >{{ cadreIconOf(pos) }} {{ pos }}</el-tag>
          <span v-if="!(row.cadre_positions?.length)" class="text-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="联系电话" min-width="130" />
      <el-table-column prop="parent_phone" label="家长电话" min-width="130" />
      <el-table-column prop="warning_status" label="学业预警" width="100">
        <template #default="{ row }">
          <span class="status-chip" :class="row.warning_status">
            <span class="status-dot" :class="row.warning_status" />
            {{ warnLabel(row.warning_status) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="$router.push(`/students/${row.id}`)">
            360
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getClassStudents, getClassContacts } from '@/api/class360.js'

const props = defineProps({ cid: { type: Number, required: true } })
const rows = ref([])
const loading = ref(false)
const kw = ref('')

const filtered = computed(() => {
  if (!kw.value) return rows.value
  const k = kw.value.toLowerCase()
  return rows.value.filter(r =>
    (r.name || '').toLowerCase().includes(k) ||
    (r.student_no || '').includes(k) ||
    (r.phone || '').includes(k)
  )
})

function warnLabel(s) {
  if (s === 'red') return '红灯'
  if (s === 'yellow') return '黄灯'
  return '绿灯'
}

// 班干部职务 → 图标 / tag 颜色
function cadreIconOf(pos) {
  if (!pos) return ''
  if (pos.includes('班长')) return '👑'
  if (pos.includes('团支书') || pos.includes('团支部')) return '🎗️'
  if (pos.includes('学习')) return '📘'
  if (pos.includes('生活')) return '🏠'
  if (pos.includes('文艺')) return '🎨'
  if (pos.includes('体育')) return '🏃'
  if (pos.includes('宣传')) return '📢'
  if (pos.includes('心理')) return '💗'
  if (pos.includes('组织')) return '🧩'
  if (pos.includes('纪律')) return '⚖️'
  return '⭐'
}
function cadreTagType(pos) {
  if (!pos) return 'info'
  if (pos.includes('班长')) return 'danger'          // 班长 - 红（最突出）
  if (pos.includes('团支书') || pos.includes('团支部')) return 'warning'  // 团支书 - 橙
  if (pos.includes('学习')) return 'primary'
  if (pos.includes('心理')) return 'danger'
  return 'success'
}
// 学生首要职务图标：班长 > 团支书 > 其他
function cadreIcon(row) {
  const list = row.cadre_positions || []
  if (!list.length) return ''
  const priority = ['班长', '团支书', '学习', '生活', '文艺', '体育', '宣传', '心理', '组织', '纪律']
  for (const key of priority) {
    const hit = list.find(p => p.includes(key))
    if (hit) return cadreIconOf(hit)
  }
  return '⭐'
}

const contacts = ref(null)
const hasContacts = computed(() => {
  const c = contacts.value
  if (!c) return false
  return !!(c.class_teacher?.name || c.monitor?.name || c.league_secretary?.name || (c.cadres || []).length)
})
const otherCadres = computed(() => {
  const c = contacts.value
  if (!c) return []
  const skip = new Set([c.monitor?.name, c.league_secretary?.name].filter(Boolean))
  return (c.cadres || []).filter(x => !skip.has(x.name))
})

async function load() {
  if (!props.cid || Number.isNaN(Number(props.cid))) return
  loading.value = true
  try {
    const [stu, con] = await Promise.all([
      getClassStudents(props.cid),
      getClassContacts(props.cid).catch(() => null)
    ])
    rows.value = stu || []
    contacts.value = con
  } finally { loading.value = false }
}

watch(() => props.cid, load, { immediate: false })
onMounted(load)
</script>

<style scoped>
.panel-head { display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px; }
.panel-head .title { font-weight: 600; color: var(--color-sidebar-active); font-size: 15px; }
.panel-head .count { font-size: 12px; }
.panel-head > div:last-child { display:flex; gap: 8px; }
.link { color: var(--color-sidebar); font-weight: 500; }
.contact-card { margin-bottom: 12px; border-radius: 12px; background: #F5F7F9; }
.contact-title { font-weight: 600; color: #4A7A8C; margin-bottom: 8px; }
.contact-row { display: flex; flex-wrap: wrap; gap: 12px 20px; font-size: 13px; color: #303133; }
.contact-item { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; background: #ffffff; border-radius: 10px; border: 1px solid #E4E7ED; }
.contact-empty { color: #909399; font-size: 13px; }
.text-muted { color: #C0C4CC; }
.cadre-icon {
  display: inline-block;
  margin-right: 4px;
  font-size: 14px;
  vertical-align: -1px;
}
.link.is-cadre {
  color: #C7503C;
  font-weight: 700;
  border-bottom: 2px dashed rgba(199, 80, 60, 0.35);
}
</style>
