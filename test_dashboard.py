"""
测试经济驾驶舱
"""
from pathlib import Path
from courtroom.economics_dashboard import EconomicsDashboard


def test_dashboard():
    """测试经济驾驶舱"""
    print("🧪 测试经济驾驶舱\n")

    courtroom_root = Path("/home/sevenstars/CLionProjects/courtroom/courtroom")
    dashboard = EconomicsDashboard(courtroom_root, monthly_budget=5.0)

    # 测试 1: 记录成本
    print("1️⃣ 记录 API 调用成本")
    dashboard.record_cost("case_001", "judge", "claude_sonnet", 0.015)
    dashboard.record_cost("case_001", "prosecutor", "gpt4o_mini", 0.0002)
    dashboard.record_cost("case_001", "defender", "gpt4o_mini", 0.0002)
    dashboard.record_cost("case_002", "judge", "claude_sonnet", 0.012)
    dashboard.record_cost("case_003", "jury", "local_7b", 0.0)
    print()

    # 测试 2: 查看成本统计
    print("2️⃣ 成本统计")
    cost_stats = dashboard.get_cost_statistics()
    print(f"   总成本: ${cost_stats['total_cost']:.4f}")
    print(f"   本月成本: ${cost_stats['monthly_cost']:.4f}")
    print(f"   预算使用: {cost_stats['budget_usage']:.1%}")
    print(f"   预算剩余: ${cost_stats['budget_remaining']:.4f}")
    print(f"   平均每案件: ${cost_stats['avg_cost_per_case']:.4f}")
    print()

    print("   按角色分布:")
    for role, cost in cost_stats['by_role'].items():
        print(f"   - {role}: ${cost:.4f}")
    print()

    # 测试 3: 记录判决结果
    print("3️⃣ 记录判决结果")
    dashboard.record_verdict("case_001", "approved", quality_score=0.9)
    dashboard.record_verdict("case_002", "rejected", quality_score=0.8)
    dashboard.record_verdict("case_003", "approved", quality_score=0.95)
    print()

    # 测试 4: 质量统计
    print("4️⃣ 质量统计")
    quality_stats = dashboard.get_quality_statistics()
    print(f"   总案件数: {quality_stats['total_cases']}")
    print(f"   批准率: {quality_stats['approval_rate']:.1%}")
    print(f"   驳回率: {quality_stats['rejection_rate']:.1%}")
    print(f"   平均质量分: {quality_stats['avg_quality_score']:.2f}/1.0")
    print()

    # 测试 5: 速度统计
    print("5️⃣ 速度统计")
    dashboard.record_duration("case_001", 120)
    dashboard.record_duration("case_002", 90)
    dashboard.record_duration("case_003", 150)

    speed_stats = dashboard.get_speed_statistics()
    print(f"   平均审理时长: {speed_stats['avg_duration']:.1f}s")
    print(f"   最快: {speed_stats['min_duration']}s")
    print(f"   最慢: {speed_stats['max_duration']}s")
    print()

    # 测试 6: 综合仪表盘
    print("6️⃣ 综合仪表盘")
    print(dashboard.render_dashboard())
    print()

    # 测试 7: 预算燃尽图
    print("7️⃣ 预算燃尽图")
    burndown = dashboard.get_budget_burndown()
    print(f"   已用天数: {burndown['days_elapsed']}")
    print(f"   剩余天数: {burndown['days_remaining']}")
    print(f"   当前消耗速率: ${burndown['current_burn_rate']:.4f}/天")
    print(f"   预计耗尽日期: {burndown['estimated_depletion_date']}")
    print()

    # 测试 8: 策略建议
    print("8️⃣ 策略建议")
    recommendations = dashboard.get_recommendations()
    print("   建议:")
    for rec in recommendations:
        print(f"   - {rec}")
    print()

    # 测试 9: 调整策略
    print("9️⃣ 调整策略（保守 ↔ 激进）")
    print("   当前策略: 平衡")
    dashboard.set_strategy("conservative")
    print("   调整为: 保守")
    print(f"   - 法官模型: {dashboard.strategy['judge_model']}")
    print(f"   - 陪审团规模: {dashboard.strategy['jury_size']}")
    print(f"   - 辩论轮数: {dashboard.strategy['debate_rounds']}")
    print()

    dashboard.set_strategy("aggressive")
    print("   调整为: 激进")
    print(f"   - 法官模型: {dashboard.strategy['judge_model']}")
    print(f"   - 陪审团规模: {dashboard.strategy['jury_size']}")
    print(f"   - 辩论轮数: {dashboard.strategy['debate_rounds']}")
    print()

    # 测试 10: 导出报告
    print("🔟 导出月度报告")
    report_file = dashboard.export_monthly_report()
    print(f"   报告已保存: {report_file}")
    print()

    print("✅ 经济驾驶舱测试完成！")
    print("\n📊 系统特性:")
    print("   - 实时成本追踪")
    print("   - 预算燃尽图")
    print("   - 质量和速度监控")
    print("   - 策略调整（保守/平衡/激进）")
    print("   - 智能建议")
    print("   - 月度报告导出")


if __name__ == "__main__":
    test_dashboard()
