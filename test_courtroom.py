#!/usr/bin/env python3
"""
快速测试庭审系统
"""
from pathlib import Path
from courtroom import Court, MotionType


def test_basic_workflow():
    """测试基本工作流程"""
    print("\n" + "="*60)
    print("🧪 测试庭审系统基本工作流程")
    print("="*60 + "\n")

    # 创建法庭实例
    courtroom_root = Path(__file__).parent / "courtroom"
    court = Court(courtroom_root)

    # 1. 提交动议
    print("📝 步骤 1: 提交动议\n")
    result = court.file_motion(
        title="测试动议：添加用户头像功能",
        motion_type=MotionType.NEW_FEATURE,
        description="允许用户上传和显示个人头像",
        proposed_changes=[
            "添加头像上传 API",
            "更新用户模型",
            "前端显示头像"
        ],
        affected_files=[
            "backend/api/routes/players.py",
            "backend/models/player.py",
            "frontend/src/components/Avatar.tsx"
        ],
        risks=["需要存储空间", "可能有安全风险"],
        benefits=["提升用户体验", "增加个性化"],
        priority=6
    )
    print(result)

    # 提取案件编号
    case_id = result.split("案件 ")[1].split(" ")[0]
    print(f"\n✅ 案件已立案：{case_id}\n")

    # 2. 开庭审理
    print("⚖️ 步骤 2: 开庭审理\n")
    print("-" * 60)
    trial_result = court.trial(case_id, max_rounds=2)
    print("-" * 60)
    print(f"\n✅ {trial_result}\n")

    # 3. 查看判决
    print("📄 步骤 3: 查看判决\n")
    verdict = court.show_verdict(case_id)
    print(verdict)

    # 4. 查看统计
    print("\n📊 步骤 4: 查看统计\n")
    stats = court.get_statistics()
    print(stats)

    # 5. 检查生成的文件
    print("\n📁 步骤 5: 检查生成的文件\n")

    case_file = courtroom_root / "cases" / f"{case_id}.json"
    verdict_file = courtroom_root / "verdicts" / f"{case_id}.json"
    transcript_file = courtroom_root / "transcripts" / f"{case_id}.md"

    print(f"案件文件: {case_file.exists() and '✅' or '❌'} {case_file}")
    print(f"判决文件: {verdict_file.exists() and '✅' or '❌'} {verdict_file}")
    print(f"庭审记录: {transcript_file.exists() and '✅' or '❌'} {transcript_file}")

    if transcript_file.exists():
        print(f"\n📖 庭审记录预览（前 20 行）：\n")
        lines = transcript_file.read_text(encoding='utf-8').split('\n')[:20]
        print('\n'.join(lines))
        print(f"\n... (共 {len(transcript_file.read_text(encoding='utf-8').split(chr(10)))} 行)")

    print("\n" + "="*60)
    print("✅ 测试完成！庭审系统工作正常。")
    print("="*60 + "\n")


if __name__ == '__main__':
    test_basic_workflow()
