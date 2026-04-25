"""
多模型陪审团系统 - 用多个弱模型提升决策鲁棒性
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import random


class JurorModel(str, Enum):
    """陪审员模型"""
    # 免费/廉价模型
    LOCAL_7B = "local_7b"              # 本地 7B 模型
    GPT4O_MINI = "gpt4o_mini"          # GPT-4o-mini ($0.15/1M tokens)
    DEEPSEEK_V3 = "deepseek_v3"        # DeepSeek-V3 ($0.27/1M tokens)
    CLAUDE_HAIKU = "claude_haiku"      # Claude Haiku ($0.25/1M tokens)
    GEMINI_FLASH = "gemini_flash"      # Gemini Flash (免费)

    # 强模型（法官用）
    CLAUDE_SONNET = "claude_sonnet"    # Claude Sonnet ($3/1M tokens)
    GPT4O = "gpt4o"                    # GPT-4o ($2.5/1M tokens)


class VoteType(str, Enum):
    """投票类型"""
    APPROVE = "approve"                # 同意
    REJECT = "reject"                  # 反对
    MODIFY = "modify"                  # 需修改


class JurorVote(BaseModel):
    """陪审员投票"""
    juror_id: str
    juror_model: JurorModel
    vote: VoteType
    reasoning: str  # 一句话理由
    confidence: float = Field(ge=0.0, le=1.0)  # 置信度
    voted_at: datetime = Field(default_factory=datetime.now)


class VotingResult(BaseModel):
    """投票结果"""
    votes: List[JurorVote]
    consensus: VoteType  # 多数意见
    consensus_ratio: float  # 共识比例（如 5:0 = 1.0, 3:2 = 0.6）
    has_strong_consensus: bool  # 是否有强共识（>= 80%）
    has_split: bool  # 是否分歧（差距 <= 1 票）
    needs_expert_witness: bool  # 是否需要专家证人
    summary: str  # 投票摘要


class MultiModelJury:
    """多模型陪审团"""

    def __init__(
        self,
        juror_models: Optional[List[JurorModel]] = None,
        use_real_models: bool = False
    ):
        """
        初始化陪审团

        Args:
            juror_models: 陪审员模型列表，默认使用 5 个廉价模型
            use_real_models: 是否使用真实模型（需要 API key）
        """
        if juror_models is None:
            # 默认配置：5 个廉价模型
            juror_models = [
                JurorModel.LOCAL_7B,
                JurorModel.GPT4O_MINI,
                JurorModel.DEEPSEEK_V3,
                JurorModel.CLAUDE_HAIKU,
                JurorModel.GEMINI_FLASH
            ]

        self.juror_models = juror_models
        self.use_real_models = use_real_models

    def deliberate(
        self,
        motion_summary: str,
        prosecutor_arguments: List[str],
        defender_arguments: List[str]
    ) -> VotingResult:
        """
        陪审团评议

        Args:
            motion_summary: 动议摘要
            prosecutor_arguments: 检察官论点
            defender_arguments: 辩护律师论点

        Returns:
            投票结果
        """
        votes = []

        for i, model in enumerate(self.juror_models):
            vote = self._get_juror_vote(
                juror_id=f"juror_{i+1}",
                model=model,
                motion_summary=motion_summary,
                prosecutor_arguments=prosecutor_arguments,
                defender_arguments=defender_arguments
            )
            votes.append(vote)

        # 分析投票结果
        return self._analyze_votes(votes)

    def _get_juror_vote(
        self,
        juror_id: str,
        model: JurorModel,
        motion_summary: str,
        prosecutor_arguments: List[str],
        defender_arguments: List[str]
    ) -> JurorVote:
        """
        获取单个陪审员的投票

        Args:
            juror_id: 陪审员 ID
            model: 使用的模型
            motion_summary: 动议摘要
            prosecutor_arguments: 检察官论点
            defender_arguments: 辩护律师论点

        Returns:
            投票
        """
        if self.use_real_models:
            # 调用真实模型
            return self._call_real_model(
                juror_id, model, motion_summary,
                prosecutor_arguments, defender_arguments
            )
        else:
            # 使用模拟投票（用于测试）
            return self._simulate_vote(
                juror_id, model, motion_summary,
                prosecutor_arguments, defender_arguments
            )

    def _call_real_model(
        self,
        juror_id: str,
        model: JurorModel,
        motion_summary: str,
        prosecutor_arguments: List[str],
        defender_arguments: List[str]
    ) -> JurorVote:
        """
        调用真实模型获取投票

        Args:
            juror_id: 陪审员 ID
            model: 模型
            motion_summary: 动议摘要
            prosecutor_arguments: 检察官论点
            defender_arguments: 辩护律师论点

        Returns:
            投票
        """
        # 构建提示
        prompt = f"""你是陪审员，需要对以下动议投票：

动议摘要：
{motion_summary}

检察官论点：
{chr(10).join(f"- {arg}" for arg in prosecutor_arguments)}

辩护律师论点：
{chr(10).join(f"- {arg}" for arg in defender_arguments)}

请投票并给出一句话理由。

投票选项：
- approve: 同意批准
- reject: 反对批准
- modify: 需要修改后批准

