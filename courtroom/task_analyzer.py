"""
任务复杂度分析器
根据动议和判决内容评估任务复杂度,为执行策略提供依据
"""
from enum import Enum
from typing import Dict, List, Optional
from pathlib import Path

from .schemas import Motion, Verdict, MotionType


class TaskComplexity(Enum):
    """任务复杂度等级"""
    TRIVIAL = "trivial"      # 微小任务 (1分钟内)
    SIMPLE = "simple"        # 简单任务 (5分钟内)
    MODERATE = "moderate"    # 中等任务 (15分钟内)
    COMPLEX = "complex"      # 复杂任务 (30分钟内)
    VERY_COMPLEX = "very_complex"  # 极复杂任务 (60分钟内)


class TaskAnalyzer:
    """任务复杂度分析器"""

    def __init__(self):
        # 复杂度权重配置
        self.weights = {
            "file_count": 2.0,
            "change_count": 1.5,
            "description_length": 0.5,
            "motion_type": 1.0,
            "risk_count": 1.0,
            "has_architecture": 3.0,
            "has_performance": 2.0,
            "has_security": 2.5,
        }

    def analyze(self, motion: Motion, verdict: Optional[Verdict] = None) -> Dict:
        """
        分析任务复杂度

        Args:
            motion: 动议对象
            verdict: 判决对象(可选)

        Returns:
            分析结果字典
        """
        score = 0.0
        factors = {}

        # 1. 文件数量分析
        file_count = len(motion.affected_files) if motion.affected_files else 0
        file_score = self._score_file_count(file_count)
        score += file_score * self.weights["file_count"]
        factors["file_count"] = {"value": file_count, "score": file_score}

        # 2. 变更数量分析
        change_count = len(motion.proposed_changes) if motion.proposed_changes else 0
        if verdict and verdict.approved_changes:
            change_count = len(verdict.approved_changes)
        change_score = self._score_change_count(change_count)
        score += change_score * self.weights["change_count"]
        factors["change_count"] = {"value": change_count, "score": change_score}

        # 3. 描述长度分析
        desc_length = len(motion.description) if motion.description else 0
        desc_score = self._score_description_length(desc_length)
        score += desc_score * self.weights["description_length"]
        factors["description_length"] = {"value": desc_length, "score": desc_score}

        # 4. 动议类型分析
        type_score = self._score_motion_type(motion.motion_type)
        score += type_score * self.weights["motion_type"]
        factors["motion_type"] = {"value": motion.motion_type.value, "score": type_score}

        # 5. 风险数量分析
        risk_count = len(motion.risks) if motion.risks else 0
        risk_score = self._score_risk_count(risk_count)
        score += risk_score * self.weights["risk_count"]
        factors["risk_count"] = {"value": risk_count, "score": risk_score}

        # 6. 关键词分析
        text = f"{motion.title} {motion.description}".lower()

        if any(kw in text for kw in ["架构", "architecture", "重构", "refactor", "设计", "design"]):
            score += self.weights["has_architecture"]
            factors["has_architecture"] = True

        if any(kw in text for kw in ["性能", "performance", "优化", "optimize", "加速", "缓存"]):
            score += self.weights["has_performance"]
            factors["has_performance"] = True

        if any(kw in text for kw in ["安全", "security", "漏洞", "vulnerability", "加密", "认证"]):
            score += self.weights["has_security"]
            factors["has_security"] = True

        # 7. 判决执行计划分析
        if verdict and verdict.execution_plan:
            plan_steps = len(verdict.execution_plan)
            plan_score = self._score_execution_plan(plan_steps)
            score += plan_score * 1.5
            factors["execution_plan_steps"] = {"value": plan_steps, "score": plan_score}

        # 确定复杂度等级
        complexity = self._determine_complexity(score)

        return {
            "complexity": complexity,
            "score": score,
            "factors": factors,
            "recommendation": self._get_recommendation(complexity)
        }

    def _score_file_count(self, count: int) -> float:
        """文件数量评分"""
        if count == 0:
            return 1.0
        elif count <= 2:
            return 2.0
        elif count <= 5:
            return 4.0
        elif count <= 10:
            return 6.0
        else:
            return 8.0

    def _score_change_count(self, count: int) -> float:
        """变更数量评分"""
        if count == 0:
            return 1.0
        elif count <= 3:
            return 2.0
        elif count <= 8:
            return 4.0
        elif count <= 15:
            return 6.0
        else:
            return 8.0

    def _score_description_length(self, length: int) -> float:
        """描述长度评分"""
        if length < 50:
            return 1.0
        elif length < 200:
            return 2.0
        elif length < 500:
            return 3.0
        elif length < 1000:
            return 4.0
        else:
            return 5.0

    def _score_motion_type(self, motion_type: MotionType) -> float:
        """动议类型评分"""
        type_scores = {
            MotionType.BUG_FIX: 2.0,
            MotionType.NEW_FEATURE: 4.0,
            MotionType.REFACTOR: 5.0,
            MotionType.PERFORMANCE: 6.0,
            MotionType.SECURITY: 6.0,
            MotionType.ARCHITECTURE: 8.0,
        }
        return type_scores.get(motion_type, 3.0)

    def _score_risk_count(self, count: int) -> float:
        """风险数量评分"""
        if count == 0:
            return 0.0
        elif count <= 2:
            return 1.0
        elif count <= 5:
            return 2.0
        else:
            return 3.0

    def _score_execution_plan(self, steps: int) -> float:
        """执行计划步骤评分"""
        if steps <= 3:
            return 1.0
        elif steps <= 6:
            return 2.0
        elif steps <= 10:
            return 4.0
        else:
            return 6.0

    def _determine_complexity(self, score: float) -> TaskComplexity:
        """根据分数确定复杂度等级"""
        if score < 5:
            return TaskComplexity.TRIVIAL
        elif score < 15:
            return TaskComplexity.SIMPLE
        elif score < 30:
            return TaskComplexity.MODERATE
        elif score < 50:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.VERY_COMPLEX

    def _get_recommendation(self, complexity: TaskComplexity) -> Dict:
        """获取执行建议"""
        recommendations = {
            TaskComplexity.TRIVIAL: {
                "executor": "copilot",
                "timeout": 60,
                "strategy": "single_shot",
                "description": "微小任务,使用 Copilot 快速生成"
            },
            TaskComplexity.SIMPLE: {
                "executor": "claude_code",
                "timeout": 300,
                "strategy": "single_shot",
                "description": "简单任务,Claude Code 单次执行"
            },
            TaskComplexity.MODERATE: {
                "executor": "claude_code",
                "timeout": 900,
                "strategy": "single_shot",
                "description": "中等任务,Claude Code 标准执行"
            },
            TaskComplexity.COMPLEX: {
                "executor": "claude_code",
                "timeout": 1800,
                "strategy": "monitored",
                "description": "复杂任务,Claude Code 监控执行"
            },
            TaskComplexity.VERY_COMPLEX: {
                "executor": "claude_code",
                "timeout": 3600,
                "strategy": "step_by_step",
                "description": "极复杂任务,分步执行并验证"
            }
        }
        return recommendations[complexity]
