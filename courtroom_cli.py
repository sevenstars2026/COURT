"""
庭审系统 CLI - 命令行接口
"""
import sys
import argparse
from pathlib import Path

from courtroom import Court, MotionType


def main():
    parser = argparse.ArgumentParser(
        description="⚖️ Courtroom Collaboration System - 庭审式 Agent 协作框架"
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # file-motion 命令
    file_parser = subparsers.add_parser('file-motion', help='提交动议')
    file_parser.add_argument('--title', required=True, help='动议标题')
    file_parser.add_argument('--type', required=True,
                            choices=['new_feature', 'refactor', 'bug_fix',
                                   'architecture', 'security', 'performance'],
                            help='动议类型')
    file_parser.add_argument('--description', required=True, help='详细描述')
    file_parser.add_argument('--changes', nargs='+', required=True, help='提议的变更')
    file_parser.add_argument('--files', nargs='+', required=True, help='影响的文件')
    file_parser.add_argument('--risks', nargs='+', default=[], help='已知风险')
    file_parser.add_argument('--benefits', nargs='+', default=[], help='预期收益')
    file_parser.add_argument('--priority', type=int, default=5, help='优先级 1-10')

    # trial 命令
    trial_parser = subparsers.add_parser('trial', help='开庭审理')
    trial_parser.add_argument('--case-id', required=True, help='案件编号')
    trial_parser.add_argument('--rounds', type=int, default=3, help='辩论轮数')

    # show-verdict 命令
    verdict_parser = subparsers.add_parser('show-verdict', help='查看判决')
    verdict_parser.add_argument('--case-id', required=True, help='案件编号')

    # list-cases 命令
    list_parser = subparsers.add_parser('list-cases', help='列出案件')
    list_parser.add_argument('--all', action='store_true', help='包括已结案件')

    # stats 命令
    subparsers.add_parser('stats', help='查看统计数据')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 创建法庭实例
    courtroom_root = Path(__file__).parent / "courtroom"
    court = Court(courtroom_root)

    # 执行命令
    if args.command == 'file-motion':
        result = court.file_motion(
            title=args.title,
            motion_type=MotionType(args.type),
            description=args.description,
            proposed_changes=args.changes,
            affected_files=args.files,
            risks=args.risks,
            benefits=args.benefits,
            priority=args.priority
        )
        print(result)

    elif args.command == 'trial':
        result = court.trial(args.case_id, max_rounds=args.rounds)
        print(result)

    elif args.command == 'show-verdict':
        result = court.show_verdict(args.case_id)
        print(result)

    elif args.command == 'list-cases':
        result = court.list_cases(active_only=not args.all)
        print(result)

    elif args.command == 'stats':
        result = court.get_statistics()
        print(result)


if __name__ == '__main__':
    main()
