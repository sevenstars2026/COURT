"""
法庭主控制器 - 协调整个庭审流程
"""
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

from .schemas import (
    Motion, TrialTranscript, MotionStatus, MotionType
)
from .agents.judge import Judge
from .agents.prosecutor import Prosecutor
from .agents.defender import Defender
from .agents.jury import Jury
from .agents.court_reporter import CourtReporter
from .agents.code_analyst import CodeAnalyst
from .agents.execution_engineer import ExecutionEngineer
from .agents.qa_inspector import QAInspector
from .retrial_analyzer import RetrialAnalyzer


# 检查 LLM 是否可用
try:
    from .agents.prosecutor_llm import ProsecutorLLM
    from .agents.defender_llm import DefenderLLM
    from .agents.judge_llm import JudgeLLM
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class Court:
    """法庭 - 主控制器"""

    def __init__(self, courtroom_root: Path = None, use_llm: bool = False, codebase_path: Path = None):
        """
        初始化法庭

        Args:
            courtroom_root: 法庭根目录
            use_llm: 是否使用 LLM Agent（需要 ANTHROPIC_API_KEY）
            codebase_path: 代码库路径（用于代码分析和执行）
        """
        if courtroom_root is None:
            courtroom_root = Path(__file__).parent

        self.root = courtroom_root
        self.use_llm = use_llm and LLM_AVAILABLE
        self.codebase_path = codebase_path or courtroom_root.parent

        if self.use_llm:
            print("🤖 使用 LLM 驱动的 Agent")

        self.judge = Judge(self.root)
        self.prosecutor = Prosecutor()
        self.defender = Defender()
        self.jury = Jury()
        self.reporter = CourtReporter(self.root / "transcripts")

        # 新增的 Agent
        self.code_analyst = CodeAnalyst(self.root)
        self.execution_engineer = ExecutionEngineer(self.root)
        self.qa_inspector = QAInspector(self.root)
        self.retrial_analyzer = RetrialAnalyzer(self.root)

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
        priority: int = 5,
        run_analysis: bool = True
    ) -> str:
        """提交动议"""
        # 生成案件编号
        case_id = self._generate_case_id()

        # 步骤 0: 代码分析（可选）
        if run_analysis:
            print(f"\n🔍 代码分析师预审案件 {case_id}...")
            analysis_report = self.code_analyst.analyze_for_motion(
                case_id=case_id,
                motion_title=title,
                motion_description=description,
                affected_files=affected_files,
                codebase_path=self.codebase_path
            )
            print(f"   分析完成 - 复杂度: {analysis_report.complexity_score}/10")
            print(f"   风险评估: {analysis_report.risk_assessment}")
            if analysis_report.potential_issues:
                print(f"   发现 {len(analysis_report.potential_issues)} 个潜在问题")

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

    def trial(self, case_id: str, max_rounds: int = 3, on_progress=None, progress_callback=None, retry_count: int = 0, max_retries: int = 2) -> str:
        """开庭审理
        Args:
            case_id: 案件编号
            max_rounds: 辩论轮数
            on_progress: 进度回调(phase, summary)，phase: 阶段名, summary: 一句话摘要
            progress_callback: Celery 任务进度回调(stage, progress, message)
            retry_count: 当前重试次数
            max_retries: 最大重试次数
        """
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
        if on_progress: on_progress("prosecutor_opening", "检察官开场陈述")
        if progress_callback: progress_callback("prosecutor_opening", 10, "检察官开场陈述")

        prosecutor_opening = self.prosecutor.opening_statement(motion)
        transcript.arguments.append(prosecutor_opening)
        print(f"👨‍⚖️ 检察官：\n{prosecutor_opening.content}\n")
        if on_progress: on_progress("prosecutor_opening_done", "检察官陈述完毕")
        if progress_callback: progress_callback("prosecutor_opening_done", 15, "检察官陈述完毕")

        if on_progress: on_progress("defender_opening", "辩护律师开场陈述")
        if progress_callback: progress_callback("defender_opening", 20, "辩护律师开场陈述")
        defender_opening = self.defender.opening_statement(motion)
        transcript.arguments.append(defender_opening)
        print(f"👩‍⚖️ 辩护律师：\n{defender_opening.content}\n")
        if on_progress: on_progress("defender_opening_done", "辩护律师陈述完毕")
        if progress_callback: progress_callback("defender_opening_done", 25, "辩护律师陈述完毕")

        # 2. 交叉辩论
        print("\n⚔️ 交叉辩论阶段\n")

        for round_num in range(max_rounds):
            print(f"--- 第 {round_num + 1} 轮 ---\n")
            if on_progress: on_progress("debate", f"交叉辩论 第{round_num + 1}轮")
            progress_pct = 30 + (round_num * 15)
            if progress_callback: progress_callback("debate", progress_pct, f"交叉辩论 第{round_num + 1}轮")

            if on_progress: on_progress("prosecutor_rebut", "检察官反驳")
            prosecutor_rebut = self.prosecutor.rebut(defender_opening, motion)
            transcript.arguments.append(prosecutor_rebut)
            print(f"👨‍⚖️ 检察官反驳：\n{prosecutor_rebut.content}\n")

            if on_progress: on_progress("defender_cross", "辩护律师质询")
            defender_cross = self.defender.cross_examine(prosecutor_rebut, motion)
            transcript.arguments.append(defender_cross)
            print(f"👩‍⚖️ 辩护律师质询：\n{defender_cross.content}\n")

        # 3. 结案陈词
        print("\n📝 结案陈词阶段\n")
        if on_progress: on_progress("closing", "结案陈词")
        if progress_callback: progress_callback("closing", 60, "结案陈词")

        if on_progress: on_progress("prosecutor_closing", "检察官结案陈词")
        prosecutor_closing = self.prosecutor.closing_statement(motion)
        transcript.arguments.append(prosecutor_closing)
        print(f"👨‍⚖️ 检察官：\n{prosecutor_closing.content}\n")

        if on_progress: on_progress("defender_closing", "辩护律师结案陈词")
        defender_closing = self.defender.closing_statement(motion, concerns_addressed=True)
        transcript.arguments.append(defender_closing)
        print(f"👩‍⚖️ 辩护律师：\n{defender_closing.content}\n")

        # 4. 陪审团评议
        print("\n🗳️ 陪审团评议阶段\n")
        if on_progress: on_progress("jury", "陪审团评议中")
        if progress_callback: progress_callback("jury", 70, "陪审团评议中")

        jury_votes = self.jury.deliberate(motion, transcript.arguments)
        transcript.jury_votes = jury_votes

        for vote in jury_votes:
            print(f"• {vote.juror}: {vote.vote.value}")
            print(f"  理由: {vote.reasoning}\n")
        if on_progress: on_progress("jury_done", "陪审团投票完成")
        if progress_callback: progress_callback("jury_done", 75, "陪审团投票完成")

        # 5. 法官判决
        print("\n⚖️ 法官评议中...\n")
        if on_progress: on_progress("judge", "法官评议中")
        if progress_callback: progress_callback("judge", 80, "法官评议中")

        self.judge.update_motion_status(case_id, MotionStatus.DELIBERATION)

        reasoning = self._generate_judge_reasoning(transcript)
        verdict = self.judge.make_verdict(case_id, transcript, reasoning)

        transcript.verdict = verdict
        transcript.ended_at = datetime.now()

        print(f"⚖️ 判决结果：{verdict.verdict_type.value.upper()}\n")
        print(f"判决理由：\n{verdict.reasoning}\n")
        if on_progress: on_progress("verdict", f"判决: {verdict.verdict_type.value}")
        if progress_callback: progress_callback("verdict", 85, f"判决: {verdict.verdict_type.value}")

        if verdict.execution_plan:
            print("执行计划：")
            for step in verdict.execution_plan:
                print(f"  {step}")

        # 6. 执行判决（如果批准）
        from .schemas import VerdictType
        if verdict.verdict_type in [VerdictType.APPROVED, VerdictType.APPROVED_WITH_MODIFICATIONS]:
            print("\n🔧 执行工程师开始执行判决...\n")
            if on_progress: on_progress("execution", "执行工程师执行中")
            if progress_callback: progress_callback("execution", 90, "执行工程师执行中")

            # 定义执行进度回调
            def execution_progress(status, progress, message):
                if progress_callback:
                    progress_callback(f"execution_{status}", 90, message)

            execution_result = self.execution_engineer.execute_verdict(
                verdict=verdict,
                codebase_path=self.codebase_path,
                use_copilot=True,
                dry_run=False,
                progress_callback=execution_progress
            )

            if on_progress: on_progress("execution_done", "执行完成")
            if progress_callback: progress_callback("execution_done", 95, "执行完成")

            # 7. 质量检查
            print("\n🔍 质量检查员验证结果...\n")
            if on_progress: on_progress("qa", "质量检查中")
            if progress_callback: progress_callback("qa", 97, "质量检查中")

            qa_report = self.qa_inspector.inspect(
                case_id=case_id,
                execution_result=execution_result,
                codebase_path=self.codebase_path
            )

            if on_progress: on_progress("qa_done", "质量检查完成")
            if progress_callback: progress_callback("qa_done", 99, "质量检查完成")

            # 8. 判断是否需要重审
            if qa_report.should_retry:
                print(f"\n⚠️  质量检查未通过: {qa_report.retry_reason}")

                # 使用重审分析器分析失败原因
                print(f"\n🔍 重审分析器分析失败原因...")
                if on_progress: on_progress("retrial_analysis", "分析失败原因")
                if progress_callback: progress_callback("retrial_analysis", 98, "分析失败原因")

                retrial_analysis = self.retrial_analyzer.analyze_failure(
                    case_id=case_id,
                    motion=motion,
                    verdict=verdict,
                    execution_result=execution_result,
                    qa_report=qa_report,
                    retry_count=retry_count,
                    max_retries=max_retries
                )

                # 如果达到最大重试次数，停止重审
                if retrial_analysis.max_retries_reached:
                    print(f"\n❌ 已达到最大重试次数 ({max_retries})，停止重审")
                    self.judge.update_motion_status(case_id, MotionStatus.VERDICT)
                    return f"❌ 案件 {case_id} 执行失败，已达到最大重试次数\n原因: {qa_report.retry_reason}"

                # 自动触发重审
                print(f"\n🔄 自动触发重审 (第 {retry_count + 2} 次尝试)...")
                print(f"   根因: {retrial_analysis.root_cause}")
                print(f"   设计缺陷: {len(retrial_analysis.design_flaws)} 个")
                print(f"   建议改进: {len(retrial_analysis.suggested_changes)} 个")

                # 更新动议，添加重审分析结果
                motion.description += f"\n\n【重审分析 - 第 {retry_count + 1} 次失败】\n"
                motion.description += f"根因: {retrial_analysis.root_cause}\n\n"

                if retrial_analysis.design_flaws:
                    motion.description += "设计缺陷:\n"
                    for flaw in retrial_analysis.design_flaws:
                        motion.description += f"- {flaw}\n"
                    motion.description += "\n"

                if retrial_analysis.suggested_changes:
                    motion.description += "建议改进:\n"
                    for change in retrial_analysis.suggested_changes:
                        motion.description += f"- {change}\n"
                    motion.description += "\n"

                if retrial_analysis.missing_context:
                    motion.description += "缺失的上下文:\n"
                    for context in retrial_analysis.missing_context:
                        motion.description += f"- {context}\n"
                    motion.description += "\n"

                # 保存更新后的动议
                import json
                case_file = self.judge.cases_dir / f"{case_id}.json"
                with open(case_file, "w", encoding="utf-8") as f:
                    json.dump(motion.dict(), f, indent=2, ensure_ascii=False, default=str)

                # 重新检索代码（如果需要）
                if retrial_analysis.additional_evidence_needed:
                    print(f"\n🔍 重新检索代码...")
                    analysis_report = self.code_analyst.analyze_for_motion(
                        case_id=case_id,
                        motion_title=motion.title,
                        motion_description=motion.description,
                        affected_files=motion.affected_files,
                        codebase_path=self.codebase_path
                    )
                    print(f"   检索到 {len(analysis_report.relevant_code)} 个相关代码片段")

                # 更新状态为重新提交
                self.judge.update_motion_status(case_id, MotionStatus.FILED)

                # 递归调用 trial，开始新一轮庭审
                print(f"\n{'='*60}")
                print(f"🔄 开始第 {retry_count + 2} 次庭审")
                print(f"{'='*60}\n")

                return self.trial(
                    case_id=case_id,
                    max_rounds=max_rounds,
                    on_progress=on_progress,
                    progress_callback=progress_callback,
                    retry_count=retry_count + 1,
                    max_retries=max_retries
                )
            else:
                print(f"\n✅ 质量检查通过")
                if qa_report.recommendations:
                    print("建议:")
                    for rec in qa_report.recommendations[:3]:
                        print(f"  - {rec}")

        # 9. 书记员归档
        transcript_file = self.reporter.write_transcript(transcript)
        print(f"\n📄 庭审记录已保存：{transcript_file}")
        if progress_callback: progress_callback("complete", 100, "庭审完成")

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

    def list_motions(self) -> list:
        """返回所有案件列表（用于 API）"""
        motions = []
        cases_dir = self.root / "cases"
        if cases_dir.exists():
            # 从文件系统加载所有案件
            for case_file in sorted(cases_dir.glob("case_*.json"), reverse=True):
                try:
                    with open(case_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        motion = Motion(**data)
                        motions.append(motion)
                except Exception as e:
                    print(f"⚠️ 加载案件 {case_file.name} 失败: {e}")
        return motions

    def get_motion(self, case_id: str):
        """获取单个案件"""
        return self.judge.load_motion(case_id)

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
