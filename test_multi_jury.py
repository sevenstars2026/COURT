"""
测试多模型陪审团系统
"""
from courtroom.multi_jury import (
    MultiModelJury, JurorModel, VoteType
)


def test_multi_jury():
    """测试多模型陪审团"""
    print("🧪 测试多模型陪审团系统\n")

    # 创建陪审团（5 个廉价模型）
    jury = MultiModelJury(use_real_models=False)

    # 测试 1: 强共识场景
    print("1️⃣ 测试强共识场景（检察官论点压倒性优势）")
    result1 = jury.deliberate(
        motion_summary="添加 Redis 缓存层，提升性能",
        prosecutor_arguments=[
            "性能测试显示响应时间减少 80%",
            "数据库负载降低 60%",
            "用户体验显著提升",
            "技术方案成熟可靠",
            "已有完整的测试覆盖"
        ],
        defender_arguments=[
            "可能增加系统复杂度",
            "需要额外的 Redis 服务器"
        ]
    )

    print(f"   投票结果: {result1.consensus.value}")
    print(f"   共识比例: {result1.consensus_ratio:.0%}")
    print(f"   强共识: {'✅' if result1.has_strong_consensus else '❌'}")
    print(f"   需要专家证人: {'是' if result1.needs_expert_witness else '否'}")
    print(f"\n   {result1.summary}\n")

    # 测试 2: 分歧场景
    print("2️⃣ 测试分歧场景（双方论点势均力敌）")
    result2 = jury.deliberate(
        motion_summary="重构认证系统，从 JWT 迁移到 OAuth2",
        prosecutor_arguments=[
            "OAuth2 更安全",
            "支持第三方登录",
            "符合行业标准"
        ],
        defender_arguments=[
            "迁移风险高，可能导致用户无法登录",
            "需要数据库迁移",
            "OAuth2 配置复杂"
        ]
    )

    print(f"   投票结果: {result2.consensus.value}")
    print(f"   共识比例: {result2.consensus_ratio:.0%}")
    print(f"   存在分歧: {'⚠️ 是' if result2.has_split else '否'}")
    print(f"   需要专家证人: {'✅ 是' if result2.needs_expert_witness else '否'}")
    print(f"\n   {result2.summary}\n")

    # 测试 3: 查看详细投票
    print("3️⃣ 查看详细投票记录")
    for i, vote in enumerate(result2.votes, 1):
        print(f"   陪审员 {i} ({vote.juror_model.value}):")
        print(f"   - 投票: {vote.vote.value}")
        print(f"   - 理由: {vote.reasoning}")
        print(f"   - 置信度: {vote.confidence:.0%}\n")

    # 测试 4: 成本估算
    print("4️⃣ 成本估算")
    cost = jury.get_cost_estimate()
    print(f"   总成本: ${cost['total_cost']:.6f}")
    print(f"   每陪审员: ${cost['cost_per_juror']:.6f}")
    print(f"   预估 tokens: {cost['estimated_tokens']}")
    print(f"\n   成本分解:")
    for model, model_cost in cost['breakdown'].items():
        print(f"   - {model}: ${model_cost:.6f}")
    print()

    # 测试 5: 不同陪审团配置
    print("5️⃣ 测试不同陪审团配置")

    # 配置 1: 全免费模型
    jury_free = MultiModelJury(
        juror_models=[
            JurorModel.LOCAL_7B,
            JurorModel.GEMINI_FLASH,
            JurorModel.LOCAL_7B
        ],
        use_real_models=False
    )
    cost_free = jury_free.get_cost_estimate()
    print(f"   全免费配置: ${cost_free['total_cost']:.6f}")

    # 配置 2: 混合配置
    jury_mixed = MultiModelJury(
        juror_models=[
            JurorModel.LOCAL_7B,
            JurorModel.GPT4O_MINI,
            JurorModel.DEEPSEEK_V3,
            JurorModel.GEMINI_FLASH
        ],
        use_real_models=False
    )
    cost_mixed = jury_mixed.get_cost_estimate()
    print(f"   混合配置: ${cost_mixed['total_cost']:.6f}")

    # 配置 3: 全付费配置
    jury_paid = MultiModelJury(
        juror_models=[
            JurorModel.GPT4O_MINI,
            JurorModel.DEEPSEEK_V3,
            JurorModel.CLAUDE_HAIKU,
            JurorModel.GPT4O_MINI,
            JurorModel.DEEPSEEK_V3
        ],
        use_real_models=False
    )
    cost_paid = jury_paid.get_cost_estimate()
    print(f"   全付费配置: ${cost_paid['total_cost']:.6f}\n")

    print("✅ 多模型陪审团测试完成！")
    print("\n📊 系统特性:")
    print("   - 使用 3-5 个廉价模型作为陪审员")
    print("   - 每次审议成本约 $0.0002-0.0005")
    print("   - 自动检测强共识（>= 80%）")
    print("   - 分歧时触发加时辩论")
    print("   - 提供详细的投票分析")
    print("   - 支持多种模型配置")


if __name__ == "__main__":
    test_multi_jury()
