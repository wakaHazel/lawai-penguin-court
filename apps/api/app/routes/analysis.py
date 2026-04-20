from fastapi import APIRouter, HTTPException

from ..orchestrators.trial_state_machine import TRIAL_STAGE_SEQUENCE
from ..orchestrators.workflow_catalog import get_workflow_node
from ..orchestrators.workflow_rules import summarize_hidden_state
from ..repositories.analysis_repository import (
    get_latest_opponent_snapshot,
    get_latest_win_rate_snapshot,
    save_opponent_snapshot,
    save_win_rate_snapshot,
)
from ..repositories.case_repository import get_case
from ..repositories.report_repository import get_latest_replay_report, save_replay_report
from ..repositories.simulation_repository import get_simulation
from ..repositories.trial_run_repository import (
    get_trial_run,
    list_simulation_turns_for_run,
)
from ..schemas.analysis import (
    OpponentBehaviorSnapshot,
    ReplayReportSection,
    ReplayReportSnapshot,
    SimulationContextRequest,
    WinRateAnalysisSnapshot,
    utc_now_iso,
)
from ..schemas.case import CaseProfile, EvidenceStrength, OpponentProfile
from ..schemas.common import CaseParticipantRole, ResponseEnvelope
from ..schemas.trial_workflow import TrialRunSnapshot, WorkflowChoice, WorkflowNodeDefinition
from ..schemas.turn import SimulationSnapshot, SimulationUserInputEntry, TrialStage

router = APIRouter(prefix="/api/cases", tags=["analysis"])

_STAGE_PROGRESS_WEIGHT: dict[TrialStage, int] = {
    TrialStage.PREPARE: -4,
    TrialStage.INVESTIGATION: -1,
    TrialStage.EVIDENCE: 3,
    TrialStage.DEBATE: 6,
    TrialStage.FINAL_STATEMENT: 8,
    TrialStage.MEDIATION_OR_JUDGMENT: 10,
    TrialStage.REPORT_READY: 12,
}

_STAGE_CONFIDENCE: dict[TrialStage, float] = {
    TrialStage.PREPARE: 0.38,
    TrialStage.INVESTIGATION: 0.48,
    TrialStage.EVIDENCE: 0.6,
    TrialStage.DEBATE: 0.72,
    TrialStage.FINAL_STATEMENT: 0.8,
    TrialStage.MEDIATION_OR_JUDGMENT: 0.86,
    TrialStage.REPORT_READY: 0.9,
}

_STAGE_LABELS: dict[TrialStage, str] = {
    TrialStage.PREPARE: "庭前准备",
    TrialStage.INVESTIGATION: "法庭调查",
    TrialStage.EVIDENCE: "举证质证",
    TrialStage.DEBATE: "法庭辩论",
    TrialStage.FINAL_STATEMENT: "最后陈述",
    TrialStage.MEDIATION_OR_JUDGMENT: "调解/判决",
    TrialStage.REPORT_READY: "复盘报告",
}

_STATE_SUMMARY_LABELS: dict[str, str] = {
    "evidence_strength": "证据强度",
    "procedure_control": "程序控制",
    "judge_trust": "法官信任",
    "opponent_pressure": "对方压迫感",
    "contradiction_risk": "矛盾风险",
    "surprise_exposure": "突袭暴露度",
    "settlement_tendency": "调解倾向",
}


