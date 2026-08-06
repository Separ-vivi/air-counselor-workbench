/**
 * mitt 事件总线 · 用于全局搜索面板打开等跨组件通信
 * air 前端已有 mitt 依赖；若无，可等价用简单 EventEmitter
 */
import mitt from 'mitt'
export default mitt()
