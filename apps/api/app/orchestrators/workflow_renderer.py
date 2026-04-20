from __future__ import annotations

from ..schemas.case import CaseProfile
from ..schemas.trial_workflow import HiddenStateSnapshot, WorkflowNodeDefinition
from .workflow_rules import describe_pressure_shift, summarize_hidden_state


def render_workflow_scene(
    case_profile: CaseProfile,
    node: WorkflowNodeDefinition,
    state: HiddenStateSnapshot,
) -> dict[str, str | dict[str, str]]:
    focus_text = _build_focus_text(case_profile)
    cg_caption = (
        f"【CG画面：{_build_case_subject(case_profile)}推进到“{node.title}”，"
        f"法庭灯光压低一层，所有目光都收束到{focus_text}。】"
    )
    court_progress = _build_court_progress(node, focus_text)
    hearing_dynamic = _build_hearing_dynamic(case_profile, node, state, focus_text)
    pressure_shift = _build_pressure_shift(state)
    choice_prompt = "【请选择本轮回应策略】"
    cg_scene = _build_cg_scene(case_profile, node, state)
    action_cards = [
        {
            "choice_id": choice.choice_id,
            "action": choice.label,
            "intent": choice.intent,
            "risk_tip": choice.risk_tip,
            "emphasis": choice.emphasis,
        }
        for choice in node.choices
    ]
    scene_text = "\n\n".join(
        [cg_caption, court_progress, hearing_dynamic, pressure_shift, choice_prompt]
    )

    return {
        "cg_caption": cg_caption,
        "cg_scene": cg_scene,
        "court_progress": court_progress,
        "pressure_shift": pressure_shift,
        "stage_objective": node.stage_objective,
        "current_task": node.current_task,
        "choice_prompt": choice_prompt,
        "action_cards": action_cards,
        "scene_text": scene_text,
        "hidden_state_summary": summarize_hidden_state(state),
    }


def _build_case_subject(case_profile: CaseProfile) -> str:
    return case_profile.title or "当前案件"


def _build_court_progress(node: WorkflowNodeDefinition, focus_text: str) -> str:
    stage_label = _stage_label(node.stage.value)
    return (
        f"【法庭进程：现在进入{stage_label}。"
        f"{_build_stage_progress_line(node.stage.value, node.title, focus_text)}】"
    )


def _build_stage_progress_line(stage: str, title: str, focus_text: str) -> str:
    return {
        "prepare": (
            f"法官先把庭审推进到“{title}”，"
            f"庭上正在确认这场庭审将如何围绕{focus_text}展开。"
        ),
        "investigation": f"法官把询问推进到“{title}”，要求双方把与{focus_text}有关的事实说清。",
        "evidence": f"双方已经进入证据攻防，庭上开始逐项检验哪些材料真的能撑住{focus_text}。",
        "debate": f"辩论压力明显上来，双方都在试图用最短的话抢占对{focus_text}的定义权。",
        "final_statement": f"法庭准备收束争议，留给你的时间只够把{focus_text}压缩成最后一击。",
        "mediation_or_judgment": f"法官开始观察案件收束方式，庭上正在判断{focus_text}会走向调解还是直接结果。",
        "report_ready": f"本轮推演已经落定，现在可以回看整条围绕{focus_text}展开的庭审路径。",
    }.get(stage, f"庭审正在围绕{focus_text}继续推进。")


def _build_pressure_shift(state: HiddenStateSnapshot) -> str:
    return f"【局势变化：{describe_pressure_shift(state)}。】"


