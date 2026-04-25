"""
庭审系统数据结构定义
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MotionType(str, Enum):
    """动议类型"""
    NEW_FEATURE = "new_feature"
    REFACTOR = "refactor"
    BUG_FIX = "bug_fix"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"


class MotionStatus(str, Enum):
    """动议状态"""
    FILED = "filed"              # 已立案
    DISCOVERY = "discovery"      # 证据交换中
    TRIAL = "trial"              # 庭审中
    DELIBERATION = "deliberation"  # 评议中
    VERDICT = "verdict"          # 已判决


class VerdictType(str, Enum):
    """判决类型"""
    APPROVED = "approved"        # 批准
    REJECTED = "rejected"        # 驳回
    MODIFIED = "modified"        # 修改后批准
    APPROVED_WITH_MODIFICATIONS = "approved_with_modifications"  # 有条件批准
    DEFERRED = "deferred"        # 延期审理


class ArgumentType(str, Enum):
    """论点类型"""
    OPENING = "opening"          # 开场陈述
    REBUTTAL = "rebuttal"        # 反驳
    EVIDENCE = "evidence"        # 证据展示
    CLOSING = "closing"          # 结案陈词


class Motion(BaseModel):
    """动议（案件）"""
    case_id: str = Field(..., description="案件编号")
    title: str = Field(..., description="动议标题")
    motion_type: MotionType = Field(..., description="动议类型")
    description: str = Field(..., description="详细描述")
    proposer: str = Field(default="prosecutor", description="提案人")
    filed_at: datetime = Field(default_factory=datetime.now, description="立案时间")
    status: MotionStatus = Field(default=MotionStatus.FILED, description="当前状态")

    # 提案内容
    proposed_changes: List[str] = Field(default_factory=list, description="提议的变更")
    affected_files: List[str] = Field(default_factory=list, description="影响的文件")
    risks: List[str] = Field(default_factory=list, description="已知风险")
    benefits: List[str] = Field(default_factory=list, description="预期收益")

    # 元数据
    priority: int = Field(default=5, ge=1, le=10, description="优先级 1-10")
    estimated_effort: str = Field(default="medium", description="预估工作量")
    tags: List[str] = Field(default_factory=list, description="标签")

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "case_001",
                "title": "增加自动重试机制",
                "motion_type": "new_feature",
                "description": "为 API 调用添加指数退避重试，提高系统稳定性",
                "proposed_changes": [
                    "在 api/client.ts 中添加 RetryPolicy 类",
                    "为所有 HTTP 请求包装重试逻辑"
                ],
                "affected_files": ["frontend/src/api/client.ts"],
                "risks": ["可能增加请求延迟", "需要处理幂等性"],
                "benefits": ["提高弱网环境下的可用性", "减少用户报错"]
            }
        }


class Argument(BaseModel):
    """论点"""
    speaker: str = Field(..., description="发言人角色")
    argument_type: ArgumentType = Field(..., description="论点类型")
    content: str = Field(..., description="论点内容")
    evidence_refs: List[str] = Field(default_factory=list, description="引用的证据")
    timestamp: datetime = Field(default_factory=datetime.now, description="发言时间")

    class Config:
        json_schema_extra = {
            "example": {
                "speaker": "prosecutor",
                "argument_type": "opening",
                "content": "如果不加重试机制，整个系统在弱网环境下会频繁崩溃！",
                "evidence_refs": ["error_logs_2024.txt"]
            }
        }


class Evidence(BaseModel):
    """证据"""
    evidence_id: str = Field(..., description="证据编号")
    title: str = Field(..., description="证据标题")
    type: str = Field(..., description="证据类型：code/log/test/benchmark")
    content: str = Field(..., description="证据内容")
    submitted_by: str = Field(..., description="提交人")
    submitted_at: datetime = Field(default_factory=datetime.now, description="提交时间")

    class Config:
        json_schema_extra = {
            "example": {
                "evidence_id": "evidence_001",
                "title": "错误日志统计",
                "type": "log",
                "content": "过去一周网络错误 247 次，其中 89% 是暂时性故障",
                "submitted_by": "prosecutor"
            }
        }


class JuryVote(BaseModel):
    """陪审团投票"""
    juror: str = Field(..., description="陪审员名称")
    vote: VerdictType = Field(..., description="投票意见")
    reasoning: str = Field(..., description="投票理由")
    timestamp: datetime = Field(default_factory=datetime.now, description="投票时间")


class FunctionDesign(BaseModel):
    """函数设计"""
    file: str = Field(..., description="文件路径")
    function_name: str = Field(..., description="函数名")
    signature: str = Field(..., description="完整的函数签名")
    purpose: str = Field(..., description="函数职责")
    key_logic: str = Field(..., description="关键逻辑描述或伪代码")
    variables: List[str] = Field(default_factory=list, description="需要的变量")


class ArchitectureDesign(BaseModel):
    """架构设计"""
    new_classes: List[str] = Field(default_factory=list, description="新增的类及职责")
    modified_classes: List[str] = Field(default_factory=list, description="修改的类及内容")
    class_relationships: str = Field(default="", description="类之间的关系和依赖")
    data_flow: str = Field(default="", description="数据流向说明")


class Verdict(BaseModel):
    """判决书"""
    case_id: str = Field(..., description="案件编号")
    verdict_type: VerdictType = Field(..., description="判决类型")
    reasoning: str = Field(..., description="判决理由")

    # 判决内容
    approved_changes: List[str] = Field(default_factory=list, description="批准的变更")
    rejected_changes: List[str] = Field(default_factory=list, description="驳回的变更")
    conditions: List[str] = Field(default_factory=list, description="附加条件")

    # 技术设计（新增）
    architecture_design: Optional[ArchitectureDesign] = Field(None, description="架构设计")
    function_design: List[FunctionDesign] = Field(default_factory=list, description="函数级别设计")

    # 执行指令
    execution_plan: List[str] = Field(default_factory=list, description="执行计划")
    assigned_to: Optional[str] = Field(None, description="指派执行人")

    # 判例引用
    precedents: List[str] = Field(default_factory=list, description="引用的先例")

    # 元数据
    judge: str = Field(default="judge", description="主审法官")
    verdict_at: datetime = Field(default_factory=datetime.now, description="判决时间")

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "case_001",
                "verdict_type": "modified",
                "reasoning": "重试机制有必要，但需要限制重试次数和添加幂等性检查",
                "approved_changes": [
                    "添加 RetryPolicy 类，最多重试 3 次",
                    "使用指数退避策略"
                ],
                "conditions": [
                    "必须为所有 POST/PUT 请求添加幂等性 token",
                    "需要添加单元测试覆盖重试逻辑"
                ],
                "execution_plan": [
                    "1. 实现 RetryPolicy 类",
                    "2. 添加幂等性支持",
                    "3. 编写测试用例",
                    "4. 集成到现有 API 客户端"
                ]
            }
        }


class TrialTranscript(BaseModel):
    """庭审记录"""
    case_id: str = Field(..., description="案件编号")
    motion: Motion = Field(..., description="动议内容")
    arguments: List[Argument] = Field(default_factory=list, description="所有论点")
    evidence: List[Evidence] = Field(default_factory=list, description="所有证据")
    jury_votes: List[JuryVote] = Field(default_factory=list, description="陪审团投票")
    verdict: Optional[Verdict] = Field(None, description="最终判决")

    started_at: datetime = Field(default_factory=datetime.now, description="开庭时间")
    ended_at: Optional[datetime] = Field(None, description="闭庭时间")

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "case_001",
                "motion": {"case_id": "case_001", "title": "增加自动重试机制"},
                "arguments": [],
                "evidence": [],
                "jury_votes": []
            }
        }


class CourtState(BaseModel):
    """法庭状态（共享状态）"""
    active_cases: List[str] = Field(default_factory=list, description="活跃案件")
    completed_cases: List[str] = Field(default_factory=list, description="已结案件")
    case_law: Dict[str, Any] = Field(default_factory=dict, description="判例法库")
    statistics: Dict[str, int] = Field(default_factory=dict, description="统计数据")

    class Config:
        json_schema_extra = {
            "example": {
                "active_cases": ["case_001", "case_002"],
                "completed_cases": [],
                "case_law": {},
                "statistics": {
                    "total_cases": 2,
                    "approved": 0,
                    "rejected": 0
                }
            }
        }
