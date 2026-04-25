"""
并行预审与法庭排期器 - 提升吞吐量
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import json


class CasePriority(str, Enum):
    """案件优先级"""
    CRITICAL = "critical"      # 紧急（生产故障）
    HIGH = "high"              # 高（重要功能）
    NORMAL = "normal"          # 普通
    LOW = "low"                # 低（优化、重构）


class CaseStatus(str, Enum):
    """案件状态"""
    PENDING = "pending"        # 待审理
    PRE_TRIAL = "pre_trial"    # 预审中
    TRIAL = "trial"            # 正式审理中
    COMPLETED = "completed"    # 已完成
    REJECTED = "rejected"      # 预审驳回


class PreTrialResult(BaseModel):
    """预审结果"""
    case_id: str
    passed: bool               # 是否通过预审
    issues: List[str]          # 发现的问题
    estimated_complexity: int  # 复杂度评分（1-10）
    recommended_priority: CasePriority
    should_proceed: bool       # 是否应该进入正式审理


class ScheduledCase(BaseModel):
    """排期案件"""
    case_id: str
    title: str
    motion_type: str
    priority: CasePriority
    status: CaseStatus
    submitted_at: datetime
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: int = 300  # 预估时长（秒）
    pre_trial_result: Optional[PreTrialResult] = None


class CourtScheduler:
    """法庭排期器"""

    def __init__(self, courtroom_root: Path, max_parallel: int = 3):
        """
        初始化排期器

        Args:
            courtroom_root: 法庭根目录
            max_parallel: 最大并行案件数
        """
        self.root = courtroom_root
        self.max_parallel = max_parallel
        self.schedule_file = self.root / "schedule.json"
        self.cases: Dict[str, ScheduledCase] = {}
        self._load_schedule()

    def _load_schedule(self):
        """加载排期表"""
        if self.schedule_file.exists():
            with open(self.schedule_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for case_data in data:
                    case = ScheduledCase(**case_data)
                    self.cases[case.case_id] = case

    def _save_schedule(self):
        """保存排期表"""
        data = [case.model_dump(mode='json') for case in self.cases.values()]
        with open(self.schedule_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def submit_case(
        self,
        case_id: str,
        title: str,
        motion_type: str,
        priority: CasePriority = CasePriority.NORMAL
    ) -> ScheduledCase:
        """
        提交案件

        Args:
            case_id: 案件 ID
            title: 标题
            motion_type: 动议类型
            priority: 优先级

        Returns:
            排期案件
        """
        case = ScheduledCase(
            case_id=case_id,
            title=title,
            motion_type=motion_type,
            priority=priority,
            status=CaseStatus.PENDING,
            submitted_at=datetime.now()
        )

        self.cases[case_id] = case
        self._save_schedule()

        print(f"📋 案件已提交: {case_id} ({priority.value})")
        return case

    async def pre_trial(self, case_id: str) -> PreTrialResult:
        """
        预审（快速检查）

        Args:
            case_id: 案件 ID

        Returns:
            预审结果
        """
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"案件不存在: {case_id}")

        print(f"🔍 预审开始: {case_id}")
        case.status = CaseStatus.PRE_TRIAL
        self._save_schedule()

        # 模拟预审检查（实际应该调用 LLM）
        await asyncio.sleep(0.5)  # 模拟 API 调用

        issues = []
        complexity = 5

        # 检查 1: 标题是否清晰
        if len(case.title) < 10:
            issues.append("标题过于简短，缺少上下文")

        # 检查 2: 动议类型是否合理
        if case.motion_type not in ["new_feature", "bug_fix", "refactor", "performance"]:
            issues.append(f"未知的动议类型: {case.motion_type}")

        # 检查 3: 优先级是否合理
        if case.priority == CasePriority.CRITICAL:
            complexity += 2

        # 决定是否通过
        passed = len(issues) == 0
        should_proceed = passed or len(issues) <= 1

        # 调整优先级
        if complexity >= 8:
            recommended_priority = CasePriority.HIGH
        elif complexity <= 3:
            recommended_priority = CasePriority.LOW
        else:
            recommended_priority = case.priority

        result = PreTrialResult(
            case_id=case_id,
            passed=passed,
            issues=issues,
            estimated_complexity=complexity,
            recommended_priority=recommended_priority,
            should_proceed=should_proceed
        )

        case.pre_trial_result = result

        if should_proceed:
            case.status = CaseStatus.PENDING
            print(f"✅ 预审通过: {case_id}")
        else:
            case.status = CaseStatus.REJECTED
            print(f"❌ 预审驳回: {case_id}")
            print(f"   问题: {', '.join(issues)}")

        self._save_schedule()
        return result

    async def batch_pre_trial(self, case_ids: List[str]) -> List[PreTrialResult]:
        """
        批量并行预审

        Args:
            case_ids: 案件 ID 列表

        Returns:
            预审结果列表
        """
        print(f"🚀 批量预审开始: {len(case_ids)} 个案件")

        # 并行执行预审
        tasks = [self.pre_trial(case_id) for case_id in case_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常
        valid_results = [r for r in results if isinstance(r, PreTrialResult)]

        print(f"✅ 批量预审完成: {len(valid_results)}/{len(case_ids)} 通过")
        return valid_results

    def get_next_cases(self, limit: int = 3) -> List[ScheduledCase]:
        """
        获取下一批待审理案件（按优先级排序）

        Args:
            limit: 数量限制

        Returns:
            案件列表
        """
        # 筛选待审理的案件
        pending_cases = [
            case for case in self.cases.values()
            if case.status == CaseStatus.PENDING and case.pre_trial_result
            and case.pre_trial_result.should_proceed
        ]

        # 按优先级排序
        priority_order = {
            CasePriority.CRITICAL: 0,
            CasePriority.HIGH: 1,
            CasePriority.NORMAL: 2,
            CasePriority.LOW: 3
        }

        pending_cases.sort(
            key=lambda c: (priority_order[c.priority], c.submitted_at)
        )

        return pending_cases[:limit]

    def start_trial(self, case_id: str):
        """开始审理"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"案件不存在: {case_id}")

        case.status = CaseStatus.TRIAL
        case.started_at = datetime.now()
        self._save_schedule()

        print(f"⚖️ 开庭审理: {case_id}")

    def complete_trial(self, case_id: str):
        """完成审理"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"案件不存在: {case_id}")

        case.status = CaseStatus.COMPLETED
        case.completed_at = datetime.now()
        self._save_schedule()

        duration = (case.completed_at - case.started_at).total_seconds()
        print(f"✅ 审理完成: {case_id} (耗时 {duration:.1f}s)")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.cases)
        by_status = {}
        by_priority = {}

        for case in self.cases.values():
            by_status[case.status] = by_status.get(case.status, 0) + 1
            by_priority[case.priority] = by_priority.get(case.priority, 0) + 1

        # 计算平均审理时长
        completed_cases = [
            c for c in self.cases.values()
            if c.status == CaseStatus.COMPLETED and c.started_at and c.completed_at
        ]

        if completed_cases:
            avg_duration = sum(
                (c.completed_at - c.started_at).total_seconds()
                for c in completed_cases
            ) / len(completed_cases)
        else:
            avg_duration = 0

        return {
            "total_cases": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "avg_duration_seconds": avg_duration,
            "completed_count": len(completed_cases)
        }

    def get_queue_status(self) -> str:
        """获取队列状态（可视化）"""
        lines = ["📊 法庭排期状态\n"]

        # 按优先级分组
        by_priority = {
            CasePriority.CRITICAL: [],
            CasePriority.HIGH: [],
            CasePriority.NORMAL: [],
            CasePriority.LOW: []
        }

        for case in self.cases.values():
            if case.status in [CaseStatus.PENDING, CaseStatus.PRE_TRIAL]:
                by_priority[case.priority].append(case)

        # 显示各优先级队列
        for priority in [CasePriority.CRITICAL, CasePriority.HIGH, CasePriority.NORMAL, CasePriority.LOW]:
            cases = by_priority[priority]
            if cases:
                lines.append(f"\n{priority.value.upper()} ({len(cases)} 个):")
                for case in cases[:3]:  # 只显示前 3 个
                    status_icon = "🔍" if case.status == CaseStatus.PRE_TRIAL else "⏳"
                    lines.append(f"  {status_icon} {case.title}")
                if len(cases) > 3:
                    lines.append(f"  ... 还有 {len(cases) - 3} 个")

        # 正在审理的案件
        in_trial = [c for c in self.cases.values() if c.status == CaseStatus.TRIAL]
        if in_trial:
            lines.append(f"\n⚖️ 正在审理 ({len(in_trial)} 个):")
            for case in in_trial:
                lines.append(f"  - {case.title}")

        return "\n".join(lines)
