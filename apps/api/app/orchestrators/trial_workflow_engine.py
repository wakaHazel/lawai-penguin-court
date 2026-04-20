from __future__ import annotations

from uuid import uuid4

from ..schemas.case import CaseProfile
from ..schemas.trial_workflow import (
    RunCheckpointSnapshot,
    TrialRunSnapshot,
    WorkflowChoice,
    WorkflowNodeDefinition,
)
from ..schemas.turn import SimulationSnapshot
from .workflow_catalog import get_civil_trial_workflow, get_workflow_node
from .workflow_renderer import render_workflow_scene
from .workflow_rules import apply_effect_template, build_initial_state


def start_trial_run(case_profile: CaseProfile) -> tuple[TrialRunSnapshot, SimulationSnapshot]:
    workflow = get_civil_trial_workflow()
    opening_node = workflow.nodes[0]
    state = build_initial_state(case_profile.case_type)
    simulation_id = f"sim_{uuid4().hex[:12]}"
    run = TrialRunSnapshot(
        trial_run_id=simulation_id,
        case_id=case_profile.case_id or "",
        current_node_id=opening_node.node_id,
        current_stage=opening_node.stage,
        turn_index=1,
        state=state,
        visited_node_ids=[opening_node.node_id],
        selected_choice_ids=[],
    )
    snapshot = _build_snapshot(
        case_profile=case_profile,
        simulation_id=simulation_id,
        node=opening_node,
        turn_index=1,
        state=state,
    )
    return run, snapshot


def advance_trial_run(
    case_profile: CaseProfile,
    current_run: TrialRunSnapshot,
    selected_choice_id: str,
) -> tuple[TrialRunSnapshot, SimulationSnapshot, RunCheckpointSnapshot | None]:
    current_node = get_workflow_node(current_run.current_node_id)
    choice = resolve_choice(current_node, selected_choice_id)
    next_node = get_workflow_node(choice.next_node_id)
    next_state = apply_effect_template(current_run.state, choice.effect_key)
    next_turn_index = current_run.turn_index + 1

    updated_run = current_run.model_copy(
        update={
            "current_node_id": next_node.node_id,
            "current_stage": next_node.stage,
            "turn_index": next_turn_index,
            "state": next_state,
            "visited_node_ids": [*current_run.visited_node_ids, next_node.node_id],
            "selected_choice_ids": [*current_run.selected_choice_ids, choice.choice_id],
        }
    )
    snapshot = _build_snapshot(
        case_profile=case_profile,
        simulation_id=current_run.trial_run_id,
        node=next_node,
        turn_index=next_turn_index,
        state=next_state,
    )
    checkpoint = (
        build_checkpoint(updated_run)
        if next_node.checkpoint_enabled
        else None
    )
    return updated_run, snapshot, checkpoint


def resume_trial_run(
    case_profile: CaseProfile,
    checkpoint: RunCheckpointSnapshot,
) -> tuple[TrialRunSnapshot, SimulationSnapshot]:
    run = TrialRunSnapshot.model_validate_json(checkpoint.payload_json)
    node = get_workflow_node(run.current_node_id)
    snapshot = _build_snapshot(
        case_profile=case_profile,
        simulation_id=run.trial_run_id,
        node=node,
        turn_index=run.turn_index,
        state=run.state,
    )
    return run, snapshot


def resolve_choice(
    node: WorkflowNodeDefinition,
    choice_id: str,
) -> WorkflowChoice:
    return next(choice for choice in node.choices if choice.choice_id == choice_id)


def map_selected_action_to_choice_id(
    node_id: str,
    selected_action: str,
) -> str:
    node = get_workflow_node(node_id)
    for choice in node.choices:
        if choice.label == selected_action:
            return choice.choice_id
    raise KeyError(selected_action)


def build_checkpoint(run: TrialRunSnapshot) -> RunCheckpointSnapshot:
    return RunCheckpointSnapshot(
        checkpoint_id=f"{run.trial_run_id}:cp:{run.current_node_id}:{run.turn_index}",
        case_id=run.case_id,
        trial_run_id=run.trial_run_id,
        source_node_id=run.current_node_id,
        turn_index=run.turn_index,
        payload_json=run.model_dump_json(),
    )


def _build_snapshot(
    case_profile: CaseProfile,
    simulation_id: str,
    node: WorkflowNodeDefinition,
    turn_index: int,
    state,
) -> SimulationSnapshot:
    rendered = render_workflow_scene(case_profile=case_profile, node=node, state=state)
    return SimulationSnapshot(
        simulation_id=simulation_id,
        case_id=case_profile.case_id or "",
        current_stage=node.stage,
        turn_index=turn_index,
        node_id=node.node_id,
        branch_focus=node.focus_key,
        scene_title=node.title,
        scene_text=rendered["scene_text"],
        cg_caption=rendered["cg_caption"],
        court_progress=rendered["court_progress"],
        pressure_shift=rendered["pressure_shift"],
        stage_objective=rendered["stage_objective"],
        current_task=rendered["current_task"],
        choice_prompt=rendered["choice_prompt"],
        hidden_state_summary=rendered["hidden_state_summary"],
        speaker_role=node.speaker_role,
        available_actions=[choice.label for choice in node.choices],
        action_cards=rendered["action_cards"],
        workflow_hints=[],
    )