@router.post("/{case_id}/opponent-behavior/snapshot", response_model=ResponseEnvelope)
def build_opponent_behavior_snapshot(
    case_id: str,
    request: SimulationContextRequest,
) -> ResponseEnvelope:
    case_profile, simulation, run, _history = resolve_context(
        case_id=case_id,
        simulation_id=request.simulation_id,
    )

    opponent_profile = (
        case_profile.opponent_profile
        if case_profile.opponent_profile is not None
        else OpponentProfile(
            role=CaseParticipantRole.OTHER,
            display_name="对方当事人",
        )
    )

    state_summary = summarize_hidden_state(run.state)
    likely_arguments = sanitize_text_list(opponent_profile.likely_arguments) or infer_opponent_arguments(
        case_profile
    )
    likely_evidence = sanitize_text_list(opponent_profile.likely_evidence) or infer_opponent_evidence(
        case_profile
    )
    likely_strategies = [
        *(sanitize_text_list(opponent_profile.likely_strategies) or infer_opponent_strategies(case_profile)),
        f"局面判断：对方当前压迫感为“{state_summary['opponent_pressure']}”",
        f"出手方式：突袭暴露度为“{state_summary['surprise_exposure']}”",
    ]

    data = OpponentBehaviorSnapshot(
        case_id=case_profile.case_id or case_id,
        simulation_id=simulation.simulation_id,
        current_stage=simulation.current_stage,
        opponent_name=opponent_profile.display_name,
        opponent_role=opponent_profile.role.value,
        branch_focus=simulation.branch_focus,
        likely_arguments=likely_arguments,
        likely_evidence=likely_evidence,
        likely_strategies=likely_strategies,
        recommended_responses=build_recommended_responses(case_profile, simulation, run),
        risk_points=build_risk_points(case_profile, simulation, run),
        confidence=build_confidence(simulation.current_stage, run.turn_index),
    )

    saved_snapshot = save_opponent_snapshot(data)

    return ResponseEnvelope(
        success=True,
        message="opponent_behavior_snapshot_ready",
        data=saved_snapshot.model_dump(mode="json"),
        error_code=None,
    )


@router.get("/{case_id}/opponent-behavior/latest", response_model=ResponseEnvelope)
def get_latest_opponent_behavior(case_id: str) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    snapshot = get_latest_opponent_snapshot(case_id)
    return ResponseEnvelope(
        success=True,
        message=(
            "opponent_behavior_snapshot_loaded"
            if snapshot is not None
            else "opponent_behavior_snapshot_empty"
        ),
        data=snapshot.model_dump(mode="json") if snapshot is not None else None,
        error_code=None,
    )


@router.post("/{case_id}/win-rate/analyze", response_model=ResponseEnvelope)
def build_win_rate_analysis(
    case_id: str,
    request: SimulationContextRequest,
) -> ResponseEnvelope:
    case_profile, simulation, run, _history = resolve_context(
        case_id=case_id,
        simulation_id=request.simulation_id,
    )

    strong_evidence_count = sum(
        1
        for evidence in case_profile.evidence_items
        if evidence.strength == EvidenceStrength.STRONG
    )
    medium_evidence_count = sum(
        1
        for evidence in case_profile.evidence_items
        if evidence.strength == EvidenceStrength.MEDIUM
    )
    weak_evidence_count = sum(
        1
        for evidence in case_profile.evidence_items
        if evidence.strength == EvidenceStrength.WEAK
    )

    estimated_win_rate = estimate_win_rate(
        case_profile=case_profile,
        simulation=simulation,
        run=run,
        strong_evidence_count=strong_evidence_count,
        medium_evidence_count=medium_evidence_count,
        weak_evidence_count=weak_evidence_count,
    )

    data = WinRateAnalysisSnapshot(
        case_id=case_profile.case_id or case_id,
        simulation_id=simulation.simulation_id,
        current_stage=simulation.current_stage,
        estimated_win_rate=estimated_win_rate,
        confidence=build_confidence(simulation.current_stage, run.turn_index),
        positive_factors=build_positive_factors(
            case_profile=case_profile,
            simulation=simulation,
            run=run,
            strong_evidence_count=strong_evidence_count,
            medium_evidence_count=medium_evidence_count,
        ),
        negative_factors=build_negative_factors(
            case_profile=case_profile,
            run=run,
            weak_evidence_count=weak_evidence_count,
        ),
        evidence_gap_actions=build_evidence_gap_actions(case_profile, simulation),
        recommended_next_actions=build_next_step_plan(simulation),
    )

    saved_snapshot = save_win_rate_snapshot(data)

    return ResponseEnvelope(
        success=True,
        message="win_rate_analysis_ready",
        data=saved_snapshot.model_dump(mode="json"),
        error_code=None,
    )


