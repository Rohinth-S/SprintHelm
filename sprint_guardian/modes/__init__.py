"""
CodinzHub Sprint Guardian 9 Specialized Operational Modes.
"""

from sprint_guardian.modes.base import BaseMode
from sprint_guardian.modes.shape_sprint import ShapeSprintMode
from sprint_guardian.modes.triage_queue import TriageQueueMode
from sprint_guardian.modes.suggest_owner import SuggestOwnerMode
from sprint_guardian.modes.balance_load import BalanceLoadMode
from sprint_guardian.modes.inspect_sprint import InspectSprintMode
from sprint_guardian.modes.surface_risk import SurfaceRiskMode
from sprint_guardian.modes.progress_pulse import ProgressPulseMode
from sprint_guardian.modes.standup_brief import StandupBriefMode
from sprint_guardian.modes.retro_notes import RetroNotesMode

MODE_REGISTRY = {
    "shape-sprint": ShapeSprintMode,
    "triage-queue": TriageQueueMode,
    "suggest-owner": SuggestOwnerMode,
    "balance-load": BalanceLoadMode,
    "inspect-sprint": InspectSprintMode,
    "surface-risk": SurfaceRiskMode,
    "progress-pulse": ProgressPulseMode,
    "standup-brief": StandupBriefMode,
    "retro-notes": RetroNotesMode,
}

__all__ = [
    "BaseMode",
    "ShapeSprintMode",
    "TriageQueueMode",
    "SuggestOwnerMode",
    "BalanceLoadMode",
    "InspectSprintMode",
    "SurfaceRiskMode",
    "ProgressPulseMode",
    "StandupBriefMode",
    "RetroNotesMode",
    "MODE_REGISTRY",
]
