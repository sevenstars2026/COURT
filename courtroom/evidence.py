"""
证据管理系统 - 允许 Agent 提交和引用证据
"""
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import json


class EvidenceType(str, Enum):
    """证据类型"""
    CODE_SNIPPET = "code_snippet"      # 代码片段
    LOG_FILE = "log_file"              # 日志文件
    TEST_RESULT = "test_result"        # 测试结果
    BENCHMARK = "benchmark"            # 性能基准测试
    SCREENSHOT = "screenshot"          # 截图
    DOCUMENTATION = "documentation"    # 文档
    COMMIT_HISTORY = "commit_history"  # Git 提交历史
    ISSUE_REPORT = "issue_report"      # Issue 报告
    USER_FEEDBACK = "user_feedback"    # 用户反馈
    OTHER = "other"                    # 其他


class Evidence(BaseModel):
    """证据"""
    evidence_id: str = Field(default_factory=lambda: f"evidence_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    case_id: str
    submitted_by: str  # prosecutor, defender, jury
    evidence_type: EvidenceType
    title: str
    description: str
    content: str  # 证据内容（代码、日志、JSON 等）
    file_path: Optional[str] = None  # 如果是文件，记录路径
    metadata: Dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)


class EvidenceManager:
    """证据管理器"""

    def __init__(self, evidence_dir: Path):
        """
        初始化证据管理器

        Args:
            evidence_dir: 证据存储目录
        """
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def submit_evidence(
        self,
        case_id: str,
        submitted_by: str,
        evidence_type: EvidenceType,
        title: str,
        description: str,
        content: str,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Evidence:
        """
        提交证据

        Args:
            case_id: 案件 ID
            submitted_by: 提交者（prosecutor/defender/jury）
            evidence_type: 证据类型
            title: 标题
            description: 描述
            content: 内容
            file_path: 文件路径（可选）
            metadata: 元数据（可选）
            tags: 标签（可选）

        Returns:
            证据对象
        """
        evidence = Evidence(
            case_id=case_id,
            submitted_by=submitted_by,
            evidence_type=evidence_type,
            title=title,
            description=description,
            content=content,
            file_path=file_path,
            metadata=metadata or {},
            tags=tags or []
        )

        # 保存到文件
        evidence_file = self.evidence_dir / f"{evidence.evidence_id}.json"
        with open(evidence_file, "w", encoding="utf-8") as f:
            json.dump(evidence.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

        print(f"📎 证据已提交: {evidence.evidence_id} - {title}")
        return evidence

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """
        获取证据

        Args:
            evidence_id: 证据 ID

        Returns:
            证据对象，如果不存在则返回 None
        """
        evidence_file = self.evidence_dir / f"{evidence_id}.json"
        if not evidence_file.exists():
            return None

        with open(evidence_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Evidence(**data)

    def list_evidence(self, case_id: str) -> List[Evidence]:
        """
        列出案件的所有证据

        Args:
            case_id: 案件 ID

        Returns:
            证据列表
        """
        evidence_list = []
        for evidence_file in self.evidence_dir.glob("*.json"):
            with open(evidence_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                evidence = Evidence(**data)
                if evidence.case_id == case_id:
                    evidence_list.append(evidence)

        # 按提交时间排序
        evidence_list.sort(key=lambda e: e.submitted_at)
        return evidence_list

    def search_evidence(
        self,
        case_id: Optional[str] = None,
        evidence_type: Optional[EvidenceType] = None,
        submitted_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Evidence]:
        """
        搜索证据

        Args:
            case_id: 案件 ID（可选）
            evidence_type: 证据类型（可选）
            submitted_by: 提交者（可选）
            tags: 标签（可选）

        Returns:
            匹配的证据列表
        """
        evidence_list = []
        for evidence_file in self.evidence_dir.glob("*.json"):
            with open(evidence_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                evidence = Evidence(**data)

                # 过滤条件
                if case_id and evidence.case_id != case_id:
                    continue
                if evidence_type and evidence.evidence_type != evidence_type:
                    continue
                if submitted_by and evidence.submitted_by != submitted_by:
                    continue
                if tags and not any(tag in evidence.tags for tag in tags):
                    continue

                evidence_list.append(evidence)

        evidence_list.sort(key=lambda e: e.submitted_at)
        return evidence_list

    def generate_evidence_report(self, case_id: str) -> str:
        """
        生成证据报告

        Args:
            case_id: 案件 ID

        Returns:
            Markdown 格式的证据报告
        """
        evidence_list = self.list_evidence(case_id)

        if not evidence_list:
            return "## 📎 证据清单\n\n无证据提交。\n"

        lines = ["## 📎 证据清单\n"]

        # 按提交者分组
        by_submitter = {}
        for evidence in evidence_list:
            if evidence.submitted_by not in by_submitter:
                by_submitter[evidence.submitted_by] = []
            by_submitter[evidence.submitted_by].append(evidence)

        for submitter, evidences in by_submitter.items():
            submitter_name = {
                "prosecutor": "检察官",
                "defender": "辩护律师",
                "jury": "陪审团"
            }.get(submitter, submitter)

            lines.append(f"### {submitter_name}提交的证据\n")

            for evidence in evidences:
                lines.append(f"#### 📎 {evidence.title}\n")
                lines.append(f"**证据编号**: {evidence.evidence_id}")
                lines.append(f"**证据类型**: {evidence.evidence_type.value}")
                lines.append(f"**提交时间**: {evidence.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if evidence.tags:
                    lines.append(f"**标签**: {', '.join(evidence.tags)}")
                lines.append(f"\n**描述**: {evidence.description}\n")

                # 根据证据类型格式化内容
                if evidence.evidence_type == EvidenceType.CODE_SNIPPET:
                    lines.append("```python")
                    lines.append(evidence.content)
                    lines.append("```\n")
                elif evidence.evidence_type == EvidenceType.TEST_RESULT:
                    lines.append("```")
                    lines.append(evidence.content)
                    lines.append("```\n")
                else:
                    lines.append(evidence.content)
                    lines.append("")

                if evidence.file_path:
                    lines.append(f"**文件路径**: `{evidence.file_path}`\n")

                lines.append("---\n")

        return "\n".join(lines)


# 便捷函数
def submit_code_evidence(
    manager: EvidenceManager,
    case_id: str,
    submitted_by: str,
    title: str,
    code: str,
    file_path: str,
    description: str = ""
) -> Evidence:
    """提交代码证据"""
    return manager.submit_evidence(
        case_id=case_id,
        submitted_by=submitted_by,
        evidence_type=EvidenceType.CODE_SNIPPET,
        title=title,
        description=description or f"来自 {file_path} 的代码片段",
        content=code,
        file_path=file_path,
        tags=["code"]
    )


def submit_test_evidence(
    manager: EvidenceManager,
    case_id: str,
    submitted_by: str,
    title: str,
    test_output: str,
    passed: bool,
    description: str = ""
) -> Evidence:
    """提交测试结果证据"""
    return manager.submit_evidence(
        case_id=case_id,
        submitted_by=submitted_by,
        evidence_type=EvidenceType.TEST_RESULT,
        title=title,
        description=description or "测试执行结果",
        content=test_output,
        metadata={"passed": passed},
        tags=["test", "passed" if passed else "failed"]
    )


def submit_benchmark_evidence(
    manager: EvidenceManager,
    case_id: str,
    submitted_by: str,
    title: str,
    benchmark_data: Dict[str, Any],
    description: str = ""
) -> Evidence:
    """提交性能基准测试证据"""
    return manager.submit_evidence(
        case_id=case_id,
        submitted_by=submitted_by,
        evidence_type=EvidenceType.BENCHMARK,
        title=title,
        description=description or "性能基准测试结果",
        content=json.dumps(benchmark_data, indent=2),
        metadata=benchmark_data,
        tags=["benchmark", "performance"]
    )