def _build_hearing_dynamic(
    case_profile: CaseProfile,
    node: WorkflowNodeDefinition,
    state: HiddenStateSnapshot,
    focus_text: str,
) -> str:
    stage = node.stage.value
    claim_text = _first_text(case_profile.claims, "我方当前诉请")
    missing_text = _first_text(case_profile.missing_evidence, "关键证据缺口")
    opponent_argument = _top_opponent_argument(case_profile)
    opponent_evidence = _top_opponent_evidence(case_profile)

    if stage == "prepare":
        if "否认范围" in node.title or "边界" in node.title:
            text = (
                "程序性开场已经结束，审判席现在更想听清本案到底围绕哪些事实和法律关系发生争议。"
                f" 你如果先把“{claim_text}”和“{focus_text}”的位置说准，后续调查会更集中；"
                "但只要边界一说松，对方就会马上把案件往更有利于它的解释方向带。"
            )
        else:
            text = (
                "书记员核对到庭情况后，法官没有给双方太多铺垫空间，"
                f"而是直接把争点框定、举证期限和“{focus_text}”的入口摆到台面上。"
                " 对方现在更像是在观察你会先抢程序位置，还是先暴露实体主线。"
            )
    elif stage == "investigation":
        text = (
            f"法庭问答已经推进到“{node.title}”，法官正在判断“{claim_text}”究竟该从哪组事实切入。"
            f" 你如果能把“{focus_text}”和具体事实节点对应起来，下一轮追问会沿着你的主线展开；"
            f"一旦在“{missing_text}”附近说虚，对方就会立刻接手解释权。"
        )
    elif stage == "evidence":
        text = (
            "证据被一份份推到审判席前，纸页翻动和插话质证把法庭气压一点点压低。"
            f" 这一轮不只是看谁材料更多，而是看谁能把材料真正压到“{focus_text}”上。"
            f" 对方现在最可能借“{opponent_evidence}”或“{opponent_argument}”来拆我方证明链。"
        )
        if state.surprise_exposure >= 60:
            text += " 对方刚抛出的新细节还挂在庭上，你此刻任何一句回应都不能再给它反咬空间。"
        elif state.evidence_strength >= 65:
            text += " 只要你把证明关系接稳，这一段的主动权还有机会重新回到我方手里。"
    elif stage == "debate":
        text = (
            f"进入辩论之后，双方已经不再重复铺陈事实，而是在争谁有资格替“{focus_text}”下最后的定义。"
            f" 对方此刻最可能把重心压在“{opponent_argument}”上，试图迫使你跟着它的问法走。"
            " 庭上的耐心正在下降，空话会比前面任何时候都更快暴露。"
        )
        if state.opponent_pressure >= 60:
            text += " 对方这时的攻击点已经很集中，稍微答散一点，就会被他顺势切开。"
        elif state.judge_trust >= 60:
            text += " 法官目前还愿意顺着你的论证往下听，但这份信任只要撞到细节硬伤就会往下掉。"
    elif stage == "final_statement":
        text = (
            "庭审已经接近收束，审判席不会再给长篇展开的空间。"
            f" 真正能留下来的，只会是你最终替“{focus_text}”钉下去的那一句结论，以及支撑它的最短理由。"
        )
    elif stage == "mediation_or_judgment":
        text = (
            "法官的语气已经从追问转向判断，桌面上的每一次停顿都像是在试探双方还能不能接受结果收束。"
            f" 此时你无论是继续守“{claim_text}”，还是释放调解窗口，都会直接影响最后出口的形状。"
        )
    else:
        text = (
            "庭上发言已经结束，留在桌面上的不再是声音，"
            "而是刚才每一步选择留下来的路径、代价和可回看的转折点。"
        )

    return f"【庭上动态：{text}】"


def _build_focus_text(case_profile: CaseProfile) -> str:
    if case_profile.focus_issues:
        return "、".join(case_profile.focus_issues[:2])
    if case_profile.claims:
        return "、".join(case_profile.claims[:2])
    return "核心诉请"


def _first_text(items: list[str], fallback: str) -> str:
    for item in items:
        normalized = item.strip()
        if normalized:
            return normalized
    return fallback


def _top_opponent_argument(case_profile: CaseProfile) -> str:
    if case_profile.opponent_profile is not None:
        return _first_text(
            case_profile.opponent_profile.likely_arguments,
            "对我方关键事实提出替代解释",
        )
    return "对我方关键事实提出替代解释"


def _top_opponent_evidence(case_profile: CaseProfile) -> str:
    if case_profile.opponent_profile is not None:
        return _first_text(
            case_profile.opponent_profile.likely_evidence,
            "一份会削弱我方叙事的临时材料",
        )
    return "一份会削弱我方叙事的临时材料"


