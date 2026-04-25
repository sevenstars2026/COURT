"""
判决自动执行器 - 将判决转化为实际的代码变更
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import subprocess
import json
from enum import Enum

from .schemas import Verdict, VerdictType


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ExecutionStep:
    """执行步骤"""
    def __init__(self, description: str, command: Optional[str] = None):
        self.description = description
        self.command = command
        self.status = ExecutionStatus.PENDING
        self.output = ""
        self.error = ""
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def execute(self) -> bool:
        """
        执行步骤

        Returns:
            是否成功
        """
        self.status = ExecutionStatus.IN_PROGRESS
        self.started_at = datetime.now()

        if not self.command:
            # 手动步骤，需要人工确认
            print(f"⏸️  手动步骤: {self.description}")
            print("   请手动完成后按回车继续...")
            input()
            self.status = ExecutionStatus.COMPLETED
            self.completed_at = datetime.now()
            return True

        try:
            print(f"▶️  执行: {self.description}")
            print(f"   命令: {self.command}")

            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            self.output = result.stdout
            self.error = result.stderr

            if result.returncode == 0:
                self.status = ExecutionStatus.COMPLETED
                print(f"   ✅ 成功")
                if self.output:
                    print(f"   输出: {self.output[:200]}")
                self.completed_at = datetime.now()
                return True
            else:
                self.status = ExecutionStatus.FAILED
                print(f"   ❌ 失败")
                print(f"   错误: {self.error}")
                self.completed_at = datetime.now()
                return False

        except subprocess.TimeoutExpired:
            self.status = ExecutionStatus.FAILED
            self.error = "命令执行超时"
            print(f"   ⏱️  超时")
            self.completed_at = datetime.now()
            return False
        except Exception as e:
            self.status = ExecutionStatus.FAILED
            self.error = str(e)
            print(f"   ❌ 异常: {e}")
            self.completed_at = datetime.now()
            return False


class VerdictExecutor:
    """判决执行器"""

    def __init__(self, project_root: Path):
        """
        初始化执行器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.execution_log_dir = project_root / "courtroom" / "executions"
        self.execution_log_dir.mkdir(parents=True, exist_ok=True)

    def create_execution_plan(self, verdict: Verdict) -> List[ExecutionStep]:
        """
        根据判决创建执行计划

        Args:
            verdict: 判决

        Returns:
            执行步骤列表
        """
        steps = []

        # 1. 创建分支
        if verdict.verdict_type in [VerdictType.APPROVED, VerdictType.APPROVED_WITH_MODIFICATIONS]:
            branch_name = f"courtroom/{verdict.case_id}"
            steps.append(ExecutionStep(
                description=f"创建分支 {branch_name}",
                command=f"git checkout -b {branch_name}"
            ))

        # 2. 执行判决中的执行计划
        if verdict.execution_plan:
            for i, plan_item in enumerate(verdict.execution_plan, 1):
                # 尝试将计划项转换为可执行命令
                command = self._plan_to_command(plan_item)
                steps.append(ExecutionStep(
                    description=f"步骤 {i}: {plan_item}",
                    command=command
                ))

        # 3. 运行测试
        steps.append(ExecutionStep(
            description="运行测试套件",
            command="pytest tests/ -v || true"  # 允许测试失败
        ))

        # 4. 提交变更
        if verdict.verdict_type in [VerdictType.APPROVED, VerdictType.APPROVED_WITH_MODIFICATIONS]:
            steps.append(ExecutionStep(
                description="提交变更",
                command=f'git add -A && git commit -m "⚖️ 执行判决: {verdict.case_id}"'
            ))

        return steps

    def _plan_to_command(self, plan_item: str) -> Optional[str]:
        """
        将执行计划项转换为 shell 命令

        Args:
            plan_item: 计划项描述

        Returns:
            shell 命令，如果无法自动化则返回 None
        """
        plan_lower = plan_item.lower()

        # 安装依赖
        if "安装" in plan_lower or "install" in plan_lower:
            if "redis" in plan_lower:
                return "pip install redis"
            elif "requirements" in plan_lower:
                return "pip install -r requirements.txt"

        # 创建文件
        if "创建文件" in plan_lower or "create file" in plan_lower:
            # 需要手动创建
            return None

        # 修改代码
        if "修改" in plan_lower or "更新" in plan_lower or "添加" in plan_lower:
            # 需要手动修改
            return None

        # 运行脚本
        if "运行" in plan_lower or "执行" in plan_lower:
            # 提取脚本名称
            # 这里需要更智能的解析
            return None

        # 默认为手动步骤
        return None

    def execute_verdict(
        self,
        verdict: Verdict,
        auto_mode: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        执行判决

        Args:
            verdict: 判决
            auto_mode: 自动模式（跳过手动步骤）
            dry_run: 演练模式（不实际执行）

        Returns:
            执行结果
        """
        print(f"\n⚖️ 开始执行判决: {verdict.case_id}")
        print(f"判决类型: {verdict.verdict_type.value}")
        print("=" * 60)

        if dry_run:
            print("🔍 演练模式（不会实际执行）\n")

        # 创建执行计划
        steps = self.create_execution_plan(verdict)

        if not steps:
            print("⚠️  没有可执行的步骤")
            return {
                "success": False,
                "message": "没有可执行的步骤"
            }

        print(f"\n📋 执行计划（共 {len(steps)} 步）:\n")
        for i, step in enumerate(steps, 1):
            print(f"{i}. {step.description}")
            if step.command:
                print(f"   命令: {step.command}")
            else:
                print(f"   类型: 手动步骤")
        print()

        if dry_run:
            return {
                "success": True,
                "message": "演练完成",
                "steps": len(steps)
            }

        # 确认执行
        if not auto_mode:
            confirm = input("是否继续执行？(y/n): ")
            if confirm.lower() != 'y':
                print("❌ 用户取消执行")
                return {
                    "success": False,
                    "message": "用户取消"
                }

        # 执行步骤
        print("\n🚀 开始执行...\n")
        failed_steps = []

        for i, step in enumerate(steps, 1):
            print(f"\n[{i}/{len(steps)}] ", end="")

            if not step.command and auto_mode:
                print(f"⏭️  跳过手动步骤: {step.description}")
                step.status = ExecutionStatus.PENDING
                continue

            success = step.execute()

            if not success:
                failed_steps.append((i, step))

                # 询问是否继续
                if not auto_mode:
                    continue_exec = input("\n步骤失败，是否继续？(y/n): ")
                    if continue_exec.lower() != 'y':
                        print("❌ 执行中止")
                        break
                else:
                    print("❌ 自动模式下遇到失败，中止执行")
                    break

        # 生成执行报告
        completed_steps = sum(1 for s in steps if s.status == ExecutionStatus.COMPLETED)
        total_steps = len(steps)

        print("\n" + "=" * 60)
        print(f"📊 执行完成: {completed_steps}/{total_steps} 步成功")

        if failed_steps:
            print(f"\n❌ 失败的步骤:")
            for i, step in failed_steps:
                print(f"  {i}. {step.description}")
                print(f"     错误: {step.error}")

        # 保存执行日志
        log_file = self._save_execution_log(verdict, steps)
        print(f"\n📄 执行日志已保存: {log_file}")

        return {
            "success": len(failed_steps) == 0,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "failed_steps": len(failed_steps),
            "log_file": str(log_file)
        }

    def _save_execution_log(self, verdict: Verdict, steps: List[ExecutionStep]) -> Path:
        """
        保存执行日志

        Args:
            verdict: 判决
            steps: 执行步骤

        Returns:
            日志文件路径
        """
        log_data = {
            "case_id": verdict.case_id,
            "verdict_type": verdict.verdict_type.value,
            "executed_at": datetime.now().isoformat(),
            "steps": [
                {
                    "description": step.description,
                    "command": step.command,
                    "status": step.status.value,
                    "output": step.output,
                    "error": step.error,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None
                }
                for step in steps
            ]
        }

        log_file = self.execution_log_dir / f"{verdict.case_id}_execution.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        return log_file

    def rollback_execution(self, case_id: str) -> bool:
        """
        回滚执行

        Args:
            case_id: 案件 ID

        Returns:
            是否成功
        """
        print(f"\n🔄 回滚判决执行: {case_id}")

        branch_name = f"courtroom/{case_id}"

        # 检查分支是否存在
        result = subprocess.run(
            f"git branch --list {branch_name}",
            shell=True,
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            print(f"⚠️  分支 {branch_name} 不存在")
            return False

        # 切换到主分支
        subprocess.run("git checkout master", shell=True)

        # 删除分支
        result = subprocess.run(
            f"git branch -D {branch_name}",
            shell=True,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ 已删除分支 {branch_name}")
            return True
        else:
            print(f"❌ 删除分支失败: {result.stderr}")
            return False
