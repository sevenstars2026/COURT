"""
测试判例演化系统
"""
from pathlib import Path
from courtroom.precedent_evolution import PrecedentEvolution, PrecedentStatus


def test_precedent_evolution():
    """测试判例演化系统"""
    print("🧪 测试判例演化系统\n")

    courtroom_root = Path("/home/sevenstars/CLionProjects/Oasis/courtroom")
    evolution = PrecedentEvolution(courtroom_root)

    # 测试 1: 添加判例
    print("1️⃣ 添加判例")
    p1 = evolution.add_precedent(
        case_id="case_001",
        title="添加 Redis 缓存层",
        motion_type="performance",
        verdict_type="approved",
        core_principle="性能优化类动议在收益明显且风险可控时应批准",
        reasoning="缓存方案成熟，性能提升显著",
        tags=["performance", "cache", "redis"]
    )

    p2 = evolution.add_precedent(
        case_id="case_002",
        title="重构认证系统",
        motion_type="refactor",
        verdict_type="rejected",
        core_principle="重构类动议在风险过高时应驳回",
        reasoning="迁移风险高，可能导致用户无法登录",
        tags=["refactor", "auth", "security"]
    )

    p3 = evolution.add_precedent(
        case_id="case_003",
        title="优化数据库查询",
        motion_type="performance",
        verdict_type="approved",
        core_principle="性能优化类动议在有充分测试时应批准",
        reasoning="查询优化效果明显，测试覆盖完整",
        tags=["performance", "database"]
    )
    print()

    # 测试 2: 搜索判例
    print("2️⃣ 搜索性能优化相关判例")
    results = evolution.search_precedents(motion_type="performance", limit=10)
    print(f"   找到 {len(results)} 个判例:")
    for p in results:
        print(f"   - {p.title}")
        print(f"     原则: {p.core_principle}")
        print(f"     权重: {p.weight:.2f}, 引用: {p.reference_count} 次")
    print()

    # 测试 3: 记录成功案例
    print("3️⃣ 记录成功案例")
    evolution.record_success(p1.precedent_id)
    evolution.record_success(p1.precedent_id)
    evolution.record_success(p3.precedent_id)
    print(f"   {p1.title}: 引用 {evolution.precedents[p1.precedent_id].reference_count} 次")
    print()

    # 测试 4: 标记危险判例
    print("4️⃣ 标记危险判例")
    evolution.mark_dangerous(
        p2.precedent_id,
        "该判例导致了一次生产事故，用户无法登录"
    )
    print()

    # 测试 5: 检测冲突
    print("5️⃣ 检测判例冲突")

    # 添加一个冲突的判例
    p4 = evolution.add_precedent(
        case_id="case_004",
        title="另一个重构认证系统的案例",
        motion_type="refactor",
        verdict_type="approved",
        core_principle="重构类动议在有完整测试时应批准",
        reasoning="测试覆盖完整，风险可控",
        tags=["refactor", "auth"]
    )

    conflicts = evolution.detect_conflicts()
    print(f"   发现 {len(conflicts)} 个冲突:")
    for p_a, p_b in conflicts:
        print(f"   - {p_a.title} vs {p_b.title}")
        print(f"     原则 A: {p_a.core_principle}")
        print(f"     原则 B: {p_b.core_principle}")
    print()

    # 测试 6: 调和冲突
    if conflicts:
        print("6️⃣ 调和冲突")
        p_a, p_b = conflicts[0]
        resolution = evolution.resolve_conflict(
            p_a.precedent_id,
            p_b.precedent_id,
            refined_principle="重构类动议应根据测试覆盖度和风险评估决定：测试完整且风险可控时批准，否则驳回",
            conditions=[
                "必须有完整的测试覆盖（>= 80%）",
                "必须有回滚预案",
                "必须在测试环境验证"
            ]
        )
        print(f"   适用条件:")
        for cond in resolution.conditions:
            print(f"   - {cond}")
        print()

    # 测试 7: 统计信息
    print("7️⃣ 统计信息")
    stats = evolution.get_statistics()
    print(f"   总判例数: {stats['total_precedents']}")
    print(f"   按状态分布: {stats['by_status']}")
    print(f"   危险判例: {stats['dangerous_count']} 个")
    print(f"   冲突调和: {stats['conflict_resolutions']} 个")
    print()

    print("   最常引用判例:")
    for item in stats['most_referenced']:
        print(f"   - {item['title']}: {item['references']} 次 (权重 {item['weight']:.2f})")
    print()

    # 测试 8: 生成报告
    print("8️⃣ 生成判例库报告")
    report = evolution.generate_report()
    print(report)

    print("✅ 判例演化系统测试完成！")
    print("\n📊 系统特性:")
    print("   - 自动检测判例冲突")
    print("   - 冲突调和机制")
    print("   - 危险判例标记")
    print("   - 成功案例追踪")
    print("   - 动态权重调整")
    print("   - 判例库报告生成")


if __name__ == "__main__":
    test_precedent_evolution()
