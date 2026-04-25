"""
检察官 Agent - 提出变更提案，推进任务
"""
from typing import List
from datetime import datetime

from ..schemas import Motion, Argument, ArgumentType, MotionType


class Prosecutor:
    """检察官 - 提出动议，为变更辩护"""

    def __init__(self, name: str = "prosecutor"):
        self.name = name

    def file_motion(
        self,
        case_id: str,
        title: str,
        motion_type: MotionType,
        description: str,
        proposed_changes: List[str],
        affected_files: List[str],
        risks: List[str] = None,
        benefits: List[str] = None,
        priority: int = 5
    ) -> Motion:
        """提交动议"""
        return Motion(
            case_id=case_id,
            title=title,
            motion_type=motion_type,
            description=description,
            proposer=self.name,
            proposed_changes=proposed_changes,
            affected_files=affected_files,
            risks=risks or [],
            benefits=benefits or [],
            priority=priority,
            filed_at=datetime.now()
        )

    def opening_statement(self, motion: Motion) -> Argument:
        """开场陈述"""
        content = f"""
尊敬的法官，各位陪审员：

我代表开发团队提出动议：{motion.title}

【背景】
{motion.description}

【提议的变更】
{self._format_list(motion.proposed_changes)}

【预期收益】
{self._format_list(motion.benefits)}

【已知风险】
{self._format_list(motion.risks)}

我们认为这些变更是必要的，风险是可控的。请法庭批准该动议。
        """.strip()

        return Argument(
            speaker=self.name,
            argument_type=ArgumentType.OPENING,
            content=content,
            timestamp=datetime.now()
        )

    def rebut(self, defender_argument: Argument, motion: Motion) -> Argument:
        """反驳辩护律师的论点"""
        # 实际应该调用 LLM 生成反驳
        content = f"""
针对辩护律师的质疑，我有以下回应：

辩护律师提到的风险确实存在，但我们已经有相应的缓解措施：

1. 我们会进行充分的测试
2. 变更会分阶段推出
3. 我们有回滚预案

相比风险，不做这个变更的代价更大。请法庭考虑整体利益。
        """.strip()

        return Argument(
            speaker=self.name,
            argument_type=ArgumentType.REBUTTAL,
            content=content,
            timestamp=datetime.now()
        )

    def closing_statement(self, motion: Motion) -> Argument:
        """结案陈词"""
        content = f"""
尊敬的法官：

经过充分的辩论，我相信法庭已经清楚地了解了这个动议的必要性和可行性。

{motion.title} 不仅能够解决当前的问题，还能为未来的发展奠定基础。

我们请求法庭批准该动议，让我们能够尽快实施这些改进。

谢谢！
        """.strip()

        return Argument(
            speaker=self.name,
            argument_type=ArgumentType.CLOSING,
            content=content,
            timestamp=datetime.now()
        )

    def _format_list(self, items: List[str]) -> str:
        """格式化列表"""
        if not items:
            return "（无）"
        return "\n".join(f"- {item}" for item in items)
