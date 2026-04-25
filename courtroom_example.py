"""
庭审系统示例 - 演示如何使用
"""
from pathlib import Path
from courtroom import Court, MotionType


def example_1_simple_feature():
    """示例 1: 简单的新功能提案"""
    print("\n" + "="*60)
    print("示例 1: 提交一个简单的新功能动议")
    print("="*60 + "\n")

    court = Court(Path(__file__).parent / "courtroom")

    # 提交动议
    result = court.file_motion(
        title="为聊天系统添加表情符号支持",
        motion_type=MotionType.NEW_FEATURE,
        description="用户反馈希望在聊天中使用表情符号，提升交互体验",
        proposed_changes=[
            "在 ChatPanel.tsx 中添加表情选择器组件",
            "更新消息模型支持表情符号",
            "添加表情符号渲染逻辑"
        ],
        affected_files=[
            "frontend/src/components/ChatPanel.tsx",
            "frontend/src/components/EmojiPicker.tsx",
            "backend/models/message.py"
        ],
        risks=[
            "可能增加消息存储空间",
            "需要处理不同平台的表情符号兼容性"
        ],
        benefits=[
            "提升用户体验",
            "增加聊天互动性",
            "符合现代聊天应用标准"
        ],
        priority=7
    )

    print(result)

    # 提取案件编号
    case_id = result.split("案件 ")[1].split(" ")[0]

    # 开庭审理
    input("\n按回车键开始庭审...")
    court.trial(case_id, max_rounds=2)


def example_2_risky_refactor():
    """示例 2: 有风险的重构提案"""
    print("\n" + "="*60)
    print("示例 2: 提交一个有风险的重构动议")
    print("="*60 + "\n")

    court = Court(Path(__file__).parent / "courtroom")

    result = court.file_motion(
        title="重构认证系统，从 JWT 迁移到 OAuth2",
        motion_type=MotionType.ARCHITECTURE,
        description="当前 JWT 认证方案存在安全隐患，建议迁移到 OAuth2",
        proposed_changes=[
            "替换 JWT 认证中间件为 OAuth2",
            "更新所有 API 端点的认证逻辑",
            "迁移现有用户 token",
            "更新前端认证流程"
        ],
        affected_files=[
            "backend/utils/auth.py",
            "backend/api/routes/*.py",
            "frontend/src/api/client.ts",
            "frontend/src/contexts/AuthContext.tsx"
        ],
        risks=[
            "迁移过程中可能导致用户无法登录",
            "需要数据库迁移，可能丢失数据",
            "OAuth2 配置复杂，容易出错",
            "影响所有现有用户"
        ],
        benefits=[
            "提升安全性",
            "支持第三方登录",
            "符合行业标准"
        ],
        priority=9
    )

    print(result)

    case_id = result.split("案件 ")[1].split(" ")[0]

    input("\n按回车键开始庭审...")
    court.trial(case_id, max_rounds=3)


def example_3_performance_optimization():
    """示例 3: 性能优化提案"""
    print("\n" + "="*60)
    print("示例 3: 提交一个性能优化动议")
    print("="*60 + "\n")

    court = Court(Path(__file__).parent / "courtroom")

    result = court.file_motion(
        title="为数据库查询添加 Redis 缓存层",
        motion_type=MotionType.PERFORMANCE,
        description="当前数据库查询响应慢，添加 Redis 缓存可以显著提升性能",
        proposed_changes=[
            "集成 Redis 客户端",
            "为热点查询添加缓存逻辑",
            "实现缓存失效策略",
            "添加缓存监控"
        ],
        affected_files=[
            "backend/services/cache_service.py",
            "backend/api/routes/map.py",
            "backend/api/routes/tasks.py",
            "backend/requirements.txt"
        ],
        risks=[
            "缓存一致性问题",
            "增加系统复杂度",
            "需要额外的 Redis 服务器"
        ],
        benefits=[
            "查询响应时间减少 80%",
            "降低数据库负载",
            "提升用户体验"
        ],
        priority=8
    )

    print(result)

    case_id = result.split("案件 ")[1].split(" ")[0]

    input("\n按回车键开始庭审...")
    court.trial(case_id, max_rounds=2)


def show_menu():
    """显示菜单"""
    print("\n" + "="*60)
    print("⚖️ Courtroom Collaboration System - 示例演示")
    print("="*60)
    print("\n请选择要运行的示例：\n")
    print("1. 简单的新功能提案（表情符号支持）")
    print("2. 有风险的架构重构（JWT → OAuth2）")
    print("3. 性能优化提案（Redis 缓存）")
    print("4. 查看法庭统计")
    print("5. 列出所有案件")
    print("0. 退出")
    print()


def main():
    """主函数"""
    court = Court(Path(__file__).parent / "courtroom")

    while True:
        show_menu()
        choice = input("请输入选项 (0-5): ").strip()

        if choice == '1':
            example_1_simple_feature()
        elif choice == '2':
            example_2_risky_refactor()
        elif choice == '3':
            example_3_performance_optimization()
        elif choice == '4':
            print(court.get_statistics())
        elif choice == '5':
            print(court.list_cases(active_only=False))
        elif choice == '0':
            print("\n再见！")
            break
        else:
            print("\n❌ 无效选项，请重新选择")

        input("\n按回车键继续...")


if __name__ == '__main__':
    main()
