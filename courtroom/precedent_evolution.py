"""
判例演化系统 - 让系统越跑越聪明
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json
from enum import Enum


class PrecedentStatus(str, Enum):
    """判例状态"""
    ACTIVE = "active"              # 活跃
    DANGEROUS = "dangerous"        # 危险（导致过 Bug）
    DEPRECATED = "deprecated"      # 已废弃
    CONFLICTED = "conflicted"      # 存在冲突


class Precedent(BaseModel):
    """判例"""
    precedent_id: str
    case_id: str
    title: str
    motion_type: str
    verdict_type: str
    core_principle: str            # 核心原则（一句话）
    reasoning: str                 # 判决理由
    created_at: datetime
    status: PrecedentStatus = PrecedentStatus.ACTIVE
    reference_count: int = 0       # 被引用次数
    success_count: int = 0         # 成功案例数
    failure_count: int = 0         # 失败案例数
    weight: float = 1.0            # 权重（0-1）
    tags: List[str] = Field(default_factory=list)
    conflicts_with: List[str] = Field(default_factory=list)  # 冲突的判例 ID


class ConflictResolution(BaseModel):
    """冲突调和方案"""
    resolution_id: str
    conflicting_precedents: List[str]
    refined_principle: str         # 精炼后的原则
    conditions: List[str]          # 适用条件
    created_at: datetime


class PrecedentEvolution:
    """判例演化系统"""

    def __init__(self, courtroom_root: Path):
        """
        初始化判例演化系统

        Args:
            courtroom_root: 法庭根目录
        """
        self.root = courtroom_root
        self.precedents_dir = self.root / "precedents"
        self.precedents_dir.mkdir(parents=True, exist_ok=True)
        self.precedents: Dict[str, Precedent] = {}
        self.resolutions: Dict[str, ConflictResolution] = {}
        self._load_precedents()

    def _load_precedents(self):
        """加载判例库"""
        for file in self.precedents_dir.glob("precedent_*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                precedent = Precedent(**data)
                self.precedents[precedent.precedent_id] = precedent

    def add_precedent(
        self,
        case_id: str,
        title: str,
        motion_type: str,
        verdict_type: str,
        core_principle: str,
        reasoning: str,
        tags: Optional[List[str]] = None
    ) -> Precedent:
        """
        添加判例

        Args:
            case_id: 案件 ID
            title: 标题
            motion_type: 动议类型
            verdict_type: 判决类型
            core_principle: 核心原则
            reasoning: 判决理由
            tags: 标签

        Returns:
            判例
        """
        precedent_id = f"precedent_{case_id}"

        precedent = Precedent(
            precedent_id=precedent_id,
            case_id=case_id,
            title=title,
            motion_type=motion_type,
            verdict_type=verdict_type,
            core_principle=core_principle,
            reasoning=reasoning,
            created_at=datetime.now(),
            tags=tags or []
        )

        self.precedents[precedent_id] = precedent
        self._save_precedent(precedent)

        print(f"📚 添加判例: {precedent_id}")
        return precedent

    def _save_precedent(self, precedent: Precedent):
        """保存判例"""
        file_path = self.precedents_dir / f"{precedent.precedent_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(precedent.model_dump(mode='json'), f, indent=2, ensure_ascii=False, default=str)

    def search_precedents(
        self,
        motion_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[PrecedentStatus] = None,
        limit: int = 5
    ) -> List[Precedent]:
        """
        搜索判例

        Args:
            motion_type: 动议类型
            tags: 标签
            status: 状态
            limit: 数量限制

        Returns:
            判例列表
        """
        results = []

        for precedent in self.precedents.values():
            # 过滤条件
            if motion_type and precedent.motion_type != motion_type:
                continue
            if status and precedent.status != status:
                continue
            if tags and not any(tag in precedent.tags for tag in tags):
                continue

            results.append(precedent)

        # 按权重和引用次数排序
        results.sort(
            key=lambda p: (p.weight, p.reference_count),
            reverse=True
        )

        return results[:limit]

    def detect_conflicts(self) -> List[tuple[Precedent, Precedent]]:
        """
        检测判例冲突

        Returns:
            冲突的判例对列表
        """
        conflicts = []
        precedent_list = list(self.precedents.values())

        for i, p1 in enumerate(precedent_list):
            for p2 in precedent_list[i+1:]:
                # 检查是否同类型但判决相反
                if (p1.motion_type == p2.motion_type and
                    p1.verdict_type != p2.verdict_type and
                    self._principles_conflict(p1.core_principle, p2.core_principle)):
                    conflicts.append((p1, p2))

        return conflicts

    def _principles_conflict(self, principle1: str, principle2: str) -> bool:
        """
        判断两个原则是否冲突（简化版）

        Args:
            principle1: 原则 1
            principle2: 原则 2

        Returns:
            是否冲突
        """
        # 简化版：检查关键词
        keywords1 = set(principle1.lower().split())
        keywords2 = set(principle2.lower().split())

        # 如果有相同的关键词但结论相反
        common = keywords1 & keywords2
        if len(common) >= 2:
            # 检查是否有相反的词
            opposite_pairs = [
                ("批准", "驳回"),
                ("允许", "禁止"),
                ("可以", "不可以"),
                ("应该", "不应该")
            ]

            for word1, word2 in opposite_pairs:
                if word1 in principle1 and word2 in principle2:
                    return True
                if word2 in principle1 and word1 in principle2:
                    return True

        return False

    def resolve_conflict(
        self,
        precedent1_id: str,
        precedent2_id: str,
        refined_principle: str,
        conditions: List[str]
    ) -> ConflictResolution:
        """
        调和冲突

        Args:
            precedent1_id: 判例 1 ID
            precedent2_id: 判例 2 ID
            refined_principle: 精炼后的原则
            conditions: 适用条件

        Returns:
            调和方案
        """
        resolution_id = f"resolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        resolution = ConflictResolution(
            resolution_id=resolution_id,
            conflicting_precedents=[precedent1_id, precedent2_id],
            refined_principle=refined_principle,
            conditions=conditions,
            created_at=datetime.now()
        )

        self.resolutions[resolution_id] = resolution

        # 标记冲突
        if precedent1_id in self.precedents:
            self.precedents[precedent1_id].status = PrecedentStatus.CONFLICTED
            self.precedents[precedent1_id].conflicts_with.append(precedent2_id)
            self._save_precedent(self.precedents[precedent1_id])

        if precedent2_id in self.precedents:
            self.precedents[precedent2_id].status = PrecedentStatus.CONFLICTED
            self.precedents[precedent2_id].conflicts_with.append(precedent1_id)
            self._save_precedent(self.precedents[precedent2_id])

        print(f"⚖️ 冲突已调和: {resolution_id}")
        print(f"   精炼原则: {refined_principle}")

        return resolution

    def mark_dangerous(self, precedent_id: str, reason: str):
        """
        标记危险判例（导致了 Bug）

        Args:
            precedent_id: 判例 ID
            reason: 原因
        """
        if precedent_id not in self.precedents:
            return

        precedent = self.precedents[precedent_id]
        precedent.status = PrecedentStatus.DANGEROUS
        precedent.weight *= 0.5  # 降低权重
        precedent.failure_count += 1
        self._save_precedent(precedent)

        print(f"⚠️ 判例标记为危险: {precedent_id}")
        print(f"   原因: {reason}")
        print(f"   权重降低至: {precedent.weight:.2f}")

    def record_success(self, precedent_id: str):
        """
        记录成功案例

        Args:
            precedent_id: 判例 ID
        """
        if precedent_id not in self.precedents:
            return

        precedent = self.precedents[precedent_id]
        precedent.success_count += 1
        precedent.reference_count += 1

        # 提升权重
        if precedent.status == PrecedentStatus.ACTIVE:
            precedent.weight = min(1.0, precedent.weight + 0.05)

        self._save_precedent(precedent)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.precedents)
        by_status = {}
        by_type = {}

        for precedent in self.precedents.values():
            by_status[precedent.status] = by_status.get(precedent.status, 0) + 1
            by_type[precedent.motion_type] = by_type.get(precedent.motion_type, 0) + 1

        # 最常引用的判例
        most_referenced = sorted(
            self.precedents.values(),
            key=lambda p: p.reference_count,
            reverse=True
        )[:5]

        # 危险判例
        dangerous = [
            p for p in self.precedents.values()
            if p.status == PrecedentStatus.DANGEROUS
        ]

        return {
            "total_precedents": total,
            "by_status": by_status,
            "by_type": by_type,
            "most_referenced": [
                {
                    "id": p.precedent_id,
                    "title": p.title,
                    "references": p.reference_count,
                    "weight": p.weight
                }
                for p in most_referenced
            ],
            "dangerous_count": len(dangerous),
            "conflict_resolutions": len(self.resolutions)
        }

    def generate_report(self) -> str:
        """生成判例库报告"""
        stats = self.get_statistics()

        lines = ["# 📚 判例库报告\n"]
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        lines.append(f"## 总览\n")
        lines.append(f"- 总判例数: {stats['total_precedents']}")
        lines.append(f"- 冲突调和: {stats['conflict_resolutions']} 个")
        lines.append(f"- 危险判例: {stats['dangerous_count']} 个\n")

        lines.append(f"## 按状态分布\n")
        for status, count in stats['by_status'].items():
            lines.append(f"- {status}: {count}")
        lines.append("")

        lines.append(f"## 最常引用判例\n")
        for item in stats['most_referenced']:
            lines.append(f"- {item['title']}")
            lines.append(f"  引用次数: {item['references']}, 权重: {item['weight']:.2f}")
        lines.append("")

        return "\n".join(lines)