@router.get("/{case_id}/win-rate/latest", response_model=ResponseEnvelope)
def get_latest_win_rate(case_id: str) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    snapshot = get_latest_win_rate_snapshot(case_id)
    return ResponseEnvelope(
        success=True,
        message=(
            "win_rate_analysis_loaded"
            if snapshot is not None
            else "win_rate_analysis_empty"
        ),
        data=snapshot.model_dump(mode="json") if snapshot is not None else None,
        error_code=None,
    )


@router.post("/{case_id}/replay-report/generate", response_model=ResponseEnvelope)
def build_replay_report(
    case_id: str,
    request: SimulationContextRequest,
) -> ResponseEnvelope:
    case_profile, simulation, run, history = resolve_context(
        case_id=case_id,
        simulation_id=request.simulation_id,
    )

    stage_path = build_stage_path(history, simulation.current_stage)
    branch_decisions = build_branch_decisions(run)
    state_summary = summarize_hidden_state(run.state)
    timeline_items = build_timeline_items(history)
    evidence_risk_items = build_evidence_risk_items(case_profile, run)
    opponent_items = build_opponent_section_items(case_profile, run, simulation)
    next_step_plan = build_next_step_plan(simulation)
    result_summary = build_result_summary(case_profile, simulation, run)

    report_sections = [
        ReplayReportSection(
            key="header",
            title="报告头部",
            items=[
                case_profile.title,
                f"案件编号：{case_profile.case_id or case_id}",
                f"本轮阶段：{_STAGE_LABELS[simulation.current_stage]}",
            ],
        ),
        ReplayReportSection(
            key="main_axis",
            title="本轮主轴概览",
            items=stage_path,
        ),
        ReplayReportSection(
            key="turning_points",
            title="关键转折点",
            items=branch_decisions,
        ),
        ReplayReportSection(
            key="timeline",
            title="庭审过程回顾",
            items=timeline_items,
        ),
        ReplayReportSection(
            key="evidence_risk",
            title="证据与风险面",
            items=evidence_risk_items,
        ),
        ReplayReportSection(
            key="opponent",
            title="对方战术画像",
            items=opponent_items,
        ),
        ReplayReportSection(
            key="suggestions",
            title="下一轮建议",
            items=next_step_plan,
        ),
        ReplayReportSection(
            key="result",
            title="结果结算",
            items=result_summary,
        ),
    ]

    data = ReplayReportSnapshot(
        case_id=case_profile.case_id or case_id,
        simulation_id=simulation.simulation_id,
        report_title=f"{case_profile.title} · 庭审推演复盘报告",
        generated_at=utc_now_iso(),
        current_stage=simulation.current_stage,
        stage_path=stage_path,
        branch_decisions=branch_decisions,
        state_summary=state_summary,
        report_sections=report_sections,
        report_markdown=build_report_markdown(
            report_title=f"{case_profile.title} · 庭审推演复盘报告",
            report_sections=report_sections,
            state_summary=state_summary,
        ),
    )

    saved_report = save_replay_report(data)

    return ResponseEnvelope(
        success=True,
        message="replay_report_ready",
        data=saved_report.model_dump(mode="json"),
        error_code=None,
    )


@router.get("/{case_id}/replay-report/latest", response_model=ResponseEnvelope)
def get_latest_report(case_id: str) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    report = get_latest_replay_report(case_id)
    return ResponseEnvelope(
        success=True,
        message=(
            "replay_report_loaded"
            if report is not None
            else "replay_report_empty"
        ),
        data=report.model_dump(mode="json") if report is not None else None,
        error_code=None,
    )


def resolve_context(
    case_id: str,
    simulation_id: str,
) -> tuple[CaseProfile, SimulationSnapshot, TrialRunSnapshot, list[SimulationSnapshot]]:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    simulation = get_simulation(simulation_id)
    if simulation is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "simulation_not_found", "error_code": "simulation_not_found"},
        )

    if simulation.case_id != case_id:
        raise HTTPException(
            status_code=409,
            detail={"message": "simulation_case_mismatch", "error_code": "simulation_case_mismatch"},
        )

    run = get_trial_run(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "trial_run_not_found", "error_code": "trial_run_not_found"},
        )

    history = list_simulation_turns_for_run(simulation_id)
    if not history:
        history = [simulation]

    return case_profile, simulation, run, history


