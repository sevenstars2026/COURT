# ⚖️ 庭审系统 - 完整功能说明

## 📌 项目概述

**庭审系统（Courtroom Collaboration System）** 是一个基于法庭庭审隐喻的 AI Agent 协作框架，用于评审代码变更、架构决策和技术方案。

**核心理念**：用法庭司法流程来确保每个重大决策都经过充分的对抗式辩论，避免单一视角的盲点。

---

## 🎭 角色系统（8 个 Agent）

| 角色 | 图标 | 职责 | 工作模式 |
|------|------|------|----------|
| **检察官** (Prosecutor) | 👨‍⚖️ | 提交动议，论证变更的必要性和收益 | 规则引擎 / API |
| **辩护律师** (Defender) | 👩‍⚖️ | 质疑提案，发现潜在问题和风险 | 规则引擎 / API |
| **法官** (Judge) | ⚖️ | 主持庭审，综合所有意见做出最终判决 | 规则引擎 / API |
| **陪审团** (Jury) | 🗳️ | 多模型投票，提供多元视角 | 规则引擎 / API |
| **书记员** (Court Reporter) | 📝 | 生成庭审记录和判决书 | 规则引擎 |
| **代码分析师** (Code Analyst) | 🔍 | 分析代码质量、复杂度、依赖关系 | 规则引擎 |
| **执行工程师** (Execution Engineer) | ⚙️ | 自动执行判决，应用代码变更 | Claude Code |
| **质量检查员** (QA Inspector) | ✅ | 验证执行结果，决定是否需要重审 | 规则引擎 |

**工作模式说明**：
- **规则引擎**：基于预设规则和模板生成输出（快速、免费、离线可用）
- **API 模式**：调用外部 LLM API（如 OpenAI、DeepSeek、yunwu.ai）进行智能推理
- **Claude Code**：调用 Anthropic 的 Claude Code 工具执行代码变更

---

## 🌐 三种交互方式

### 1️⃣ Web UI（主要方式）

**启动方式**：
```bash
python3 courtroom_web.py
# 访问 http://localhost:5000
```

**功能模块**：

#### 📋 庭审大厅（主界面）
- **Agent 状态栏**：实时显示 8 个 Agent 的工作模式（规则引擎/API/Claude Code）
- **提交动议表单**：
  - 标题（必填）
  - 类型：新功能 / Bug 修复 / 重构 / 性能优化 / 安全 / 架构
  - 优先级：1-10（1=低，10=紧急）
  - 描述（必填）
  - 上传附件：支持 .txt, .md, .json, .py, .js, .java, .yaml, .pdf, .doc 等
- **案件列表**：
  - 显示所有历史案件
  - 每个案件卡片显示：标题、类型、优先级、状态、时间
  - 点击"开始庭审"按钮启动庭审流程
  - 实时显示庭审进度（通过 WebSocket 推送）

#### 💬 自由讨论
- 直接提问，所有 Agent 同时回答
- 不需要走正式庭审流程
- 适合快速咨询、头脑风暴
- 显示 4 个视角：
  - 检察官：方案提出
  - 辩护律师：风险审查
  - 陪审团：专家补充
  - 法官：综合总结

#### 🔌 接入外部 Agent
- **全局 API 配置**：为所有 Agent 统一配置 API
- **单独配置**：为每个 Agent 单独配置不同的 API
- 支持任何 OpenAI 格式的 API：
  - OpenAI (gpt-4, gpt-3.5-turbo)
  - DeepSeek (deepseek-v4-pro)
  - yunwu.ai (gpt-5.4)
  - Ollama（本地部署）
  - vLLM（自建服务）
- 配置项：
  - 模式：规则引擎 / API
  - API URL
  - API Key
  - 模型名称

#### 👤 用户设置
- 用户名配置
- 偏好设置
- 系统配置

---

### 2️⃣ 命令行工具（CLI）

**启动方式**：
```bash
python courtroom_cli.py [命令] [参数]
```

**支持的命令**：

#### 提交动议
```bash
python courtroom_cli.py file-motion \
  --title "添加 Redis 缓存层" \
  --type "performance" \
  --description "为热点查询添加缓存，提升响应速度" \
  --changes "集成 Redis 客户端" "添加缓存逻辑" \
  --files "backend/services/cache_service.py" \
  --risks "缓存一致性问题" \
  --benefits "响应时间减少 80%"
```

#### 开庭审理
```bash
python courtroom_cli.py trial --case-id case_20260425_120000
```

#### 查看判决
```bash
python courtroom_cli.py show-verdict --case-id case_20260425_120000
```

