<template>
  <div class="sys-settings">
    <div class="page-header">
      <h2>系统设置 · 数据管理</h2>
      <el-button :icon="Refresh" @click="loadHealth" :loading="loadingHealth">刷新健康状态</el-button>
    </div>


    <!-- V5-B AI 配置 -->
    <el-card shadow="hover" class="section-card llm-card">
      <template #header>
        <div class="card-header">
          <span>🤖 AI 配置（知识库问答）</span>
          <el-tag v-if="llmSaved" type="success" size="small" round>已保存</el-tag>
        </div>
      </template>
      <el-form :model="llmForm" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="API Key">
              <el-input
                v-model="llmForm.api_key"
                placeholder="sk-xxxxxxxxxxxxxxxx"
                type="password"
                show-password
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Base URL">
              <el-input v-model="llmForm.base_url" placeholder="https://api.deepseek.com" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="模型名称">
              <el-input v-model="llmForm.model" placeholder="deepseek-chat" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="显示名">
              <el-input v-model="llmForm.model_name" placeholder="DeepSeek V3" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" @click="onSaveLlm" :loading="llmSaving">💾 保存配置</el-button>
          <el-button @click="onTestLlm" :loading="llmTesting" :disabled="!llmSaved">🔌 测试连通</el-button>
          <el-button link type="info" @click="llmShowHelp = true">怎么用？</el-button>
        </el-form-item>
        <el-form-item v-if="llmTestResult">
          <el-alert
            :type="llmTestResult.ok ? 'success' : 'error'"
            :closable="false"
            show-icon
          >
            <template #title>{{ llmTestResult.message }}</template>
          </el-alert>
        </el-form-item>
      </el-form>
      <el-divider />
      <div class="llm-hint">
        💡 目前支持任何兼容 OpenAI 协议的接口：DeepSeek / OpenAI / 本地 Ollama / 中转站
        <br>DeepSeek 注册地址：<a href="https://platform.deepseek.com" target="_blank" style="color:#5B92E5">https://platform.deepseek.com</a>
        ；最低充值 ¥10，约可支持几千次问答
      </div>
    </el-card>

        <!-- 数据库健康检查 -->
    <el-card shadow="hover" class="section-card">
      <template #header>
        <div class="card-header">
          <span>🩺 数据库健康检查</span>
          <el-tag v-if="health?.ok" type="success" size="small">正常</el-tag>
          <el-tag v-else-if="health" type="danger" size="small">异常</el-tag>
        </div>
      </template>
      <div v-if="loadingHealth" v-loading="loadingHealth" style="height: 120px" />
      <div v-else-if="health">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-statistic title="学生总数" :value="health.counts?.students || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="班级数" :value="health.counts?.classes || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="成绩记录" :value="health.counts?.grades || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="业务记录合计" :value="health.counts?.total_business || 0" />
          </el-col>
        </el-row>
        <el-divider />
        <div v-if="health.schema_issues && health.schema_issues.length">
          <el-alert type="warning" show-icon :closable="false">
            <template #title>发现 {{ health.schema_issues.length }} 处 schema 漂移</template>
            <div>
              <div v-for="(issue, i) in health.schema_issues" :key="i">- {{ issue }}</div>
            </div>
          </el-alert>
        </div>
        <div v-else>
          <el-alert type="success" show-icon :closable="false" title="所有表结构与 model 一致" />
        </div>
        <div v-if="health.db_path" style="color:#909399; font-size:12px; margin-top:8px">
          数据库路径：{{ health.db_path }}
        </div>
      </div>
      <el-empty v-else description="尚未加载" />
    </el-card>

    <!-- 一键操作 -->
    <el-card shadow="hover" class="section-card">
      <template #header>
        <div class="card-header">
          <span>🚀 一键操作</span>
          <el-tag type="danger" size="small">高风险</el-tag>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="8">
          <el-card shadow="never" class="op-card">
            <div class="op-title">🌱 生成 300+ 全域测试数据</div>
            <div class="op-desc">
              一键生成 48 班 × 336+ 学生，覆盖所有 20+ 侧边栏功能。用于新环境快速测试。
              <br><b style="color:#e6a23c">已有数据不会被删除，会追加。</b>
            </div>
            <el-button type="primary" @click="onSeedLarge" :loading="loadingSeed">生成测试数据</el-button>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never" class="op-card">
            <div class="op-title">🧹 清空业务数据</div>
            <div class="op-desc">
              清空所有业务数据（学生/成绩/预警/活动/心理/家校/记事/校历 + 年级/专业/班级）。仅保留 系统设置。
              <br><b style="color:#f56c6c">此操作不可逆，请先备份。</b>
            </div>
            <el-button type="warning" @click="onClearBusiness" :loading="loadingClear">清空业务数据</el-button>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never" class="op-card">
            <div class="op-title">💥 一键重建数据库</div>
            <div class="op-desc">
              删除所有表并重建为【空数据库】，不灌演示数据。如需 300+ 演示学生，请另点"生成测试数据"。
              <br><b style="color:#f56c6c">此操作不可恢复！</b>
            </div>
            <el-button type="danger" @click="onReinit" :loading="loadingReinit">重建数据库</el-button>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 备份与恢复 -->
    <el-card shadow="hover" class="section-card">
      <template #header>
        <div class="card-header">
          <span>💾 备份与恢复</span>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card shadow="never" class="op-card">
            <div class="op-title">📥 下载数据库备份</div>
            <div class="op-desc">
              下载完整的 SQLite 数据库文件（.db），可离线保存或迁移到其他环境。
            </div>
            <el-button type="success" @click="onBackup">下载备份 (.db)</el-button>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never" class="op-card">
            <div class="op-title">📤 上传恢复</div>
            <div class="op-desc">
              上传之前的 .db 备份文件恢复数据。
              <br><b style="color:#f56c6c">当前数据会被覆盖！</b>
            </div>
            <el-upload
              :show-file-list="false"
              :before-upload="onRestoreBefore"
              :http-request="onRestore"
              accept=".db"
            >
              <el-button type="warning">选择 .db 文件恢复</el-button>
            </el-upload>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { system } from '@/api/modules'