def sanitize_text_list(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item and item.strip()]


def infer_opponent_arguments(case_profile: CaseProfile) -> list[str]:
    focus_issues = sanitize_text_list(case_profile.focus_issues)
    if focus_issues:
        return [
            f"围绕“{focus_issues[0]}”提出反驳",
            "尝试削弱本方事实主线和证据闭环之间的联系",
        ]
    return ["否认关键事实成立", "质疑现有证据不足以支撑诉请"]


def infer_opponent_evidence(case_profile: CaseProfile) -> list[str]:
    if case_profile.case_type.value == "labor_dispute":
        return ["考勤管理解释材料", "合作关系或项目结算记录"]
    if case_profile.case_type.value == "divorce_dispute":
        return ["家庭支出流水", "财产归属说明材料"]
    if case_profile.case_type.value == "tort_liability":
        return ["事故经过说明", "损害结果异议材料"]
    return ["转账用途说明", "对账记录或收据说明"]


def infer_opponent_strategies(case_profile: CaseProfile) -> list[str]:
    if case_profile.case_type.value == "private_lending":
        return ["否认借贷合意", "把转账解释为其他往来"]
    return ["压缩争议范围", "把焦点转移到本方证据瑕疵"]


def build_recommended_responses(
    case_profile: CaseProfile,
    simulation: SimulationSnapshot,
    run: TrialRunSnapshot,
) -> list[str]:
    state_summary = summarize_hidden_state(run.state)
    responses = [
        f"围绕当前节点“{simulation.scene_title}”继续收束主轴，不要被支线问题带偏。",
        f"优先处理“{simulation.branch_focus}”对应的证明责任，避免法官信任从“{state_summary['judge_trust']}”继续下滑。",
    ]
    latest_user_input = get_latest_user_input(simulation)
    if latest_user_input is not None:
        responses.append(
            f"把这条{latest_user_input.label}“{latest_user_input.content}”继续压回证据、事实和法条对应关系。"
        )
    responses.extend(build_evidence_gap_actions(case_profile)[:2])
    if simulation.available_actions:
        responses.append(f"下一手优先考虑：{simulation.available_actions[0]}")
    return responses


def build_risk_points(
    case_profile: CaseProfile,
    simulation: SimulationSnapshot,
    run: TrialRunSnapshot,
) -> list[str]:
    state_summary = summarize_hidden_state(run.state)
    risk_points: list[str] = []
    if case_profile.missing_evidence:
        risk_points.extend(
            [f"证据缺口：{item}" for item in sanitize_text_list(case_profile.missing_evidence)[:2]]
        )
    risk_points.append(f"矛盾风险：{state_summary['contradiction_risk']}")
    risk_points.append(f"突袭暴露：{state_summary['surprise_exposure']}")
    latest_user_input = get_latest_user_input(simulation)
    if latest_user_input is not None:
        risk_points.append(
            f"这条{latest_user_input.label}若不能继续补强来源、时间或证明目的，容易被对方反向利用。"
        )
    if simulation.current_stage in {TrialStage.DEBATE, TrialStage.FINAL_STATEMENT}:
        risk_points.append("当前已进入结果导向阶段，如果证据链仍未闭环，说服力会明显下降。")
    return risk_points


def estimate_win_rate(
    case_profile: CaseProfile,
    simulation: SimulationSnapshot,
    run: TrialRunSnapshot,
    strong_evidence_count: int,
    medium_evidence_count: int,
    weak_evidence_count: int,
) -> int:
    evidence_score = (
        strong_evidence_count * 8
        + medium_evidence_count * 4
        - weak_evidence_count * 5
        - len(sanitize_text_list(case_profile.missing_evidence)) * 6
        + len(sanitize_text_list(case_profile.claims)) * 2
    )
    state_score = round(
        (run.state.evidence_strength - 50) * 0.28
        + (run.state.procedure_control - 50) * 0.16
        + (run.state.judge_trust - 50) * 0.22
        - (run.state.opponent_pressure - 50) * 0.12
        - (run.state.contradiction_risk - 50) * 0.18
        - (run.state.surprise_exposure - 50) * 0.16
        - max(0, run.state.settlement_tendency - 60) * 0.05
    )
    raw_score = 50 + evidence_score + _STAGE_PROGRESS_WEIGHT[simulation.current_stage] + state_score
    raw_score += get_user_input_win_rate_bonus(get_latest_user_input(simulation))
    return max(15, min(92, raw_score))


