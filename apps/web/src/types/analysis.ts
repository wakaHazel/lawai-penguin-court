import type { TrialStage } from "./turn";

export interface OpponentBehaviorSnapshot {
  case_id: string;
  simulation_id: string;
  current_stage: TrialStage;
  opponent_name: string;
  opponent_role: string;
  branch_focus: string;
  likely_arguments: string[];
  likely_evidence: string[];
  likely_strategies: string[];
  likely_cross_examination_lines: string[];
  likely_legal_references: string[];
  likely_reasoning_paths: string[];
  surprise_attack_actions: string[];
  recommended_responses: string[];
  risk_points: string[];
  confidence: number;
}

export interface WinRateAnalysisSnapshot {
  case_id: string;
  simulation_id: string;
  current_stage: TrialStage;
  estimated_win_rate: number;
  confidence: number;
  positive_factors: string[];
  negative_factors: string[];
  evidence_gap_actions: string[];
  recommended_next_actions: string[];
  likely_opponent_lines?: string[];
  stable_response_lines?: string[];
  fallback_response_lines?: string[];
  critical_evidence_items?: string[];
  legal_reasoning_notes?: string[];
  top_loss_risks?: string[];
}

export interface ReplayReportSection {
  key: string;
  title: string;
  items: string[];
}

export interface ReplayReportSnapshot {
  case_id: string;
  simulation_id: string;
  report_title: string;
  generated_at: string;
  current_stage: TrialStage;
  stage_path: string[];
  branch_decisions: string[];
  state_summary: Record<string, string>;
  report_sections: ReplayReportSection[];
  report_markdown: string;
  report_summary?: string;
}