#### 列出所有案件
```bash
python courtroom_cli.py list-cases
```

---

### 3️⃣ Python API（编程集成）

```python
from courtroom.court import Court
from courtroom.schemas import MotionType

# 初始化法庭
court = Court(use_llm=True)  # 启用 LLM 模式

# 提交动议
motion = court.file_motion(
    title="添加 Redis 缓存层",
    motion_type=MotionType.PERFORMANCE,
    description="为热点查询添加缓存",
    proposed_changes=["集成 Redis 客户端"],
    affected_files=["backend/services/cache_service.py"],
    risks=["缓存一致性问题"],
    benefits=["响应时间减少 80%"]
)

# 开庭审理
result = court.trial(motion.case_id, max_rounds=2)

# 查看判决
print(result.verdict.verdict_type)  # approved / rejected / modified
print(result.verdict.reasoning)
```

---

## 🔄 完整庭审流程

### 阶段 1：立案（Filing）
1. 用户提交动议（通过 Web UI / CLI / API）
2. 系统生成唯一案件编号（case_YYYYMMDD_HHMMSS）
3. 保存案件数据到 `courtroom/cases/case_*.json`
4. 状态：`filed`（已立案）

### 阶段 2：证据收集（Discovery）
1. 上传的附件保存到 `courtroom/uploads/`
2. 代码分析师分析相关代码文件
3. 生成证据报告：`courtroom/evidence_report.md`
4. 状态：`discovery`（证据交换中）

### 阶段 3：开庭辩论（Trial）
**实时进度通过 WebSocket 推送到前端**

#### 3.1 检察官开场陈述
- 论证变更的必要性
- 展示预期收益
- 引用证据支持论点

#### 3.2 辩护律师质询
- 质疑提案的风险
- 指出潜在问题
- 提出替代方案

#### 3.3 检察官反驳
- 回应辩护律师的质疑
- 补充论据
- 强化论点

#### 3.4 多轮交叉辩论
- 默认 2 轮辩论
- 可配置最大轮数
- 每轮包含：检察官陈述 → 辩护律师反驳

#### 3.5 陪审团评议
- 多个陪审员独立投票
- 投票选项：赞成 / 反对 / 中立
- 每个陪审员提供投票理由

### 阶段 4：法官判决（Verdict）
1. 法官综合所有论点和陪审团意见
2. 做出最终判决：
   - ✅ **批准** (approved)
   - ❌ **驳回** (rejected)
   - 🔄 **修改后批准** (modified)
   - ⚠️ **有条件批准** (approved_with_modifications)
   - ⏸️ **延期审理** (deferred)
3. 生成判决理由
4. 制定执行计划（如果批准）

### 阶段 5：执行判决（Execution）
**仅在判决为"批准"或"有条件批准"时执行**

1. 执行工程师接收判决
2. 调用 Claude Code 工具执行代码变更
3. 实时推送执行进度
4. 生成执行报告

### 阶段 6：质量检查（QA）
1. QA 检查员验证执行结果
2. 检查项：
   - 是否成功加载 Motion 信息
   - 是否发现设计缺陷
   - 是否需要额外证据
   - 是否应该重审
3. 如果发现问题，自动触发重审

### 阶段 7：重审（Retrial，可选）
- 如果 QA 检查发现问题，自动触发
- 重新走一遍完整庭审流程
- 最多重审 2 次
- 每次重审会参考上次的问题

### 阶段 8：归档（Archive）
1. 生成完整庭审记录：`courtroom/transcripts/transcript_*.json`
2. 生成判决书：`courtroom/verdicts/verdict_*.md`
3. 更新判例库：`courtroom/precedents/`
4. 状态：`verdict`（已判决）

---

## 📊 实时进度显示（WebSocket）

**前端实时接收的进度事件**：

| 阶段代码 | 显示文本 | 说明 |
|---------|---------|------|
| `starting` | 准备开庭... | 初始化阶段 |
| `prosecutor_opening` | 检察官开场陈述 | 检察官论证 |
| `defender_cross` | 辩护律师质询 | 辩护律师质疑 |
| `prosecutor_rebuttal` | 检察官反驳 | 检察官回应 |
| `jury` | 陪审团评议中 | 陪审团投票 |
| `jury_done` | 陪审团投票完成 | 投票结束 |
| `judge` | 法官评议中 | 法官综合判断 |
| `verdict` | 判决: approved/rejected | 判决结果 |
| `execution` | 执行工程师执行中 | 应用变更 |
| `execution_done` | 执行完成 | 执行结束 |
| `qa` | 质量检查中 | QA 验证 |
| `qa_done` | 质量检查完成 | QA 结束 |
| `completed` | 庭审结束 | 全部完成 |