def build_positive_factors(
    case_profile: CaseProfile,
    simulation: SimulationSnapshot,
    run: TrialRunSnapshot,
    strong_evidence_count: int,
    medium_evidence_count: int,
) -> list[str]:
    state_summary = summarize_hidden_state(run.state)
    factors: list[str] = []
    if strong_evidence_count > 0:
        factors.append(f"当前已有 {strong_evidence_count} 项强证明力证据。")
    if medium_evidence_count > 0:
        factors.append(f"当前已有 {medium_evidence_count} 项中等证明力证据可继续放大。")
    latest_user_input = get_latest_user_input(simulation)
    if latest_user_input is not None:
        factors.append(f"已新增{latest_user_input.label}：{latest_user_input.content}")
    factors.append(f"法官信任度：{state_summary['judge_trust']}")
    factors.append(f"程序控制：{state_summary['procedure_control']}")
    if simulation.current_stage in {
        TrialStage.DEBATE,
        TrialStage.FINAL_STATEMENT,
        TrialStage.MEDIATION_OR_JUDGMENT,
        TrialStage.REPORT_READY,
    }:
        factors.append("本轮已经进入结果导向区间，论证焦点更容易收束。")
    if sanitize_text_list(case_profile.claims):
        factors.append("主要诉请结构已经明确，便于围绕主轴持续推进。")
    return factors


def build_negative_factors(
    case_profile: CaseProfile,
    run: TrialRunSnapshot,
    weak_evidence_count: int,
) -> list[str]:
    state_summary = summarize_hidden_state(run.state)
    factors: list[str] = []
    if case_profile.missing_evidence:
        factors.append(f"当前仍存在 {len(sanitize_text_list(case_profile.missing_evidence))} 项待补证据。")
    if weak_evidence_count > 0:
        factors.append(f"已有 {weak_evidence_count} 项证据证明力偏弱，容易被对方攻击。")
    factors.append(f"对方压迫感：{state_summary['opponent_pressure']}")
    factors.append(f"突袭暴露度：{state_summary['surprise_exposure']}")
    factors.append(f"矛盾风险：{state_summary['contradiction_risk']}")
    return factors


def build_evidence_gap_actions(
    case_profile: CaseProfile,
    simulation: SimulationSnapshot | None = None,
) -> list[str]:
    actions: list[str] = []
    latest_user_input = get_latest_user_input(simulation) if simulation is not None else None
    if latest_user_input is not None:
        actions.append(
            f"把这条{latest_user_input.label}“{latest_user_input.content}”补成完整证明链。"
        )
    missing = sanitize_text_list(case_profile.missing_evidence)
    if missing:
        actions.extend(f"优先补齐：{item}" for item in missing)
        return actions
    actions.append("继续核验现有证据的来源、时间和证明目的。")
    return actions


def build_stage_path(
    history: list[SimulationSnapshot],
    current_stage: TrialStage,
) -> list[str]:
    seen: set[TrialStage] = set()
    stage_path: list[str] = []
    for turn in history:
        if turn.current_stage not in seen:
            seen.add(turn.current_stage)
            stage_path.append(_STAGE_LABELS[turn.current_stage])

    if stage_path:
        return stage_path

    fallback: list[str] = []
    for stage in TRIAL_STAGE_SEQUENCE:
        fallback.append(_STAGE_LABELS[stage])
        if stage == current_stage:
            break
    return fallback


