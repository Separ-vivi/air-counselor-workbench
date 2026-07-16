<template>
  <el-cascader
    v-model="cascaderValue"
    :options="options"
    :props="cascaderProps"
    placeholder="全年级 / 按专业 / 按班级"
    clearable
    filterable
    @change="onChange"
    style="width: 320px"
  />
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useOrgStore } from '@/stores/org.js'
import { useRouter } from 'vue-router'

const orgStore = useOrgStore()
const router = useRouter()

const cascaderProps = {
  checkStrictly: true,
  emitPath: true,
  value: 'value',
  label: 'label',
  children: 'children'
}

/** 组织树 → 级联选项 */
const options = computed(() => {
  return orgStore.orgTree.map(g => ({
    value: `g:${g.id}`,
    label: g.grade_name,
    children: (g.majors || []).map(m => ({
      value: `m:${m.id}`,
      label: m.major_name,
      children: (m.classes || []).map(c => ({
        value: `c:${c.id}`,
        label: `${c.class_name}（${c.student_count || 0}人）`
      }))
    }))
  }))
})

/** 双向绑定的级联值：读 store → 拼数组 */
const cascaderValue = ref([])

function syncFromStore() {
  const v = []
  if (orgStore.filterGradeId) v.push(`g:${orgStore.filterGradeId}`)
  if (orgStore.filterMajorId) v.push(`m:${orgStore.filterMajorId}`)
  if (orgStore.filterClassId) v.push(`c:${orgStore.filterClassId}`)
  cascaderValue.value = v
}
syncFromStore()
watch(
  () => [orgStore.filterGradeId, orgStore.filterMajorId, orgStore.filterClassId],
  syncFromStore
)

function onChange(val) {
  if (!val || !val.length) {
    orgStore.resetFilter()
    return
  }
  let g = null, m = null, c = null
  val.forEach(v => {
    if (typeof v !== 'string') return
    const [type, id] = v.split(':')
    const n = Number(id)
    if (type === 'g') g = n
    else if (type === 'm') m = n
    else if (type === 'c') c = n
  })
  orgStore.setFilter({ gradeId: g, majorId: m, classId: c })

  // 若选到班级层 → 直接进入班级 360
  if (c) {
    router.push(`/classes/${c}`)
  }
}
</script>

<style scoped>
:deep(.el-cascader .el-input__wrapper) {
  background: #F5EFE3;
  border-radius: 12px;
}
</style>
