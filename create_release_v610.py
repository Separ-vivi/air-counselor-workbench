#!/usr/bin/env python3
"""
GitHub Release v6.10 创建脚本
功能：谈心记录AI摘要 + Dashboard智能预警
"""
import subprocess
import sys

TAG = "v6.10"
TITLE = "V6.10 - AI 智能摘要 & 智能预警"
NOTES = """## ✨ 新增功能

### 🧠 谈心记录 AI 摘要
- 访谈详情对话框新增 **AI 智能摘要** 区域
- 一键生成结构化分析：情绪状态、问题类型、跟进建议、谈话摘要
- 摘要结果自动缓存，避免重复调用 LLM
- 符合冰蓝薄荷色系 UI 设计

### 🚨 Dashboard 智能预警
- Dashboard 新增 **AI 智能预警** 卡片
- 规则引擎自动识别 5 类风险：成绩预警、缺勤过多、心理关注、纪律处分、访谈待跟进
- LLM 增强分析：AI 给出优先级排序和工作建议
- 点击预警学生可跳转到 Student360 查看详情
- 数据缓存 1 小时，高性能

## 🔧 技术改进
- 新增后端接口：`POST /api/interview/{id}/ai-summary`、`GET /api/dashboard/ai-warnings`
- StudentInterview 模型新增 `ai_summary` 字段（AI 摘要缓存）
- 使用现有 LLMAdapter（DeepSeek V4-Flash），单次成本 < 0.01 元
- LLM 未配置时自动降级，不影响现有功能

## 📦 包说明
- **完整包**：`air-counselor-workbench-v6.10-full.zip` - 全新部署
- **增量包**：`air-counselor-workbench-v6.10-delta.zip` - 从 V6.9 升级

## ⬆️ 升级步骤
1. 备份数据库（data/*.db）
2. 解压增量包，覆盖对应文件
3. 重启后端（数据库自动迁移）
4. （可选）在系统设置中配置 LLM API Key

---
*由 AI 辅助开发，辅导员工作平台 V6.10*
"""

# Run git commands
def run(cmd):
    print(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr.strip()}")
    else:
        print(f"  OK: {result.stdout.strip()}")
    return result.returncode == 0

# Tag
run(f'git tag -d {TAG}')  # Remove if exists
run(f'git add -A')
run(f'git commit -m "V6.10: AI 谈心摘要 + Dashboard 智能预警"')
run(f'git tag -a {TAG} -m "{TITLE}"')

print(f"\n✅ Release {TAG} created locally")
print(f"To push: git push origin main --tags")
print(f"\nRelease notes:\n{NOTES[:200]}...")
