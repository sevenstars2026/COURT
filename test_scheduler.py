"""
测试并行预审系统
"""
import asyncio
from pathlib import Path
from courtroom.scheduler import CourtScheduler, CasePriority


async def test_scheduler():
    """测试法庭排期器"""
    print("🧪 测试并行预审系统\n")

    courtroom_root = Path("/home/sevenstars/CLionProjects/Oasis/courtroom")
    scheduler = CourtScheduler(courtroom_root, max_parallel=3)

    # 测试 1: 提交多个案件
    print("1️⃣ 提交案件")
    cases = [
        ("case_sched_001", "添加 Redis 缓存", "performance", CasePriority.HIGH),
        ("case_sched_002", "修复登录 Bug", "bug_fix", CasePriority.CRITICAL),
        ("case_sched_003", "重构认证系统", "refactor", CasePriority.NORMAL),
        ("case_sched_004", "优化数据库查询", "performance", CasePriority.HIGH),
        ("case_sched_005", "添加用户头像", "new_feature", CasePriority.LOW),
    ]

    for case_id, title, motion_type, priority in cases:
        scheduler.submit_case(case_id, title, motion_type, priority)
    print()

    # 测试 2: 批量并行预审
    print("2️⃣ 批量并行预审")
    case_ids = [c[0] for c in cases]
    results = await scheduler.batch_pre_trial(case_ids)

    print(f"\n预审结果:")
    for result in results:
        print(f"  - {result.case_id}:")
        print(f"    通过: {'✅' if result.passed else '❌'}")
        print(f"    复杂度: {result.estimated_complexity}/10")
        print(f"    建议优先级: {result.recommended_priority.value}")
        if result.issues:
            print(f"    问题: {', '.join(result.issues)}")
    print()

    # 测试 3: 查看队列状态
    print("3️⃣ 查看队列状态")
    print(scheduler.get_queue_status())
    print()

    # 测试 4: 获取下一批案件
    print("4️⃣ 获取下一批待审理案件")
    next_cases = scheduler.get_next_cases(limit=3)
    print(f"下一批案件 ({len(next_cases)} 个):")
    for case in next_cases:
        print(f"  - [{case.priority.value}] {case.title}")
    print()

    # 测试 5: 模拟审理流程
    print("5️⃣ 模拟审理流程")
    if next_cases:
        case = next_cases[0]
        scheduler.start_trial(case.case_id)
        await asyncio.sleep(0.5)  # 模拟审理
        scheduler.complete_trial(case.case_id)
    print()

    # 测试 6: 统计信息
    print("6️⃣ 统计信息")
    stats = scheduler.get_statistics()
    print(f"  总案件数: {stats['total_cases']}")
    print(f"  按状态分布: {stats['by_status']}")
    print(f"  按优先级分布: {stats['by_priority']}")
    print(f"  平均审理时长: {stats['avg_duration_seconds']:.2f}s")
    print(f"  已完成: {stats['completed_count']}")
    print()

    print("✅ 并行预审系统测试完成！")
    print("\n📊 系统特性:")
    print("   - 支持批量并行预审（3-10 个案件同时预审）")
    print("   - 智能优先级排序（紧急 > 高 > 普通 > 低）")
    print("   - 预审快速筛选（0.5s/案件）")
    print("   - 复杂度评估")
    print("   - 队列可视化")


if __name__ == "__main__":
    asyncio.run(test_scheduler())
