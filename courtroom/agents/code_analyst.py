"""
代码分析师 - 在庭审前分析代码库，生成技术报告
使用 Claude Code CLI 进行深度代码分析
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class CodeAnalysisReport:
    """代码分析报告"""
    def __init__(self):
        self.case_id: str = ""
        self.analyzed_at: datetime = datetime.now()
        self.codebase_structure: Dict[str, Any] = {}
        self.relevant_files: List[str] = []
        self.dependencies: List[str] = []
        self.potential_issues: List[str] = []
        self.recommendations: List[str] = []
        self.complexity_score: int = 0  # 1-10
        self.risk_assessment: str = ""
        self.estimated_effort: str = ""  # low, medium, high
        self.raw_analysis: str = ""


class CodeAnalyst:
    """代码分析师 - 使用 Claude Code 分析代码库"""

    def __init__(self, project_root: Path, claude_cli: str = "claude"):
        """
        初始化代码分析师

        Args:
            project_root: 项目根目录
            claude_cli: Claude Code CLI 路径
        """
        self.project_root = project_root
        self.claude_cli = claude_cli
        self.reports_dir = project_root / "courtroom" / "analysis_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def analyze_for_motion(
        self,
        case_id: str,
        motion_title: str,
        motion_description: str,
        affected_files: List[str],
        codebase_path: Path
    ) -> CodeAnalysisReport:
        """
        为动议分析代码库

        Args:
            case_id: 案件编号
            motion_title: 动议标题
            motion_description: 动议描述
            affected_files: 声称影响的文件
            codebase_path: 代码库路径

        Returns:
            代码分析报告
        """
        report = CodeAnalysisReport()
        report.case_id = case_id

        print(f"\n🔍 代码分析师开始分析案件 {case_id}...")

        # 步骤 1: 分析代码库结构
        print("  步骤 1: 分析代码库结构...")
        structure = self._analyze_structure(codebase_path)
        report.codebase_structure = structure

        # 步骤 2: 使用 Claude Code 深度分析
        print("  步骤 2: 使用 Claude Code 深度分析...")
        analysis_result = self._deep_analysis_with_claude(
            motion_title,
            motion_description,
            affected_files,
            codebase_path
        )
        report.raw_analysis = analysis_result

        # 步骤 3: 解析分析结果
        print("  步骤 3: 解析分析结果...")
        self._parse_analysis_result(analysis_result, report)

        # 步骤 4: 评估复杂度和风险
        print("  步骤 4: 评估复杂度和风险...")
        report.complexity_score = self._estimate_complexity(report)
        report.risk_assessment = self._assess_risk(report)
        report.estimated_effort = self._estimate_effort(report)

        # 保存报告
        self._save_report(report)

        print(f"  ✅ 分析完成 - 复杂度: {report.complexity_score}/10, 风险: {report.risk_assessment}")

        return report

    def _analyze_structure(self, codebase_path: Path) -> Dict[str, Any]:
        """分析代码库结构"""
        structure = {
            "total_files": 0,
            "python_files": 0,
            "test_files": 0,
            "directories": [],
            "has_tests": False,
            "has_requirements": False,
            "has_git": False
        }

        try:
            # 统计文件
            all_files = list(codebase_path.rglob("*"))
            structure["total_files"] = len([f for f in all_files if f.is_file()])
            structure["python_files"] = len(list(codebase_path.rglob("*.py")))
            structure["test_files"] = len(list(codebase_path.rglob("test_*.py"))) + \
                                     len(list(codebase_path.rglob("*_test.py")))

            # 检查关键文件
            structure["has_tests"] = structure["test_files"] > 0
            structure["has_requirements"] = (codebase_path / "requirements.txt").exists()
            structure["has_git"] = (codebase_path / ".git").exists()

            # 主要目录
            structure["directories"] = [
                d.name for d in codebase_path.iterdir()
                if d.is_dir() and not d.name.startswith('.')
            ]

        except Exception as e:
            structure["error"] = str(e)

        return structure

    def _deep_analysis_with_claude(
        self,
        motion_title: str,
        motion_description: str,
        affected_files: List[str],
        codebase_path: Path
    ) -> str:
        """使用 Claude Code 进行深度分析"""
        try:
            # 构建分析提示
            prompt = f"""你是一位资深代码分析师，需要分析以下需求对代码库的影响。

【需求信息】
标题: {motion_title}
描述: {motion_description}
声称影响的文件: {', '.join(affected_files) if affected_files else '未指定'}

【分析任务】
请进行以下分析，并以结构化格式输出：

1. **相关文件识别**
   - 列出所有真正需要修改的文件（不只是声称的文件）
   - 识别依赖关系和间接影响的文件

2. **依赖分析**
   - 列出需要的外部依赖（库、包）
   - 检查是否已安装

3. **潜在问题**
   - 识别可能的技术风险
   - 指出代码冲突或兼容性问题
   - 发现被忽略的边界情况