def build_branch_decisions(run: TrialRunSnapshot) -> list[str]:
    if not run.selected_choice_ids:
        return ["本轮尚未发生关键分叉，仍处于主轴起点。"]

    decisions: list[str] = []
    for index, choice_id in enumerate(run.selected_choice_ids):
        node_id = run.visited_node_ids[index]
        node = get_workflow_node(node_id)
        choice = find_choice(node, choice_id)
        if choice is None:
            continue
        next_node = get_workflow_node(choice.next_node_id)
        decisions.append(
            f"第 {index + 1} 次选择｜{node.title}：{choice.label} → 进入 {next_node.title}"
        )

    return decisions or ["本轮已推进，但关键选择尚未成功回放。"]


def build_timeline_items(history: list[SimulationSnapshot]) -> list[str]:
    items: list[str] = []
    seen_entry_ids: set[str] = set()
    for turn in history:
        items.append(
            f"第 {turn.turn_index} 轮｜{_STAGE_LABELS[turn.current_stage]}｜{turn.scene_title}"
        )
        sorted_entries = sorted(
            turn.user_input_entries,
            key=lambda entry: (entry.turn_index, entry.created_at, entry.entry_id),
        )
        for entry in sorted_entries:
            if entry.entry_id in seen_entry_ids:
                continue
            seen_entry_ids.add(entry.entry_id)
            items.append(f"用户输入｜{entry.label}｜{entry.content}")
    return items


def build_evidence_risk_items(
    case_profile: CaseProfile,
    run: TrialRunSnapshot,
) -> list[str]:
    state_summary = summarize_hidden_state(run.state)
    items = [
        *[
            f"现有证据｜{evidence.name}｜证明力 {describe_evidence_strength(evidence.strength)}"
            for evidence in case_profile.evidence_items[:3]
        ],
        *[f"待补证据｜{item}" for item in sanitize_text_list(case_profile.missing_evidence)[:3]],
        f"隐性风险｜矛盾风险 {state_summary['contradiction_risk']}",
        f"隐性风险｜突袭暴露 {state_summary['surprise_exposure']}",
    ]
    return items


def build_opponent_section_items(
    case_profile: CaseProfile,
    run: TrialRunSnapshot,
    simulation: SimulationSnapshot | None = None,
) -> list[str]:
    state_summary = summarize_hidden_state(run.state)
    opponent_profile = case_profile.opponent_profile
    arguments = sanitize_text_list(opponent_profile.likely_arguments) if opponent_profile else []
    evidence = sanitize_text_list(opponent_profile.likely_evidence) if opponent_profile else []
    strategies = sanitize_text_list(opponent_profile.likely_strategies) if opponent_profile else []

    items = [
        *[f"可能主张｜{item}" for item in (arguments or infer_opponent_arguments(case_profile))[:2]],
        *[f"可能证据｜{item}" for item in (evidence or infer_opponent_evidence(case_profile))[:2]],
        *[f"可能策略｜{item}" for item in (strategies or infer_opponent_strategies(case_profile))[:2]],
        f"局面体感｜对方压迫感 {state_summary['opponent_pressure']}",
        f"局面体感｜调解倾向 {state_summary['settlement_tendency']}",
    ]
    latest_user_input = get_latest_user_input(simulation) if simulation is not None else None
    if latest_user_input is not None:
        items.append(
            f"针对这条{latest_user_input.label}｜对方大概率会优先攻击“{latest_user_input.content}”的证明力。"
        )
    return items


def build_next_step_plan(simulation: SimulationSnapshot) -> list[str]:
    latest_user_input = get_latest_user_input(simulation)
    if simulation.current_stage == TrialStage.REPORT_READY:
        items = [
            "把本轮分叉和高风险节点整理进答辩提纲或演示稿。",
            "针对报告中的待补证据，准备下一轮补强方案。",
            "保留当前运行结果，供历史案件页回放和展示使用。",
        ]
        if latest_user_input is not None:
            items.insert(
                0,
                f"把这条{latest_user_input.label}“{latest_user_input.content}”写进复盘重点。",
            )
        return items
    items: list[str] = []
    if latest_user_input is not None:
        items.append(
            f"优先把这条{latest_user_input.label}“{latest_user_input.content}”接入本轮主轴。"
        )
    if simulation.available_actions:
        items.extend(f"优先动作：{action}" for action in simulation.available_actions[:3])
        return items
    items.append("当前节点没有新的动作可选，建议先回看关键节点后再继续。")
    return items


