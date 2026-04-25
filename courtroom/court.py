"""
法庭主控制器 - 协调整个庭审流程
"""
from pathlib import Path
from datetime import datetime
from typing import Optional

from .schemas import (
    Motion, TrialTranscript, MotionStatus, MotionType
)
from .agents.judge import Judge
from .agents.prosecutor import Prosecutor
from .agents.defender import Defender
from .agents.jury import Jury
from .agents.court_reporter import CourtReporter


class Court:
    """法庭 - 主控制器"""

    def __init__(self, courtroom_root: Path = None, use_llm: bool = False):
        """
        初始化法庭

        Args:
            courtroom_root: 法庭根目录
            use_llm: 是否使用 LLM Agent（需要 ANTHROPIC_API_KEY）
        """
        if courtroom_root is None:
            courtroom_root = Path(__file__).parent

        self.root = courtroom_root
        self.use_llm = use_llm and LLM_AVAILABLE

        if self.use_llm:
            print("🤖 使用 LLM 驱动的 Agent")

        self.judge = Judge(self.root)
        self.prosecutor = Prosecutor()
        self.defender = Defender()
        self.jury = Jury()
        self.reporter = CourtReporter(self.root / "transcripts")

        # LLM 版本的 Agent（如果启用）
        if self.use_llm:
            try:
                self.prosecutor_llm = ProsecutorLLM(use_llm=True)
                self.defender_llm = DefenderLLM(use_llm=True)
                self.judge_llm = JudgeLLM(use_llm=True)
            except Exception as e:
                print(f"⚠️ LLM 初始化失败，回退到规则引擎: {e}")
                self.use_llm = False

    def file_motion(
        self,
        title: str,
        motion_type: MotionType,
        description: str,
        proposed_changes: list,
        affected_files: list,
        risks: list = None,
        benefits: list = None,
        priority: int = 5
    ) -> str:
        """提交动议"""
        # 生成案件编号
        case_id = self._generate_case_id()

        # 检察官提交动议
        motion = self.prosecutor.file_motion(
            case_id=case_id,
            title=title,
            motion_type=motion_type,
            description=description,
            proposed_changes=proposed_changes,
            affected_files=affected_files,
            risks=risks,
            benefits=benefits,
            priority=priority
        )

        # 法官接受动议
        result = self.judge.accept_motion(motion)

        return f"{result}\n\n使用 `court.trial('{case_id}')` 开始庭审"

    def trial(self, case_id: str, max_rounds: int = 3) -> str:
        """开庭审理"""
        # 加载案件
        motion = self.judge.load_motion(case_id)
        if not motion:
            return f"❌ 案件 {case_id} 不存在"

        # 更新状态为庭审中
        self.judge.update_motion_status(case_id, MotionStatus.TRIAL)

        # 创建庭审记录
        transcript = TrialTranscript(
            case_id=case_id,
            motion=motion,
            started_at=datetime.now()
        )

        print(f"\n⚖️ 开庭审理案件：{motion.title}\n")
        print("=" * 60)

        # 1. 开场陈述
        print("\n📢 开场陈述阶段\n")

        prosecutor_opening = self.prosecutor.opening_statement(motion)
        transcript.arguments.append(prosecutor_opening)
        print(f"👨‍⚖️ 检察官：\n{prosecutor_opening.content}\n")

        defender_opening = self.defender.opening_statement(motion)
        transcript.arguments.append(defender_opening)
        print(f"👩‍⚖️ 辩护律师：\n{defender_opening.content}\n")

        # 2. 交叉辩论
        print("\n⚔️ 交叉辩论阶段\n")

        for round_num in range(max_rounds):
            print(f"--- 第 {round_num + 1} 轮 ---\n")

            prosecutor_rebut = self.prosecutor.rebut(defender_opening, motion)
            transcript.arguments.append(prosecutor_rebut)
            print(f"👨‍⚖️ 检察官反驳：\n{prosecutor_rebut.content}\n")

            defender_cross = self.defender.cross_examine(prosecutor_rebut, motion)
            transcript.arguments.append(defender_cross)
            print(f"👩‍⚖️ 辩护律师质询：\n{defender_cross.content}\n")

        # 3. 结案陈词
        print("\n📝 结案陈词阶段\n")

        prosecutor_closing = self.prosecutor.closing_statement(motion)
        transcript.arguments.append(prosecutor_closing)
        print(f"👨‍⚖️ 检察官：\n{prosecutor_closing.content}\n")

        defender_closing = self.defender.closing_statement(motion, concerns_addressed=True)
        transcript.arguments.append(defender_closing)
        print(f"👩‍⚖️ 辩护律师：\n{defender_closing.content}\n")

        # 4. 陪审团评议
        print("\n🗳️ 陪审团评议阶段\n")

        jury_votes = self.jury.deliberate(motion, transcript.arguments)
        transcript.jury_votes = jury_votes

        for vote in jury_votes:
            print(f"• {vote.juror}: {vote.vote.value}")
            print(f"  理由: {vote.reasoning}\n")

        # 5. 法官判决
        print("\n⚖️ 法官评议中...\n")

        self.judge.update_motion_status(case_id, MotionStatus.DELIBERATION)

        reasoning = self._generate_judge_reasoning(transcript)
        verdict = self.judge.make_verdict(case_id, transcript, reasoning)

        transcript.verdict = verdict
        transcript.ended_at = datetime.now()

        print(f"⚖️ 判决结果：{verdict.verdict_type.value.upper()}\n")
        print(f"判决理由：\n{verdict.reasoning}\n")

        if verdict.execution_plan:
            print("执行计划：")
            for step in verdict.execution_plan:
                print(f"  {step}")

        # 6. 书记员归档
        transcript_file = self.reporter.write_transcript(transcript)
        print(f"\n📄 庭审记录已保存：{transcript_file}")

        return f"✅ 案件 {case_id} 审理完毕，判决：{verdict.verdict_type.value}"

    def show_verdict(self, case_id: str) -> Optional[str]:
        """查看判决"""
        verdict_file = self.judge.verdicts_dir / f"{case_id}.json"
        if not verdict_file.exists():
            return f"❌ 案件 {case_id} 尚未判决"

        import json
        verdict_data = json.loads(verdict_file.read_text(encoding='utf-8'))

        return f"""
⚖️ 案件 {case_id} 判决书

判决类型: {verdict_data['verdict_type']}
判决理由: {verdict_data['reasoning']}

批准的变更:
{self._format_list(verdict_data.get('approved_changes', []))}

执行计划:
{self._format_list(verdict_data.get('execution_plan', []))}
        """.strip()

    def list_cases(self, active_only: bool = True) -> str:
        """列出案件"""
        if active_only:
            cases = self.judge.list_active_cases()
            title = "活跃案件"
        else:
            cases = self.judge.list_completed_cases()
            title = "已结案件"

        if not cases:
            return f"📋 {title}：（无）"

        result = f"📋 {title}：\n\n"
        for case_id in cases:
            motion = self.judge.load_motion(case_id)
            if motion:
                result += f"• {case_id}: {motion.title} ({motion.status.value})\n"

        return result

    def get_statistics(self) -> str:
        """获取统计数据"""
        stats = self.judge.get_statistics()

        return f"""
📊 法庭统计

总案件数: {stats.get('total_cases', 0)}
批准: {stats.get('approved', 0)}
驳回: {stats.get('rejected', 0)}
修改后批准: {stats.get('modified', 0)}
延期审理: {stats.get('deferred', 0)}
        """.strip()

    def _generate_case_id(self) -> str:
        """生成案件编号"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"case_{timestamp}"

    def _generate_judge_reasoning(self, transcript: TrialTranscript) -> str:
        """生成法官判决理由"""
        # 简化版，实际应该调用 LLM
        jury_consensus = self.jury.get_consensus(transcript.jury_votes)

        reasoning = f"""
经过充分的庭审辩论和陪审团评议，本庭认为：

1. 检察官提出的变更具有一定的必要性和合理性
2. 辩护律师提出的风险质疑也值得重视
3. 陪审团的专家意见倾向于：{jury_consensus.value}

综合考虑各方意见，本庭做出如下判决。
        """.strip()

        return reasoning

    def _format_list(self, items: list) -> str:
        """格式化列表"""
        if not items:
            return "（无）"
        return "\n".join(f"  - {item}" for item in items)


# 便捷函数
def create_court(courtroom_root: Path = None) -> Court:
    """创建法庭实例"""
    return Court(courtroom_root)
