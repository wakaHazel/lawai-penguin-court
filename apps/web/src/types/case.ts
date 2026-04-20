export type CaseDomain = "civil" | "criminal" | "administrative";

export type CaseType =
  | "private_lending"
  | "labor_dispute"
  | "divorce_dispute"
  | "tort_liability";

export type CaseParticipantRole =
  | "plaintiff"
  | "defendant"
  | "applicant"
  | "respondent"
  | "agent"
  | "witness"
  | "judge"
  | "other";

export type UserPerspectiveRole =
  | "claimant_side"
  | "respondent_side"
  | "neutral_observer"
  | "learner"
  | "other";

export type UserGoal =
  | "simulate_trial"
  | "analyze_win_rate"
  | "prepare_checklist"
  | "review_evidence";

export type EvidenceType =
  | "contract"
  | "transfer_record"
  | "chat_record"
  | "document"
  | "audio_video"
  | "medical_record"
  | "witness_statement"
  | "other";

export type EvidenceStrength = "strong" | "medium" | "weak" | "unassessed";

export const CASE_TYPE_DOMAIN_MAP: Record<CaseType, CaseDomain> = {
  private_lending: "civil",
  labor_dispute: "civil",
  divorce_dispute: "civil",
  tort_liability: "civil",
};

export const DOMAIN_CASE_TYPE_MAP: Record<CaseDomain, CaseType[]> = {
  civil: [
    "private_lending",
    "labor_dispute",
    "divorce_dispute",
    "tort_liability",
  ],
  criminal: [],
  administrative: [],
};

export function isCaseTypeAllowedForDomain(
  domain: CaseDomain,
  caseType: CaseType,
): boolean {
  return CASE_TYPE_DOMAIN_MAP[caseType] === domain;
}

export interface ResponseEnvelope<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
  error_code: string | null;
}

export interface PartyProfile {
  party_id: string | null;
  role: CaseParticipantRole;
  display_name: string;
  relation_to_case: string | null;
  stance_summary: string | null;
}

export interface EvidenceItem {
  evidence_id: string | null;
  name: string;
  evidence_type: EvidenceType;
  summary: string;
  source: string | null;
  supports: string[];
  risk_points: string[];
  strength: EvidenceStrength;
  is_available: boolean;
}

export interface OpponentProfile {
  role: CaseParticipantRole;
  display_name: string;
  likely_arguments: string[];
  likely_evidence: string[];
  likely_strategies: string[];
}

export interface TimelineEvent {
  event_id: string | null;
  time_label: string;
  event_text: string;
  significance: string | null;
  related_evidence_ids: string[];
}

export interface CaseProfile {
  case_id: string | null;
  domain: CaseDomain;
  case_type: CaseType;
  title: string;
  summary: string;
  user_perspective_role: UserPerspectiveRole;
  user_goals: UserGoal[];
  parties: PartyProfile[];
  claims: string[];
  core_facts: string[];
  timeline_events: TimelineEvent[];
  focus_issues: string[];
  evidence_items: EvidenceItem[];
  missing_evidence: string[];
  opponent_profile: OpponentProfile | null;
  notes: string | null;
}
