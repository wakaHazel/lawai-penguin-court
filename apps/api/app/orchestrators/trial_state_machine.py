from uuid import uuid4

from ..schemas.case import CaseProfile
from ..schemas.common import CaseParticipantRole
from ..schemas.turn import SimulationSnapshot, TrialStage

TRIAL_STAGE_SEQUENCE: list[TrialStage] = [
    TrialStage.PREPARE,
    TrialStage.INVESTIGATION,
    TrialStage.EVIDENCE,
    TrialStage.DEBATE,
    TrialStage.FINAL_STATEMENT,
    TrialStage.MEDIATION_OR_JUDGMENT,
    TrialStage.REPORT_READY,
]

_STAGE_TITLES: dict[TrialStage, str] = {
    TrialStage.PREPARE: "庭前准备",
    TrialStage.INVESTIGATION: "法庭调查",
    TrialStage.EVIDENCE: "举证质证",
    TrialStage.DEBATE: "法庭辩论",
    TrialStage.FINAL_STATEMENT: "最后陈述",
    TrialStage.MEDIATION_OR_JUDGMENT: "调解/判决",
    TrialStage.REPORT_READY: "复盘报告",
}

_PREPARE_ACTIONS = [
    "梳理请求与争议焦点",
    "补足关键证据缺口",
    "进入法庭调查",
]
_INVESTIGATION_ACTIONS = [
    "围绕事实经过发问",
    "补强请求主张证据",
    "进入举证质证",
]
_EVIDENCE_ACTIONS = [
    "围绕证据链补充说明",
    "指出对方证据漏洞",
    "进入法庭辩论",
]
_DEBATE_ACTIONS = [
    "围绕法律关系展开论证",
    "强调证据链闭环",
    "进入最后陈述",
]
_FINAL_ACTIONS = [
    "凝练核心主张",
    "回应对方主要抗辩",
    "进入调解/判决",
]
_MEDIATION_ACTIONS = [
    "评估调解方案可接受度",
    "请求法院依法裁判",
    "生成复盘报告",
]


def start_simulation(case_profile: CaseProfile) -> SimulationSnapshot:
    return SimulationSnapshot(
        simulation_id=f"sim_{uuid4().hex[:12]}",
        case_id=case_profile.case_id or "",
        current_stage=TrialStage.PREPARE,
        turn_index=1,
        branch_focus="intake_alignment",
        scene_title=_STAGE_TITLES[TrialStage.PREPARE],
        scene_text=build_prepare_scene(case_profile),
        speaker_role=CaseParticipantRole.JUDGE,
        available_actions=_PREPARE_ACTIONS,
    )


def advance_simulation(
    case_profile: CaseProfile,
    current_snapshot: SimulationSnapshot,
    selected_action: str,
) -> SimulationSnapshot:
    next_stage = get_next_stage(current_snapshot.current_stage)
    branch_focus, scene_text, available_actions = build_stage_content(
        case_profile=case_profile,
        stage=next_stage,
        selected_action=selected_action,
    )
    return SimulationSnapshot(
        simulation_id=current_snapshot.simulation_id,
        case_id=current_snapshot.case_id,
        current_stage=next_stage,
        turn_index=current_snapshot.turn_index + 1,
        branch_focus=branch_focus,
        scene_title=_STAGE_TITLES[next_stage],
        scene_text=scene_text,
        speaker_role=CaseParticipantRole.JUDGE,
        available_actions=available_actions,
    )


def get_next_stage(current_stage: TrialStage) -> TrialStage:
    current_index = TRIAL_STAGE_SEQUENCE.index(current_stage)
    if current_index >= len(TRIAL_STAGE_SEQUENCE) - 1:
        return current_stage
    return TRIAL_STAGE_SEQUENCE[current_index + 1]


def is_terminal_stage(stage: TrialStage) -> bool:
    return stage == TrialStage.REPORT_READY


