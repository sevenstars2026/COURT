"""
证据管理系统测试
"""
from pathlib import Path
from courtroom.evidence import (
    EvidenceManager, EvidenceType,
    submit_code_evidence, submit_test_evidence, submit_benchmark_evidence
)


def test_evidence_system():
    """测试证据管理系统"""
    print("🧪 测试证据管理系统\n")

    # 创建证据管理器
    evidence_dir = Path("./courtroom/evidence")
    manager = EvidenceManager(evidence_dir)

    case_id = "case_test_evidence"

    # 1. 检察官提交代码证据
    print("1️⃣ 检察官提交代码证据")
    code_evidence = submit_code_evidence(
        manager=manager,
        case_id=case_id,
        submitted_by="prosecutor",
        title="新增的缓存逻辑",
        code="""
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
""",
        file_path="backend/services/cache.py",
        description="这是新增的缓存逻辑，可以减少 80% 的数据库查询"
    )
    print(f"   ✅ 证据 ID: {code_evidence.evidence_id}\n")

    # 2. 辩护律师提交测试失败证据
    print("2️⃣ 辩护律师提交测试失败证据")
    test_evidence = submit_test_evidence(
        manager=manager,
        case_id=case_id,
        submitted_by="defender",
        title="缓存一致性测试失败",
        test_output="""
FAILED tests/test_cache.py::test_cache_invalidation
AssertionError: 缓存未正确失效
Expected: {'name': 'Updated Name'}
Got: {'name': 'Old Name'}
""",
        passed=False,
        description="当数据库更新时，缓存没有正确失效，导致读取到过期数据"
    )
    print(f"   ✅ 证据 ID: {test_evidence.evidence_id}\n")

    # 3. 检察官提交性能基准测试证据
    print("3️⃣ 检察官提交性能基准测试证据")
    benchmark_evidence = submit_benchmark_evidence(
        manager=manager,
        case_id=case_id,
        submitted_by="prosecutor",
        title="缓存性能提升数据",
        benchmark_data={
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
        },
        description="性能测试显示缓存带来显著提升"
    )
    print(f"   ✅ 证据 ID: {benchmark_evidence.evidence_id}\n")

    # 4. 列出所有证据
    print("4️⃣ 列出案件的所有证据")
    all_evidence = manager.list_evidence(case_id)
    print(f"   共 {len(all_evidence)} 条证据\n")

    # 5. 搜索特定类型的证据
    print("5️⃣ 搜索测试相关证据")
    test_evidences = manager.search_evidence(
        case_id=case_id,
        evidence_type=EvidenceType.TEST_RESULT
    )
    print(f"   找到 {len(test_evidences)} 条测试证据\n")

    # 6. 生成证据报告
    print("6️⃣ 生成证据报告")
    report = manager.generate_evidence_report(case_id)

    report_file = Path("./courtroom/evidence_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# 案件 {case_id} 证据报告\n\n")
        f.write(report)

    print(f"   ✅ 报告已保存到: {report_file}\n")

    print("✅ 所有测试通过！\n")
    print("📊 证据统计:")
    print(f"   - 代码证据: {len(manager.search_evidence(case_id=case_id, evidence_type=EvidenceType.CODE_SNIPPET))}")
    print(f"   - 测试证据: {len(manager.search_evidence(case_id=case_id, evidence_type=EvidenceType.TEST_RESULT))}")
    print(f"   - 性能证据: {len(manager.search_evidence(case_id=case_id, evidence_type=EvidenceType.BENCHMARK))}")


if __name__ == "__main__":
    test_evidence_system()
