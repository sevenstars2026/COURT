# ⚖️ 庭审系统 LLM 集成指南

## 概述

庭审系统现在支持两种模式：

1. **规则引擎模式**（默认）：使用预定义的模板生成论点
2. **LLM 模式**：使用 Claude API 生成智能、上下文相关的论点

## 安装依赖

```bash
cd courtroom
pip install -r requirements.txt
```

## 配置 API 密钥

设置环境变量：

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

或者在代码中传入：

```python
from courtroom.llm_client import get_llm_client

client = get_llm_client(api_key="your-api-key-here")
```

## 使用 LLM 模式

### Python API

```python
from pathlib import Path
from courtroom import Court, MotionType

# 创建启用 LLM 的法庭
court = Court(Path("./courtroom"), use_llm=True)

# 提交动议
court.file_motion(
    title="添加 Redis 缓存层",
    motion_type=MotionType.PERFORMANCE,
    description="为热点查询添加 Redis 缓存，提升性能",
    proposed_changes=["集成 Redis", "添加缓存逻辑"],
    affected_files=["backend/services/cache.py"],
    risks=["缓存一致性问题"],
    benefits=["响应时间减少 80%"],
    priority=8
)

# 开庭审理（LLM 会生成智能论点）
court.trial("case_xxx", max_rounds=3)
```

### CLI

```bash
# 使用 LLM 模式
export USE_LLM=true
python courtroom_cli.py trial --case-id case_xxx
```

## LLM Agent 特性

### 检察官 (ProsecutorLLM)

- 根据动议内容生成定制化的开场陈述
- 智能反驳辩护律师的质疑
- 强调收益和必要性
- 提供具体的缓解措施

### 辩护律师 (DefenderLLM)

- 发现提案中的潜在问题和风险
- 提出尖锐但建设性的质疑
- 要求更多证据和测试
- 有条件地支持或反对

### 法官 (JudgeLLM)

- 综合双方论点和陪审团意见
- 生成详细的判决理由
- 提供具体的执行计划
- 做出公正的裁决

## 对比：规则引擎 vs LLM

| 特性 | 规则引擎 | LLM 模式 |
|------|---------|---------|
| 响应速度 | 快（毫秒级） | 慢（秒级） |
| 论点质量 | 通用模板 | 上下文相关 |
| 成本 | 免费 | API 调用费用 |
| 可预测性 | 高 | 中等 |
| 适用场景 | 快速测试 | 重要决策 |

## 示例对比

### 规则引擎输出

```
尊敬的法官：

我代表系统稳定性和代码质量，对动议提出以下质疑：

【风险分析】
- 缓存一致性问题
- 增加系统复杂度

【需要澄清的问题】
1. 是否有充分的测试覆盖？
2. 回滚方案是否完善？
...
```

### LLM 输出

```
尊敬的法官：

虽然 Redis 缓存确实能显著提升性能，但我必须指出几个关键风险：

首先，缓存一致性是分布式系统中最棘手的问题之一。当数据库更新时，
如何保证缓存及时失效？如果处理不当，用户可能看到过期数据，
这在交易系统中是不可接受的。

其次，引入 Redis 意味着增加了一个关键依赖。如果 Redis 服务宕机，
整个系统是否有降级方案？我们需要看到具体的容错设计。

最后，缓存策略的选择至关重要。是使用 TTL 过期？还是主动失效？
不同的策略有不同的权衡，提案中并未说明...
```

## 成本估算

使用 Claude Sonnet 4.6：

- 每次庭审约 5-10 次 API 调用
- 每次调用约 1000-2000 tokens
- 总成本约 $0.05-0.10 per trial

对于重要决策，这个成本是值得的。

## 最佳实践

1. **日常开发**：使用规则引擎模式，快速迭代
2. **重要决策**：使用 LLM 模式，获得深度分析
3. **混合模式**：规则引擎做初筛，LLM 做最终评审

## 故障回退

如果 LLM 调用失败（网络问题、API 限额等），系统会自动回退到规则引擎模式，确保庭审能够继续。

```python
# 自动回退示例
prosecutor_llm = ProsecutorLLM(use_llm=True)
# 如果 API 密钥无效，自动切换到规则引擎
# ⚠️ 未找到 API 密钥，回退到规则引擎模式
```

## 调试

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

查看 LLM 请求和响应：

```python
from courtroom.llm_client import get_llm_client

client = get_llm_client()
response = client.generate("测试提示", system="你是法官")
print(response)
```
