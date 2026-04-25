"""
执行工程师 - 负责将判决转化为实际的代码变更
集成 Claude Code CLI 和 Copilot CLI,支持智能执行策略
"""
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from ..schemas import Verdict, VerdictType, Motion
from ..code_output_manager import CodeOutputManager
from ..strategy_manager import StrategyManager


class ExecutionResult:
    """执行结果"""
    def __init__(self):
        self.success = False
        self.modified_files: List[str] = []
        self.created_files: List[str] = []
        self.deleted_files: List[str] = []
        self.test_results: Optional[str] = None
        self.error_message: Optional[str] = None
        self.execution_log: List[str] = []
        self.claude_output: Optional[str] = None
        self.copilot_suggestions: List[str] = []
        self.strategy_info: Optional[Dict] = None  # 执行策略信息
        self.complexity_analysis: Optional[Dict] = None  # 复杂度分析


class ExecutionEngineer:
    """执行工程师 - 使用 Claude Code 和 Copilot CLI 执行代码变更"""

    def __init__(self, project_root: Path, claude_cli: str = "claude", copilot_cli: str = "copilot", use_smart_strategy: bool = True):
        """
        初始化执行工程师

        Args:
            project_root: 项目根目录
            claude_cli: Claude Code CLI 路径
            copilot_cli: Copilot CLI 路径
            use_smart_strategy: 是否使用智能执行策略
        """
        self.project_root = project_root
        self.claude_cli = claude_cli
        self.copilot_cli = copilot_cli
        self.execution_log_dir = project_root / "courtroom" / "execution_logs"
        self.execution_log_dir.mkdir(parents=True, exist_ok=True)
        self.cases_dir = project_root / "courtroom" / "cases"
        self.output_manager = CodeOutputManager()
        self.use_smart_strategy = use_smart_strategy
        self.strategy_manager = StrategyManager(claude_cli, copilot_cli) if use_smart_strategy else None

    def _load_motion_from_verdict(self, verdict: Verdict) -> Optional[Motion]:
        """从案件文件加载 Motion"""
        try:
            case_file = self.cases_dir / f"{verdict.case_id}.json"
            if case_file.exists():
                with open(case_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return Motion(**data)
        except Exception as e:
            print(f"加载 Motion 失败: {e}")
        return None

    def _execute_with_smart_strategy(
        self,
        motion: Motion,
        verdict: Verdict,
        codebase_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> tuple[bool, str, Dict]:
        """使用智能执行策略"""
        # 构建提示
        prompt = self._build_claude_prompt(verdict, [])

        # 使用策略管理器执行
        success, output, execution_info = self.strategy_manager.execute_with_fallback(
            motion,
            verdict,
            prompt,
            codebase_path,
            progress_callback
        )

        return success, output, execution_info

    def execute_verdict(
        self,
        verdict: Verdict,
        codebase_path: Path,
        use_copilot: bool = True,
        dry_run: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> ExecutionResult:
        """
        执行判决

        Args:
            verdict: 判决对象
            codebase_path: 代码库路径
            use_copilot: 是否使用 Copilot 辅助 (仅在非智能模式下生效)
            dry_run: 演练模式
            progress_callback: 进度回调函数

        Returns:
            执行结果
        """
        result = ExecutionResult()
        result.execution_log.append(f"[{datetime.now()}] 开始执行判决: {verdict.case_id}")

        # 只执行批准的判决
        if verdict.verdict_type not in [VerdictType.APPROVED, VerdictType.APPROVED_WITH_MODIFICATIONS]:
            result.error_message = f"判决类型为 {verdict.verdict_type.value}，无需执行"
            result.execution_log.append(result.error_message)
            return result

        if dry_run:
            result.execution_log.append("[演练模式] 不会实际修改文件")
            result.success = True
            return result

        # 加载 Motion
        motion = self._load_motion_from_verdict(verdict)
        if not motion:
            result.error_message = "无法加载 Motion 信息"
            result.execution_log.append(result.error_message)
            return result

        # 使用智能执行策略
        if self.use_smart_strategy and self.strategy_manager:
            result.execution_log.append("使用智能执行策略...")
            success, output, strategy_info = self._execute_with_smart_strategy(
                motion, verdict, codebase_path, progress_callback
            )
            result.claude_output = output
            result.strategy_info = strategy_info
            result.execution_log.append(f"  策略: {strategy_info['strategy']}, 复杂度: {strategy_info['complexity']}")
            result.execution_log.append(f"  尝试次数: {len(strategy_info['attempts'])}")

            if not success:
                result.error_message = f"智能执行失败: {output[:500]}"
                result.execution_log.append(result.error_message)
                return result

        else:
            # 传统执行方式
            result.execution_log.append("使用传统执行方式...")

            # 步骤 1: 使用 Copilot 获取快速建议（可选）
            if use_copilot:
                result.execution_log.append("步骤 1: 使用 Copilot 获取代码建议...")
                copilot_suggestions = self._get_copilot_suggestions(verdict, codebase_path)
                result.copilot_suggestions = copilot_suggestions
                result.execution_log.append(f"  获得 {len(copilot_suggestions)} 条建议")

            # 步骤 2: 使用 Claude Code 执行主要变更
            result.execution_log.append("步骤 2: 使用 Claude Code 执行代码变更...")
            claude_success, claude_output = self._execute_with_claude_code(
                verdict,
                codebase_path,
                copilot_suggestions=result.copilot_suggestions if use_copilot else []
            )

            result.claude_output = claude_output
            result.execution_log.append(f"  Claude Code 执行{'成功' if claude_success else '失败'}")

            if not claude_success:
                result.error_message = f"Claude Code 执行失败: {claude_output[:500]}"
                result.execution_log.append(result.error_message)
                return result

        # 步骤 3: 检测变更的文件
        result.execution_log.append("步骤 3: 检测文件变更...")
        modified, created, deleted = self._detect_file_changes(codebase_path)
        result.modified_files = modified
        result.created_files = created
        result.deleted_files = deleted
        result.execution_log.append(f"  修改: {len(modified)}, 创建: {len(created)}, 删除: {len(deleted)}")

        # 步骤 4: 运行测试（如果有）
        result.execution_log.append("步骤 4: 运行测试验证...")
        test_success, test_output = self._run_tests(codebase_path)
        result.test_results = test_output
        result.execution_log.append(f"  测试{'通过' if test_success else '失败'}")

        result.success = test_success or test_output == "无测试"

        # 步骤 5: 保存生成的代码到版本控制
        if result.success and (result.modified_files or result.created_files):
            result.execution_log.append("步骤 5: 保存代码输出到版本控制...")
            version_id = self._save_code_output(verdict.case_id, codebase_path, result)
            result.execution_log.append(f"  代码已保存，版本: {version_id}")

        # 保存执行日志
        self._save_execution_log(verdict.case_id, result)

        return result

    def _get_copilot_suggestions(self, verdict: Verdict, codebase_path: Path) -> List[str]:
        """使用 Copilot CLI 获取代码建议"""
        suggestions = []

        try:
            # 构建 Copilot 提示
            prompt = self._build_copilot_prompt(verdict)

            # 调用 Copilot CLI
            cmd = [
                self.copilot_cli,
                "-p",  # 非交互模式
                prompt,
                "--add-dir", str(codebase_path)
            ]

            result = subprocess.run(
                cmd,
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and result.stdout:
                # 解析 Copilot 输出
                suggestions.append(result.stdout.strip())

        except Exception as e:
            suggestions.append(f"Copilot 调用失败: {e}")

        return suggestions

    def _execute_with_claude_code(
        self,
        verdict: Verdict,
        codebase_path: Path,
        copilot_suggestions: List[str] = None
    ) -> tuple[bool, str]:
        """使用 Claude Code CLI 执行代码变更"""
        try:
            # 构建 Claude Code 提示
            prompt = self._build_claude_prompt(verdict, copilot_suggestions)

            # 创建临时文件保存提示
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name

            # 调用 Claude Code CLI
            cmd = [
                self.claude_cli,
                "-p",  # 非交互模式（print mode）
                "--add-dir", str(codebase_path),
                "--output-format", "text",
                prompt
            ]

            result = subprocess.run(
                cmd,
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            # 清理临时文件
            Path(prompt_file).unlink(missing_ok=True)

            output = result.stdout + "\n" + result.stderr
            success = result.returncode == 0

            return success, output

        except subprocess.TimeoutExpired:
            return False, "Claude Code 执行超时（5分钟）"
        except Exception as e:
            return False, f"Claude Code 调用异常: {e}"

    def _build_copilot_prompt(self, verdict: Verdict) -> str:
        """构建 Copilot 提示"""
        # 从判决中获取案件信息
        motion = self._load_motion_from_verdict(verdict)
        if not motion:
            return f"""请为以下判决提供代码建议：

判决: {verdict.verdict_type.value}
判决理由: {verdict.reasoning[:500]}

请提供具体的代码实现建议。
"""

        prompt = f"""请为以下需求提供代码建议：

需求: {motion.title}
描述: {motion.description}

判决: {verdict.verdict_type.value}
判决理由: {verdict.reasoning[:500]}

请提供具体的代码实现建议。
"""
        return prompt

    def _build_claude_prompt(self, verdict: Verdict, copilot_suggestions: List[str] = None) -> str:
        """构建 Claude Code 提示"""
        # 从判决中获取案件信息
        motion = self._load_motion_from_verdict(verdict)

        if not motion:
            prompt = f"""你是一位执行工程师，需要根据以下判决执行代码变更。

【案件信息】
案件编号: {verdict.case_id}

【判决结果】
判决类型: {verdict.verdict_type.value}
判决理由: {verdict.reasoning[:1000]}

【执行计划】
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(verdict.execution_plan)) if verdict.execution_plan else "（无具体计划）"}
"""
        else:
            prompt = f"""你是一位执行工程师，需要根据以下判决执行代码变更。

【案件信息】
案件编号: {verdict.case_id}
需求标题: {motion.title}
需求描述: {motion.description[:500]}

【提议的变更】
{chr(10).join(f"- {c}" for c in motion.proposed_changes) if motion.proposed_changes else "（无）"}

【影响的文件】
{chr(10).join(f"- {f}" for f in motion.affected_files) if motion.affected_files else "（无）"}

【判决结果】
判决类型: {verdict.verdict_type.value}
判决理由: {verdict.reasoning[:1000]}

【批准的变更】
{chr(10).join(f"- {c}" for c in verdict.approved_changes) if verdict.approved_changes else "（同提议的变更）"}

【执行计划】
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(verdict.execution_plan)) if verdict.execution_plan else "（无具体计划）"}
"""

        if copilot_suggestions:
            prompt += f"""

【Copilot 建议】
{chr(10).join(f"- {s[:200]}" for s in copilot_suggestions)}
"""

        prompt += """

【你的任务】
1. 分析现有代码结构
2. 根据判决和执行计划，修改或创建相应的文件
3. 确保代码质量和一致性
4. 如果有测试文件，也要相应更新

请直接执行代码变更，不要只是讨论。使用 Edit 和 Write 工具修改文件。
"""

        return prompt

    def _detect_file_changes(self, codebase_path: Path) -> tuple[List[str], List[str], List[str]]:
        """检测文件变更（使用 git status）"""
        modified = []
        created = []
        deleted = []

        try:
            # 使用 git status 检测变更
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    status = line[:2]
                    filepath = line[3:]

                    if status.strip() == 'M':
                        modified.append(filepath)
                    elif status.strip() in ['A', '??']:
                        created.append(filepath)
                    elif status.strip() == 'D':
                        deleted.append(filepath)

        except Exception as e:
            print(f"检测文件变更失败: {e}")

        return modified, created, deleted

    def _run_tests(self, codebase_path: Path) -> tuple[bool, str]:
        """运行测试"""
        # 检查是否有测试文件
        test_files = list(codebase_path.glob("test_*.py")) + list(codebase_path.glob("*_test.py"))

        if not test_files:
            return True, "无测试"

        try:
            # 运行 pytest
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=120
            )

            output = result.stdout + "\n" + result.stderr
            success = result.returncode == 0

            return success, output

        except subprocess.TimeoutExpired:
            return False, "测试执行超时（2分钟）"
        except FileNotFoundError:
            return True, "pytest 未安装，跳过测试"
        except Exception as e:
            return False, f"测试执行异常: {e}"

    def _save_execution_log(self, case_id: str, result: ExecutionResult):
        """保存执行日志"""
        log_data = {
            "case_id": case_id,
            "timestamp": datetime.now().isoformat(),
            "success": result.success,
            "modified_files": result.modified_files,
            "created_files": result.created_files,
            "deleted_files": result.deleted_files,
            "test_results": result.test_results,
            "error_message": result.error_message,
            "execution_log": result.execution_log,
            "copilot_suggestions_count": len(result.copilot_suggestions),
            "claude_output_length": len(result.claude_output) if result.claude_output else 0,
            "strategy_info": result.strategy_info,
            "complexity_analysis": result.complexity_analysis
        }

        log_file = self.execution_log_dir / f"{case_id}_execution.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

    def _save_code_output(self, case_id: str, codebase_path: Path, result: ExecutionResult) -> str:
        """保存生成的代码到版本控制"""
        files = {}

        # 读取所有修改和创建的文件
        all_files = result.modified_files + result.created_files
        for rel_path in all_files:
            file_path = codebase_path / rel_path
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    files[rel_path] = content
                except Exception as e:
                    print(f"读取文件 {rel_path} 失败: {e}")

        # 保存元数据
        metadata = {
            "modified_files": result.modified_files,
            "created_files": result.created_files,
            "deleted_files": result.deleted_files,
            "test_results": result.test_results,
            "claude_output_summary": result.claude_output[:500] if result.claude_output else None
        }

        version_id = self.output_manager.save_output(case_id, files, metadata)
        return version_id

    def get_execution_summary(self, case_id: str) -> Optional[Dict[str, Any]]:
        """获取执行摘要"""
        log_file = self.execution_log_dir / f"{case_id}_execution.json"
        if not log_file.exists():
            return None

        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