def _stage_label(stage: str) -> str:
    return {
        "prepare": "开庭准备",
        "investigation": "法庭调查",
        "evidence": "举证质证",
        "debate": "法庭辩论",
        "final_statement": "最后陈述",
        "mediation_or_judgment": "调解/判决",
        "report_ready": "复盘报告",
    }.get(stage, stage)


def _build_cg_scene(
    case_profile: CaseProfile,
    node: WorkflowNodeDefinition,
    state: HiddenStateSnapshot,
) -> dict[str, str]:
    stage = node.stage.value
    speaker_role = node.speaker_role.value
    focus_text = _build_focus_text(case_profile)

    return {
        "background_id": _pick_background_id(stage),
        "shot_type": _pick_shot_type(stage),
        "speaker_role": speaker_role,
        "speaker_emotion": _pick_speaker_emotion(stage, state),
        "left_character_id": _pick_left_character_id(speaker_role),
        "right_character_id": _pick_right_character_id(speaker_role),
        "emphasis_target": _pick_emphasis_target(stage),
        "effect_id": _pick_effect_id(stage, state),
        "title": node.title,
        "caption": f"{_build_case_subject(case_profile)}推进到“{node.title}”，镜头正聚焦于{focus_text}。",
    }


def _pick_background_id(stage: str) -> str:
    return {
        "prepare": "courtroom_entry",
        "investigation": "fact_inquiry",
        "evidence": "evidence_confrontation",
        "debate": "argument_pressure",
        "final_statement": "closing_focus",
        "mediation_or_judgment": "judgment_moment",
        "report_ready": "replay_archive",
    }.get(stage, "courtroom_entry")


def _pick_shot_type(stage: str) -> str:
    return {
        "prepare": "wide",
        "investigation": "medium",
        "evidence": "close",
        "debate": "medium",
        "final_statement": "close",
        "mediation_or_judgment": "wide",
        "report_ready": "insert",
    }.get(stage, "medium")


def _pick_speaker_emotion(stage: str, state: HiddenStateSnapshot) -> str:
    if stage in {"evidence", "debate"} and (
        state.opponent_pressure >= 55 or state.surprise_exposure >= 45
    ):
        return "pressing"
    if stage in {"prepare", "mediation_or_judgment"}:
        return "stern"
    if stage == "final_statement":
        return "reflective"
    if state.judge_trust >= 65:
        return "steady"
    return "calm"


def _pick_left_character_id(speaker_role: str) -> str:
    return {
        "judge": "judge_penguin",
        "plaintiff": "plaintiff_penguin",
        "applicant": "plaintiff_penguin",
        "agent": "plaintiff_agent_penguin",
        "defendant": "defendant_penguin",
        "respondent": "defendant_penguin",
        "witness": "witness_penguin",
        "other": "clerk_penguin",
    }.get(speaker_role, "judge_penguin")


def _pick_right_character_id(speaker_role: str) -> str:
    return {
        "judge": "defendant_agent_penguin",
        "plaintiff": "judge_penguin",
        "applicant": "judge_penguin",
        "agent": "judge_penguin",
        "defendant": "judge_penguin",
        "respondent": "judge_penguin",
        "witness": "judge_penguin",
        "other": "plaintiff_agent_penguin",
    }.get(speaker_role, "judge_penguin")


def _pick_emphasis_target(stage: str) -> str:
    return {
        "prepare": "bench",
        "investigation": "claim_sheet",
        "evidence": "evidence_screen",
        "debate": "argument_outline",
        "final_statement": "closing_notes",
        "mediation_or_judgment": "judgment_paper",
        "report_ready": "archive_scroll",
    }.get(stage, "bench")


def _pick_effect_id(stage: str, state: HiddenStateSnapshot) -> str:
    if stage == "prepare":
        return "gavel_flash"
    if stage == "evidence":
        return "evidence_flash"
    if stage == "debate":
        return "pressure_dark" if state.opponent_pressure >= 55 else "spotlight"
    if stage == "mediation_or_judgment":
        return "judgment_seal"
    if stage == "report_ready":
        return "archive_glow"
    return "spotlight"
