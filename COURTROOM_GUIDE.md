# ⚖️ Courtroom Collaboration System

## 快速开始指南

### 安装依赖

```bash
pip install pydantic
```

### 运行示例

```bash
# 交互式示例演示
python courtroom_example.py

# 命令行方式提交动议
python courtroom_cli.py file-motion \
  --title "增加自动重试机制" \
  --type "new_feature" \
  --description "为 API 调用添加指数退避重试，提高系统稳定性" \
  --changes "添加 RetryPolicy 类" "包装 HTTP 请求" \
  --files "frontend/src/api/client.ts" \
  --risks "可能增加延迟" "需要处理幂等性" \
  --benefits "提高弱网可用性" "减少用户报错"

# 开庭审理
python courtroom_cli.py trial --case-id case_20260425_120000

# 查看判决
python courtroom_cli.py show-verdict --case-id case_20260425_120000

# 列出所有案件
python courtroom_cli.py list-cases --all

# 查看统计
python courtroom_cli.py stats
```

### Python API 使用

```python
from pathlib import Path
from courtroom import Court, MotionType

# 创建法庭实例
court = Court(Path("./courtroom"))

# 提交动议
result = court.file_motion(
    title="为聊天系统添加表情符号支持",
    motion_type=MotionType.NEW_FEATURE,
    description="用户希望在聊天中使用表情符号",
    proposed_changes=[
        "添加表情选择器组件",
        "更新消息模型"
    ],
    affected_files=[
        "frontend/src/components/ChatPanel.tsx"
    ],
    risks=["增加存储空间"],
    benefits=["提升用户体验"],
    priority=7
)

# 开庭审理
court.trial("case_001", max_rounds=3)

# 查看判决
verdict = court.show_verdict("case_001")
print(verdict)
```

## 目录说明

- `courtroom/` - 核心系统代码
  - `agents/` - 各种 Agent 实现
  - `cases/` - 案件文件（JSON）
  - `verdicts/` - 判决书（JSON）
  - `transcripts/` - 庭审记录（Markdown）
  - `evidence/` - 证据材料
  
- `courtroom_cli.py` - 命令行工具
- `courtroom_example.py` - 交互式示例
- `COURTROOM_GUIDE.md` - 详细文档

## 工作流程

1. **检察官**提交动议（Motion）
2. **法官**立案，分发给**辩护律师**
3. 双方收集**证据**（Evidence）
4. **开庭辩论**：
   - 开场陈述
   - 交叉辩论（多轮）
   - 结案陈词
5. **陪审团**评议投票
6. **法官**做出判决（Verdict）
7. **书记员**生成庭审记录

## 特点

✅ 结构化协作 - 所有状态都是 JSON，不依赖 Markdown  
✅ 对抗式辩论 - 自动发现提案中的问题  
✅ 完全可审计 - 每个决策都有完整记录  
✅ 人类友好 - 庭审记录像剧本一样有趣  
✅ 独立运行 - 不影响 Oasis 游戏代码

## 与 Oasis 的关系

庭审系统是一个**独立的 Agent 协作框架**，可用于：

- 重大架构决策
- 数据库迁移方案
- 安全相关变更
- 性能优化方案
- 新功能设计评审

完全不影响 Oasis 的游戏逻辑和代码结构。
