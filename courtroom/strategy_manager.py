"""
执行策略管理器
根据任务复杂度选择最优执行策略,支持自动降级和重试
"""
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .task_analyzer import TaskComplexity, TaskAnalyzer
from .schemas import Motion, Verdict


class ExecutionStrategy:
    """执行策略基类"""

    def __init__(self, name: str, timeout: int, description: str):
        self.name = name
        self.timeout = timeout
        self.description = description

    def execute(
        self,
        prompt: str,
        codebase_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> tuple[bool, str]:
        """执行策略,返回 (成功, 输出)"""
        raise NotImplementedError


class CopilotStrategy(ExecutionStrategy):
    """Copilot CLI 快速执行策略"""

    def __init__(self, copilot_cli: str = "copilot"):
        super().__init__("copilot", 60, "Copilot 快速生成")
        self.copilot_cli = copilot_cli

    def execute(
        self,
        prompt: str,
        codebase_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("copilot_executing", 0.5, "Copilot 生成代码中...")

            cmd = [self.copilot_cli, "-p", prompt, "--add-dir", str(codebase_path)]

            result = subprocess.run(
                cmd,
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            output = result.stdout + "\n" + result.stderr
            success = result.returncode == 0

            if progress_callback:
                progress_callback("copilot_done", 1.0, "Copilot 执行完成")

            return success, output

        except subprocess.TimeoutExpired:
            return False, f"Copilot 执行超时 ({self.timeout}秒)"
        except Exception as e:
            return False, f"Copilot 执行异常: {e}"


class ClaudeCodeSingleShotStrategy(ExecutionStrategy):
    """Claude Code 单次执行策略"""

    def __init__(self, claude_cli: str = "claude", timeout: int = 300):
        super().__init__("claude_single", timeout, "Claude Code 单次执行")
        self.claude_cli = claude_cli

    def execute(
        self,
        prompt: str,
        codebase_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("claude_executing", 0.5, "Claude Code 执行中...")

            cmd = [
                self.claude_cli,
                "-p",
                "--add-dir", str(codebase_path),
                "--output-format", "text",
                prompt
            ]

            result = subprocess.run(
                cmd,
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            output = result.stdout + "\n" + result.stderr
            success = result.returncode == 0

            if progress_callback:
                progress_callback("claude_done", 1.0, "Claude Code 执行完成")

            return success, output

        except subprocess.TimeoutExpired:
            return False, f"Claude Code 执行超时 ({self.timeout}秒)"
        except Exception as e:
            return False, f"Claude Code 执行异常: {e}"


class ClaudeCodeMonitoredStrategy(ExecutionStrategy):
    """Claude Code 监控执行策略 (带进度反馈)"""

    def __init__(self, claude_cli: str = "claude", timeout: int = 1800):
        super().__init__("claude_monitored", timeout, "Claude Code 监控执行")
        self.claude_cli = claude_cli

    def execute(
        self,
        prompt: str,
        codebase_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("claude_executing", 0.1, "Claude Code 启动中...")

            cmd = [
                self.claude_cli,
                "-p",
                "--add-dir", str(codebase_path),
                "--output-format", "text",
                prompt
            ]

            # 使用 Popen 实时读取输出
            process = subprocess.Popen(
                cmd,
                cwd=str(codebase_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            output_lines = []
            start_time = time.time()

            # 实时读取输出
            while True:
                # 检查超时
                if time.time() - start_time > self.timeout:
                    process.kill()
                    return False, f"Claude Code 执行超时 ({self.timeout}秒)"

                # 读取一行输出
                line = process.stdout.readline()
                if line:
                    output_lines.append(line)
                    if progress_callback:
                        # 根据输出估算进度
                        progress = min(0.9, 0.1 + len(output_lines) * 0.01)
                        progress_callback("claude_executing", progress, line.strip()[:100])

                # 检查进程是否结束
                if process.poll() is not None:
                    break

            # 读取剩余输出
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                output_lines.append(remaining_stdout)
            if remaining_stderr:
                output_lines.append(remaining_stderr)

            output = "".join(output_lines)
            success = process.returncode == 0

            if progress_callback:
                progress_callback("claude_done", 1.0, "Claude Code 执行完成")

            return success, output

        except Exception as e:
            return False, f"Claude Code 执行异常: {e}"


class ClaudeCodeStepByStepStrategy(ExecutionStrategy):
    """Claude Code 分步执行策略"""

    def __init__(self, claude_cli: str = "claude", timeout_per_step: int = 600):
        super().__init__("claude_step_by_step", timeout_per_step * 10, "Claude Code 分步执行")
        self.claude_cli = claude_cli
        self.timeout_per_step = timeout_per_step

    def execute(
        self,
        prompt: str,
        codebase_path: Path,
        progress_callback: Optional[Callable] = None,
        execution_plan: Optional[list] = None
    ) -> tuple[bool, str]:
        """
        分步执行,如果提供了 execution_plan 则按步骤执行
        """
        if not execution_plan:
            # 如果没有执行计划,降级为单次执行
            strategy = ClaudeCodeMonitoredStrategy(self.claude_cli, self.timeout_per_step * 3)
            return strategy.execute(prompt, codebase_path, progress_callback)

        all_outputs = []
        total_steps = len(execution_plan)

        for i, step in enumerate(execution_plan):
            step_num = i + 1
            if progress_callback:
                progress = (i / total_steps) * 0.9
                progress_callback("claude_step", progress, f"执行步骤 {step_num}/{total_steps}: {step[:50]}")

            # 构建步骤提示
            step_prompt = f"""你是执行工程师,正在执行一个复杂任务的第 {step_num}/{total_steps} 步。

【当前步骤】
{step}

【整体任务】
{prompt[:500]}

【要求】
- 只完成当前步骤,不要超出范围
- 使用 Edit 和 Write 工具修改文件
- 确保代码质量和一致性
"""

            # 执行单步
            cmd = [
                self.claude_cli,
                "-p",
                "--add-dir", str(codebase_path),
                "--output-format", "text",
                step_prompt
            ]

            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(codebase_path),
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_per_step
                )

                step_output = result.stdout + "\n" + result.stderr
                all_outputs.append(f"=== 步骤 {step_num}/{total_steps} ===\n{step_output}\n")

                if result.returncode != 0:
                    # 步骤失败,返回已完成的部分
                    return False, "".join(all_outputs) + f"\n步骤 {step_num} 失败"

            except subprocess.TimeoutExpired:
                return False, "".join(all_outputs) + f"\n步骤 {step_num} 超时"
            except Exception as e:
                return False, "".join(all_outputs) + f"\n步骤 {step_num} 异常: {e}"

        if progress_callback:
            progress_callback("claude_done", 1.0, "所有步骤执行完成")

        return True, "".join(all_outputs)


class StrategyManager:
    """执行策略管理器"""

    def __init__(self, claude_cli: str = "claude", copilot_cli: str = "copilot"):
        self.claude_cli = claude_cli
        self.copilot_cli = copilot_cli
        self.analyzer = TaskAnalyzer()

        # 注册所有策略
        self.strategies = {
            "copilot": CopilotStrategy(copilot_cli),
            "claude_single": ClaudeCodeSingleShotStrategy(claude_cli, 300),
            "claude_moderate": ClaudeCodeSingleShotStrategy(claude_cli, 900),
            "claude_monitored": ClaudeCodeMonitoredStrategy(claude_cli, 1800),
            "claude_step_by_step": ClaudeCodeStepByStepStrategy(claude_cli, 600),
        }

    def select_strategy(
        self,
        motion: Motion,
        verdict: Optional[Verdict] = None
    ) -> tuple[ExecutionStrategy, Dict]:
        """
        根据任务复杂度选择执行策略

        Returns:
            (策略对象, 分析结果)
        """
        analysis = self.analyzer.analyze(motion, verdict)
        complexity = analysis["complexity"]
        recommendation = analysis["recommendation"]

        # 根据推荐选择策略
        executor = recommendation["executor"]
        timeout = recommendation["timeout"]

        if executor == "copilot":
            strategy = self.strategies["copilot"]
        elif complexity == TaskComplexity.SIMPLE:
            strategy = self.strategies["claude_single"]
        elif complexity == TaskComplexity.MODERATE:
            strategy = self.strategies["claude_moderate"]
        elif complexity == TaskComplexity.COMPLEX:
            strategy = self.strategies["claude_monitored"]
        else:  # VERY_COMPLEX
            strategy = self.strategies["claude_step_by_step"]

        return strategy, analysis

    def execute_with_fallback(
        self,
        motion: Motion,
        verdict: Optional[Verdict],
        prompt: str,
        codebase_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> tuple[bool, str, Dict]:
        """
        执行任务,支持自动降级

        Returns:
            (成功, 输出, 执行信息)
        """
        strategy, analysis = self.select_strategy(motion, verdict)

        execution_info = {
            "strategy": strategy.name,
            "complexity": analysis["complexity"].value,
            "score": analysis["score"],
            "attempts": []
        }

        if progress_callback:
            progress_callback(
                "strategy_selected",
                0.0,
                f"选择策略: {strategy.description} (复杂度: {analysis['complexity'].value})"
            )

        # 第一次尝试
        attempt = {
            "strategy": strategy.name,
            "start_time": datetime.now().isoformat(),
        }

        # 如果是分步执行,传入执行计划
        if strategy.name == "claude_step_by_step" and verdict and verdict.execution_plan:
            success, output = strategy.execute(
                prompt,
                codebase_path,
                progress_callback,
                execution_plan=verdict.execution_plan
            )
        else:
            success, output = strategy.execute(prompt, codebase_path, progress_callback)

        attempt["end_time"] = datetime.now().isoformat()
        attempt["success"] = success
        attempt["output_length"] = len(output)
        execution_info["attempts"].append(attempt)

        # 如果失败,尝试降级
        if not success and "超时" in output:
            if progress_callback:
                progress_callback("fallback", 0.0, "执行超时,尝试降级策略...")

            # 降级策略: 复杂任务 -> 中等任务
            if strategy.name in ["claude_monitored", "claude_step_by_step"]:
                fallback_strategy = self.strategies["claude_moderate"]

                attempt = {
                    "strategy": fallback_strategy.name,
                    "start_time": datetime.now().isoformat(),
                    "is_fallback": True
                }

                success, output = fallback_strategy.execute(prompt, codebase_path, progress_callback)

                attempt["end_time"] = datetime.now().isoformat()
                attempt["success"] = success
                attempt["output_length"] = len(output)
                execution_info["attempts"].append(attempt)

        return success, output, execution_info