**技术实现**：
- 后端：Flask-SocketIO（threading 模式）
- 前端：Socket.IO 客户端
- 命名空间：`/`（默认）
- 事件名：`trial_progress`
- 数据格式：`{case_id, phase, summary}`

---

## 🗂️ 数据结构

### 动议（Motion）
```json
{
  "case_id": "case_20260425_183845",
  "title": "SNN 加速器 se_driver 乒乓预取优化",
  "motion_type": "performance",
  "description": "优化 SNN 加速器的数据预取机制",
  "proposer": "prosecutor",
  "filed_at": "2026-04-25T18:38:45",
  "status": "filed",
  "proposed_changes": ["修改预取逻辑", "添加乒乓缓冲"],
  "affected_files": ["se_driver.v", "prefetch_ctrl.v"],
  "risks": ["时序可能不满足", "面积增加"],
  "benefits": ["性能提升 30%", "功耗降低 15%"],
  "priority": 7,
  "estimated_effort": "medium",
  "tags": ["hardware", "optimization"]
}
```

### 判决（Verdict）
```json
{
  "case_id": "case_20260425_183845",
  "verdict_type": "approved",
  "reasoning": "经过充分辩论，该优化方案收益明显...",
  "execution_plan": [
    "修改 se_driver.v 第 120-150 行",
    "添加 prefetch_ctrl.v 模块",
    "更新测试用例"
  ],
  "conditions": [],
  "decided_at": "2026-04-25T19:15:30"
}
```

### 庭审记录（Transcript）
```json
{
  "case_id": "case_20260425_183845",
  "motion": { /* Motion 对象 */ },
  "arguments": [
    {
      "speaker": "prosecutor",
      "argument_type": "opening",
      "content": "当前预取机制存在严重性能瓶颈...",
      "evidence_refs": ["perf_report.txt"],
      "timestamp": "2026-04-25T19:00:00"
    },
    {
      "speaker": "defender",
      "argument_type": "rebuttal",
      "content": "该方案可能导致时序违例...",
      "evidence_refs": [],
      "timestamp": "2026-04-25T19:05:00"
    }
  ],
  "jury_votes": [
    {
      "juror": "juror_1",
      "vote": "approve",
      "reasoning": "收益大于风险"
    }
  ],
  "verdict": { /* Verdict 对象 */ },
  "started_at": "2026-04-25T19:00:00",
  "ended_at": "2026-04-25T19:15:30"
}
```

---

## 🔧 配置系统

### API 配置文件：`courtroom/api_settings.json`

```json
{
  "global": {
    "mode": "rule_engine",
    "url": "",
    "api_key": "",
    "model": ""
  },
  "prosecutor": {
    "mode": "api",
    "url": "https://yunwu.ai/v1",
    "api_key": "sk-xxx",
    "model": "gpt-5.4"
  },
  "defender": {
    "mode": "rule_engine",
    "url": "",
    "api_key": "",
    "model": ""
  },
  "judge": {
    "mode": "api",
    "url": "https://api.deepseek.com",
    "api_key": "sk-xxx",
    "model": "deepseek-v4-pro"
  },
  "jury": {
    "mode": "api",
    "url": "https://yunwu.ai/v1",
    "api_key": "sk-xxx",
    "model": "gpt-5.4"
  }
}
```

**配置优先级**：
1. 单独配置（如 `prosecutor.mode`）
2. 全局配置（`global.mode`）
3. 默认值（`rule_engine`）

---

## 📁 文件系统结构

```
courtroom/
├── cases/                    # 案件数据
│   ├── case_20260425_183845.json
│   └── case_20260425_190000.json
├── verdicts/                 # 判决书
│   ├── verdict_20260425_183845.md
│   └── verdict_20260425_190000.md
├── transcripts/              # 庭审记录
│   ├── transcript_20260425_183845.json
│   └── transcript_20260425_190000.json
├── uploads/                  # 上传的附件
│   ├── case_20260425_183845/
│   │   ├── design_doc.pdf
│   │   └── code_snippet.py
│   └── case_20260425_190000/
├── evidence/                 # 证据文件
│   └── evidence_report.md
├── precedents/               # 判例库
│   ├── precedent_001.json
│   └── precedent_002.json
├── summaries/                # 案件摘要
│   └── summary_20260425.md
└── api_settings.json         # API 配置
```

---

## 🎯 核心特性

