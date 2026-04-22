from __future__ import annotations

import os
import time

from fastapi import APIRouter, HTTPException

from ..orchestrators.trial_workflow_engine import (
    advance_trial_run,
    map_selected_action_to_choice_id,
    resume_trial_run,
    start_trial_run,
)
from ..repositories.case_repository import get_case
from ..repositories.checkpoint_repository import (
    get_checkpoint,
    list_case_checkpoints,
    list_run_checkpoints,
    save_checkpoint,
)
from ..repositories.simulation_repository import (
    get_latest_simulation,
    get_simulation,
    save_simulation,
)
from ..repositories.trial_run_repository import (
    append_simulation_turn,
    get_trial_run,
    list_simulation_turns,
    list_simulation_turns_for_run,
    save_trial_run,
)
from ..schemas.common import ResponseEnvelope
from ..schemas.trial_workflow import TrialRunSnapshot
from ..schemas.turn import SimulationSnapshot, SimulationTurnRequest, TrialStage
from ..services.backend_orchestrator import BackendOrchestrator
from ..services.yuanqi_bridge import YuanqiBridge
from ..services.yuanqi_client import YuanqiClient, YuanqiClientError
from ..services.yuanqi_context_store import YuanqiContextStore
from ..services.yuanqi_payload_adapter import YuanqiPayloadAdapter
from ..services.yuanqi_response_merger import YuanqiResponseMerger
from ..services.gemini_image_client import GeminiImageClient, GeminiImageClientError
from ..services.static_cg_library import StaticCgLibrary
from ..services.zhipu_client import ZhipuClient, ZhipuClientError

router = APIRouter(prefix="/api/cases", tags=["simulation"])
_BACKEND_ORCHESTRATOR = BackendOrchestrator()
_YUANQI_BRIDGE = YuanqiBridge()
_YUANQI_CONTEXT_STORE = YuanqiContextStore()
_YUANQI_PAYLOAD_ADAPTER = YuanqiPayloadAdapter()
_YUANQI_RESPONSE_MERGER = YuanqiResponseMerger()
_ZHIPU_CLIENT = ZhipuClient.from_env()
_YUANQI_CLIENT = YuanqiClient.from_env()
_GEMINI_IMAGE_CLIENT = GeminiImageClient.from_env()
_STATIC_CG_LIBRARY = StaticCgLibrary.from_env()

_DEFAULT_START_ACTION = "__simulation_start__"
_DEFAULT_RESUME_ACTION = "__checkpoint_resume__"
_OPPONENT_HINT_STAGES = {
    TrialStage.DEBATE,
    TrialStage.FINAL_STATEMENT,
}
_OUTCOME_HINT_STAGES = {
    TrialStage.MEDIATION_OR_JUDGMENT,
    TrialStage.REPORT_READY,
}
_LIVE_SIMULATION_MODES = {"live", "hybrid", "remote"}
_YUANQI_FIRST_PROVIDERS = {"yuanqi", "yuanqi_only", "default"}
_YUANQI_RETRY_COOLDOWN_SECONDS = 180
_YUANQI_DISABLED_UNTIL = 0.0


@router.post("/{case_id}/simulate/start", response_model=ResponseEnvelope)
def start_case_simulation(case_id: str) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    run, snapshot = start_trial_run(case_profile)
    simulation = prepare_snapshot_for_response(
        case_profile=case_profile,
        run=run,
        snapshot=snapshot,
        selected_action=_DEFAULT_START_ACTION,
    )
    save_trial_run(run)
    append_simulation_turn(simulation)
    save_simulation(simulation)
    return ResponseEnvelope(
        success=True,
        message="simulation_started",
        data=simulation.model_dump(mode="json"),
        error_code=None,
    )


@router.get("/{case_id}/simulate/latest", response_model=ResponseEnvelope)
def get_latest_case_simulation(case_id: str) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    simulation = get_latest_simulation(case_id)
    if simulation is None:
        return ResponseEnvelope(
            success=True,
            message="simulation_not_started",
            data=None,
            error_code=None,
        )

    return ResponseEnvelope(
        success=True,
        message="simulation_loaded",
        data=simulation.model_dump(mode="json"),
        error_code=None,
    )


