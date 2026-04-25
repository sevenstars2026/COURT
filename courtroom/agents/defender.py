"""
辩护律师 Agent - 质疑提案，发现风险
"""
from typing import List
from datetime import datetime

from ..schemas import Motion, Argument, ArgumentType


class Defender:
    """辩护律师 - 质疑动议，保护系统稳定性"""

    def __init__(self, name: str = "defender"):
        self.name = name

    def opening_statement(self, motion: Motion) -> Argument:
        """开场陈述 - 提出质疑"""
        content = f"""
尊敬的法官：

我代表系统稳定性和代码质量，对动议 "{motion.title}" 提出以下质疑：

【风险分析】
{self._format_list(motion.risks)}

【潜在问题】
{self._analyze_risks(motion)}

【需要澄清的问题】
1. 是否有充分的测试覆盖？
2. 回滚方案是否完善？
3. 是否考虑了边界情况？
4. 对现有功能的影响评估是否充分？

我们需要更多证据来证明这些变更是安全的。
        """.strip()

        return Argument(
            speaker=self.name,
            argument_type=ArgumentType.OPENING,
            content=content,
            timestamp=datetime.now()
        )

    def cross_examine(self, prosecutor_argument: Argument, motion: Motion) -> Argument:
        """交叉询问 - 质疑检察官的论点"""
        content = f"""
针对检察官的陈述，我有以下质疑：

1. **测试覆盖不足**: 提案中没有提到具体的测试计划
2. **回滚风险**: 如果变更出现问题，回滚是否会影响已有数据？
3. **性能影响**: 这些变更对系统性能的影响评估在哪里？
4. **兼容性**: 是否考虑了向后兼容性？

这些都是关键问题，必须在批准前得到解答。
        """.strip()

        return Argument(
            speaker=self.name,
            argument_type=ArgumentType.REBUTTAL,
            content=content,
            timestamp=datetime.now()
        )

    def closing_statement(self, motion: Motion, concerns_addressed: bool = False) -> Argument:
        """结案陈词"""
        if concerns_addressed:
            content = f"""
尊敬的法官：

经过充分的辩论，检察官已经回应了我的大部分质疑。

虽然仍有一些风险，但如果能够满足以下条件，我不反对批准该动议：

1. 必须有完整的测试覆盖
2. 必须有明确的回滚预案
3. 必须进行充分的代码审查
4. 建议分阶段推出，先在测试环境验证

谢谢！
            """.strip()
        else:
            content = f"""
尊敬的法官：

检察官未能充分回应我的质疑，风险依然存在。

基于系统稳定性的考虑，我建议驳回该动议，或要求提供更多证据后再审理。

谢谢！
            """.strip()

        return Argument(
            speaker=self.name,
            argument_type=ArgumentType.CLOSING,
            content=content,
            timestamp=datetime.now()
        )

    def _analyze_risks(self, motion: Motion) -> str:
        """分析风险"""
        risks = []

        # 根据动议类型分析特定风险
        if motion.motion_type.value == "new_feature":
            risks.append("- 新功能可能引入未知 Bug")
            risks.append("- 增加代码复杂度，提高维护成本")

        if motion.motion_type.value == "refactor":
            risks.append("- 重构可能破坏现有功能")
            risks.append("- 需要大量回归测试")

        if motion.motion_type.value == "architecture":
            risks.append("- 架构变更影响范围广")
            risks.append("- 可能需要数据迁移")

        # 根据影响文件数量评估风险
        if len(motion.affected_files) > 5:
            risks.append("- 影响文件过多，变更范围过大")

        if not risks:
            risks.append("- 需要进一步评估潜在风险")

        return "\n".join(risks)

    def _format_list(self, items: List[str]) -> str:
        """格式化列表"""
        if not items:
            return "（检察官未充分说明风险）"
        return "\n".join(f"- {item}" for item in items)
