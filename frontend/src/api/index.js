/**
 * axios 实例 · 全局 HTTP 客户端
 * - baseURL: /api（Vite 代理透传到后端）
 * - 全局关闭 GET 缓存（air 强验收：搜索/下拉不允许任何缓存）
 * - 401/500 统一 Message 提示
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',
  timeout: 20000,
  // 全局关闭浏览器 GET 缓存
  headers: {
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
  }
})

// 请求拦截器：GET 请求追加时间戳（彻底防止 axios/浏览器缓存）
http.interceptors.request.use((config) => {
  if ((config.method || 'get').toLowerCase() === 'get') {
    config.params = { ...(config.params || {}), _t: Date.now() }
  }
  return config
})

// 响应拦截器
http.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    const status = err?.response?.status
    const detail = err?.response?.data?.detail || err?.response?.data?.message || err.message
    if (status === 422) {
      ElMessage.error('参数校验失败：' + (typeof detail === 'string' ? detail : JSON.stringify(detail)))
    } else if (status === 404) {
      ElMessage.error('资源不存在（404）')
    } else if (status === 500) {
      ElMessage.error('服务器内部错误（500），请稍后重试')
    } else if (status) {
      ElMessage.error(`请求失败 [${status}]：${detail || '未知错误'}`)
    } else {
      ElMessage.error('网络异常，请检查后端是否运行')
    }
    return Promise.reject(err)
  }
)

export default http
