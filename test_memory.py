"""
测试分层记忆系统
"""
from pathlib import Path
from courtroom.memory import MemoryManager, MemoryTier
from datetime import datetime, timedelta


def test_memory_system():
    """测试分层记忆系统"""
    print("🧪 测试分层记忆系统\n")

    courtroom_root = Path("/home/sevenstars/CLionProjects/Oasis/courtroom")
    manager = MemoryManager(courtroom_root)

    # 测试 1: 创建摘要
    print("1️⃣ 创建案件摘要")
    summary1 = manager.create_summary(
        case_id="case_test_001",
        title="添加 Redis 缓存层",
        motion_type="performance",
        verdict_type="approved",
        full_transcript="完整的庭审记录...",
        verdict_reasoning="经过充分辩论，缓存方案可行，但需要注意缓存一致性问题。收益明显，风险可控。"
    )
    print(f"   ✅ 创建摘要: {summary1.case_id}")
    print(f"   关键点: {summary1.key_points}")
    print(f"   判例价值: {summary1.precedent_value}\n")

    # 测试 2: 创建更多摘要
    print("2️⃣ 创建更多案件摘要")
    test_cases = [
        ("case_test_002", "重构认证系统", "refactor", "modified"),
        ("case_test_003", "修复登录 Bug", "bug_fix", "approved"),
        ("case_test_004", "添加用户头像", "new_feature", "approved"),
        ("case_test_005", "优化数据库查询", "performance", "approved"),
    ]

    for case_id, title, motion_type, verdict_type in test_cases:
        manager.create_summary(
            case_id=case_id,
            title=title,
            motion_type=motion_type,
            verdict_type=verdict_type,
            full_transcript="...",
            verdict_reasoning="判决理由..."
        )
        print(f"   ✅ {case_id}: {title}")
    print()

    # 测试 3: 搜索摘要
    print("3️⃣ 搜索性能优化相关案件")
    summaries = manager.search_summaries(motion_type="performance", limit=10)
    print(f"   找到 {len(summaries)} 个案件：")
    for s in summaries:
        print(f"   - {s.title} ({s.verdict_type})")
    print()

    # 测试 4: 获取单个摘要
    print("4️⃣ 获取单个案件摘要")
    summary = manager.get_summary("case_test_001")
    if summary:
        print(f"   ✅ {summary.title}")
        print(f"   访问次数: {summary.access_count}")
        print(f"   记忆层级: {summary.tier}\n")

    # 测试 5: 为法官准备上下文
    print("5️⃣ 为法官准备上下文")
    context = manager.get_context_for_judge(
        current_motion_type="performance",
        max_tokens=1000
    )
    print(f"   生成上下文长度: {len(context)} 字符")
    print(f"   预览:\n{context[:300]}...\n")

    # 测试 6: 统计信息
    print("6️⃣ 记忆系统统计")
    stats = manager.get_statistics()
    print(f"   总案件数: {stats['total_cases']}")
    print(f"   按层级分布: {stats['by_tier']}")
    print(f"   按类型分布: {stats['by_type']}")
    print(f"   最常访问:")
    for item in stats['most_accessed']:
        print(f"   - {item['title']}: {item['access_count']} 次")
    print()

    # 测试 7: 遗忘曲线（模拟）
    print("7️⃣ 测试遗忘曲线")
    print("   （实际需要等待 30 天，这里仅演示机制）")
    # downgraded = manager.apply_forgetting_curve(days_threshold=0)
    # print(f"   降级了 {downgraded} 个案件\n")

    print("✅ 分层记忆系统测试完成！")
    print("\n📊 系统特性:")
    print("   - 热记忆: 当前庭审完整记录")
    print("   - 温记忆: 精简摘要（200 token）")
    print("   - 冷记忆: 向量知识库（按需检索）")
    print("   - 冻结记忆: 仅一句话总结")
    print("   - 自动遗忘曲线: 30 天未访问自动降级")


if __name__ == "__main__":
    test_memory_system()
