"""
庭审系统完整示例 - 展示新的执行流程
"""
from pathlib import Path
from courtroom import Court, MotionType


def main():
    print("=" * 60)
    print("⚖️  庭审系统完整流程演示")
    print("=" * 60)

    # 创建法庭实例（指定代码库路径）
    courtroom_root = Path(__file__).parent / "courtroom"
    codebase_path = Path(__file__).parent  # 当前项目作为代码库

    court = Court(
        courtroom_root=courtroom_root,
        codebase_path=codebase_path,
        use_llm=False
    )

    print("\n📋 场景：为游戏添加新功能\n")

    # 提交动议（会自动运行代码分析）
    case_id_result = court.file_motion(
        title="为游戏添加存档功能",
        motion_type=MotionType.NEW_FEATURE,
        description="玩家希望能够保存游戏进度，下次继续游戏",
        proposed_changes=[
            "添加 SaveManager 类处理存档",
            "实现 save() 和 load() 方法",
            "添加存档文件格式（JSON）"
        ],
        affected_files=[
            "game/save_manager.py",
            "game/game_state.py"
        ],
        risks=[
            "存档文件可能损坏",
            "版本兼容性问题"
        ],
        benefits=[
            "提升用户体验",
            "增加游戏可玩性"
        ],
        priority=8,
        run_analysis=True  # 启用代码分析
    )

    print(f"\n{case_id_result}\n")

    # 提取 case_id
    import re
    match = re.search(r'case_\d+_\d+', case_id_result)
    if not match:
        print("❌ 无法提取案件编号")
        return

    case_id = match.group()

    # 开庭审理（包含执行和质量检查）
    print("\n" + "=" * 60)
    print("开始庭审")
    print("=" * 60)

    result = court.trial(case_id, max_rounds=2)

    print("\n" + "=" * 60)
    print("庭审结果")
    print("=" * 60)
    print(result)

    # 查看判决
    print("\n" + "=" * 60)
    print("判决详情")
    print("=" * 60)
    verdict = court.show_verdict(case_id)
    print(verdict)

    # 查看执行日志
    print("\n" + "=" * 60)
    print("执行摘要")
    print("=" * 60)
    execution_summary = court.execution_engineer.get_execution_summary(case_id)
    if execution_summary:
        print(f"执行状态: {'成功' if execution_summary['success'] else '失败'}")
        print(f"修改文件: {len(execution_summary['modified_files'])} 个")
        print(f"创建文件: {len(execution_summary['created_files'])} 个")
        if execution_summary['error_message']:
            print(f"错误: {execution_summary['error_message']}")
    else:
        print("无执行记录")

    # 查看质量检查报告
    print("\n" + "=" * 60)
    print("质量检查报告")
    print("=" * 60)
    qa_report = court.qa_inspector.get_report(case_id)
    if qa_report:
        print(f"检查结果: {'通过' if qa_report.passed else '未通过'}")
        if qa_report.code_quality_issues:
            print(f"代码质量问题: {len(qa_report.code_quality_issues)} 个")
        if qa_report.security_issues:
            print(f"安全问题: {len(qa_report.security_issues)} 个")
        if qa_report.should_retry:
            print(f"建议重审: {qa_report.retry_reason}")
    else:
        print("无质量检查记录")


if __name__ == '__main__':
    main()
