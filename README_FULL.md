# ⚖️ Courtroom Collaboration System - 完整工作流程

**庭审式 Agent 协作框架 + 代码执行能力**

## 🎯 核心改进

现在系统不仅能"讨论"，还能**真正执行代码变更**！

### 新增 Agent 角色

| 角色 | 职责 | 工具 |
|------|------|------|
| 🔍 **代码分析师** (Code Analyst) | 庭审前分析代码库，生成技术报告 | Claude Code CLI |
| 🔧 **执行工程师** (Execution Engineer) | 根据判决执行代码变更 | Claude Code CLI + Copilot CLI |
| ✅ **质量检查员** (QA Inspector) | 验证执行结果，失败时触发重审 | pytest + 代码质量检查 |

## 🔄 完整工作流程

```
用户提交需求
  ↓
【代码分析师】分析代码库，生成技术报告
  ├─ 识别相关文件
  ├─ 分析依赖关系
  ├─ 评估复杂度和风险
  └─ 提供实施建议
  ↓
【检察官】基于分析报告提出实施方案
  ↓
【辩护律师】审查方案，指出风险
  ↓
【陪审团 + 法官】判决
  ↓
【执行工程师】执行判决 ⭐ 新增！
  ├─ 调用 Copilot CLI 获取代码建议
  ├─ 调用 Claude Code CLI 执行变更
  ├─ 检测文件变更（git status）
  └─ 运行测试
  ↓
【质量检查员】验证结果 ⭐ 新增！
  ├─ 运行测试套件
  ├─ 代码质量检查
  ├─ 安全检查
  └─ 性能检查
  ↓
如果失败 → 重新开庭（带上错误信息）
如果成功 → 归档完成
```

## 🚀 快速开始

### 1. 基础使用（规则引擎）

```python
from courtroom import Court, MotionType
from pathlib import Path

# 创建法庭（指定代码库路径）
court = Court(
    courtroom_root=Path("./courtroom"),
    codebase_path=Path("./my_game"),  # 你的游戏项目路径
    use_llm=False
)

# 提交动议（自动运行代码分析）
court.file_motion(
    title="为游戏添加存档功能",
    motion_type=MotionType.NEW_FEATURE,
    description="玩家希望能够保存游戏进度",
    proposed_changes=["添加 SaveManager 类", "实现 save/load 方法"],
    affected_files=["game/save_manager.py"],
    run_analysis=True  # 启用代码分析
)

# 开庭审理（自动执行代码变更）
court.trial("case_20260425_120000")
```

### 2. 完整示例

```bash
# 运行完整示例
python courtroom_example_full.py
```

### 3. Web UI

```bash
# 启动 Web 界面
python courtroom_web.py

# 访问 http://localhost:5000
```

## 📁 新增文件

```
courtroom/
├── agents/
│   ├── code_analyst.py          # 代码分析师
│   ├── execution_engineer.py    # 执行工程师
│   └── qa_inspector.py          # 质量检查员
├── analysis_reports/            # 代码分析报告
├── execution_logs/              # 执行日志
└── qa_reports/                  # 质量检查报告
```

## 🔧 集成的 CLI 工具

### Claude Code CLI
- **用途**: 深度代码分析、智能代码生成和修改
- **调用方式**: `claude -p "prompt" --add-dir /path/to/code`
- **能力**: 
  - 理解代码上下文
  - 自动修改多个文件
  - 智能重构

### Copilot CLI
- **用途**: 快速代码建议
- **调用方式**: `copilot -p "prompt" --add-dir /path/to/code`
- **能力**:
  - 快速代码补全
  - 辅助建议

## 🎮 实际应用场景

### 场景 1: 游戏功能开发
```python
court.file_motion(
    title="添加多人联机功能",
    motion_type=MotionType.NEW_FEATURE,
    description="实现 2-4 人本地联机",
    proposed_changes=[
        "添加 MultiplayerManager",
        "实现玩家同步逻辑",
        "添加输入映射"
    ],
    affected_files=["game/multiplayer.py", "game/input_handler.py"]
)
```

### 场景 2: 代码优化
```python
court.file_motion(
    title="优化渲染性能",
    motion_type=MotionType.PERFORMANCE,
    description="游戏在低端设备上帧率过低",
    proposed_changes=[
        "实现对象池",
        "优化碰撞检测",
        "添加 LOD 系统"
    ],
    affected_files=["game/renderer.py", "game/physics.py"]
)
```

### 场景 3: Bug 修复
```python
court.file_motion(
    title="修复存档丢失问题",
    motion_type=MotionType.BUG_FIX,
    description="玩家报告存档偶尔会丢失",
    proposed_changes=[
        "添加存档备份机制",
        "增强错误处理",
        "添加数据校验"
    ],
    affected_files=["game/save_manager.py"]
)
```

## 🔍 执行结果查看

```python
# 查看执行摘要
execution_summary = court.execution_engineer.get_execution_summary(case_id)
print(f"修改文件: {execution_summary['modified_files']}")
print(f"创建文件: {execution_summary['created_files']}")

# 查看质量检查报告
qa_report = court.qa_inspector.get_report(case_id)
print(f"测试结果: {qa_report.test_results}")
print(f"代码质量问题: {qa_report.code_quality_issues}")
```

## ⚙️ 配置选项

```python
court = Court(
    courtroom_root=Path("./courtroom"),
    codebase_path=Path("./my_project"),
    use_llm=False  # True 则使用 Claude API 增强辩论
)

# 提交动议时
court.file_motion(
    ...,
    run_analysis=True  # 是否运行代码分析
)

# 开庭时
court.trial(
    case_id,
    max_rounds=3  # 辩论轮数
)
```

## 🛡️ 安全机制

1. **代码分析**: 提前发现潜在问题
2. **对抗式辩论**: 检察官 vs 辩护律师，充分讨论
3. **质量检查**: 自动运行测试和代码检查
4. **重审机制**: 失败时自动触发重审
5. **Git 集成**: 所有变更可追溯

## 📊 优势

- ✅ **减少 AI 幻觉**: 通过对抗式辩论发现问题
- ✅ **自动执行**: 判决后自动生成和修改代码
- ✅ **质量保证**: 自动测试和代码检查
- ✅ **可追溯**: 完整的庭审记录和执行日志
- ✅ **反馈循环**: 失败时自动重审

## 🔗 相关文档

- [快速开始指南](COURTROOM_GUIDE.md)
- [实现报告](COURTROOM_IMPLEMENTATION_REPORT.md)
- [工作总结](WORK_SUMMARY_COURTROOM.md)

## 📝 注意事项

1. 确保已安装 Claude Code CLI 和 Copilot CLI
2. 首次使用建议先在测试项目上试验
3. 重要项目建议先使用 `dry_run=True` 模式
4. 执行前建议先提交 git，方便回滚

## 🎯 下一步

- [ ] 添加更多代码质量检查规则
- [ ] 支持更多编程语言
- [ ] 集成更多 AI 工具（如 Cursor）
- [ ] 添加可视化执行流程图
- [ ] 支持分布式执行
