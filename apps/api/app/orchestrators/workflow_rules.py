from __future__ import annotations

from ..schemas.common import CaseType
from ..schemas.trial_workflow import HiddenStateSnapshot


BASELINE_STATE = HiddenStateSnapshot()

CASE_TYPE_MODIFIERS: dict[CaseType, dict[str, int]] = {
    CaseType.LABOR_DISPUTE: {
        "evidence_strength": -8,
        "opponent_pressure": 4,
        "contradiction_risk": 8,
        "surprise_exposure": 8,
        "settlement_tendency": 4,
    },
    CaseType.PRIVATE_LENDING: {
        "evidence_strength": 6,
        "contradiction_risk": -4,
        "surprise_exposure": 4,
        "settlement_tendency": -6,
    },
    CaseType.DIVORCE_DISPUTE: {
        "evidence_strength": -6,
        "opponent_pressure": 6,
        "contradiction_risk": 6,
        "settlement_tendency": 18,
    },
    CaseType.TORT_LIABILITY: {
        "evidence_strength": -4,
        "opponent_pressure": 2,
        "surprise_exposure": 4,
        "settlement_tendency": -2,
    },
}

EFFECT_TEMPLATES: dict[str, dict[str, int]] = {
    "procedure_objection": {
        "procedure_control": 8,
        "judge_trust": 4,
        "surprise_exposure": -8,
    },
    "direct_explanation": {
        "judge_trust": 8,
        "contradiction_risk": -8,
        "surprise_exposure": -4,
    },
    "evidence_reinforcement": {
        "evidence_strength": 12,
        "procedure_control": 4,
        "surprise_exposure": -8,
    },
    "evidence_reinforcement_strong": {
        "evidence_strength": 16,
        "procedure_control": 4,
        "surprise_exposure": -12,
        "settlement_tendency": -4,
    },
    "mainline_refocus": {
        "procedure_control": 8,
        "judge_trust": 4,
        "opponent_pressure": -4,
    },
    "controlled_concession": {
        "contradiction_risk": -12,
        "judge_trust": 4,
        "settlement_tendency": 8,
        "opponent_pressure": 4,
    },
}


def build_initial_state(case_type: CaseType) -> HiddenStateSnapshot:
    state = BASELINE_STATE.model_copy(deep=True)
    for key, delta in CASE_TYPE_MODIFIERS.get(case_type, {}).items():
        setattr(state, key, _clamp_state_value(getattr(state, key) + delta))
    return state


def apply_effect_template(
    state: HiddenStateSnapshot,
    effect_key: str,
) -> HiddenStateSnapshot:
    updated = state.model_copy(deep=True)
    for key, delta in EFFECT_TEMPLATES.get(effect_key, {}).items():
        setattr(updated, key, _clamp_state_value(getattr(updated, key) + delta))
    return updated


def summarize_hidden_state(state: HiddenStateSnapshot) -> dict[str, str]:
    return {
        "evidence_strength": _describe_level(state.evidence_strength, positive=True),
        "procedure_control": _describe_level(state.procedure_control, positive=True),
        "judge_trust": _describe_level(state.judge_trust, positive=True),
        "opponent_pressure": _describe_level(state.opponent_pressure, positive=False),
        "contradiction_risk": _describe_level(state.contradiction_risk, positive=False),
        "surprise_exposure": _describe_level(state.surprise_exposure, positive=False),
        "settlement_tendency": _describe_level(state.settlement_tendency, positive=False),
    }


def describe_pressure_shift(state: HiddenStateSnapshot) -> str:
    if state.surprise_exposure >= 70:
        return "对方这轮突袭来得很快，庭上注意力已经被它带偏，你现在不能再沿用原来的回答节奏"
    if state.opponent_pressure >= 65:
        return "对方施压很紧，任何一句泛泛回应都会被顺手放大成我方漏洞"
    if state.procedure_control >= 70:
        return "程序节奏暂时还在我方手里，只要下一句不失手，法庭会继续顺着这条主线往下走"
    if state.judge_trust >= 65:
        return "法官目前愿意顺着我方叙事继续听，但这份接受度还没有稳到可以容忍明显失误"
    if state.contradiction_risk >= 60:
        return "眼下最危险的不是声量，而是细节自撞，一旦回答不齐，矛盾会被立刻放大"
    return "庭上还在拉锯，但胜负并没有先偏向谁，谁先把主线说实，谁就更容易拿到下一轮主动"


def _describe_level(value: int, *, positive: bool) -> str:
    if positive:
        if value >= 75:
            return "明显占优"
        if value >= 55:
            return "占优"
        if value <= 25:
            return "明显承压"
        if value <= 45:
            return "承压"
        return "中性"

    if value >= 75:
        return "明显偏高"
    if value >= 55:
        return "偏高"
    if value <= 25:
        return "可控"
    if value <= 45:
        return "中低"
    return "中性"


def _clamp_state_value(value: int) -> int:
    return max(0, min(100, value))
