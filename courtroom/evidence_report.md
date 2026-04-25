# 案件 case_test_evidence 证据报告

## 📎 证据清单

### 检察官提交的证据

#### 📎 新增的缓存逻辑

**证据编号**: evidence_20260425_123536_212236
**证据类型**: code_snippet
**提交时间**: 2026-04-25 12:35:36
**标签**: code

**描述**: 这是新增的缓存逻辑，可以减少 80% 的数据库查询

```python

def get_user_with_cache(user_id: int):
    # 先查缓存
    cached = redis_client.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)

    # 缓存未命中，查数据库
    user = db.query(User).filter(User.id == user_id).first()

    # 写入缓存
    redis_client.setex(f"user:{user_id}", 3600, json.dumps(user))
    return user

```

**文件路径**: `backend/services/cache.py`

---

#### 📎 缓存性能提升数据

**证据编号**: evidence_20260425_123536_212480
**证据类型**: benchmark
**提交时间**: 2026-04-25 12:35:36
**标签**: benchmark, performance

**描述**: 性能测试显示缓存带来显著提升

{
  "without_cache": {
    "avg_response_time_ms": 250,
    "p95_response_time_ms": 450,
    "requests_per_second": 400
  },
  "with_cache": {
    "avg_response_time_ms": 50,
    "p95_response_time_ms": 80,
    "requests_per_second": 2000
  },
  "improvement": {
    "response_time": "80% faster",
    "throughput": "5x increase"
  }
}

---

### 辩护律师提交的证据

#### 📎 缓存一致性测试失败

**证据编号**: evidence_20260425_123536_212376
**证据类型**: test_result
**提交时间**: 2026-04-25 12:35:36
**标签**: test, failed

**描述**: 当数据库更新时，缓存没有正确失效，导致读取到过期数据

```

FAILED tests/test_cache.py::test_cache_invalidation
AssertionError: 缓存未正确失效
Expected: {'name': 'Updated Name'}
Got: {'name': 'Old Name'}

```

---
