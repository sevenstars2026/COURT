"""
法官 Agent - 唯一有权修改共享状态的实体
"""
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..schemas import (
    Motion, Argument, Evidence, Verdict, TrialTranscript,
    VerdictType, MotionStatus, CourtState
)


class Judge:
    """法官 - 主持庭审，做出最终裁决"""

    def __init__(self, courtroom_root: Path):
        self.root = courtroom_root
        self.cases_dir = self.root / "cases"
        self.verdicts_dir = self.root / "verdicts"
        self.transcripts_dir = self.root / "transcripts"
        self.state_file = self.root / "court_state.json"

        # 确保目录存在
        for d in [self.cases_dir, self.verdicts_dir, self.transcripts_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 加载或初始化法庭状态
        self.state = self._load_state()

    def _load_state(self) -> CourtState:
        """加载法庭状态"""
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text(encoding='utf-8'))
            return CourtState(**data)
        return CourtState()

    def _save_state(self):
        """保存法庭状态"""
        self.state_file.write_text(
            self.state.model_dump_json(indent=2),
            encoding='utf-8'
        )

    def accept_motion(self, motion: Motion) -> str:
        """接受动议，立案"""
        # 保存案件文件
        case_file = self.cases_dir / f"{motion.case_id}.json"
        case_file.write_text(motion.model_dump_json(indent=2), encoding='utf-8')

        # 更新法庭状态
        if motion.case_id not in self.state.active_cases:
            self.state.active_cases.append(motion.case_id)
        self._save_state()

        return f"✅ 案件 {motion.case_id} 已立案：{motion.title}"

    def load_motion(self, case_id: str) -> Optional[Motion]:
        """加载案件"""
        case_file = self.cases_dir / f"{case_id}.json"
        if not case_file.exists():
            return None
        data = json.loads(case_file.read_text(encoding='utf-8'))
        return Motion(**data)

    def update_motion_status(self, case_id: str, status: MotionStatus):
        """更新案件状态"""
        motion = self.load_motion(case_id)
        if motion:
            motion.status = status
            case_file = self.cases_dir / f"{case_id}.json"
            case_file.write_text(motion.model_dump_json(indent=2), encoding='utf-8')

    def make_verdict(
        self,
        case_id: str,
        transcript: TrialTranscript,
        reasoning: str = ""
    ) -> Verdict:
        """做出判决"""
        motion = transcript.motion

        # 分析辩论内容
        prosecutor_points = [
            arg for arg in transcript.arguments
            if arg.speaker == "prosecutor"
        ]
        defender_points = [
            arg for arg in transcript.arguments
            if arg.speaker == "defender"
        ]

        # 简单的判决逻辑（实际应该调用 LLM）
        verdict_type = self._determine_verdict_type(
            prosecutor_points,
            defender_points,
            transcript.jury_votes
        )

        # 构建判决
        verdict = Verdict(
            case_id=case_id,
            verdict_type=verdict_type,
            reasoning=reasoning or self._generate_reasoning(
                verdict_type,
                prosecutor_points,
                defender_points
            ),
            approved_changes=motion.proposed_changes if verdict_type == VerdictType.APPROVED else [],
            execution_plan=self._generate_execution_plan(motion, verdict_type),
            judge="judge",
            verdict_at=datetime.now()
        )

        # 保存判决
        verdict_file = self.verdicts_dir / f"{case_id}.json"
        verdict_file.write_text(verdict.model_dump_json(indent=2), encoding='utf-8')

        # 更新案件状态
        self.update_motion_status(case_id, MotionStatus.VERDICT)

        # 移动到已结案件
        if case_id in self.state.active_cases:
            self.state.active_cases.remove(case_id)
        if case_id not in self.state.completed_cases:
            self.state.completed_cases.append(case_id)

        # 更新统计
        verdict_key = verdict_type.value
        self.state.statistics[verdict_key] = self.state.statistics.get(verdict_key, 0) + 1
        self.state.statistics['total_cases'] = len(self.state.completed_cases)

        # 添加到判例法库
        self.state.case_law[case_id] = {
            "title": motion.title,
            "type": motion.motion_type.value,
            "verdict": verdict_type.value,
            "date": verdict.verdict_at.isoformat()
        }

        self._save_state()

        return verdict

    def _determine_verdict_type(
        self,
        prosecutor_points: List[Argument],
        defender_points: List[Argument],
        jury_votes: List
    ) -> VerdictType:
        """判断判决类型（简化版）"""
        # 实际应该调用 LLM 进行综合分析
        # 这里用简单的计分逻辑

        prosecutor_score = len(prosecutor_points) * 2
        defender_score = len(defender_points) * 2

        # 陪审团投票权重更高
        for vote in jury_votes:
            if vote.vote == VerdictType.APPROVED:
                prosecutor_score += 5
            elif vote.vote == VerdictType.REJECTED:
                defender_score += 5

        if prosecutor_score > defender_score * 1.5:
            return VerdictType.APPROVED
        elif defender_score > prosecutor_score * 1.5:
            return VerdictType.REJECTED
        else:
            return VerdictType.MODIFIED

    def _generate_reasoning(
        self,
        verdict_type: VerdictType,
        prosecutor_points: List[Argument],
        defender_points: List[Argument]
    ) -> str:
        """生成判决理由"""
        if verdict_type == VerdictType.APPROVED:
            return "经审理，检察官提出的论点充分，风险可控，批准该动议。"
        elif verdict_type == VerdictType.REJECTED:
            return "经审理，辩护律师提出的质疑合理，风险过高，驳回该动议。"
        else:
            return "经审理，双方论点均有道理，批准部分变更，但需满足附加条件。"

    def _generate_execution_plan(self, motion: Motion, verdict_type: VerdictType) -> List[str]:
        """生成执行计划"""
        if verdict_type == VerdictType.REJECTED:
            return []

        plan = [
            f"1. 审查影响的文件：{', '.join(motion.affected_files)}",
            "2. 实施批准的变更",
            "3. 编写或更新测试用例",
            "4. 进行代码审查",
            "5. 合并到主分支"
        ]
        return plan

    def get_precedents(self, motion_type: str, limit: int = 5) -> List[dict]:
        """查询判例"""
        precedents = [
            case for case_id, case in self.state.case_law.items()
            if case.get('type') == motion_type
        ]
        return precedents[-limit:]  # 返回最近的判例

    def get_statistics(self) -> dict:
        """获取统计数据"""
        return self.state.statistics

    def list_active_cases(self) -> List[str]:
        """列出活跃案件"""
        return self.state.active_cases

    def list_completed_cases(self) -> List[str]:
        """列出已结案件"""
        return self.state.completed_cases