const health = ref(null)
const loadingHealth = ref(false)
const llmForm = ref({ api_key: '', base_url: 'https://api.deepseek.com', model: 'deepseek-chat', model_name: 'DeepSeek V3' })
const llmSaving = ref(false)
const llmSaved = ref(false)
const llmTesting = ref(false)
const llmTestResult = ref(null)
const llmShowHelp = ref(false)
const loadingSeed = ref(false)
const loadingClear = ref(false)
const loadingReinit = ref(false)

async function loadLlm() {
  try {
    const r = await system.llmGet()
    if (r && typeof r === 'object') {
      if (r.base_url) llmForm.value.base_url = r.base_url
      if (r.model) llmForm.value.model = r.model
      if (r.model_name) llmForm.value.model_name = r.model_name
      if (r.api_key_masked) {
        // 有保存过的 key，保留 placeholder 提示
        llmForm.value.api_key = r.api_key_masked
        llmSaved.value = true
      }
    }
  } catch (e) {
    console.warn('loadLlm err', e)
  }
}

async function onSaveLlm() {
  llmSaving.value = true
  llmTestResult.value = null
  try {
    await system.llmUpdate(llmForm.value)
    ElMessage.success('✅ AI 配置已保存')
    llmSaved.value = true
    await loadLlm()
  } catch (e) {
    ElMessage.error('保存失败：' + (e?.message || e))
  } finally {
    llmSaving.value = false
  }
}

async function onTestLlm() {
  llmTesting.value = true
  llmTestResult.value = null
  try {
    const r = await system.llmTest()
    llmTestResult.value = {
      ok: r?.ok === true,
      message: r?.ok ? `✅ 连通成功 · 模型：${r.model || llmForm.value.model}` : `❌ ${r?.error || '连通失败'}`,
    }
  } catch (e) {
    llmTestResult.value = {
      ok: false,
      message: '❌ 测试失败：' + (e?.response?.data?.detail || e?.message || e),
    }
  } finally {
    llmTesting.value = false
  }
}

async function loadHealth() {
  loadingHealth.value = true
  try {
    health.value = await system.health()
  } catch (e) {
    ElMessage.error('健康检查失败：' + (e?.message || e))
  } finally {
    loadingHealth.value = false
  }
}

async function onSeedLarge() {
  try {
    await ElMessageBox.confirm(
      '确认生成 300+ 学生 + 全域测试数据？此操作会向数据库追加大量记录。',
      '生成测试数据',
      { type: 'warning' }
    )
  } catch { return }
  loadingSeed.value = true
  try {
    const res = await system.seedLarge()
    // 后端识别到已有学生数据 → 引导 air 走"重建数据库"或强制追加
    if (res?.need_confirm) {
      loadingSeed.value = false
      try {
        await ElMessageBox.confirm(
          res.message || `数据库已有 ${res.student_count} 名学生。追加会尝试补齐到 300+（撞学号会跳过）。要完全清空重来请先点"清空业务数据"或"重建数据库"。`,
          '已有数据',
          { type: 'warning', confirmButtonText: '继续追加', cancelButtonText: '取消（改用重建）' }
        )
      } catch { return }
      loadingSeed.value = true
      const res2 = await system.seedLarge(true)
      const added2 = res2?.stats?.students || res2?.stats?.count || 0
      ElMessage.success(`✅ 追加完成 · 新增 ${added2} 学生`)
      await loadHealth()
      return
    }
    const added = res?.stats?.students || res?.stats?.count || 0
    ElMessage.success(`✅ 生成完成 · 新增 ${added} 学生`)
    await loadHealth()
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || e
    ElMessage.error('生成失败：' + detail)
    console.error('seedLarge error:', e)
  } finally {
    loadingSeed.value = false
  }
}

