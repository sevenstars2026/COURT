# 庭审系统启动指南

## 系统架构

庭审系统现在支持异步执行和实时进度更新:

- **Flask Web 服务器**: 提供 Web UI 和 API
- **Redis**: 消息队列和任务状态存储
- **Celery Worker**: 异步执行庭审任务
- **WebSocket**: 实时推送庭审进度到前端

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Redis

**方式 A: 使用 Docker (推荐)**
```bash
docker run -d -p 6379:6379 redis:latest
```

**方式 B: 本地安装**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# 验证 Redis 是否运行
redis-cli ping  # 应该返回 PONG
```

### 3. 启动 Celery Worker

在项目根目录打开新终端:

```bash
celery -A courtroom.celery_app worker --loglevel=info
```

**提示**: 保持这个终端运行,它会处理所有异步庭审任务

### 4. 启动 Web 服务器

在另一个终端:

```bash
python courtroom_web.py
```

访问: http://localhost:5000

## 功能说明

### 1. 提交动议
- 填写标题、类型、描述
- 可上传附件(代码文件、文档等)
- 支持优先级设置

### 2. 开始庭审
- 点击"⚖️ 庭审"按钮启动异步庭审
- 实时查看庭审进度(WebSocket 推送)
- 庭审阶段:
  - 检察官开场陈述 (10%)
  - 辩护律师开场陈述 (20%)
  - 交叉辩论 (30-60%)
  - 结案陈词 (70-75%)
  - 陪审团评议 (80-85%)
  - 法官判决 (90-95%)
  - 执行判决 (97-99%)
  - 质量检查 (100%)

### 3. 下载生成的代码
- 庭审完成后,点击"📦 下载代码"按钮
- 支持多版本管理
- 自动打包为 ZIP 文件

### 4. 接入外部 Agent
- 配置全局 API (OpenAI 兼容)
- 按 Agent 单独配置
- 支持 OpenAI、Ollama、vLLM 等

## 超时配置

### Claude Code CLI 超时
- 默认: 1800 秒 (30 分钟)
- 修改位置: `courtroom/agents/execution_engineer.py:200`

### Celery 任务超时
- 硬超时: 3600 秒 (1 小时)
- 软超时: 3000 秒 (50 分钟)
- 修改位置: `courtroom/celery_app.py`

## 故障排查

### Redis 连接失败
```bash
# 检查 Redis 是否运行
redis-cli ping

# 检查端口占用
lsof -i :6379

# 查看 Redis 日志
docker logs <redis-container-id>
```

### Celery Worker 无响应
```bash
# 重启 Worker
pkill -f "celery worker"
celery -A courtroom.celery_app worker --loglevel=info

# 查看任务队列
celery -A courtroom.celery_app inspect active
```

### WebSocket 连接失败
- 检查浏览器控制台是否有错误
- 确认 Flask-SocketIO 正确初始化
- 尝试刷新页面

### 庭审超时
- 检查 Claude Code CLI 是否已登录: `claude --version`
- 增加超时时间 (见上方配置)
- 简化任务复杂度

## 环境变量

创建 `.env` 文件:

```bash
# Redis 配置
REDIS_URL=redis://localhost:6379/0

# Claude Code CLI (可选)
CLAUDE_CLI_PATH=claude

# Copilot CLI (可选)
COPILOT_CLI_PATH=copilot
```

## 生产部署建议

1. **使用 Gunicorn + Eventlet**
   ```bash
   gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 courtroom_web:app
   ```

2. **使用 Supervisor 管理进程**
   - Web 服务器
   - Celery Worker
   - Redis (如果不用 Docker)

3. **配置 Nginx 反向代理**
   - 处理静态文件
   - WebSocket 升级
   - SSL/TLS 终止

4. **监控和日志**
   - Celery Flower: 监控任务队列
   - Redis Commander: 查看 Redis 数据
   - 集中日志收集

## 开发模式 vs 生产模式

### 开发模式 (当前)
- Flask 内置服务器
- Debug 模式开启
- 单进程 Celery Worker

### 生产模式
- Gunicorn + Eventlet
- Debug 模式关闭
- 多进程 Celery Worker
- Redis 持久化
- 负载均衡

## 下一步优化

- [ ] 实现智能执行策略 (Task #13)
- [ ] 添加任务取消功能
- [ ] 支持断点续传
- [ ] 添加执行历史记录
- [ ] 实现代码 diff 预览
