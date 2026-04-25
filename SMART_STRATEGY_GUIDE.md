# 智能执行策略测试指南

## 功能概述

智能执行策略会根据任务复杂度自动选择最优的执行方式:

- **微小任务** (Trivial): 使用 Copilot CLI 快速生成 (1分钟)
- **简单任务** (Simple): Claude Code 单次执行 (5分钟)
- **中等任务** (Moderate): Claude Code 标准执行 (15分钟)
- **复杂任务** (Complex): Claude Code 监控执行 (30分钟)
- **极复杂任务** (Very Complex): Claude Code 分步执行 (60分钟)

## 复杂度评估因素

系统会综合以下因素评估任务复杂度:

### 1. 文件数量 (权重: 2.0)
- 0 个文件: 1 分
- 1-2 个文件: 2 分
- 3-5 个文件: 4 分
- 6-10 个文件: 6 分
- 10+ 个文件: 8 分

### 2. 变更数量 (权重: 1.5)
- 0 个变更: 1 分
- 1-3 个变更: 2 分
- 4-8 个变更: 4 分
- 9-15 个变更: 6 分
- 15+ 个变更: 8 分

### 3. 描述长度 (权重: 0.5)
- < 50 字符: 1 分
- 50-200 字符: 2 分
- 200-500 字符: 3 分
- 500-1000 字符: 4 分
- 1000+ 字符: 5 分

### 4. 动议类型 (权重: 1.0)
- Bug 修复: 2 分
- 新功能: 4 分
- 重构: 5 分
- 性能优化: 6 分
- 安全: 6 分
- 架构: 8 分

### 5. 关键词检测
- 包含"架构/重构/设计": +3 分
- 包含"性能/优化/加速": +2 分
- 包含"安全/漏洞/加密": +2.5 分

### 6. 执行计划步骤 (权重: 1.5)
- 1-3 步: 1 分
- 4-6 步: 2 分
- 7-10 步: 4 分
- 10+ 步: 6 分

## 复杂度等级划分

- **总分 < 5**: Trivial (微小)
- **总分 5-15**: Simple (简单)
- **总分 15-30**: Moderate (中等)
- **总分 30-50**: Complex (复杂)
- **总分 > 50**: Very Complex (极复杂)

## 测试用例

### 测试 1: 微小任务 (Trivial)
```
标题: 修改配置文件端口
类型: Bug 修复
描述: 将 config.json 中的端口从 8080 改为 3000
影响文件: config.json
变更: 1 个

预期策略: Copilot (60秒超时)
预期复杂度: Trivial (分数 < 5)
```

### 测试 2: 简单任务 (Simple)
```
标题: 添加用户登录日志
类型: 新功能
描述: 在用户登录成功后记录日志,包括用户名、IP、时间戳
影响文件: auth.py, logger.py
变更: 2-3 个

预期策略: Claude Code 单次执行 (300秒超时)
预期复杂度: Simple (分数 5-15)
```

### 测试 3: 中等任务 (Moderate)
```
标题: 实现 Redis 缓存层
类型: 新功能
描述: 为 API 响应添加 Redis 缓存,支持 TTL 配置,实现缓存失效策略
影响文件: cache.py, api.py, config.py, requirements.txt
变更: 5-8 个

预期策略: Claude Code 标准执行 (900秒超时)
预期复杂度: Moderate (分数 15-30)
```

### 测试 4: 复杂任务 (Complex)
```
标题: 重构认证系统为 JWT
类型: 重构
描述: 将现有的 Session 认证重构为 JWT Token 认证,支持刷新令牌,添加权限控制
影响文件: auth.py, middleware.py, models.py, api.py, tests/test_auth.py
变更: 10+ 个

预期策略: Claude Code 监控执行 (1800秒超时)
预期复杂度: Complex (分数 30-50)
```

### 测试 5: 极复杂任务 (Very Complex)
```
标题: SNN 硬件加速优化
类型: 架构 + 性能优化
描述: 优化脉冲神经网络的硬件实现,包括 CUDA 内核优化、内存管理、并行计算策略
影响文件: 15+ 个 (kernel.cu, memory.cpp, scheduler.py, ...)
变更: 20+ 个
关键词: 架构、性能、优化、硬件

预期策略: Claude Code 分步执行 (3600秒超时)
预期复杂度: Very Complex (分数 > 50)
```

## 自动降级策略

如果执行超时,系统会自动降级:

```
Complex/Very Complex 超时
  ↓
降级为 Moderate (900秒)
  ↓
如果仍然超时,标记为需要人工介入
```

## 启用智能执行策略

### 方式 1: 默认启用 (推荐)
智能执行策略默认启用,无需配置。

### 方式 2: 手动控制
```python
from courtroom.agents.execution_engineer import ExecutionEngineer

# 启用智能策略
engineer = ExecutionEngineer(
    project_root=Path("."),
    use_smart_strategy=True
)

# 禁用智能策略 (使用传统方式)
engineer = ExecutionEngineer(
    project_root=Path("."),
    use_smart_strategy=False
)
```

## 查看执行信息

庭审完成后,执行日志会包含策略信息:

```json
{
  "strategy_info": {
    "strategy": "claude_monitored",
    "complexity": "complex",
    "score": 35.5,
    "attempts": [
      {
        "strategy": "claude_monitored",
        "start_time": "2026-04-25T20:00:00",
        "end_time": "2026-04-25T20:15:00",
        "success": true,
        "output_length": 15234
      }
    ]
  }
}
```

## Web UI 显示

庭审完成后,Web UI 会显示:
- 执行策略名称
- 任务复杂度等级
- 尝试次数
- 是否使用了降级策略

## 性能对比

| 任务类型 | 传统方式 | 智能策略 | 提升 |
|---------|---------|---------|------|
| 微小任务 | 5分钟 (Claude Code) | 1分钟 (Copilot) | 5x |
| 简单任务 | 30分钟 (固定超时) | 5分钟 (动态超时) | 6x |
| 中等任务 | 30分钟 | 15分钟 | 2x |
| 复杂任务 | 30分钟 (可能超时) | 30分钟 (监控) | 稳定性提升 |
| 极复杂任务 | 超时失败 | 60分钟分步执行 | 成功率提升 |

## 注意事项

1. **Copilot CLI 可选**: 如果未安装 Copilot,微小任务会自动降级为 Claude Code
2. **超时保护**: 所有策略都有超时保护,防止无限等待
3. **进度反馈**: 复杂任务会实时反馈执行进度
4. **自动重试**: 超时后会自动尝试降级策略
5. **日志记录**: 所有执行信息都会记录到日志文件

## 故障排查

### 策略选择不合理
- 检查动议描述是否完整
- 确认影响文件列表是否准确
- 查看执行日志中的复杂度分数

### 执行仍然超时
- 考虑拆分任务为多个小任务
- 增加执行计划的详细程度
- 手动指定更长的超时时间

### Copilot 不可用
- 系统会自动降级为 Claude Code
- 或手动禁用 Copilot: `use_copilot=False`
