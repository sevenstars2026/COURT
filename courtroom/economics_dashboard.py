"""
经济驾驶舱 - 成本、质量与速度的实时监控
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
from collections import defaultdict


class CostRecord(BaseModel):
    """成本记录"""
    case_id: str
    role: str              # judge, prosecutor, defender, jury
    model: str             # 使用的模型
    cost: float            # 成本（美元）
    timestamp: datetime


class VerdictRecord(BaseModel):
    """判决记录"""
    case_id: str
    verdict_type: str      # approved, rejected, modified
    quality_score: float   # 质量评分（0-1）
    timestamp: datetime


class DurationRecord(BaseModel):
    """时长记录"""
    case_id: str
    duration_seconds: int
    timestamp: datetime


class EconomicsDashboard:
    """经济驾驶舱"""

    def __init__(self, courtroom_root: Path, monthly_budget: float = 10.0):
        """
        初始化驾驶舱

        Args:
            courtroom_root: 法庭根目录
            monthly_budget: 月度预算（美元）
        """
        self.root = courtroom_root
        self.monthly_budget = monthly_budget
        self.metrics_file = self.root / "metrics.json"

        self.cost_records: List[CostRecord] = []
        self.verdict_records: List[VerdictRecord] = []
        self.duration_records: List[DurationRecord] = []

        # 策略配置
        self.strategy = {
            "mode": "balanced",
            "judge_model": "claude_sonnet",
            "jury_size": 5,
            "debate_rounds": 2
        }

        self._load_metrics()

    def _load_metrics(self):
        """加载指标数据"""
        if self.metrics_file.exists():
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.cost_records = [CostRecord(**r) for r in data.get("costs", [])]
                self.verdict_records = [VerdictRecord(**r) for r in data.get("verdicts", [])]
                self.duration_records = [DurationRecord(**r) for r in data.get("durations", [])]

    def _save_metrics(self):
        """保存指标数据"""
        data = {
            "costs": [r.model_dump(mode='json') for r in self.cost_records],
            "verdicts": [r.model_dump(mode='json') for r in self.verdict_records],
            "durations": [r.model_dump(mode='json') for r in self.duration_records]
        }
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def record_cost(self, case_id: str, role: str, model: str, cost: float):
        """记录成本"""
        record = CostRecord(
            case_id=case_id,
            role=role,
            model=model,
            cost=cost,
            timestamp=datetime.now()
        )
        self.cost_records.append(record)
        self._save_metrics()

    def record_verdict(self, case_id: str, verdict_type: str, quality_score: float):
        """记录判决"""
        record = VerdictRecord(
            case_id=case_id,
            verdict_type=verdict_type,
            quality_score=quality_score,
            timestamp=datetime.now()
        )
        self.verdict_records.append(record)
        self._save_metrics()

    def record_duration(self, case_id: str, duration_seconds: int):
        """记录时长"""
        record = DurationRecord(
            case_id=case_id,
            duration_seconds=duration_seconds,
            timestamp=datetime.now()
        )
        self.duration_records.append(record)
        self._save_metrics()

    def get_cost_statistics(self) -> Dict[str, Any]:
        """获取成本统计"""
        total_cost = sum(r.cost for r in self.cost_records)

        # 本月成本
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        monthly_cost = sum(
            r.cost for r in self.cost_records
            if r.timestamp >= month_start
        )

        # 按角色分布
        by_role = defaultdict(float)
        for record in self.cost_records:
            by_role[record.role] += record.cost

        # 按模型分布
        by_model = defaultdict(float)
        for record in self.cost_records:
            by_model[record.model] += record.cost

        # 平均每案件成本
        unique_cases = set(r.case_id for r in self.cost_records)
        avg_cost_per_case = total_cost / len(unique_cases) if unique_cases else 0

        return {
            "total_cost": total_cost,
            "monthly_cost": monthly_cost,
            "budget_usage": monthly_cost / self.monthly_budget if self.monthly_budget > 0 else 0,
            "budget_remaining": self.monthly_budget - monthly_cost,
            "by_role": dict(by_role),
            "by_model": dict(by_model),
            "avg_cost_per_case": avg_cost_per_case
        }

    def get_quality_statistics(self) -> Dict[str, Any]:
        """获取质量统计"""
        if not self.verdict_records:
            return {
                "total_cases": 0,
                "approval_rate": 0,
                "rejection_rate": 0,
                "modification_rate": 0,
                "avg_quality_score": 0
            }

        total = len(self.verdict_records)
        approved = sum(1 for r in self.verdict_records if r.verdict_type == "approved")
        rejected = sum(1 for r in self.verdict_records if r.verdict_type == "rejected")
        modified = sum(1 for r in self.verdict_records if r.verdict_type == "modified")

        avg_quality = sum(r.quality_score for r in self.verdict_records) / total

        return {
            "total_cases": total,
            "approval_rate": approved / total,
            "rejection_rate": rejected / total,
            "modification_rate": modified / total,
            "avg_quality_score": avg_quality
        }

    def get_speed_statistics(self) -> Dict[str, Any]:
        """获取速度统计"""
        if not self.duration_records:
            return {
                "avg_duration": 0,
                "min_duration": 0,
                "max_duration": 0
            }

        durations = [r.duration_seconds for r in self.duration_records]

        return {
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations)
        }

    def get_budget_burndown(self) -> Dict[str, Any]:
        """获取预算燃尽图数据"""
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)

        # 计算本月已用天数
        days_elapsed = (now - month_start).days + 1

        # 计算本月剩余天数
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        days_in_month = (next_month - month_start).days
        days_remaining = days_in_month - days_elapsed

        # 本月成本
        monthly_cost = sum(
            r.cost for r in self.cost_records
            if r.timestamp >= month_start
        )

        # 当前消耗速率
        burn_rate = monthly_cost / days_elapsed if days_elapsed > 0 else 0

        # 预计耗尽日期
        if burn_rate > 0:
            days_until_depletion = (self.monthly_budget - monthly_cost) / burn_rate
            estimated_depletion = now + timedelta(days=days_until_depletion)
        else:
            estimated_depletion = None

        return {
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "current_burn_rate": burn_rate,
            "estimated_depletion_date": estimated_depletion.strftime("%Y-%m-%d") if estimated_depletion else "N/A"
        }

    def get_recommendations(self) -> List[str]:
        """获取策略建议"""
        recommendations = []

        cost_stats = self.get_cost_statistics()
        quality_stats = self.get_quality_statistics()

        # 预算建议
        if cost_stats['budget_usage'] > 0.8:
            recommendations.append("⚠️ 预算使用超过 80%，建议切换到更便宜的模型")
        elif cost_stats['budget_usage'] < 0.3:
            recommendations.append("💡 预算充足，可以考虑使用更强的模型提升质量")

        # 质量建议
        if quality_stats['rejection_rate'] > 0.5:
            recommendations.append("⚠️ 驳回率过高，建议降低辩护方干预强度")
        elif quality_stats['approval_rate'] > 0.9:
            recommendations.append("💡 批准率很高，可以考虑提高审查标准")

        # 成本优化建议
        by_role = cost_stats['by_role']
        if by_role.get('judge', 0) > cost_stats['total_cost'] * 0.7:
            recommendations.append("💡 法官成本占比过高，考虑增加陪审团预审")

        if not recommendations:
            recommendations.append("✅ 系统运行良好，无需调整")

        return recommendations

    def set_strategy(self, mode: str):
        """
        设置策略

        Args:
            mode: conservative（保守）, balanced（平衡）, aggressive（激进）
        """
        if mode == "conservative":
            self.strategy = {
                "mode": "conservative",
                "judge_model": "gpt4o_mini",
                "jury_size": 3,
                "debate_rounds": 1
            }
        elif mode == "balanced":
            self.strategy = {
                "mode": "balanced",
                "judge_model": "claude_sonnet",
                "jury_size": 5,
                "debate_rounds": 2
            }
        elif mode == "aggressive":
            self.strategy = {
                "mode": "aggressive",
                "judge_model": "claude_opus",
                "jury_size": 7,
                "debate_rounds": 3
            }

    def render_dashboard(self) -> str:
        """渲染仪表盘"""
        cost_stats = self.get_cost_statistics()
        quality_stats = self.get_quality_statistics()
        speed_stats = self.get_speed_statistics()

        lines = ["=" * 60]
        lines.append("📊 经济驾驶舱")
        lines.append("=" * 60)

        # 成本
        lines.append("\n💰 成本")
        lines.append(f"  本月: ${cost_stats['monthly_cost']:.4f} / ${self.monthly_budget:.2f}")
        lines.append(f"  使用: {cost_stats['budget_usage']:.1%}")
        lines.append(f"  剩余: ${cost_stats['budget_remaining']:.4f}")

        # 质量
        lines.append("\n⭐ 质量")
        lines.append(f"  总案件: {quality_stats['total_cases']}")
        lines.append(f"  批准率: {quality_stats['approval_rate']:.1%}")
        lines.append(f"  驳回率: {quality_stats['rejection_rate']:.1%}")
        lines.append(f"  质量分: {quality_stats['avg_quality_score']:.2f}/1.0")

        # 速度
        lines.append("\n⚡ 速度")
        lines.append(f"  平均时长: {speed_stats['avg_duration']:.1f}s")

        # 策略
        lines.append("\n🎯 当前策略")
        lines.append(f"  模式: {self.strategy['mode']}")
        lines.append(f"  法官模型: {self.strategy['judge_model']}")
        lines.append(f"  陪审团: {self.strategy['jury_size']} 人")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def export_monthly_report(self) -> Path:
        """导出月度报告"""
        now = datetime.now()
        report_file = self.root / f"report_{now.strftime('%Y%m')}.md"

        cost_stats = self.get_cost_statistics()
        quality_stats = self.get_quality_statistics()
        speed_stats = self.get_speed_statistics()
        burndown = self.get_budget_burndown()

        lines = [f"# 📊 月度报告 - {now.strftime('%Y年%m月')}\n"]
        lines.append(f"生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

        lines.append("## 💰 成本统计\n")
        lines.append(f"- 总成本: ${cost_stats['total_cost']:.4f}")
        lines.append(f"- 本月成本: ${cost_stats['monthly_cost']:.4f}")
        lines.append(f"- 预算使用: {cost_stats['budget_usage']:.1%}")
        lines.append(f"- 平均每案件: ${cost_stats['avg_cost_per_case']:.4f}\n")

        lines.append("## ⭐ 质量统计\n")
        lines.append(f"- 总案件数: {quality_stats['total_cases']}")
        lines.append(f"- 批准率: {quality_stats['approval_rate']:.1%}")
        lines.append(f"- 驳回率: {quality_stats['rejection_rate']:.1%}")
        lines.append(f"- 平均质量分: {quality_stats['avg_quality_score']:.2f}/1.0\n")

        lines.append("## ⚡ 速度统计\n")
        lines.append(f"- 平均审理时长: {speed_stats['avg_duration']:.1f}s\n")

        lines.append("## 📈 预算燃尽\n")
        lines.append(f"- 已用天数: {burndown['days_elapsed']}")
        lines.append(f"- 剩余天数: {burndown['days_remaining']}")
        lines.append(f"- 消耗速率: ${burndown['current_burn_rate']:.4f}/天\n")

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return report_file
