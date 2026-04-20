import type {
  SimulationSnapshot,
  SimulationUserInputEntry,
  SimulationUserInputType,
  TrialStage,
} from "../../types/turn";

export interface TrialSupplementPreset {
  type: SimulationUserInputType;
  label: string;
  placeholder: string;
}

const INPUT_TYPE_LABELS: Record<SimulationUserInputType, string> = {
  fact: "补充事实",
  evidence: "补充证据",
  cross_exam: "质证意见",
  procedure_request: "程序申请",
  argument: "辩论主张",
  closing_statement: "最后陈述",
  settlement_position: "调解底线",
};

const STAGE_PRESETS: Record<TrialStage, TrialSupplementPreset[]> = {
  prepare: [
    {
      type: "fact",
      label: "补充事实",
      placeholder: "补一条庭前必须先说清的关键事实。",
    },
    {
      type: "procedure_request",
      label: "程序申请",
      placeholder: "写明是否申请延期、调查取证、鉴定或证人出庭。",
    },
  ],
  investigation: [
    {
      type: "fact",
      label: "补充事实",
      placeholder: "补一条能改变争点判断的新事实。",
    },
    {
      type: "evidence",
      label: "补充证据",
      placeholder: "写明新增证据、来源、形成时间和证明目的。",
    },
  ],
  evidence: [
    {
      type: "cross_exam",
      label: "质证意见",
      placeholder: "围绕真实性、合法性、关联性或证明目的写质证意见。",
    },
    {
      type: "evidence",
      label: "补充证据",
      placeholder: "写明我方还要补交的证据及其证明目标。",
    },
  ],
  debate: [
    {
      type: "argument",
      label: "辩论主张",
      placeholder: "写一段可直接开口的主论点或反驳话术。",
    },
    {
      type: "cross_exam",
      label: "补充反驳",
      placeholder: "补一条针对对方论证漏洞的反击说法。",
    },
  ],
  final_statement: [
    {
      type: "closing_statement",
      label: "最后陈述",
      placeholder: "把全场想留下的一句结论写下来。",
    },
  ],
  mediation_or_judgment: [
    {
      type: "settlement_position",
      label: "调解底线",
      placeholder: "写明可以让步到哪里，哪些条件不能退。",
    },
    {
      type: "argument",
      label: "裁判请求",
      placeholder: "补一段希望法庭采纳的最终判断理由。",
    },
  ],
  report_ready: [],
};

export function getTrialSupplementPresets(
  stage: TrialStage | undefined | null,
): TrialSupplementPreset[] {
  if (!stage) {
    return [];
  }

  return STAGE_PRESETS[stage] ?? [];
}

export function formatSimulationUserInputTypeLabel(
  type: SimulationUserInputType,
): string {
  return INPUT_TYPE_LABELS[type];
}

export function getStageSimulationUserInputs(
  entries: SimulationUserInputEntry[] | undefined,
  stage: TrialStage | undefined | null,
): SimulationUserInputEntry[] {
  if (!entries?.length || !stage) {
    return [];
  }

  return entries.filter((entry) => entry.stage === stage);
}

export function summarizeSimulationUserInputEntry(
  entry: SimulationUserInputEntry,
  maxLength = 52,
): string {
  const content = entry.content.replace(/\s+/g, " ").trim();
  if (content.length <= maxLength) {
    return content;
  }

  return `${content.slice(0, maxLength).trim()}…`;
}

export function getLatestSimulationUserInput(
  snapshot: SimulationSnapshot | null | undefined,
): SimulationUserInputEntry | null {
  const entries = snapshot?.user_input_entries;
  if (!entries?.length) {
    return null;
  }

  return entries[entries.length - 1] ?? null;
}
