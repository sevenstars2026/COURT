"""
书记员 - 生成人类可读的庭审记录
"""
from pathlib import Path
from datetime import datetime

from ..schemas import TrialTranscript, Argument, ArgumentType


class CourtReporter:
    """书记员 - 记录庭审过程"""

    def __init__(self, transcripts_dir: Path):
        self.transcripts_dir = transcripts_dir
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

    def write_transcript(self, transcript: TrialTranscript) -> Path:
        """生成庭审记录 Markdown 文件"""
        case_id = transcript.case_id
        output_file = self.transcripts_dir / f"{case_id}.md"

        content = self._generate_markdown(transcript)
        output_file.write_text(content, encoding='utf-8')

        return output_file

    def _generate_markdown(self, transcript: TrialTranscript) -> str:
        """生成 Markdown 内容"""
        motion = transcript.motion
        verdict = transcript.verdict

        # 标题和元数据
        md = f"""# ⚖️ 庭审记录：{motion.title}

**案件编号**: {motion.case_id}
**动议类型**: {motion.motion_type.value}
**提案人**: {motion.proposer}
**立案时间**: {motion.filed_at.strftime('%Y-%m-%d %H:%M:%S')}
**开庭时间**: {transcript.started_at.strftime('%Y-%m-%d %H:%M:%S')}
**闭庭时间**: {transcript.ended_at.strftime('%Y-%m-%d %H:%M:%S') if transcript.ended_at else '进行中'}

---

## 📋 案件概要

### 动议内容

{motion.description}

### 提议的变更

{self._format_list(motion.proposed_changes)}

### 影响的文件

{self._format_list(motion.affected_files)}

### 预期收益

{self._format_list(motion.benefits)}

### 已知风险

{self._format_list(motion.risks)}

---

## 🎭 庭审过程

"""

        # 按时间顺序排列论点
        sorted_arguments = sorted(transcript.arguments, key=lambda x: x.timestamp)

        for arg in sorted_arguments:
            md += self._format_argument(arg)

        # 证据部分
        if transcript.evidence:
            md += "\n---\n\n## 📎 呈堂证供\n\n"
            for i, evidence in enumerate(transcript.evidence, 1):
                md += f"""### 证据 {i}: {evidence.title}

**类型**: {evidence.type}
**提交人**: {evidence.submitted_by}
**提交时间**: {evidence.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}

```
{evidence.content}
```

"""

        # 陪审团投票
        if transcript.jury_votes:
            md += "\n---\n\n## 🗳️ 陪审团投票\n\n"
            for vote in transcript.jury_votes:
                md += f"""### {vote.juror}

**投票**: {self._format_verdict_type(vote.vote)}
**理由**: {vote.reasoning}

"""

        # 最终判决
        if verdict:
            md += f"""---

## ⚖️ 最终判决

**判决类型**: {self._format_verdict_type(verdict.verdict_type)}
**主审法官**: {verdict.judge}
**判决时间**: {verdict.verdict_at.strftime('%Y-%m-%d %H:%M:%S')}

### 判决理由

{verdict.reasoning}

"""

            if verdict.approved_changes:
                md += f"""### ✅ 批准的变更

{self._format_list(verdict.approved_changes)}

"""

            if verdict.rejected_changes:
                md += f"""### ❌ 驳回的变更

{self._format_list(verdict.rejected_changes)}

"""

            if verdict.conditions:
                md += f"""### ⚠️ 附加条件

{self._format_list(verdict.conditions)}

"""

            if verdict.execution_plan:
                md += f"""### 📝 执行计划

{self._format_list(verdict.execution_plan)}

"""

            if verdict.precedents:
                md += f"""### 📚 引用判例

{self._format_list(verdict.precedents)}

"""

        md += """---

*本记录由书记员自动生成*
"""

        return md

    def _format_argument(self, arg: Argument) -> str:
        """格式化论点"""
        speaker_emoji = {
            "prosecutor": "👨‍⚖️",
            "defender": "👩‍⚖️",
            "judge": "⚖️"
        }

        emoji = speaker_emoji.get(arg.speaker, "💬")
        type_name = {
            ArgumentType.OPENING: "开场陈述",
            ArgumentType.REBUTTAL: "反驳",
            ArgumentType.EVIDENCE: "证据展示",
            ArgumentType.CLOSING: "结案陈词"
        }.get(arg.argument_type, "发言")

        return f"""### {emoji} {arg.speaker.upper()} - {type_name}

*{arg.timestamp.strftime('%H:%M:%S')}*

{arg.content}

"""

    def _format_list(self, items: list) -> str:
        """格式化列表"""
        if not items:
            return "（无）"
        return "\n".join(f"- {item}" for item in items)

    def _format_verdict_type(self, verdict_type) -> str:
        """格式化判决类型"""
        mapping = {
            "approved": "✅ 批准",
            "rejected": "❌ 驳回",
            "modified": "⚠️ 修改后批准",
            "deferred": "⏸️ 延期审理"
        }
        return mapping.get(verdict_type.value if hasattr(verdict_type, 'value') else verdict_type, verdict_type)
