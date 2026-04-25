"""
法官 Agent (LLM 版本) - 主持庭审并做出判决
"""
from typing import List, Dict, Any
from ..schemas import Motion, Verdict, VerdictType, Argument
from ..llm_client import get_llm_client


class JudgeLLM:
    """法官 Agent - 使用 LLM 生成判决"""

    def __init__(self, use_llm: bool = True):
        """
        初始化法官

        Args:
            use_llm: 是否使用 LLM，False 则使用规则引擎
        """
        self.use_llm = use_llm
        if use_llm:
            try:
                self.llm = get_llm_client()
            except ValueError:
                print("⚠️ 未找到 API 密钥，回退到规则引擎模式")
                self.use_llm = False

    def make_verdict(
        self,
        motion: Motion,
        prosecutor_arguments: List[Argument],
        defender_arguments: List[Argument],
        jury_votes: Dict[str, str]
    ) -> Verdict:
        """
        做出判决

        Args:
            motion: 动议
            prosecutor_arguments: 检察官论点
            defender_arguments: 辩护律师论点
            jury_votes: 陪审团投票结果

        Returns:
            判决
        """
        if not self.use_llm:
            return self._rule_based_verdict(motion, jury_votes)

        # 构建辩论摘要
        debate_summary = self._build_debate_summary(
            prosecutor_arguments, defender_arguments, jury_votes
        )

        prompt = f"""你是一位法官，需要对以下动议做出判决：

**动议标题**: {motion.title}
**动议类型**: {motion.motion_type.value}
**描述**: {motion.description}

**提议的变更**:
{chr(10).join(f"- {c}" for c in motion.proposed_changes)}

**影响的文件**:
{chr(10).join(f"- {f}" for f in motion.affected_files)}

**预期收益**:
{chr(10).join(f"- {b}" for b in motion.benefits)}

**已知风险**:
{chr(10).join(f"- {r}" for r in motion.risks)}

**辩论摘要**:
{debate_summary}

**陪审团投票**:
{self._format_jury_votes(jury_votes)}

请做出判决，返回 JSON 格式：
{{
  "verdict_type": "approved|rejected|approved_with_modifications|deferred",
  "reasoning": "判决理由（200-300字）",
  "approved_changes": ["批准的变更1", "批准的变更2", ...],
  "execution_plan": ["执行步骤1", "执行步骤2", ...]
}}

判决应该：
1. 综合考虑双方论点和陪审团意见
2. 给出清晰的理由
3. 如果批准，提供具体的执行计划
4. 如果有条件批准，明确列出条件
5. 保持公正和专业"""

        system = "你是一位经验丰富的法官，擅长综合各方意见做出公正的判决。"

        try:
            result = self.llm.generate_json(prompt, system=system)

            return Verdict(
                case_id=motion.case_id,
                verdict_type=VerdictType(result["verdict_type"]),
                reasoning=result["reasoning"],
                approved_changes=result.get("approved_changes", motion.proposed_changes),
                execution_plan=result.get("execution_plan", []),
                conditions=result.get("conditions", [])
            )
        except Exception as e:
            print(f"⚠️ LLM 判决生成失败，回退到规则引擎: {e}")
            return self._rule_based_verdict(motion, jury_votes)

    def _build_debate_summary(
        self,
        prosecutor_arguments: List[Argument],
        defender_arguments: List[Argument],
        jury_votes: Dict[str, str]
    ) -> str:
        """构建辩论摘要"""
        summary_parts = []

        if prosecutor_arguments:
            summary_parts.append("**检察官论点**:")
            for i, arg in enumerate(prosecutor_arguments[:3], 1):
                summary_parts.append(f"{i}. {arg.content[:200]}...")

        if defender_arguments:
            summary_parts.append("\n**辩护律师论点**:")
            for i, arg in enumerate(defender_arguments[:3], 1):
                summary_parts.append(f"{i}. {arg.content[:200]}...")

        return "\n".join(summary_parts)

    def _format_jury_votes(self, jury_votes: Dict[str, str]) -> str:
        """格式化陪审团投票"""
        vote_counts = {}
        for vote in jury_votes.values():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1

        lines = []
        for vote, count in vote_counts.items():
            lines.append(f"- {vote}: {count} 票")

        return "\n".join(lines)

    def _rule_based_verdict(self, motion: Motion, jury_votes: Dict[str, str]) -> Verdict:
        """规则引擎版本的判决"""
        # 统计陪审团投票
        vote_counts = {}
        for vote in jury_votes.values():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1

        # 获取多数意见
        majority_vote = max(vote_counts.items(), key=lambda x: x[1])[0]

        # 根据多数意见决定判决类型
        verdict_type_map = {
            "approved": VerdictType.APPROVED,
            "rejected": VerdictType.REJECTED,
            "modified": VerdictType.APPROVED_WITH_MODIFICATIONS,
            "deferred": VerdictType.DEFERRED
        }
        verdict_type = verdict_type_map.get(majority_vote, VerdictType.APPROVED)

        reasoning = f"""经过充分的庭审辩论和陪审团评议，本庭认为：

1. 检察官提出的变更具有一定的必要性和合理性
2. 辩护律师提出的风险质疑也值得重视
3. 陪审团的专家意见倾向于：{majority_vote}

综合考虑各方意见，本庭做出如下判决。"""

        execution_plan = [
            f"1. 审查影响的文件：{', '.join(motion.affected_files[:3])}{'...' if len(motion.affected_files) > 3 else ''}",
            "2. 实施批准的变更",
            "3. 编写或更新测试用例",
            "4. 进行代码审查",
            "5. 合并到主分支"
        ]

        return Verdict(
            case_id=motion.case_id,
            verdict_type=verdict_type,
            reasoning=reasoning,
            approved_changes=motion.proposed_changes,
            execution_plan=execution_plan,
            conditions=[]
        )
