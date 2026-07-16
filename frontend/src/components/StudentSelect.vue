<template>
  <!--
    学生远程搜索选择器 · V3-A 硬要求 § 6.3.1 + v3j 增强
    - 每次弹出必重新调 API（禁止缓存）
    - remote-method 300ms debounce
    - 支持姓名 / 学号 / 拼音首字母 / 班级名
    - limit=50，避免 400 人时前 20 占满
    - v3j: modelValue 是 id 但 options 里没有时，自动 fetch 该学生
  -->
  <el-select
    :model-value="modelValue"
    filterable
    remote
    reserve-keyword
    clearable
    :remote-method="remoteSearch"
    :remote-show-suffix="true"
    :loading="loading"
    :placeholder="placeholder"
    style="width:100%"
    @update:model-value="v => $emit('update:modelValue', v)"
    @visible-change="onVisibleChange"
  >
    <el-option
      v-for="s in options"
      :key="s.id"
      :label="s.label || `${s.name} (${s.student_no}${s.class_name ? ' · ' + s.class_name : ''})`"
      :value="s.id"
    />
  </el-select>
</template>

<script setup>
import { ref, watch } from 'vue'
import { searchStudents } from '@/api/students.js'
import http from '@/api/index.js'

const props = defineProps({
  modelValue: { type: [Number, String, null], default: null },
  placeholder: { type: String, default: '搜索学号 / 姓名 / 拼音（无缓存实时查）' }
})
defineEmits(['update:modelValue'])

const options = ref([])
const loading = ref(false)
let timer = null

async function fetchIt(q) {
  loading.value = true
  try {
    const data = await searchStudents(q, 50)
    options.value = Array.isArray(data) ? data : (data?.items || [])
  } catch {
    options.value = []
  } finally {
    loading.value = false
  }
}

function remoteSearch(query) {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => fetchIt(query || ''), 300)
}

function onVisibleChange(open) {
  if (open) {
    fetchIt('')
  }
}

/**
 * v3j: 编辑弹窗回显场景 - 传入了 student_id 但当前 options 里没有该学生时
 * 单独 fetch 一次，避免 el-select 退化显示 raw id 数字（如"258"）
 */
async function ensureOptionForId(id) {
  if (!id) return
  if (options.value.find(o => String(o.id) === String(id))) return
  try {
    const s = await http.get(`/students/${id}`)
    if (s && s.id) {
      const label = `${s.name} (${s.student_no}${s.class_name ? ' · ' + s.class_name : ''})`
      options.value = [{
        id: s.id, name: s.name, student_no: s.student_no,
        class_name: s.class_name || '', label,
      }, ...options.value]
    }
  } catch (e) {
    // ignore
  }
}

watch(() => props.modelValue, (v) => { ensureOptionForId(v) }, { immediate: true })
</script>