4. **实施建议**
   - 推荐的实施步骤
   - 需要注意的关键点
   - 测试策略建议

5. **复杂度评估**
   - 评估实施难度（简单/中等/复杂）
   - 估计工作量

请使用以下格式输出：

## 相关文件
- file1.py: 原因
- file2.py: 原因

## 依赖分析
- dependency1: 状态
- dependency2: 状态

## 潜在问题
- 问题1
- 问题2

## 实施建议
1. 步骤1
2. 步骤2

## 复杂度评估
难度: [简单/中等/复杂]
工作量: [低/中/高]
风险: [低/中/高]

请开始分析。
"""

            # 调用 Claude Code CLI
            cmd = [
                self.claude_cli,
                "-p",  # 非交互模式
                "--add-dir", str(codebase_path),
                "--output-format", "text",
                prompt
            ]

            result = subprocess.run(
                cmd,
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return f"分析失败: {result.stderr}"

        except subprocess.TimeoutExpired:
            return "分析超时（2分钟）"
        except Exception as e:
            return f"分析异常: {e}"

    def _parse_analysis_result(self, analysis: str, report: CodeAnalysisReport):
        """解析 Claude 的分析结果"""
        # 简单的文本解析（实际可以用更复杂的方法）
        lines = analysis.split('\n')

        current_section = None
        for line in lines:
            line = line.strip()

            if line.startswith('## 相关文件'):
                current_section = 'files'
            elif line.startswith('## 依赖分析'):
                current_section = 'dependencies'
            elif line.startswith('## 潜在问题'):
                current_section = 'issues'
            elif line.startswith('## 实施建议'):
                current_section = 'recommendations'
            elif line.startswith('## 复杂度评估'):
                current_section = 'complexity'
            elif line.startswith('-') or line.startswith('*'):
                content = line[1:].strip()
                if current_section == 'files':
                    # 提取文件名
                    if ':' in content:
                        filename = content.split(':')[0].strip()
                        report.relevant_files.append(filename)
                elif current_section == 'dependencies':
                    report.dependencies.append(content)
                elif current_section == 'issues':
                    report.potential_issues.append(content)
            elif line.startswith(tuple(str(i) for i in range(1, 10))):
                if current_section == 'recommendations':
                    report.recommendations.append(line)

    def _estimate_complexity(self, report: CodeAnalysisReport) -> int:
        """估计复杂度（1-10）"""
        score = 5  # 基础分

        # 根据文件数量调整
        if len(report.relevant_files) > 10:
            score += 2
        elif len(report.relevant_files) > 5:
            score += 1

        # 根据依赖数量调整
        if len(report.dependencies) > 5:
            score += 1

        # 根据潜在问题数量调整
        if len(report.potential_issues) > 5:
            score += 2
        elif len(report.potential_issues) > 2:
            score += 1

        return min(10, max(1, score))

    def _assess_risk(self, report: CodeAnalysisReport) -> str:
        """评估风险"""
        if report.complexity_score >= 8 or len(report.potential_issues) > 5:
            return "高风险"
        elif report.complexity_score >= 5 or len(report.potential_issues) > 2:
            return "中等风险"
        else:
            return "低风险"

    def _estimate_effort(self, report: CodeAnalysisReport) -> str:
        """估计工作量"""
        if report.complexity_score >= 8:
            return "high"
        elif report.complexity_score >= 5:
            return "medium"
        else:
            return "low"

    def _save_report(self, report: CodeAnalysisReport):
        """保存分析报告"""
        report_data = {
            "case_id": report.case_id,
            "analyzed_at": report.analyzed_at.isoformat(),
            "codebase_structure": report.codebase_structure,
            "relevant_files": report.relevant_files,
            "dependencies": report.dependencies,
            "potential_issues": report.potential_issues,
            "recommendations": report.recommendations,
            "complexity_score": report.complexity_score,
            "risk_assessment": report.risk_assessment,
            "estimated_effort": report.estimated_effort,
            "raw_analysis": report.raw_analysis
        }

        report_file = self.reports_dir / f"{report.case_id}_analysis.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    def get_report(self, case_id: str) -> Optional[CodeAnalysisReport]:
        """获取分析报告"""
        report_file = self.reports_dir / f"{case_id}_analysis.json"
        if not report_file.exists():
            return None

        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        report = CodeAnalysisReport()
        report.case_id = data["case_id"]
        report.analyzed_at = datetime.fromisoformat(data["analyzed_at"])
        report.codebase_structure = data["codebase_structure"]
        report.relevant_files = data["relevant_files"]
        report.dependencies = data["dependencies"]
        report.potential_issues = data["potential_issues"]
        report.recommendations = data["recommendations"]
        report.complexity_score = data["complexity_score"]
        report.risk_assessment = data["risk_assessment"]
        report.estimated_effort = data["estimated_effort"]
        report.raw_analysis = data["raw_analysis"]

        return report