async function onClearBusiness() {
  try {
    await ElMessageBox.confirm(
      '将清空【所有业务数据】：学生、成绩、预警、活动、心理、家校、记事、校历倒计时、以及年级/专业/班级组织架构。\n\n仅保留：系统设置。\n\n此操作不可撤销，是否继续？',
      '清空所有业务数据',
      { type: 'warning', confirmButtonText: '确认清空', confirmButtonClass: 'el-button--danger' }
    )
  } catch { return }
  loadingClear.value = true
  try {
    const res = await system.clearBusiness()
    ElMessage.success(`✅ 清空完成：${res?.note || res?.message || 'OK'}`)
    await loadHealth()
  } catch (e) {
    ElMessage.error('清空失败：' + (e?.message || e))
  } finally {
    loadingClear.value = false
  }
}

async function onReinit() {
  try {
    await ElMessageBox.confirm(
      '⚠️ 危险操作：删除所有表并重建为【空数据库】（不灌任何演示数据），仅保留 系统设置。\n\n若需演示数据，重建后请另点"生成测试数据"。\n\n此操作不可撤销，是否继续？',
      '重建数据库',
      { type: 'error', confirmButtonText: '确认重建', confirmButtonClass: 'el-button--danger' }
    )
  } catch { return }
  loadingReinit.value = true
  try {
    const res = await system.reinit()
    // 后端现在返回结构 { ok, stats, holidays, error }
    if (res && res.error) {
      ElMessage.error('重建部分失败：' + res.error)
    } else if (res && res.ok === false) {
      ElMessage.warning('重建完成但 seed 有问题，请查看控制台')
      console.warn('reinit result:', res)
    } else {
      ElMessage.success('✅ 重建完成，当前为空数据库。如需演示数据请点"生成测试数据"')
    }
    // 通知全局 store 重新加载（reinit 后数据库全空，所有页面数据都要刷）
    window.dispatchEvent(new CustomEvent('system-reinit-done'))
    await loadHealth()
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || e
    ElMessage.error('重建失败：' + detail)
    console.error('reinit error:', e)
  } finally {
    loadingReinit.value = false
  }
}

function onBackup() {
  window.open(system.backupUrl(), '_blank')
}

function onRestoreBefore(file) {
  if (!file.name.endsWith('.db')) {
    ElMessage.error('请上传 .db 文件')
    return false
  }
  return true
}

async function onRestore({ file }) {
  try {
    await ElMessageBox.confirm(
      `确认用 ${file.name} 恢复数据库？当前数据会被覆盖！`,
      '恢复数据库',
      { type: 'warning' }
    )
  } catch { return }
  const fd = new FormData()
  fd.append('file', file)
  try {
    const res = await system.restore(fd)
    ElMessage.success(`✅ 恢复完成：${res?.message || 'OK'}`)
    await loadHealth()
  } catch (e) {
    ElMessage.error('恢复失败：' + (e?.message || e))
  }
}

onMounted(() => { loadHealth(); loadLlm() })
</script>

<style scoped>
.sys-settings { padding: 4px 8px; }
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { margin: 0; color: #303133; font-size: 22px; }
.section-card { margin-bottom: 16px; border-radius: 12px; }
.card-header { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.op-card {
  border-radius: 12px;
  background: #fdfaf3;
  height: 100%;
}
.op-title { font-size: 15px; font-weight: 600; margin-bottom: 8px; }
.op-desc { color: #606266; font-size: 13px; line-height: 1.6; margin-bottom: 12px; min-height: 60px; }
.llm-card {
  border: 1px solid #D6E4F5;
  background: linear-gradient(135deg, #F6F9FD, #fff);
}
.llm-hint {
  font-size: 12px; color: #606266; line-height: 1.7;
  background: #F5F7FA; padding: 10px 14px; border-radius: 6px;
}
.llm-hint a { text-decoration: none; }
.llm-hint a:hover { text-decoration: underline; }
</style>