@router.post("/{case_id}/simulate/turn", response_model=ResponseEnvelope)
def advance_case_simulation(
    case_id: str,
    turn_request: SimulationTurnRequest,
) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    current_run = get_trial_run(turn_request.simulation_id)
    if current_run is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "simulation_not_found", "error_code": "simulation_not_found"},
        )

    current_snapshot = get_simulation(turn_request.simulation_id)
    if current_snapshot is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "simulation_not_found", "error_code": "simulation_not_found"},
        )

    if current_snapshot.case_id != case_id:
        raise HTTPException(
            status_code=409,
            detail={"message": "simulation_case_mismatch", "error_code": "simulation_case_mismatch"},
        )

    if current_snapshot.current_stage == TrialStage.REPORT_READY or not current_snapshot.available_actions:
        raise HTTPException(
            status_code=409,
            detail={"message": "simulation_already_completed", "error_code": "simulation_already_completed"},
        )

    if (
        turn_request.current_stage != current_snapshot.current_stage
        or turn_request.turn_index != current_snapshot.turn_index
    ):
        raise HTTPException(
            status_code=409,
            detail={"message": "simulation_state_conflict", "error_code": "simulation_state_conflict"},
        )

    selected_choice_id = turn_request.selected_choice_id
    if not selected_choice_id:
        if turn_request.selected_action not in current_snapshot.available_actions:
            raise HTTPException(
                status_code=422,
                detail={"message": "invalid_selected_action", "error_code": "invalid_selected_action"},
            )
        try:
            selected_choice_id = map_selected_action_to_choice_id(
                node_id=current_run.current_node_id,
                selected_action=turn_request.selected_action,
            )
        except KeyError as exc:
            raise HTTPException(
                status_code=422,
                detail={"message": "invalid_selected_action", "error_code": "invalid_selected_action"},
            ) from exc

    try:
        next_run, next_snapshot, checkpoint = advance_trial_run(
            case_profile=case_profile,
            current_run=current_run,
            selected_choice_id=selected_choice_id,
        )
    except StopIteration as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": "invalid_selected_action", "error_code": "invalid_selected_action"},
        ) from exc

    next_snapshot = next_snapshot.model_copy(
        update={
            "user_input_entries": _resolve_user_input_entries(
                current_snapshot=current_snapshot,
                turn_request=turn_request,
            )
        }
    )

    simulation = prepare_snapshot_for_response(
        case_profile=case_profile,
        run=next_run,
        snapshot=next_snapshot,
        selected_action=turn_request.selected_action,
    )
    save_trial_run(next_run)
    append_simulation_turn(simulation)
    save_simulation(simulation)
    if checkpoint is not None:
        save_checkpoint(checkpoint)

    return ResponseEnvelope(
        success=True,
        message="simulation_turn_advanced",
        data=simulation.model_dump(mode="json"),
        error_code=None,
    )


@router.get("/{case_id}/simulate/history", response_model=ResponseEnvelope)
def get_case_simulation_history(
    case_id: str,
    simulation_id: str | None = None,
) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    if simulation_id:
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
        history = list_simulation_turns_for_run(simulation_id)
    else:
        history = list_simulation_turns(case_id)

    return ResponseEnvelope(
        success=True,
        message="simulation_history_loaded",
        data=[snapshot.model_dump(mode="json") for snapshot in history],
        error_code=None,
    )


@router.get("/{case_id}/simulate/checkpoints", response_model=ResponseEnvelope)
def get_case_simulation_checkpoints(
    case_id: str,
    simulation_id: str | None = None,
) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    if simulation_id:
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
        checkpoints = list_run_checkpoints(simulation_id)
    else:
        checkpoints = list_case_checkpoints(case_id)

    return ResponseEnvelope(
        success=True,
        message="simulation_checkpoints_loaded",
        data=[checkpoint.model_dump(mode="json") for checkpoint in checkpoints],
        error_code=None,
    )


