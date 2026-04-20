import type {
  SimulationCgBackgroundId,
  SimulationCgCharacterId,
  SimulationCgEmotion,
  SimulationCgShotType,
  SimulationCgTargetId,
  TrialStage,
} from "./turn";

const TRIAL_STAGE_LABELS: Record<TrialStage, string> = {
  prepare: "庭前准备",
  investigation: "法庭调查",
  evidence: "举证质证",
  debate: "法庭辩论",
  final_statement: "最后陈述",
  mediation_or_judgment: "调解 / 判决",
  report_ready: "复盘报告",
};

const PARTY_ROLE_LABELS: Record<string, string> = {
  plaintiff: "原告",
  defendant: "被告",
  applicant: "申请人",
  respondent: "被申请人",
  claimant_side: "主张方",
  respondent_side: "对方",
  agent: "代理人",
  witness: "证人",
  judge: "法官",
  other: "其他角色",
};

const FOCUS_KEY_LABELS: Record<string, string> = {
  court_opening: "开庭程序确认",
  claim_confirmation: "诉请与权利义务确认",
  plaintiff_opening: "原告开场陈述",
  defendant_answer: "被告答辩回应",
  issue_summary: "争议焦点归纳",
  evidence_layout: "我方举证布局",
  surprise_evidence: "对方突袭证据",
  procedure_response: "程序性申请与异议处理",
  primary_argument: "我方主辩展开",
  defense_counterattack: "对方反击抗辩",
  judge_questioning: "法官高压追问",
  final_statement: "最后陈述收束",
  mediation_probe: "调解意向探测",
  outcome_result: "调解 / 宣判结果",
};

const STATE_KEY_LABELS: Record<string, string> = {
  evidence_strength: "证据强度",
  procedure_control: "程序控制",
  judge_trust: "法官信任",
  opponent_pressure: "对方压迫感",
  contradiction_risk: "矛盾风险",
  surprise_exposure: "突袭暴露度",
  settlement_tendency: "调解倾向",
};

const CG_BACKGROUND_LABELS: Record<SimulationCgBackgroundId, string> = {
  courtroom_entry: "开庭场景",
  fact_inquiry: "事实调查",
  evidence_confrontation: "证据对峙",
  argument_pressure: "攻防对辩",
  closing_focus: "陈述收束",
  judgment_moment: "裁判时刻",
  replay_archive: "复盘回看",
};

const CG_SHOT_LABELS: Record<SimulationCgShotType, string> = {
  wide: "远景",
  medium: "中景",
  close: "近景",
  insert: "特写",
};

const CG_EMOTION_LABELS: Record<SimulationCgEmotion, string> = {
  calm: "平稳",
  stern: "肃正",
  pressing: "压迫",
  reflective: "凝思",
  steady: "沉着",
};

const CG_CHARACTER_LABELS: Record<SimulationCgCharacterId, string> = {
  judge_penguin: "法官企鹅",
  plaintiff_penguin: "原告企鹅",
  plaintiff_agent_penguin: "原告代理企鹅",
  defendant_penguin: "被告企鹅",
  defendant_agent_penguin: "被告代理企鹅",
  witness_penguin: "证人企鹅",
  clerk_penguin: "书记员企鹅",
};

const CG_TARGET_LABELS: Record<SimulationCgTargetId, string> = {
  bench: "审判席",
  claim_sheet: "诉请材料",
  evidence_screen: "证据屏",
  argument_outline: "辩论提纲",
  closing_notes: "陈述笔记",
  judgment_paper: "裁判文书",
  archive_scroll: "复盘卷宗",
};

export function formatTrialStageLabel(stage: TrialStage | string | null | undefined): string {
  if (!stage) {
    return "未进入阶段";
  }

  return TRIAL_STAGE_LABELS[stage as TrialStage] ?? String(stage);
}

export function formatPartyRoleLabel(role: string | null | undefined): string {
  if (!role) {
    return "未识别";
  }

  return PARTY_ROLE_LABELS[role] ?? role;
}

export function formatFocusLabel(focus: string | null | undefined): string {
  if (!focus) {
    return "未指定";
  }

  return FOCUS_KEY_LABELS[focus] ?? focus;
}

export function formatStateKeyLabel(key: string): string {
  return STATE_KEY_LABELS[key] ?? key;
}

export function formatCgBackgroundLabel(
  background: SimulationCgBackgroundId | string | null | undefined,
): string {
  if (!background) {
    return "法庭场景";
  }

  return CG_BACKGROUND_LABELS[background as SimulationCgBackgroundId] ?? String(background);
}

export function formatCgShotLabel(
  shot: SimulationCgShotType | string | null | undefined,
): string {
  if (!shot) {
    return "默认镜头";
  }

  return CG_SHOT_LABELS[shot as SimulationCgShotType] ?? String(shot);
}

export function formatCgEmotionLabel(
  emotion: SimulationCgEmotion | string | null | undefined,
): string {
  if (!emotion) {
    return "平稳";
  }

  return CG_EMOTION_LABELS[emotion as SimulationCgEmotion] ?? String(emotion);
}

export function formatCgCharacterLabel(
  character: SimulationCgCharacterId | string | null | undefined,
): string {
  if (!character) {
    return "法庭角色";
  }

  return CG_CHARACTER_LABELS[character as SimulationCgCharacterId] ?? String(character);
}

export function formatCgTargetLabel(
  target: SimulationCgTargetId | string | null | undefined,
): string {
  if (!target) {
    return "庭审焦点";
  }

  return CG_TARGET_LABELS[target as SimulationCgTargetId] ?? String(target);
}
