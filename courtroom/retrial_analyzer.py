"""
重审分析器 - 分析执行失败原因，生成改进建议
"""
from typing import List, Optional
from pathlib import Path
import json
from datetime import datetime

from .schemas import Motion, Verdict
from .agents.execution_engineer import ExecutionResult
from .agents.qa_inspector import QAReport


class RetrialAnalysis:
    """重审分析结果"""
    def __init__(self):
        self.case_id: str = ""
        self.retry_count: int = 0
        self.error_type: str = ""
        self.root_cause: str = ""
        self.design_flaws: List[str] = []
        self.missing_context: List[str] = []
        self.suggested_changes: List[str] = []
        self.additional_evidence_needed: bool = False
        self.should_retrial: bool = True
        self.max_retries_reached: bool = False


class RetrialAnalyzer:
    """重审分析器 - 分析失败原因并生成改进建议"""

    def __init__(self, project_root: Path):
        """
        初始化重审分析器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.analysis_dir = project_root / "courtroom" / "retrial_analysis"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

    def analyze_failure(
        self,
        case_id: str,
        motion: Motion,
        verdict: Verdict,
        execution_result: ExecutionResult,
        qa_report: QAReport,
        retry_count: int = 0,
        max_retries: int = 2
    ) -> RetrialAnalysis:
        """
        分析执行失败原因

        Args:
            case_id: 案件编号
            motion: 原始动议
            verdict: 判决
            execution_result: 执行结果
            qa_report: QA 报告
            retry_count: 当前重试次数
            max_retries: 最大重试次数

        Returns:
            重审分析结果
        """
        analysis = RetrialAnalysis()
        analysis.case_id = case_id
        analysis.retry_count = retry_count

        print(f"\n🔍 重审分析器开始分析案件 {case_id} (第 {retry_count + 1} 次尝试)...")

        # 检查是否达到最大重试次数
        if retry_count >= max_retries:
            analysis.should_retrial = False
            analysis.max_retries_reached = True
            print(f"  ⚠️  已达到最大重试次数，停止重审")
            self._save_analysis(analysis)
            return analysis

        # 1. 分析错误类型
        analysis.error_type = self._classify_error(execution_result, qa_report)
        print(f"  步骤 1: 错误类型 - {analysis.error_type}")

        # 2. 提取根本原因
        analysis.root_cause = self._extract_root_cause(
            execution_result, qa_report, analysis.error_type
        )
        print(f"  步骤 2: 根本原因 - {analysis.root_cause[:100]}...")

        # 3. 分析设计缺陷
        analysis.design_flaws = self._analyze_design_flaws(
            verdict, execution_result, qa_report
        )
        print(f"  步骤 3: 发现 {len(analysis.design_flaws)} 个设计缺陷")

        # 4. 识别缺失的上下文
        analysis.missing_context = self._identify_missing_context(
            motion, verdict, execution_result
        )
        print(f"  步骤 4: 发现 {len(analysis.missing_context)} 个缺失上下文")

        # 5. 生成改进建议
        analysis.suggested_changes = self._generate_suggestions(
            verdict, execution_result, qa_report, analysis.error_type
        )
        print(f"  步骤 5: 生成 {len(analysis.suggested_changes)} 个改进建议")

        # 6. 判断是否需要额外证据
        analysis.additional_evidence_needed = self._needs_more_evidence(
            motion, verdict, execution_result
        )
        print(f"  步骤 6: 需要额外证据 - {analysis.additional_evidence_needed}")

        # 7. 决定是否应该重审
        analysis.should_retrial = self._should_retrial(
            analysis.error_type, analysis.design_flaws, retry_count
        )
        print(f"  步骤 7: 应该重审 - {analysis.should_retrial}")

        print(f"  ✅ 分析完成")

        self._save_analysis(analysis)
        return analysis

    def _classify_error(
        self, execution_result: ExecutionResult, qa_report: QAReport
    ) -> str:
        """分类错误类型"""
        if not execution_result.success:
            log = "\n".join(execution_result.execution_log).lower()

            if "syntax error" in log or "syntaxerror" in log:
                return "syntax_error"
            elif "import error" in log or "modulenotfounderror" in log:
                return "import_error"
            elif "name error" in log or "nameerror" in log:
                return "name_error"
            elif "type error" in log or "typeerror" in log:
                return "type_error"
            elif "attribute error" in log or "attributeerror" in log:
                return "attribute_error"
            elif "file not found" in log or "filenotfounderror" in log:
                return "file_not_found"
            else:
                return "runtime_error"

        if qa_report.should_retry:
            return "qa_failure"

        return "unknown"

    def _extract_root_cause(
        self, execution_result: ExecutionResult, qa_report: QAReport, error_type: str
    ) -> str:
        """提取根本原因"""
        if not execution_result.success:
            # 从执行日志中提取最后的错误信息
            error_lines = [
                line for line in execution_result.execution_log
                if "error" in line.lower() or "exception" in line.lower()
            ]
            if error_lines:
                return error_lines[-1]
            return execution_result.error_message or "执行失败，但未找到明确的错误信息"

        if qa_report.should_retry:
            return qa_report.retry_reason

        return "未知原因"

    def _analyze_design_flaws(
        self, verdict: Verdict, execution_result: ExecutionResult, qa_report: QAReport
    ) -> List[str]:
        """分析设计缺陷"""
        flaws = []

        # 检查判决是否包含详细设计
        if not verdict.architecture_design:
            flaws.append("判决缺少架构设计，可能导致实现不完整")

        if not verdict.function_design:
            flaws.append("判决缺少函数级别设计，可能导致实现细节错误")

        # 检查执行日志中的常见问题
        if not execution_result.success:
            log = "\n".join(execution_result.execution_log).lower()

            if "undefined" in log or "not defined" in log:
                flaws.append("存在未定义的变量或函数，可能是设计遗漏")

            if "circular import" in log or "circular dependency" in log:
                flaws.append("存在循环依赖，架构设计需要重构")

            if "missing required" in log or "required argument" in log:
                flaws.append("函数签名设计不完整，缺少必需参数")

        return flaws

    def _identify_missing_context(
        self, motion: Motion, verdict: Verdict, execution_result: ExecutionResult
    ) -> List[str]:
        """识别缺失的上下文"""
        missing = []

        # 检查是否缺少相关文件
        if not execution_result.success:
            log = "\n".join(execution_result.execution_log)

            # 提取文件路径
            import re
            file_patterns = [
                r'File "([^"]+)"',
                r"from ([a-zA-Z0-9_./]+) import",
                r"import ([a-zA-Z0-9_./]+)",
            ]

            mentioned_files = set()
            for pattern in file_patterns:
                matches = re.findall(pattern, log)
                mentioned_files.update(matches)

            # 检查这些文件是否在原始动议的 affected_files 中
            affected = set(motion.affected_files or [])
            for file in mentioned_files:
                if file not in affected and not file.startswith("/"):
                    missing.append(f"可能缺少相关文件: {file}")

        return missing

    def _generate_suggestions(
        self,
        verdict: Verdict,
        execution_result: ExecutionResult,
        qa_report: QAReport,
        error_type: str
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 根据错误类型生成建议
        if error_type == "syntax_error":
            suggestions.append("仔细检查代码语法，确保符合 Python 规范")

        elif error_type == "import_error":
            suggestions.append("检查所有导入语句，确保模块路径正确")
            suggestions.append("确认所有依赖的文件都已创建")

        elif error_type == "name_error":
            suggestions.append("确保所有变量和函数在使用前已定义")

        elif error_type == "type_error":
            suggestions.append("检查函数调用的参数类型是否匹配")

        elif error_type == "attribute_error":
            suggestions.append("检查对象属性是否存在")

        # 根据设计缺陷生成建议
        if not verdict.architecture_design:
            suggestions.append("在判决中添加详细的架构设计")

        if not verdict.function_design:
            suggestions.append("在判决中添加函数级别的设计细节")

        return suggestions

    def _needs_more_evidence(
        self, motion: Motion, verdict: Verdict, execution_result: ExecutionResult
    ) -> bool:
        """判断是否需要更多证据（重新检索代码）"""
        log = "\n".join(execution_result.execution_log).lower()

        if "import error" in log or "modulenotfounderror" in log:
            return True

        if "file not found" in log or "filenotfounderror" in log:
            return True

        missing_context = self._identify_missing_context(motion, verdict, execution_result)
        if missing_context:
            return True

        return False

    def _should_retrial(
        self, error_type: str, design_flaws: List[str], retry_count: int
    ) -> bool:
        """决定是否应该重审"""
        # 如果存在设计缺陷，应该重审
        if design_flaws:
            return True

        # 如果是导入错误或文件未找到，应该重审
        if error_type in ["import_error", "file_not_found"]:
            return True

        # 其他情况，根据重试次数决定
        return retry_count < 1

    def _save_analysis(self, analysis: RetrialAnalysis):
        """保存分析报告"""
        report_file = self.analysis_dir / f"{analysis.case_id}_retry_{analysis.retry_count}.json"

        report_data = {
            "case_id": analysis.case_id,
            "retry_count": analysis.retry_count,
            "timestamp": datetime.now().isoformat(),
            "error_type": analysis.error_type,
            "root_cause": analysis.root_cause,
            "design_flaws": analysis.design_flaws,
            "missing_context": analysis.missing_context,
            "suggested_changes": analysis.suggested_changes,
            "additional_evidence_needed": analysis.additional_evidence_needed,
            "should_retrial": analysis.should_retrial,
            "max_retries_reached": analysis.max_retries_reached,
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