### 1. 对抗式辩论
- 检察官和辩护律师自动对抗
- 多轮交叉辩论
- 自动发现提案中的问题

### 2. 多模型陪审团
- 支持多个 LLM 模型同时投票
- 提供多元视角
- 降低单一模型的偏见

### 3. 完整证据管理
支持 9 种证据类型：
- 代码文件
- 测试报告
- 性能数据
- 安全审计
- 用户反馈
- 设计文档
- API 文档
- 依赖分析
- 历史记录

### 4. 自动执行
- 判决批准后自动执行
- 调用 Claude Code 工具
- 实时推送执行进度
- 生成执行报告

### 5. 质量检查与重审
- 自动验证执行结果
- 发现问题自动触发重审
- 最多重审 2 次
- 每次重审参考上次问题

### 6. 判例演化
- 历史判决影响未来决策
- 判例库自动更新
- 支持判例检索

### 7. 分层记忆
- 短期记忆：当前庭审上下文
- 长期记忆：历史案件和判例
- 自动记忆管理

### 8. 实时 WebSocket 推送
- 前端实时显示庭审进度
- 无需刷新页面
- 支持多用户同时观看

---

## 🚀 使用场景

### 1. 代码审查
- 提交代码变更动议
- 自动发现潜在问题
- 多角度评估风险
- 自动执行批准的变更

### 2. 架构决策
- 提交架构变更提案
- 对抗式辩论优缺点
- 陪审团多模型投票
- 生成决策记录

### 3. 技术选型
- 提交技术选型动议
- 评估不同方案
- 综合多方意见
- 做出最终决策

### 4. 性能优化
- 提交优化方案
- 评估性能收益
- 分析潜在风险
- 自动应用优化

### 5. 安全审计
- 提交安全改进动议
- 发现安全漏洞
- 评估修复方案
- 自动修复漏洞

---

## 🔌 API 兼容性

支持任何 OpenAI 格式的 API：

### 官方 API
- **OpenAI**: https://api.openai.com/v1
- **Anthropic**: https://api.anthropic.com/v1
- **DeepSeek**: https://api.deepseek.com

### 第三方 API
- **yunwu.ai**: https://yunwu.ai/v1
- **OpenRouter**: https://openrouter.ai/api/v1
- **Together AI**: https://api.together.xyz/v1

### 自建服务
- **Ollama**: http://localhost:11434/v1
- **vLLM**: http://your-server:8000/v1
- **LocalAI**: http://localhost:8080/v1

---

## 📊 性能指标

### 规则引擎模式
- 响应时间：< 1 秒
- 成本：免费
- 质量：基于预设规则

### API 模式
- 响应时间：5-30 秒（取决于 API）
- 成本：按 API 计费
- 质量：高质量智能推理

### 混合模式
- 关键角色用 API（法官、检察官）
- 辅助角色用规则引擎（书记员、代码分析师）
- 平衡成本和质量

---

## 🛠️ 技术栈

### 后端
- **Python 3.8+**
- **Flask**: Web 框架
- **Flask-SocketIO**: WebSocket 支持
- **Pydantic**: 数据验证
- **requests**: HTTP 客户端

### 前端
- **原生 JavaScript**（无框架）
- **Socket.IO 客户端**: WebSocket
- **CSS3**: 样式
- **HTML5**: 结构

### 存储
- **JSON 文件**: 案件、判决、记录
- **Markdown**: 判决书、报告
- **文件系统**: 证据、附件

---

## 🔒 安全性

### API Key 管理
- 存储在 `api_settings.json`
- 不提交到 Git（已加入 .gitignore）
- 支持环境变量覆盖

### 文件上传
- 限制文件类型
- 限制文件大小
- 隔离存储（按案件分目录）

### 代码执行
- 仅在判决批准后执行
- 调用 Claude Code 工具（沙箱环境）
- 生成执行日志

---

## 📈 未来规划

### 短期
- [ ] 支持更多证据类型
- [ ] 优化 WebSocket 性能
- [ ] 添加用户认证
- [ ] 支持多语言

### 中期
- [ ] 分布式部署
- [ ] 数据库存储
- [ ] 高级搜索
- [ ] 数据可视化

### 长期
- [ ] 插件系统
- [ ] 自定义 Agent
- [ ] 机器学习优化
- [ ] 云服务版本

---

## 📞 联系方式

- **项目地址**: /home/sevenstars/CLionProjects/courtroom
- **Web UI**: http://localhost:5000
- **文档**: README.md, COURTROOM_GUIDE.md

---

**最后更新**: 2026-04-26
**版本**: 1.0.0