@router.post("/{case_id}/simulate/checkpoints/{checkpoint_id}/resume", response_model=ResponseEnvelope)
def resume_case_simulation_from_checkpoint(
    case_id: str,
    checkpoint_id: str,
) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "case_not_found", "error_code": "case_not_found"},
        )

    checkpoint = get_checkpoint(checkpoint_id)
    if checkpoint is None or checkpoint.case_id != case_id:
        raise HTTPException(
            status_code=404,
            detail={"message": "checkpoint_not_found", "error_code": "checkpoint_not_found"},
        )

    run, snapshot = resume_trial_run(case_profile=case_profile, checkpoint=checkpoint)
    simulation = prepare_snapshot_for_response(
        case_profile=case_profile,
        run=run,
        snapshot=snapshot,
        selected_action=_DEFAULT_RESUME_ACTION,
    )
    save_trial_run(run)
    save_simulation(simulation)
    return ResponseEnvelope(
        success=True,
        message="simulation_resumed_from_checkpoint",
        data=simulation.model_dump(mode="json"),
        error_code=None,
    )


def prepare_snapshot_for_response(
    *,
    case_profile,
    run: TrialRunSnapshot,
    snapshot: SimulationSnapshot,
    selected_action: str,
) -> SimulationSnapshot:
    historical_dialogs = _YUANQI_CONTEXT_STORE.build_historical_dialogs(snapshot.simulation_id)
    yuanqi_snapshot = snapshot
    if _is_live_simulation_enabled():
        yuanqi_snapshot = maybe_execute_yuanqi(
            case_profile=case_profile,
            snapshot=snapshot,
            selected_action=selected_action,
            historical_dialogs=historical_dialogs,
        )
    merged_snapshot = _BACKEND_ORCHESTRATOR.enrich_snapshot(
        case_profile=case_profile,
        snapshot=yuanqi_snapshot,
        run=run,
        selected_action=selected_action,
        historical_dialogs=historical_dialogs,
        preserve_existing=True,
    )
    merged_snapshot = apply_static_cg_image(
        case_profile=case_profile,
        snapshot=merged_snapshot,
    )
    merged_snapshot = maybe_render_cg_image(
        case_profile=case_profile,
        snapshot=merged_snapshot,
    )
    return attach_workflow_hints(
        case_profile=case_profile,
        snapshot=merged_snapshot,
        hint_snapshot=yuanqi_snapshot,
        selected_action=selected_action,
        historical_dialogs=historical_dialogs,
    )


def apply_static_cg_image(
    *,
    case_profile,
    snapshot: SimulationSnapshot,
) -> SimulationSnapshot:
    if snapshot.cg_scene and snapshot.cg_scene.image_url:
        return snapshot

    return _STATIC_CG_LIBRARY.apply_to_snapshot(
        case_profile=case_profile,
        snapshot=snapshot,
    )


def maybe_render_cg_image(
    *,
    case_profile,
    snapshot: SimulationSnapshot,
) -> SimulationSnapshot:
    if snapshot.cg_scene and snapshot.cg_scene.image_model == "static_cartoon_library":
        return snapshot

    if not _GEMINI_IMAGE_CLIENT.is_enabled():
        return snapshot

    if snapshot.cg_scene and snapshot.cg_scene.image_url:
        return snapshot

    try:
        return _GEMINI_IMAGE_CLIENT.render_snapshot(
            case_profile=case_profile,
            snapshot=snapshot,
        )
    except GeminiImageClientError:
        degraded_flags = list(snapshot.degraded_flags)
        if "gemini_cg_failed" not in degraded_flags:
            degraded_flags.append("gemini_cg_failed")
        return snapshot.model_copy(update={"degraded_flags": degraded_flags})