请以 JSON 格式返回：
{{
  "vote": "approve|reject|modify",
  "reasoning": "一句话理由",
  "confidence": 0.0-1.0
}}
"""

        # 根据模型类型调用不同的 API
        # 这里简化处理，实际需要集成各个模型的 API
        if model == JurorModel.CLAUDE_HAIKU:
            # 调用 Claude Haiku
            pass
        elif model == JurorModel.GPT4O_MINI:
            # 调用 GPT-4o-mini
            pass
        # ... 其他模型

        # 临时返回模拟结果
        return self._simulate_vote(
            juror_id, model, motion_summary,
            prosecutor_arguments, defender_arguments
        )

    def _simulate_vote(
        self,
        juror_id: str,
        model: JurorModel,
        motion_summary: str,
        prosecutor_arguments: List[str],
        defender_arguments: List[str]
    ) -> JurorVote:
        """
        模拟投票（用于测试）

        Args:
            juror_id: 陪审员 ID
            model: 模型
            motion_summary: 动议摘要
            prosecutor_arguments: 检察官论点
            defender_arguments: 辩护律师论点

        Returns:
            投票
        """
        # 简单的模拟逻辑：根据论点数量和模型特性
        prosecutor_score = len(prosecutor_arguments) * 2
        defender_score = len(defender_arguments) * 2

        # 不同模型有不同的倾向
        if model == JurorModel.LOCAL_7B:
            # 本地模型更保守
            defender_score += 1
        elif model == JurorModel.DEEPSEEK_V3:
            # DeepSeek 更激进
            prosecutor_score += 1

        # 添加随机性
        prosecutor_score += random.randint(-1, 1)
        defender_score += random.randint(-1, 1)

        # 决定投票
        if prosecutor_score > defender_score * 1.5:
            vote = VoteType.APPROVE
            reasoning = "检察官论点更有说服力，收益明显"
            confidence = 0.8
        elif defender_score > prosecutor_score * 1.5:
            vote = VoteType.REJECT
            reasoning = "辩护律师提出的风险值得重视"
            confidence = 0.8
        else:
            vote = VoteType.MODIFY
            reasoning = "双方论点都有道理，建议修改后批准"
            confidence = 0.6

        return JurorVote(
            juror_id=juror_id,
            juror_model=model,
            vote=vote,
            reasoning=reasoning,
            confidence=confidence
        )

    def _analyze_votes(self, votes: List[JurorVote]) -> VotingResult:
        """
        分析投票结果

        Args:
            votes: 投票列表

        Returns:
            投票结果
        """
        # 统计投票
        vote_counts = {
            VoteType.APPROVE: 0,
            VoteType.REJECT: 0,
            VoteType.MODIFY: 0
        }

        for vote in votes:
            vote_counts[vote.vote] += 1

        total_votes = len(votes)

        # 找出多数意见
        consensus = max(vote_counts, key=vote_counts.get)
        consensus_count = vote_counts[consensus]
        consensus_ratio = consensus_count / total_votes

        # 判断是否有强共识（>= 80%）
        has_strong_consensus = consensus_ratio >= 0.8

        # 判断是否分歧（最高票和次高票差距 <= 1）
        sorted_counts = sorted(vote_counts.values(), reverse=True)
        has_split = (sorted_counts[0] - sorted_counts[1]) <= 1

        # 是否需要专家证人（分歧时）
        needs_expert_witness = has_split

        # 生成摘要
        summary = self._generate_summary(
            votes, consensus, consensus_ratio,
            has_strong_consensus, has_split
        )

        return VotingResult(
            votes=votes,
            consensus=consensus,
            consensus_ratio=consensus_ratio,
            has_strong_consensus=has_strong_consensus,
            has_split=has_split,
            needs_expert_witness=needs_expert_witness,
            summary=summary
        )

    def _generate_summary(
        self,
        votes: List[JurorVote],
        consensus: VoteType,
        consensus_ratio: float,
        has_strong_consensus: bool,
        has_split: bool
    ) -> str:
        """生成投票摘要"""
        vote_counts = {}
        for vote in votes:
            vote_counts[vote.vote] = vote_counts.get(vote.vote, 0) + 1

        summary_parts = []

        # 投票分布
        vote_dist = ", ".join(f"{v.value}: {c}" for v, c in vote_counts.items())
        summary_parts.append(f"投票分布：{vote_dist}")

        # 多数意见
        summary_parts.append(f"多数意见：{consensus.value} ({consensus_ratio:.0%})")

        # 共识强度
        if has_strong_consensus:
            summary_parts.append("✅ 强共识（>= 80%）")
        elif has_split:
            summary_parts.append("⚠️ 存在分歧，建议加时辩论")
        else:
            summary_parts.append("📊 一般共识")

        # 主要理由
        consensus_votes = [v for v in votes if v.vote == consensus]
        if consensus_votes:
            main_reasoning = consensus_votes[0].reasoning
            summary_parts.append(f"主要理由：{main_reasoning}")

        return "\n".join(summary_parts)

    def get_cost_estimate(self) -> Dict[str, Any]:
        """
        估算成本

        Returns:
            成本估算
        """
        # 每个陪审员约 500 tokens 输入 + 100 tokens 输出
        tokens_per_juror = 600

        model_costs = {
            JurorModel.LOCAL_7B: 0.0,  # 免费
            JurorModel.GPT4O_MINI: 0.15 / 1_000_000,  # $0.15/1M tokens
            JurorModel.DEEPSEEK_V3: 0.27 / 1_000_000,
            JurorModel.CLAUDE_HAIKU: 0.25 / 1_000_000,
            JurorModel.GEMINI_FLASH: 0.0,  # 免费
        }

        total_cost = 0.0
        cost_breakdown = {}

        for model in self.juror_models:
            cost = model_costs.get(model, 0.0) * tokens_per_juror
            total_cost += cost
            cost_breakdown[model.value] = cost

        return {
            "total_cost": total_cost,
            "cost_per_juror": total_cost / len(self.juror_models),
            "breakdown": cost_breakdown,
            "estimated_tokens": tokens_per_juror * len(self.juror_models)
        }
