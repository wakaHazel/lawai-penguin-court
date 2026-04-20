import {
  CASE_TYPE_DOMAIN_MAP,
  type CaseDomain,
  type CaseProfile,
  type CaseType,
  type UserGoal,
  type UserPerspectiveRole,
} from "../../types/case";

export interface CaseIntakeDraft {
  domain: CaseDomain;
  case_type: CaseType;
  title: string;
  summary: string;
  user_perspective_role: UserPerspectiveRole;
  user_goals: UserGoal[];
  plaintiff_name: string;
  defendant_name: string;
  claims_text: string;
  core_facts_text: string;
  focus_issues_text: string;
  missing_evidence_text: string;
  notes: string;
}

export function createEmptyCaseIntakeDraft(): CaseIntakeDraft {
  return {
    domain: "civil",
    case_type: "private_lending",
    title: "",
    summary: "",
    user_perspective_role: "claimant_side",
    user_goals: ["simulate_trial"],
    plaintiff_name: "",
    defendant_name: "",
    claims_text: "",
    core_facts_text: "",
    focus_issues_text: "",
    missing_evidence_text: "",
    notes: "",
  };
}

export function normalizeCaseTypeForDomain(
  domain: CaseDomain,
  caseType: CaseType,
): CaseType {
  if (CASE_TYPE_DOMAIN_MAP[caseType] === domain) {
    return caseType;
  }

  if (domain !== "civil") {
    throw new Error("当前版本只开放民事案件录入。");
  }

  return "private_lending";
}

export function buildCaseProfileFromDraft(
  draft: CaseIntakeDraft,
): CaseProfile {
  const normalizedCaseType = normalizeCaseTypeForDomain(
    draft.domain,
    draft.case_type,
  );

  const plaintiffName = draft.plaintiff_name.trim() || "原告";
  const defendantName = draft.defendant_name.trim() || "被告";

  return {
    case_id: null,
    domain: draft.domain,
    case_type: normalizedCaseType,
    title: draft.title.trim(),
    summary: draft.summary.trim(),
    user_perspective_role: draft.user_perspective_role,
    user_goals: draft.user_goals,
    parties: [
      {
        party_id: null,
        role: "plaintiff",
        display_name: plaintiffName,
        relation_to_case: null,
        stance_summary: null,
      },
      {
        party_id: null,
        role: "defendant",
        display_name: defendantName,
        relation_to_case: null,
        stance_summary: null,
      },
    ],
    claims: splitMultilineText(draft.claims_text),
    core_facts: splitMultilineText(draft.core_facts_text),
    timeline_events: [],
    focus_issues: splitMultilineText(draft.focus_issues_text),
    evidence_items: [],
    missing_evidence: splitMultilineText(draft.missing_evidence_text),
    opponent_profile: {
      role: "defendant",
      display_name: defendantName,
      likely_arguments: [],
      likely_evidence: [],
      likely_strategies: [],
    },
    notes: emptyToNull(draft.notes),
  };
}

export function buildDraftFromCaseProfile(caseProfile: CaseProfile): CaseIntakeDraft {
  const claimant =
    caseProfile.parties.find(
      (party) => party.role === "plaintiff" || party.role === "applicant",
    )?.display_name ?? "";
  const respondent =
    caseProfile.parties.find(
      (party) => party.role === "defendant" || party.role === "respondent",
    )?.display_name ??
    caseProfile.opponent_profile?.display_name ??
    "";

  return {
    domain: caseProfile.domain,
    case_type: normalizeCaseTypeForDomain(caseProfile.domain, caseProfile.case_type),
    title: caseProfile.title,
    summary: caseProfile.summary,
    user_perspective_role: caseProfile.user_perspective_role,
    user_goals: [...caseProfile.user_goals],
    plaintiff_name: claimant,
    defendant_name: respondent,
    claims_text: joinTextLines(caseProfile.claims),
    core_facts_text: joinTextLines(caseProfile.core_facts),
    focus_issues_text: joinTextLines(caseProfile.focus_issues),
    missing_evidence_text: joinTextLines(caseProfile.missing_evidence),
    notes: caseProfile.notes ?? "",
  };
}

function splitMultilineText(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinTextLines(items: string[]): string {
  return items.map((item) => item.trim()).filter(Boolean).join("\n");
}

function emptyToNull(value: string): string | null {
  const normalized = value.trim();
  return normalized ? normalized : null;
}