def maybe_execute_yuanqi(
    *,
    case_profile,
    snapshot: SimulationSnapshot,
    selected_action: str,
    historical_dialogs: str,
) -> SimulationSnapshot:
    invocation = _YUANQI_PAYLOAD_ADAPTER.build_master_invocation(
        case_profile=case_profile,
        snapshot=snapshot,
        selected_action=selected_action,
        historical_dialogs=historical_dialogs,
    )
    request_payload = _YUANQI_PAYLOAD_ADAPTER.to_chat_request(
        invocation=invocation,
        assistant_id=_YUANQI_CLIENT.assistant_id,
        user_id=_YUANQI_PAYLOAD_ADAPTER.build_user_id(
            case_id=snapshot.case_id,
            simulation_id=snapshot.simulation_id,
        ),
    )

    provider = _get_live_simulation_provider()

    if provider not in _YUANQI_FIRST_PROVIDERS and _ZHIPU_CLIENT.is_enabled():
        try:
            response = _ZHIPU_CLIENT.create_turn_completion(request_payload)
            return _YUANQI_RESPONSE_MERGER.merge_snapshot(
                snapshot=snapshot,
                response=response,
            )
        except (ValueError, ZhipuClientError):
            degraded_flags = list(snapshot.degraded_flags)
            if "zhipu_call_failed" not in degraded_flags:
                degraded_flags.append("zhipu_call_failed")
            snapshot = snapshot.model_copy(update={"degraded_flags": degraded_flags})

    if _is_yuanqi_temporarily_disabled():
        return snapshot

    if not _YUANQI_CLIENT.is_enabled():
        return snapshot

    try:
        response = _YUANQI_CLIENT.create_turn_completion(request_payload)
        _clear_yuanqi_temporary_disable()
        return _YUANQI_RESPONSE_MERGER.merge_snapshot(
            snapshot=snapshot,
            response=response,
        )
    except (ValueError, YuanqiClientError):
        _mark_yuanqi_temporarily_disabled()
        degraded_flags = list(snapshot.degraded_flags)
        if "yuanqi_call_failed" not in degraded_flags:
            degraded_flags.append("yuanqi_call_failed")
        return snapshot.model_copy(update={"degraded_flags": degraded_flags})


def _is_live_simulation_enabled() -> bool:
    mode = os.getenv("PENGUIN_SIMULATION_MODE", "local").strip().lower()
    return mode in _LIVE_SIMULATION_MODES


def _get_live_simulation_provider() -> str:
    provider = os.getenv("PENGUIN_LIVE_PROVIDER", "yuanqi").strip().lower()
    if not provider:
        return "yuanqi"
    return provider


def _get_yuanqi_retry_cooldown_seconds() -> int:
    raw_value = os.getenv(
        "YUANQI_RETRY_COOLDOWN_SECONDS",
        str(_YUANQI_RETRY_COOLDOWN_SECONDS),
    ).strip()
    try:
        return max(0, int(raw_value))
    except ValueError:
        return _YUANQI_RETRY_COOLDOWN_SECONDS


def _is_yuanqi_temporarily_disabled() -> bool:
    return time.time() < _YUANQI_DISABLED_UNTIL


def _mark_yuanqi_temporarily_disabled() -> None:
    global _YUANQI_DISABLED_UNTIL
    _YUANQI_DISABLED_UNTIL = time.time() + _get_yuanqi_retry_cooldown_seconds()


def _clear_yuanqi_temporary_disable() -> None:
    global _YUANQI_DISABLED_UNTIL
    _YUANQI_DISABLED_UNTIL = 0.0


def _resolve_user_input_entries(
    *,
    current_snapshot: SimulationSnapshot,
    turn_request: SimulationTurnRequest,
):
    if turn_request.user_input_entries:
        return list(turn_request.user_input_entries)
    return list(current_snapshot.user_input_entries)


def attach_workflow_hints(
    *,
    case_profile,
    snapshot: SimulationSnapshot,
    hint_snapshot: SimulationSnapshot,
    selected_action: str,
    historical_dialogs: str,
) -> SimulationSnapshot:
    workflow_hints = [
        _YUANQI_BRIDGE.build_scene_generation_invocation(
            case_profile=case_profile,
            current_stage=snapshot.current_stage,
            turn_index=snapshot.turn_index,
            historical_dialogs=historical_dialogs,
        ),
        _YUANQI_BRIDGE.build_legal_retrieval_invocation(case_profile),
    ]

    if snapshot.current_stage in _OPPONENT_HINT_STAGES:
        workflow_hints.append(
            _YUANQI_BRIDGE.build_opponent_behavior_invocation(
                case_profile=case_profile,
                current_stage=snapshot.current_stage,
                selected_action=selected_action,
            )
        )

    if snapshot.current_stage in _OUTCOME_HINT_STAGES:
        workflow_hints.append(
            _YUANQI_BRIDGE.build_outcome_analysis_invocation(
                case_profile=case_profile,
                legal_support_summary=str(
                    hint_snapshot.legal_support.get("legal_support_summary") or ""
                ),
                simulation_timeline=_YUANQI_CONTEXT_STORE.build_simulation_timeline(
                    snapshot.simulation_id
                ),
                opponent_behavior=hint_snapshot.opponent,
            )
        )

    return snapshot.model_copy(update={"workflow_hints": workflow_hints})
