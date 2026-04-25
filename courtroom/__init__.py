"""
庭审系统 - Agent 协作框架
"""
from .court import Court, create_court
from .schemas import (
    Motion, MotionType, MotionStatus,
    Verdict, VerdictType,
    Argument, ArgumentType,
    Evidence, JuryVote,
    TrialTranscript, CourtState
)

__all__ = [
    'Court',
    'create_court',
    'Motion',
    'MotionType',
    'MotionStatus',
    'Verdict',
    'VerdictType',
    'Argument',
    'ArgumentType',
    'Evidence',
    'JuryVote',
    'TrialTranscript',
    'CourtState',
]

__version__ = '1.0.0'
