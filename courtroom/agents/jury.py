"""
陪审团 Agent - 提供专家意见和投票
"""
from typing import List
from datetime import datetime

from ..schemas import Motion, JuryVote, VerdictType, Argument


class Juror:
    """陪审员 - 专家 Agent"""

    def __init__(self, name: str, specialty: str):
        self.name = name
        self.specialty = specialty  # 专业领域：security/performance/testing/architecture

    def review(self, motion: Motion, arguments: List[Argument]) -> JuryVote:
        """审查案件并投票"""
        # 根据专业领域分析
        vote, reasoning = self._analyze_by_specialty(motion, arguments)

        return JuryVote(
            juror=self.name,
            vote=vote,
            reasoning=reasoning,
            timestamp=datetime.now()
        )

    def _analyze_by_specialty(self, motion: Motion, arguments: List[Argument]) -> tuple:
        """根据专业领域分析"""
        if self.specialty == "security":
            return self._security_analysis(motion)
        elif self.specialty == "performance":
            return self._performance_analysis(motion)
        elif self.specialty == "testing":
            return self._testing_analysis(motion)
        elif self.specialty == "architecture":
            return self._architecture_analysis(motion)
        else:
            return VerdictType.MODIFIED, "需要更多信息才能做出判断"

    def _security_analysis(self, motion: Motion) -> tuple:
        """安全性分析"""
        # 简化的安全检查
        security_keywords = ['auth', 'password', 'token', 'secret', 'api_key']
        has_security_concern = any(
            keyword in motion.description.lower()
            for keyword in security_keywords
        )

        if has_security_concern:
            return (
                VerdictType.MODIFIED,
                f"作为安全专家，我认为涉及认证/密钥的变更需要额外的安全审查和渗透测试。"
            )
        return (
            VerdictType.APPROVED,
            f"从安全角度看，该变更没有明显的安全风险。"
        )

    def _performance_analysis(self, motion: Motion) -> tuple:
        """性能分析"""
        performance_keywords = ['cache', 'query', 'index', 'optimize', 'slow']
        has_performance_impact = any(
            keyword in motion.description.lower()
            for keyword in performance_keywords
        )

        if has_performance_impact:
            return (
                VerdictType.MODIFIED,
                f"作为性能专家，我建议在批准前进行性能基准测试，确保变更不会降低系统性能。"
            )
        return (
            VerdictType.APPROVED,
            f"从性能角度看，该变更影响可控。"
        )

    def _testing_analysis(self, motion: Motion) -> tuple:
        """测试分析"""
        # 检查是否提到测试
        has_test_plan = 'test' in motion.description.lower()

        if not has_test_plan:
            return (
                VerdictType.MODIFIED,
                f"作为测试专家，我强烈建议添加完整的测试用例，包括单元测试和集成测试。"
            )
        return (
            VerdictType.APPROVED,
            f"测试计划充分，可以批准。"
        )

    def _architecture_analysis(self, motion: Motion) -> tuple:
        """架构分析"""
        if motion.motion_type.value == "architecture":
            return (
                VerdictType.MODIFIED,
                f"作为架构专家，我建议架构变更需要更详细的设计文档和影响分析。"
            )
        return (
            VerdictType.APPROVED,
            f"从架构角度看，该变更符合现有架构设计。"
        )


class Jury:
    """陪审团 - 管理多个陪审员"""

    def __init__(self):
        self.jurors: List[Juror] = [
            Juror("security_expert", "security"),
            Juror("performance_expert", "performance"),
            Juror("testing_expert", "testing"),
            Juror("architecture_expert", "architecture"),
        ]

    def deliberate(self, motion: Motion, arguments: List[Argument]) -> List[JuryVote]:
        """陪审团评议"""
        votes = []
        for juror in self.jurors:
            vote = juror.review(motion, arguments)
            votes.append(vote)
        return votes

    def get_consensus(self, votes: List[JuryVote]) -> VerdictType:
        """获取陪审团共识"""
        vote_counts = {
            VerdictType.APPROVED: 0,
            VerdictType.REJECTED: 0,
            VerdictType.MODIFIED: 0,
        }

        for vote in votes:
            vote_counts[vote.vote] += 1

        # 返回得票最多的意见
        return max(vote_counts, key=vote_counts.get)
