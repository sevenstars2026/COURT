"""
分层记忆系统 - 解决上下文窗口爆炸问题
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import sqlite3
from collections import defaultdict


class MemoryTier(str):
    """记忆层级"""
    HOT = "hot"      # 热记忆：当前庭审完整记录
    WARM = "warm"    # 温记忆：精简摘要（200 token）
    COLD = "cold"    # 冷记忆：向量知识库（按需检索）
    FROZEN = "frozen"  # 冻结记忆：仅一句话总结


class CaseSummary(BaseModel):
    """案件摘要（温记忆）"""
    case_id: str
    title: str
    motion_type: str
    verdict_type: str
    key_points: List[str] = Field(default_factory=list)  # 3-5 个关键点
    reasoning_summary: str  # 判决理由摘要（100 字）
    precedent_value: str  # 判例价值（一句话）
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    access_count: int = 0
    tier: str = MemoryTier.WARM


class MemoryManager:
    """分层记忆管理器"""

    def __init__(self, courtroom_root: Path):
        """
        初始化记忆管理器

        Args:
            courtroom_root: 法庭根目录
        """
        self.root = courtroom_root
        self.db_path = self.root / "memory.db"
        self.summaries_dir = self.root / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建摘要表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_summaries (
                case_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                motion_type TEXT NOT NULL,
                verdict_type TEXT NOT NULL,
                key_points TEXT NOT NULL,
                reasoning_summary TEXT NOT NULL,
                precedent_value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                tier TEXT DEFAULT 'warm'
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_motion_type
            ON case_summaries(motion_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verdict_type
            ON case_summaries(verdict_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_accessed
            ON case_summaries(last_accessed)
        """)

        conn.commit()
        conn.close()

    def create_summary(
        self,
        case_id: str,
        title: str,
        motion_type: str,
        verdict_type: str,
        full_transcript: str,
        verdict_reasoning: str
    ) -> CaseSummary:
        """
        创建案件摘要（从完整记录提取）

        Args:
            case_id: 案件 ID
            title: 标题
            motion_type: 动议类型
            verdict_type: 判决类型
            full_transcript: 完整庭审记录
            verdict_reasoning: 判决理由

        Returns:
            案件摘要
        """
        # 提取关键点（简化版，实际应该用 LLM）
        key_points = self._extract_key_points(full_transcript, verdict_reasoning)

        # 生成摘要
        reasoning_summary = self._summarize_reasoning(verdict_reasoning)

        # 提取判例价值
        precedent_value = self._extract_precedent_value(
            motion_type, verdict_type, reasoning_summary
        )

        summary = CaseSummary(
            case_id=case_id,
            title=title,
            motion_type=motion_type,
            verdict_type=verdict_type,
            key_points=key_points,
            reasoning_summary=reasoning_summary,
            precedent_value=precedent_value
        )

        # 保存到数据库
        self._save_summary(summary)

        return summary

    def _extract_key_points(self, transcript: str, reasoning: str) -> List[str]:
        """提取关键点（简化版）"""
        # 实际应该用 LLM 提取，这里用简单规则
        key_points = []

        # 从判决理由中提取
        if "风险" in reasoning:
            key_points.append("存在风险需要缓解")
        if "收益" in reasoning or "提升" in reasoning:
            key_points.append("有明确的收益")
        if "测试" in reasoning:
            key_points.append("需要充分测试")

        # 限制在 5 个以内
        return key_points[:5]

    def _summarize_reasoning(self, reasoning: str) -> str:
        """摘要判决理由（简化版）"""
        # 实际应该用 LLM 摘要，这里简单截取
        lines = reasoning.strip().split('\n')
        summary_lines = [line for line in lines if line.strip()][:3]
        return ' '.join(summary_lines)[:200]

    def _extract_precedent_value(
        self,
        motion_type: str,
        verdict_type: str,
        reasoning: str
    ) -> str:
        """提取判例价值（一句话）"""
        # 简化版
        if verdict_type == "approved":
            return f"{motion_type} 类动议在满足条件时可批准"
        elif verdict_type == "rejected":
            return f"{motion_type} 类动议风险过高应驳回"
        else:
            return f"{motion_type} 类动议需要修改后批准"

    def _save_summary(self, summary: CaseSummary):
        """保存摘要到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO case_summaries
            (case_id, title, motion_type, verdict_type, key_points,
             reasoning_summary, precedent_value, created_at, last_accessed,
             access_count, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            summary.case_id,
            summary.title,
            summary.motion_type,
            summary.verdict_type,
            json.dumps(summary.key_points),
            summary.reasoning_summary,
            summary.precedent_value,
            summary.created_at.isoformat(),
            summary.last_accessed.isoformat(),
            summary.access_count,
            summary.tier
        ))

        conn.commit()
        conn.close()

    def get_summary(self, case_id: str) -> Optional[CaseSummary]:
        """
        获取案件摘要

        Args:
            case_id: 案件 ID

        Returns:
            案件摘要，如果不存在则返回 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM case_summaries WHERE case_id = ?
        """, (case_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # 更新访问记录
        self._update_access(case_id)

        return CaseSummary(
            case_id=row[0],
            title=row[1],
            motion_type=row[2],
            verdict_type=row[3],
            key_points=json.loads(row[4]),
            reasoning_summary=row[5],
            precedent_value=row[6],
            created_at=datetime.fromisoformat(row[7]),
            last_accessed=datetime.fromisoformat(row[8]),
            access_count=row[9],
            tier=row[10]
        )

    def search_summaries(
        self,
        motion_type: Optional[str] = None,
        verdict_type: Optional[str] = None,
        limit: int = 10
    ) -> List[CaseSummary]:
        """
        搜索案件摘要

        Args:
            motion_type: 动议类型（可选）
            verdict_type: 判决类型（可选）
            limit: 返回数量限制

        Returns:
            案件摘要列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM case_summaries WHERE 1=1"
        params = []

        if motion_type:
            query += " AND motion_type = ?"
            params.append(motion_type)

        if verdict_type:
            query += " AND verdict_type = ?"
            params.append(verdict_type)

        query += " ORDER BY last_accessed DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        summaries = []
        for row in rows:
            summaries.append(CaseSummary(
                case_id=row[0],
                title=row[1],
                motion_type=row[2],
                verdict_type=row[3],
                key_points=json.loads(row[4]),
                reasoning_summary=row[5],
                precedent_value=row[6],
                created_at=datetime.fromisoformat(row[7]),
                last_accessed=datetime.fromisoformat(row[8]),
                access_count=row[9],
                tier=row[10]
            ))

        return summaries

    def _update_access(self, case_id: str):
        """更新访问记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE case_summaries
            SET last_accessed = ?, access_count = access_count + 1
            WHERE case_id = ?
        """, (datetime.now().isoformat(), case_id))

        conn.commit()
        conn.close()

    def apply_forgetting_curve(self, days_threshold: int = 30):
        """
        应用遗忘曲线，降级长期未访问的记忆

        Args:
            days_threshold: 天数阈值
        """
        threshold_date = datetime.now() - timedelta(days=days_threshold)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 查找长期未访问的案件
        cursor.execute("""
            SELECT case_id, tier FROM case_summaries
            WHERE last_accessed < ? AND tier != ?
        """, (threshold_date.isoformat(), MemoryTier.FROZEN))

        cases_to_downgrade = cursor.fetchall()

        # 降级
        for case_id, current_tier in cases_to_downgrade:
            if current_tier == MemoryTier.WARM:
                new_tier = MemoryTier.COLD
            elif current_tier == MemoryTier.COLD:
                new_tier = MemoryTier.FROZEN
            else:
                continue

            cursor.execute("""
                UPDATE case_summaries
                SET tier = ?
                WHERE case_id = ?
            """, (new_tier, case_id))

            print(f"📉 案件 {case_id} 从 {current_tier} 降级到 {new_tier}")

        conn.commit()
        conn.close()

        return len(cases_to_downgrade)

    def get_context_for_judge(
        self,
        current_motion_type: str,
        max_tokens: int = 2000
    ) -> str:
        """
        为法官准备上下文（智能选择记忆层级）

        Args:
            current_motion_type: 当前动议类型
            max_tokens: 最大 token 数

        Returns:
            上下文字符串
        """
        # 搜索相关的温记忆
        summaries = self.search_summaries(
            motion_type=current_motion_type,
            limit=5
        )

        context_parts = []
        token_count = 0

        context_parts.append(f"## 相关判例（{len(summaries)} 个）\n")

        for summary in summaries:
            # 估算 token 数（粗略：1 token ≈ 4 字符）
            summary_text = f"""
### {summary.title} ({summary.case_id})
- 判决：{summary.verdict_type}
- 判例价值：{summary.precedent_value}
- 关键点：{', '.join(summary.key_points)}
- 理由摘要：{summary.reasoning_summary}
"""
            estimated_tokens = len(summary_text) // 4

            if token_count + estimated_tokens > max_tokens:
                break

            context_parts.append(summary_text)
            token_count += estimated_tokens

        return '\n'.join(context_parts)

    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆系统统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总案件数
        cursor.execute("SELECT COUNT(*) FROM case_summaries")
        total = cursor.fetchone()[0]

        # 按层级统计
        cursor.execute("""
            SELECT tier, COUNT(*) FROM case_summaries GROUP BY tier
        """)
        by_tier = dict(cursor.fetchall())

        # 按类型统计
        cursor.execute("""
            SELECT motion_type, COUNT(*) FROM case_summaries GROUP BY motion_type
        """)
        by_type = dict(cursor.fetchall())

        # 最常访问的案件
        cursor.execute("""
            SELECT case_id, title, access_count
            FROM case_summaries
            ORDER BY access_count DESC
            LIMIT 5
        """)
        most_accessed = cursor.fetchall()

        conn.close()

        return {
            "total_cases": total,
            "by_tier": by_tier,
            "by_type": by_type,
            "most_accessed": [
                {"case_id": row[0], "title": row[1], "access_count": row[2]}
                for row in most_accessed
            ]
        }
