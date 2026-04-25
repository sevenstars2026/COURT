# ⚖️ Courtroom Collaboration System

**庭审式 Agent 协作框架**

一个基于法庭庭审隐喻的 Agent 协作系统，用结构化辩论替代传统消息队列，实现高质量的决策制定。

## 核心理念

```
提交动议 → 立案 → 证据收集 → 开庭辩论 → 陪审团裁决 → 法官判决 → 执行
```

用法庭司法流程来评审代码变更、架构决策和设计方案，确保每个重大决策都经过充分的对抗式辩论。

## 角色

| 角色 | 职责 |
|------|------|
| 👨‍⚖️ **法官** (Judge) | 主持庭审，做出最终判决 |
| 👮 **检察官** (Prosecutor) | 提交动议，论证变更的必要性 |
| 🛡️ **辩护律师** (Defender) | 质疑提案，发现潜在问题 |
| 👥 **陪审团** (Jury) | 多模型投票，提供多元视角 |
| 📝 **书记员** (Court Reporter) | 生成庭审记录 |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 交互式示例
python courtroom_example.py

# 提交动议
python courtroom_cli.py file-motion \
  --title "添加 Redis 缓存层" \
  --type "performance" \
  --description "为热点查询添加缓存，提升响应速度" \
  --changes "集成 Redis 客户端" "添加缓存逻辑" \
  --files "backend/services/cache_service.py" \
  --risks "缓存一致性问题" \
  --benefits "响应时间减少 80%"

# 开庭审理
python courtroom_cli.py trial --case-id case_20260425_120000

# 查看判决
python courtroom_cli.py show-verdict --case-id case_20260425_120000

# 启动 Web UI
python courtroom_web.py
# 访问 http://localhost:5000
```

## 项目结构

```
courtroom/
├── courtroom/                  # 核心系统包
│   ├── court.py               # 法庭主控制器
│   ├── schemas.py             # 数据结构定义
│   ├── evidence.py            # 证据管理系统
│   ├── executor.py            # 判决自动执行器
│   ├── contract.py            # 契约验证系统
│   ├── llm_client.py          # Claude API 客户端
│   ├── memory.py              # 分层记忆系统
│   ├── multi_jury.py          # 多模型陪审团
│   ├── precedent_evolution.py # 判例演化系统
│   ├── scheduler.py           # 并行预审系统
│   ├── economics_dashboard.py # 经济驾驶舱
│   ├── agents/                # Agent 角色实现
│   │   ├── judge.py / judge_llm.py
│   │   ├── prosecutor.py / prosecutor_llm.py
│   │   ├── defender.py / defender_llm.py
│   │   ├── jury.py
│   │   └── court_reporter.py
│   ├── web/                   # Web UI 资源
│   │   ├── templates/index.html
│   │   └── static/style.css, app.js
│   ├── cases/                 # 案件数据
│   ├── verdicts/              # 判决书
│   ├── transcripts/           # 庭审记录
│   ├── evidence/              # 证据文件
│   ├── precedents/            # 判例库
│   └── summaries/             # 案件摘要
│
├── courtroom_cli.py           # 命令行工具
├── courtroom_example.py       # 交互式示例
├── courtroom_web.py           # Flask Web 服务器
│
├── test_courtroom.py          # 基础测试
├── test_evidence.py           # 证据系统测试
├── test_multi_jury.py         # 陪审团测试
├── test_precedent.py          # 判例测试
├── test_scheduler.py          # 调度器测试
├── test_memory.py             # 记忆系统测试
├── test_contract.py           # 契约测试
├── test_dashboard.py          # 仪表板测试
│
├── COURTROOM_GUIDE.md         # 快速开始指南
├── COURTROOM_IMPLEMENTATION_REPORT.md  # 实现报告
├── WORK_SUMMARY_COURTROOM.md  # 工作总结
├── requirements.txt           # Python 依赖
└── README.md                  # 本文件
```

## 动议类型

| 类型 | 说明 |
|------|------|
| `new_feature` | 新功能提案 |
| `refactor` | 代码重构 |
| `bug_fix` | Bug 修复 |
| `architecture` | 架构变更 |
| `security` | 安全改进 |
| `performance` | 性能优化 |

## 工作流程详解

1. **检察官**提交动议，包括标题、描述、变更清单、风险/收益分析
2. **法官**审查立案，分配给**辩护律师**准备反驳
3. 双方通过**证据系统**提交材料（代码、测试、文档等）
4. **开庭辩论**（多轮交叉辩论）
5. **陪审团**从多个角度评估并投票
6. **法官**综合所有意见做出**判决**
7. **书记员**生成完整的庭审记录和判决书

## 特性

- 🎭 **对抗式辩论** — 自动发现提案中的问题
- 🤖 **LLM 增强** — 可选 Claude API 实现智能辩论
- 📎 **完整证据管理** — 9 种证据类型
- 🌐 **Web UI** — Flask 可视化界面
- ⚙️ **自动执行** — 判决可直接转化为变更
- 📚 **判例演化** — 历史判决影响未来决策
- 👥 **多模型陪审团** — 多模型交叉验证
- 🧠 **分层记忆** — 短期/长期记忆管理

## 独立运行

本项目完全独立，不依赖 Oasis 或其他项目，可作为通用 Agent 协作框架使用。
