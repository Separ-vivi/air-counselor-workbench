/**
 * 通用文件下载工具
 * v3j-B-b02 · 全站批量导出复用
 */

/**
 * 触发 blob 下载
 * @param {Blob|ArrayBuffer} blob - 后端返回的二进制数据
 * @param {string} filename - 下载文件名（含扩展名）
 */
export function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob instanceof Blob ? blob : new Blob([blob]))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * 生成带时间戳的文件名
 * @param {string} baseName - 基础名（不含扩展名）
 * @param {string} ext - 扩展名（默认 xlsx）
 */
export function stampedName(baseName, ext = 'xlsx') {
  const d = new Date()
  const stamp = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return `${baseName}_${stamp}.${ext}`
}