def build_prepare_scene(case_profile: CaseProfile) -> str:
    claims = "；".join(normalize_text_list(case_profile.claims)[:2]) or "尚未明确诉求"
    focus_issues = "；".join(normalize_text_list(case_profile.focus_issues)[:2]) or "尚未提炼争议焦点"
    return (
        f"已就《{case_profile.title}》进入庭前准备。当前应先确认主要诉求：{claims}。"
        f"同时围绕 {focus_issues} 组织后续发问和证据准备。"
    )


def build_stage_content(
    case_profile: CaseProfile,
    stage: TrialStage,
    selected_action: str,
) -> tuple[str, str, list[str]]:
    if stage == TrialStage.INVESTIGATION:
        branch_focus = resolve_branch_focus(
            selected_action,
            {
                "梳理请求与争议焦点": "claim_focus",
                "补足关键证据缺口": "evidence_readiness",
            },
            "courtroom_investigation",
        )
        return (
            branch_focus,
            f"已进入法庭调查阶段。系统将根据刚才的动作“{selected_action}”继续展开事实核对、时间线梳理与关键问题发问。",
            _INVESTIGATION_ACTIONS,
        )

    if stage == TrialStage.EVIDENCE:
        branch_focus = resolve_branch_focus(
            selected_action,
            {
                "围绕事实经过发问": "fact_timeline",
                "补强请求主张证据": "evidence_chain",
            },
            "evidence_review",
        )
        return (
            branch_focus,
            f"已进入举证质证阶段。当前重点是围绕证据链补足证明逻辑，并结合动作“{selected_action}”判断哪些证据最能支撑诉求。",
            _EVIDENCE_ACTIONS,
        )

    if stage == TrialStage.DEBATE:
        branch_focus = resolve_branch_focus(
            selected_action,
            {
                "围绕证据链补充说明": "evidence_argumentation",
                "指出对方证据漏洞": "attack_opponent_evidence",
            },
            "legal_argumentation",
        )
        return (
            branch_focus,
            f"已进入法庭辩论阶段。当前需要把事实、证据链与法律关系串起来，并围绕动作“{selected_action}”组织论证顺序。",
            _DEBATE_ACTIONS,
        )

    if stage == TrialStage.FINAL_STATEMENT:
        branch_focus = resolve_branch_focus(
            selected_action,
            {
                "围绕法律关系展开论证": "claim_consolidation",
                "强调证据链闭环": "evidence_consolidation",
            },
            "final_response",
        )
        return (
            branch_focus,
            f"已进入最后陈述阶段。系统将把前面的调查与辩论结果压缩成结尾口径，重点回应“{selected_action}”对应的陈述方向。",
            _FINAL_ACTIONS,
        )

    if stage == TrialStage.MEDIATION_OR_JUDGMENT:
        branch_focus = resolve_branch_focus(
            selected_action,
            {
                "凝练核心主张": "judgment_request",
                "回应对方主要抗辩": "response_balance",
            },
            "mediation_balance",
        )
        return (
            branch_focus,
            f"已进入调解/判决阶段。当前要结合“{selected_action}”评估结果导向，是争取调解还是直接请求裁判。",
            _MEDIATION_ACTIONS,
        )

    if stage == TrialStage.REPORT_READY:
        branch_focus = resolve_branch_focus(
            selected_action,
            {
                "请求法院依法裁判": "judgment_review",
            },
            "hearing_replay",
        )
        return (
            branch_focus,
            f"复盘报告阶段已生成。系统会围绕“{selected_action}”沉淀关键观察、证据清单和下一步备战建议。",
            [],
        )

    return ("intake_alignment", build_prepare_scene(case_profile), _PREPARE_ACTIONS)


def resolve_branch_focus(
    selected_action: str,
    mapping: dict[str, str],
    fallback: str,
) -> str:
    return mapping.get(selected_action, fallback)


def normalize_text_list(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item and item.strip()]