def build_result_summary(
    case_profile: CaseProfile,
    simulation: SimulationSnapshot,
    run: TrialRunSnapshot,
) -> list[str]:
    estimated_win_rate = estimate_win_rate(
        case_profile=case_profile,
        simulation=simulation,
        run=run,
        strong_evidence_count=sum(
            1 for evidence in case_profile.evidence_items if evidence.strength == EvidenceStrength.STRONG
        ),
        medium_evidence_count=sum(
            1 for evidence in case_profile.evidence_items if evidence.strength == EvidenceStrength.MEDIUM
        ),
        weak_evidence_count=sum(
            1 for evidence in case_profile.evidence_items if evidence.strength == EvidenceStrength.WEAK
        ),
    )
    state_summary = summarize_hidden_state(run.state)
    if simulation.current_stage == TrialStage.REPORT_READY:
        stage_result = "本轮推演已完成，可直接进入历史回放与演示。"
    elif simulation.current_stage == TrialStage.MEDIATION_OR_JUDGMENT:
        stage_result = "本轮已经逼近结果阶段，适合做裁判倾向与调解空间判断。"
    else:
        stage_result = "本轮仍在进行中，建议继续沿主轴推进，不要过早切换话题。"

    return [
        f"当前阶段：{_STAGE_LABELS[simulation.current_stage]}",
        f"估计胜诉率：{estimated_win_rate}%",
        f"法官信任：{state_summary['judge_trust']}",
        f"程序控制：{state_summary['procedure_control']}",
        *(
            [
                f"新增输入：{latest_user_input.label}｜{latest_user_input.content}"
            ]
            if (latest_user_input := get_latest_user_input(simulation)) is not None
            else []
        ),
        stage_result,
    ]


def build_report_markdown(
    report_title: str,
    report_sections: list[ReplayReportSection],
    state_summary: dict[str, str],
) -> str:
    lines = [f"# {report_title}", "", "## 状态摘要"]
    lines.extend(
        [
            f"- {_STATE_SUMMARY_LABELS.get(key, key)}：{value}"
            for key, value in state_summary.items()
        ]
    )
    lines.append("")

    for section in report_sections:
        lines.append(f"## {section.title}")
        if section.items:
            lines.extend([f"- {item}" for item in section.items])
        else:
            lines.append("- 暂无内容")
        lines.append("")

    return "\n".join(lines).strip()


def describe_evidence_strength(strength: EvidenceStrength) -> str:
    if strength == EvidenceStrength.STRONG:
        return "强"
    if strength == EvidenceStrength.MEDIUM:
        return "中"
    if strength == EvidenceStrength.WEAK:
        return "弱"
    return "待评估"


def get_latest_user_input(
    simulation: SimulationSnapshot | None,
) -> SimulationUserInputEntry | None:
    if simulation is None or not simulation.user_input_entries:
        return None
    return sorted(
        simulation.user_input_entries,
        key=lambda entry: (entry.turn_index, entry.created_at, entry.entry_id),
    )[-1]


def get_user_input_win_rate_bonus(
    latest_user_input: SimulationUserInputEntry | None,
) -> int:
    if latest_user_input is None:
        return 0
    if latest_user_input.input_type.value == "evidence":
        return 4
    if latest_user_input.input_type.value in {"argument", "cross_exam", "closing_statement"}:
        return 3
    return 2


def build_confidence(current_stage: TrialStage, turn_index: int) -> float:
    return min(0.95, round(_STAGE_CONFIDENCE[current_stage] + min(0.08, (turn_index - 1) * 0.02), 2))


def find_choice(node: WorkflowNodeDefinition, choice_id: str) -> WorkflowChoice | None:
    for choice in node.choices:
        if choice.choice_id == choice_id:
            return choice
    return None
