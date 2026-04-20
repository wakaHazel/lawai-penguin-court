export type TrialStage =
  | "prepare"
  | "investigation"
  | "evidence"
  | "debate"
  | "final_statement"
  | "mediation_or_judgment"
  | "report_ready";

export type SimulationCgBackgroundId =
  | "courtroom_entry"
  | "fact_inquiry"
  | "evidence_confrontation"
  | "argument_pressure"
  | "closing_focus"
  | "judgment_moment"
  | "replay_archive";

export type SimulationCgShotType = "wide" | "medium" | "close" | "insert";

export type SimulationCgEmotion =
  | "calm"
  | "stern"
  | "pressing"
  | "reflective"
  | "steady";

export type SimulationCgCharacterId =
  | "judge_penguin"
  | "plaintiff_penguin"
  | "plaintiff_agent_penguin"
  | "defendant_penguin"
  | "defendant_agent_penguin"
  | "witness_penguin"
  | "clerk_penguin";

export type SimulationCgEffectId =
  | "gavel_flash"
  | "evidence_flash"
  | "pressure_dark"
  | "spotlight"
  | "judgment_seal"
  | "archive_glow";

export type SimulationCgTargetId =
  | "bench"
  | "claim_sheet"
  | "evidence_screen"
  | "argument_outline"
  | "closing_notes"
  | "judgment_paper"
  | "archive_scroll";

export interface SimulationCgScene {
  background_id?: SimulationCgBackgroundId;
  shot_type?: SimulationCgShotType;
  speaker_role?: SimulationSnapshot["speaker_role"];
  speaker_emotion?: SimulationCgEmotion;
  left_character_id?: SimulationCgCharacterId | null;
  right_character_id?: SimulationCgCharacterId | null;
  emphasis_target?: SimulationCgTargetId | null;
  effect_id?: SimulationCgEffectId | null;
  title?: string;
  caption?: string;
  image_url?: string | null;
  image_prompt?: string | null;
  image_model?: string | null;
}

export interface SimulationActionCard {
  choice_id?: string | null;
  action: string;
  intent: string;
  risk_tip: string;
  emphasis: string;
}

export type SimulationUserInputType =
  | "fact"
  | "evidence"
  | "cross_exam"
  | "procedure_request"
  | "argument"
  | "closing_statement"
  | "settlement_position";

export interface SimulationUserInputEntry {
  entry_id: string;
  stage: TrialStage;
  turn_index: number;
  input_type: SimulationUserInputType;
  label: string;
  content: string;
  created_at: string;
}

export interface LegalSupportReferenceItem {
  type?: string;
  title?: string;
  id?: string | null;
  summary?: string | null;
}

export interface SimulationLegalSupport {
  retrieval_mode?: string;
  recommended_queries?: string[];
  focus_issues?: string[];
  missing_evidence?: string[];
  legal_support_summary?: string;
  referenced_laws?: LegalSupportReferenceItem[];
  referenced_cases?: LegalSupportReferenceItem[];
  [key: string]: unknown;
}

export interface SimulationOpponentPayload {
  opponent_name?: string;
  opponent_role?: string;
  branch_focus?: string;
  likely_arguments?: string[];
  likely_evidence?: string[];
  likely_strategies?: string[];
  recommended_responses?: string[];
  risk_points?: string[];
  confidence?: number;
  [key: string]: unknown;
}

export interface SimulationAnalysisPayload {
  estimated_win_rate?: number;
  confidence?: number;
  positive_factors?: string[];
  negative_factors?: string[];
  evidence_gap_actions?: string[];
  recommended_next_actions?: string[];
  report_status?: string;
  report_section_keys?: string[];
  report_overview?: string;
  [key: string]: unknown;
}

export interface SimulationSnapshot {
  simulation_id: string;
  case_id: string;
  current_stage: TrialStage;
  turn_index: number;
  node_id: string;
  branch_focus: string;
  scene_title: string;
  scene_text: string;
  cg_caption: string;
  cg_scene?: SimulationCgScene | null;
  court_progress: string;
  pressure_shift: string;
  stage_objective: string;
  current_task: string;
  choice_prompt: string;
  hidden_state_summary: Record<string, string>;
  speaker_role:
    | "plaintiff"
    | "defendant"
    | "applicant"
    | "respondent"
    | "agent"
    | "witness"
    | "judge"
    | "other";
  available_actions: string[];
  action_cards: SimulationActionCard[];
  suggested_actions: string[];
  next_stage_hint: string;
  legal_support: SimulationLegalSupport;
  opponent: SimulationOpponentPayload;
  analysis: SimulationAnalysisPayload;
  degraded_flags: string[];
  user_input_entries?: SimulationUserInputEntry[];
  yuanqi_branch_name: string | null;
  workflow_hints: Array<{
    workflow_key:
      | "courtroom_scene_generation"
      | "legal_support_retrieval"
      | "opponent_behavior_simulation"
      | "outcome_analysis_report";
    workflow_version: string;
    variables: Record<string, string | number | string[]>;
  }>;
}

export interface SimulationTurnRequest {
  simulation_id: string;
  current_stage: TrialStage;
  turn_index: number;
  selected_action: string;
  selected_choice_id?: string | null;
  user_input_entries?: SimulationUserInputEntry[];
}

export interface SimulationHistoryItem {
  simulation_id: string;
  node_id: string;
  stage: TrialStage;
  turn_index: number;
  scene_title: string;
  branch_focus: string;
}

export interface SimulationCheckpoint {
  checkpoint_id: string;
  trial_run_id: string;
  source_node_id: string;
  turn_index: number;
  stage_label: string;
}
