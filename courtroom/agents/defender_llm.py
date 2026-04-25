"""
辩护律师 Agent (LLM 版本) - 质疑动议并指出风险
"""
from typing import List
from ..schemas import Motion, Argument, ArgumentType
from ..llm_client import get_llm_client


class DefenderLLM:
    """辩护律师 Agent - 使用 LLM 生成论点"""

    def __init__(self, use_llm: bool = True):
        """
        初始化辩护律师

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

        prompt = f"""你是一位辩护律师，代表系统稳定性和代码质量，正在质疑以下动议：

**动议标题**: {motion.title}
**动议类型**: {motion.motion_type.value}
**描述**: {motion.description}

**提议的变更**:
{chr(10).join(f"- {c}" for c in motion.proposed_changes)}

**影响的文件**:
{chr(10).join(f"- {f}" for f in motion.affected_files)}

**已知风险**:
{chr(10).join(f"- {r}" for r in motion.risks)}

请生成一段专业的开场陈述，指出这个动议可能存在的问题和风险。
陈述应该：
1. 简洁明了（200-300字）
2. 指出潜在风险和问题
3. 提出需要澄清的关键问题
4. 保持专业和建设性的语气
5. 不是完全反对，而是要求更多证据

直接返回陈述内容，不要包含其他说明。"""

        system = "你是一位经验丰富的辩护律师，擅长发现提案中的漏洞和风险，但保持建设性态度。"

        return self.llm.generate(prompt, system=system, temperature=0.8)

    def challenge(self, motion: Motion, prosecutor_arguments: List[Argument]) -> str:
        """质询检察官的论点"""
        if not self.use_llm:
            return self._rule_based_challenge(motion, prosecutor_arguments)

        prosecutor_points = "\n".join(
            f"{i+1}. {arg.content}" for i, arg in enumerate(prosecutor_arguments)
        )

        prompt = f"""你是辩护律师，检察官提出了以下论点支持动议：

{prosecutor_points}

**动议信息**:
- 标题: {motion.title}
- 描述: {motion.description}
- 影响文件: {', '.join(motion.affected_files[:3])}{'...' if len(motion.affected_files) > 3 else ''}
- 已知风险: {', '.join(motion.risks)}

请生成有力的质询，指出检察官论点中的漏洞和未解决的问题。
质询应该：
1. 针对具体论点提出质疑
2. 指出缺失的信息或证据
3. 强调潜在的负面影响
4. 提出需要回答的关键问题
5. 保持专业和建设性

直接返回质询内容，不要包含其他说明。"""

        system = "你是一位经验丰富的辩护律师，擅长发现论点中的漏洞并提出尖锐的问题。"

        return self.llm.generate(prompt, system=system, temperature=0.8)

    def closing_statement(self, motion: Motion, debate_summary: str) -> str:
        """生成结案陈词"""
        if not self.use_llm:
            return self._rule_based_closing(motion)

        prompt = f"""你是辩护律师，经过充分辩论后，现在要做结案陈词。

**动议**: {motion.title}

**辩论摘要**:
{debate_summary}

请生成简洁的结案陈词，总结你的立场。
结案陈词应该：
1. 简短（100-150字）
2. 承认检察官已回应部分质疑
3. 如果风险可控，可以有条件地不反对
4. 提出必须满足的条件
5. 保持专业和建设性

直接返回结案陈词，不要包含其他说明。"""

        system = "你是一位经验丰富的辩护律师，擅长做平衡的结案陈词。"

        return self.llm.generate(prompt, system=system, temperature=0.8)

    def _rule_based_opening(self, motion: Motion) -> str:
        """规则引擎版本的开场陈述"""
        return f"""尊敬的法官：

我代表系统稳定性和代码质量，对动议 "{motion.title}" 提出以下质疑：

【风险分析】
{chr(10).join(f"- {r}" for r in motion.risks)}

【潜在问题】
- 新功能可能引入未知 Bug
- 增加代码复杂度，提高维护成本

【需要澄清的问题】
1. 是否有充分的测试覆盖？
2. 回滚方案是否完善？
3. 是否考虑了边界情况？
4. 对现有功能的影响评估是否充分？

我们需要更多证据来证明这些变更是安全的。"""

    def _rule_based_challenge(self, motion: Motion, prosecutor_arguments: List[Argument]) -> str:
        """规则引擎版本的质询"""
        return f"""针对检察官的陈述，我有以下质疑：

1. **测试覆盖不足**: 提案中没有提到具体的测试计划
2. **回滚风险**: 如果变更出现问题，回滚是否会影响已有数据？
3. **性能影响**: 这些变更对系统性能的影响评估在哪里？
4. **兼容性**: 是否考虑了向后兼容性？

这些都是关键问题，必须在批准前得到解答。"""

    def _rule_based_closing(self, motion: Motion) -> str:
        """规则引擎版本的结案陈词"""
        return f"""尊敬的法官：

经过充分的辩论，检察官已经回应了我的大部分质疑。

虽然仍有一些风险，但如果能够满足以下条件，我不反对批准该动议：

1. 必须有完整的测试覆盖
2. 必须有明确的回滚预案
3. 必须进行充分的代码审查
4. 建议分阶段推出，先在测试环境验证

谢谢！"""
