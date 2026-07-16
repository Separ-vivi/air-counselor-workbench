<template>
  <!--
    学生远程搜索选择器 · V3-A 硬要求 § 6.3.1
    - 每次弹出必重新调 API（禁止缓存）
    - remote-method 300ms debounce
    - 支持姓名 / 学号 / 拼音首字母 / 班级名
    - limit=50，避免 400 人时前 20 占满
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
import { ref } from 'vue'
import { searchStudents } from '@/api/students.js'

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
  // 300ms 防抖
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => fetchIt(query || ''), 300)
}

/**
 * 打开下拉时：强制重新加载（禁止缓存）
 * air 硬要求：每次弹出新增弹窗时，下拉框必须重新调用后端 API
 */
function onVisibleChange(open) {
  if (open) {
    fetchIt('')
  }
}
</script>
