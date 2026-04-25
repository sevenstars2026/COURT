"""
检察官 Agent (LLM 版本) - 支持动议并提供论据
"""
from typing import List
from ..schemas import Motion, Argument, ArgumentType
from ..llm_client import get_llm_client


class ProsecutorLLM:
    """检察官 Agent - 使用 LLM 生成论点"""

    def __init__(self, use_llm: bool = True):
        """
        初始化检察官

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

    def opening_statement(self, motion: Motion) -> str:
        """生成开场陈述"""
        if not self.use_llm:
            return self._rule_based_opening(motion)

        prompt = f"""你是一位检察官，正在法庭上为以下动议进行开场陈述：

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

请生成一段专业、有说服力的开场陈述，说明为什么应该批准这个动议。
陈述应该：
1. 简洁明了（200-300字）
2. 强调收益和必要性
3. 承认风险但说明可控
4. 使用正式的法庭语言

直接返回陈述内容，不要包含其他说明。"""

        system = "你是一位经验丰富的检察官，擅长在法庭上进行有说服力的陈述。"

        return self.llm.generate(prompt, system=system, temperature=0.8)

    def rebut(self, motion: Motion, defender_arguments: List[Argument]) -> str:
        """反驳辩护律师的论点"""
        if not self.use_llm:
            return self._rule_based_rebut(motion, defender_arguments)

        defender_points = "\n".join(
            f"{i+1}. {arg.content}" for i, arg in enumerate(defender_arguments)
        )

        prompt = f"""你是检察官，辩护律师对你的动议提出了以下质疑：

{defender_points}

**动议信息**:
- 标题: {motion.title}
- 描述: {motion.description}
- 收益: {', '.join(motion.benefits)}
- 风险: {', '.join(motion.risks)}

请生成有力的反驳论点，回应辩护律师的质疑。
反驳应该：
1. 逐点回应主要质疑
2. 提供具体的缓解措施
3. 强调不做变更的代价
4. 保持专业和尊重的语气

直接返回反驳内容，不要包含其他说明。"""

        system = "你是一位经验丰富的检察官，擅长反驳对方论点并提供有力证据。"

        return self.llm.generate(prompt, system=system, temperature=0.8)

    def closing_statement(self, motion: Motion, debate_summary: str) -> str:
        """生成结案陈词"""
        if not self.use_llm:
            return self._rule_based_closing(motion)

        prompt = f"""你是检察官，经过充分辩论后，现在要做结案陈词。

**动议**: {motion.title}

**辩论摘要**:
{debate_summary}

请生成简洁有力的结案陈词，总结你的立场并请求法庭批准。
结案陈词应该：
1. 简短（100-150字）
2. 总结核心论点
3. 强调动议的价值
4. 正式请求批准

直接返回结案陈词，不要包含其他说明。"""

        system = "你是一位经验丰富的检察官，擅长做有说服力的结案陈词。"

        return self.llm.generate(prompt, system=system, temperature=0.8)

    def _rule_based_opening(self, motion: Motion) -> str:
        """规则引擎版本的开场陈述"""
        return f"""尊敬的法官，各位陪审员：

我代表开发团队提出动议：{motion.title}

【背景】
{motion.description}

【提议的变更】
{chr(10).join(f"- {c}" for c in motion.proposed_changes)}

【预期收益】
{chr(10).join(f"- {b}" for b in motion.benefits)}

【已知风险】
{chr(10).join(f"- {r}" for r in motion.risks)}

我们认为这些变更是必要的，风险是可控的。请法庭批准该动议。"""

    def _rule_based_rebut(self, motion: Motion, defender_arguments: List[Argument]) -> str:
        """规则引擎版本的反驳"""
        return f"""针对辩护律师的质疑，我有以下回应：

辩护律师提到的风险确实存在，但我们已经有相应的缓解措施：

1. 我们会进行充分的测试
2. 变更会分阶段推出
3. 我们有回滚预案

相比风险，不做这个变更的代价更大。请法庭考虑整体利益。"""

    def _rule_based_closing(self, motion: Motion) -> str:
        """规则引擎版本的结案陈词"""
        return f"""尊敬的法官：

经过充分的辩论，我相信法庭已经清楚地了解了这个动议的必要性和可行性。

{motion.title} 不仅能够解决当前的问题，还能为未来的发展奠定基础。

我们请求法庭批准该动议，让我们能够尽快实施这些改进。

谢谢！"""
