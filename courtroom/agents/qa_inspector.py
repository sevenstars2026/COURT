"""
质量检查员 - 验证执行结果，失败时触发重审
"""
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from ..agents.execution_engineer import ExecutionResult


class QAReport:
    """质量检查报告"""
    def __init__(self):
        self.case_id: str = ""
        self.checked_at: datetime = datetime.now()
        self.passed: bool = False
        self.test_results: Dict[str, Any] = {}
        self.code_quality_issues: List[str] = []
        self.security_issues: List[str] = []
        self.performance_issues: List[str] = []
        self.recommendations: List[str] = []
        self.should_retry: bool = False
        self.retry_reason: str = ""


class QAInspector:
    """质量检查员 - 验证执行结果"""

    def __init__(self, project_root: Path):
        """
        初始化质量检查员

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.reports_dir = project_root / "courtroom" / "qa_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def inspect(
        self,
        case_id: str,
        execution_result: ExecutionResult,
        codebase_path: Path
    ) -> QAReport:
        """
        检查执行结果

        Args:
            case_id: 案件编号
            execution_result: 执行结果
            codebase_path: 代码库路径

        Returns:
            质量检查报告
        """
        report = QAReport()
        report.case_id = case_id

        print(f"\n🔍 质量检查员开始检查案件 {case_id}...")

        # 步骤 1: 检查执行是否成功
        if not execution_result.success:
            report.passed = False
            report.should_retry = True
            report.retry_reason = f"执行失败: {execution_result.error_message}"
            print(f"  ❌ 执行失败，建议重审")
            self._save_report(report)
            return report

        # 步骤 2: 运行测试
        print("  步骤 1: 运行测试...")
        test_passed, test_details = self._run_comprehensive_tests(codebase_path)
        report.test_results = test_details

        if not test_passed:
            report.passed = False
            report.should_retry = True
            report.retry_reason = "测试失败"
            print(f"  ❌ 测试失败，建议重审")
            self._save_report(report)
            return report

        # 步骤 3: 代码质量检查
        print("  步骤 2: 代码质量检查...")
        quality_issues = self._check_code_quality(
            execution_result.modified_files + execution_result.created_files,
            codebase_path
        )
        report.code_quality_issues = quality_issues

        # 步骤 4: 安全检查（基础）
        print("  步骤 3: 安全检查...")
        security_issues = self._check_security(
            execution_result.modified_files + execution_result.created_files,
            codebase_path
        )
        report.security_issues = security_issues

        # 步骤 5: 性能检查（基础）
        print("  步骤 4: 性能检查...")
        performance_issues = self._check_performance(
            execution_result.modified_files + execution_result.created_files,
            codebase_path
        )
        report.performance_issues = performance_issues

        # 综合判断
        total_issues = len(quality_issues) + len(security_issues) + len(performance_issues)

        if total_issues == 0:
            report.passed = True
            report.should_retry = False
            print(f"  ✅ 质量检查通过")
        elif total_issues <= 3:
            report.passed = True
            report.should_retry = False
            report.recommendations = [
                "建议修复以下问题以提高代码质量",
                *quality_issues[:3],
                *security_issues[:3],
                *performance_issues[:3]
            ]
            print(f"  ⚠️  发现 {total_issues} 个小问题，但可以接受")
        else:
            report.passed = False
            report.should_retry = True
            report.retry_reason = f"发现 {total_issues} 个质量问题"
            print(f"  ❌ 发现 {total_issues} 个问题，建议重审")

        self._save_report(report)
        return report

    def _run_comprehensive_tests(self, codebase_path: Path) -> Tuple[bool, Dict[str, Any]]:
        """运行全面的测试"""
        details = {
            "unit_tests": {"passed": False, "output": ""},
            "integration_tests": {"passed": False, "output": ""},
            "has_tests": False
        }

        # 检查是否有测试文件
        test_files = list(codebase_path.glob("test_*.py")) + list(codebase_path.glob("*_test.py"))
        details["has_tests"] = len(test_files) > 0

        if not details["has_tests"]:
            details["unit_tests"]["passed"] = True
            details["unit_tests"]["output"] = "无测试文件"
            return True, details

        try:
            # 运行 pytest
            result = subprocess.run(
                ["pytest", "-v", "--tb=short", "--maxfail=5"],
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=180
            )

            details["unit_tests"]["output"] = result.stdout + "\n" + result.stderr
            details["unit_tests"]["passed"] = result.returncode == 0

            return result.returncode == 0, details

        except subprocess.TimeoutExpired:
            details["unit_tests"]["output"] = "测试超时（3分钟）"
            return False, details
        except FileNotFoundError:
            details["unit_tests"]["output"] = "pytest 未安装"
            details["unit_tests"]["passed"] = True
            return True, details
        except Exception as e:
            details["unit_tests"]["output"] = f"测试异常: {e}"
            return False, details

    def _check_code_quality(self, files: List[str], codebase_path: Path) -> List[str]:
        """检查代码质量"""
        issues = []

        for filepath in files:
            if not filepath.endswith('.py'):
                continue

            full_path = codebase_path / filepath
            if not full_path.exists():
                continue

            try:
                content = full_path.read_text(encoding='utf-8')

                # 基础检查
                lines = content.split('\n')

                # 检查过长的行
                long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 120]
                if long_lines:
                    issues.append(f"{filepath}: 行过长 (行号: {long_lines[:3]})")

                # 检查过长的函数
                in_function = False
                function_start = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('def '):
                        if in_function and (i - function_start) > 50:
                            issues.append(f"{filepath}: 函数过长 (行 {function_start}-{i})")
                        in_function = True
                        function_start = i
                    elif line.strip().startswith('class '):
                        in_function = False

                # 检查是否有 TODO/FIXME
                todos = [i+1 for i, line in enumerate(lines) if 'TODO' in line or 'FIXME' in line]
                if todos:
                    issues.append(f"{filepath}: 包含 TODO/FIXME (行号: {todos[:3]})")

            except Exception as e:
                issues.append(f"{filepath}: 无法读取文件 - {e}")

        return issues

    def _check_security(self, files: List[str], codebase_path: Path) -> List[str]:
        """基础安全检查"""
        issues = []

        dangerous_patterns = [
            ('eval(', '使用 eval() 可能导致代码注入'),
            ('exec(', '使用 exec() 可能导致代码注入'),
            ('pickle.loads', '使用 pickle.loads 可能不安全'),
            ('shell=True', '使用 shell=True 可能导致命令注入'),
            ('password', '可能包含硬编码密码'),
            ('api_key', '可能包含硬编码 API 密钥'),
        ]

        for filepath in files:
            if not filepath.endswith('.py'):
                continue

            full_path = codebase_path / filepath
            if not full_path.exists():
                continue

            try:
                content = full_path.read_text(encoding='utf-8')

                for pattern, message in dangerous_patterns:
                    if pattern in content:
                        issues.append(f"{filepath}: {message}")

            except Exception:
                pass

        return issues

    def _check_performance(self, files: List[str], codebase_path: Path) -> List[str]:
        """基础性能检查"""
        issues = []

        performance_patterns = [
            ('time.sleep(', '使用 sleep 可能影响性能'),
            ('while True:', '无限循环可能导致性能问题'),
        ]

        for filepath in files:
            if not filepath.endswith('.py'):
                continue

            full_path = codebase_path / filepath
            if not full_path.exists():
                continue

            try:
                content = full_path.read_text(encoding='utf-8')

                for pattern, message in performance_patterns:
                    if pattern in content:
                        # 检查是否在合理的上下文中
                        if pattern == 'time.sleep(' and 'test' not in filepath.lower():
                            issues.append(f"{filepath}: {message}")
                        elif pattern == 'while True:':
                            issues.append(f"{filepath}: {message}")

            except Exception:
                pass

        return issues

    def _save_report(self, report: QAReport):
        """保存质量检查报告"""
        report_data = {
            "case_id": report.case_id,
            "checked_at": report.checked_at.isoformat(),
            "passed": report.passed,
            "test_results": report.test_results,
            "code_quality_issues": report.code_quality_issues,
            "security_issues": report.security_issues,
            "performance_issues": report.performance_issues,
            "recommendations": report.recommendations,
            "should_retry": report.should_retry,
            "retry_reason": report.retry_reason
        }

        report_file = self.reports_dir / f"{report.case_id}_qa.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    def get_report(self, case_id: str) -> Optional[QAReport]:
        """获取质量检查报告"""
        report_file = self.reports_dir / f"{case_id}_qa.json"
        if not report_file.exists():
            return None

        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        report = QAReport()
        report.case_id = data["case_id"]
        report.checked_at = datetime.fromisoformat(data["checked_at"])
        report.passed = data["passed"]
        report.test_results = data["test_results"]
        report.code_quality_issues = data["code_quality_issues"]
        report.security_issues = data["security_issues"]
        report.performance_issues = data["performance_issues"]
        report.recommendations = data["recommendations"]
        report.should_retry = data["should_retry"]
        report.retry_reason = data["retry_reason"]

        return report
