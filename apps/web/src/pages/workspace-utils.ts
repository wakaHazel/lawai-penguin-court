import { createEmptyCaseIntakeDraft, type CaseIntakeDraft } from "../features/case-intake/draft";
import type {
  OpponentBehaviorSnapshot,
  ReplayReportSnapshot,
  WinRateAnalysisSnapshot,
} from "../types/analysis";
import type {
  CaseDomain,
  CaseProfile,
  CaseType,
  UserGoal,
  UserPerspectiveRole,
} from "../types/case";
import {
  formatFocusLabel,
  formatPartyRoleLabel,
  formatStateKeyLabel,
  formatTrialStageLabel,
} from "../types/display";
import type {
  SimulationSnapshot,
  SimulationUserInputEntry,
  SimulationUserInputType,
} from "../types/turn";

export type WorkspaceStage = "intake" | "simulation" | "opponent" | "win_rate" | "replay";

export interface SessionCaseRecord {
  caseId: string;
  caseProfile: CaseProfile;
  draftSnapshot: CaseIntakeDraft;
  simulationSnapshot: SimulationSnapshot | null;
  opponentSnapshot: OpponentBehaviorSnapshot | null;
  winRateSnapshot: WinRateAnalysisSnapshot | null;
  replayReport: ReplayReportSnapshot | null;
  lastVisitedStage: WorkspaceStage;
  updatedAt: string;
}

export interface PersistedWorkspaceState {
  draft: CaseIntakeDraft;
  currentCase: CaseProfile | null;
  simulationSnapshot: SimulationSnapshot | null;
  opponentSnapshot: OpponentBehaviorSnapshot | null;
  winRateSnapshot: WinRateAnalysisSnapshot | null;
  replayReport: ReplayReportSnapshot | null;
  activeStage: WorkspaceStage;
  sessionCases: SessionCaseRecord[];
  isMockMode: boolean;
}

export const WORKSPACE_STORAGE_KEY = "penguin-court/workspace-v2";

const REPORT_SECTION_LABELS: Record<string, string> = {
  header: "报告头部",
  main_axis: "本轮主轴概览",
  turning_points: "关键转折点",
  timeline: "庭审过程回顾",
  evidence_risk: "证据与风险面",
  opponent: "对方战术画像",
  suggestions: "下一轮建议",
  result: "结果结算",
};

const ENGLISH_REPLAY_MARKERS = [
  "This run has completed the courtroom simulation",
  "The main axis stayed on",
  "recorded turn summaries were used to prepare the replay scaffold",
  "header",
  "main_axis",
  "turning_points",
  "timeline",
  "evidence_risk",
  "suggestions",
  "result",
  "evidence_strength",
  "procedure_control",
  "judge_trust",
  "opponent_pressure",
  "contradiction_risk",
  "surprise_exposure",
  "settlement_tendency",
];

const LOCAL_USER_INPUT_LABELS: Record<SimulationUserInputType, string> = {
  fact: "补充事实",
  evidence: "补充证据",
  cross_exam: "质证意见",
  procedure_request: "程序申请",
  argument: "辩论主张",
  closing_statement: "最后陈述",
  settlement_position: "调解底线",
};

export function cloneDraft(draft: CaseIntakeDraft): CaseIntakeDraft {
  return {
    ...draft,
    user_goals: [...draft.user_goals],
  };
}

export function validateDraft(draft: CaseIntakeDraft): string | null {
  if (!draft.title.trim()) {
    return "请先填写案件标题。";
  }

  if (!draft.summary.trim()) {
    return "请先填写案件概述。";
  }

  if (!draft.plaintiff_name.trim()) {
    return "请先填写原告或申请人。";
  }

  if (!draft.defendant_name.trim()) {
    return "请先填写被告或被申请人。";
  }

  if (draft.user_goals.length === 0) {
    return "请至少选择一个本次目标。";
  }

  return null;
}

export function formatPercent(value: number): string {
  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

export function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "时间未知";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function readStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean);
}

function readNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  return null;
}

function readString(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized || null;
}

function formatLocalUserInputLabel(type: SimulationUserInputType): string {
  return LOCAL_USER_INPUT_LABELS[type];
}

function summarizeLocalUserInputEntry(
  entry: SimulationUserInputEntry,
  maxLength = 34,
): string {
  const content = entry.content.replace(/\s+/g, " ").trim();
  if (content.length <= maxLength) {
    return content;
  }

  return `${content.slice(0, maxLength).trim()}…`;
}

function getRecentSimulationUserInputs(
  simulationSnapshot: SimulationSnapshot,
  limit = 3,
): SimulationUserInputEntry[] {
  const entries = simulationSnapshot.user_input_entries ?? [];
  if (entries.length === 0) {
    return [];
  }

  return entries.slice(-limit);
}

function buildLocalOpponentArgumentFromInput(
  entry: SimulationUserInputEntry,
): string {
  const summary = summarizeLocalUserInputEntry(entry);

  switch (entry.input_type) {
    case "evidence":
      return `会集中攻击你新补证据“${summary}”的三性和证明目的。`;
    case "cross_exam":
      return `会抓住你写下的质证意见“${summary}”反问依据是否充分。`;
    case "argument":
      return `会把你刚提出的主张“${summary}”拆成证据不足或法理跳跃。`;
    case "closing_statement":
      return `会把你的最后陈述“${summary}”定性为概括性表达，弱化其证明力。`;
    case "procedure_request":
      return `会反对你的程序申请“${summary}”，强调无需进一步拖延或调查。`;
    case "settlement_position":
      return `会围绕你暴露出的调解底线“${summary}”继续下压条件。`;
    case "fact":
    default:
      return `会否认你新增事实“${summary}”的外部印证强度，要求继续举证。`;
  }
}

function buildLocalEvidenceFocusFromInput(
  entry: SimulationUserInputEntry,
): string | null {
  const summary = summarizeLocalUserInputEntry(entry);

  switch (entry.input_type) {
    case "evidence":
      return `紧盯新增证据“${summary}”的来源、形成时间和原始载体。`;
    case "fact":
      return `要求你就新增事实“${summary}”继续提交外部印证材料。`;
    default:
      return null;
  }
}

function buildLocalResponseFromInput(entry: SimulationUserInputEntry): string {
  const label = entry.label || formatLocalUserInputLabel(entry.input_type);
  const summary = summarizeLocalUserInputEntry(entry);

  switch (entry.input_type) {
    case "evidence":
      return `把${label}“${summary}”拆成来源、时间、证明目的三句法庭表达。`;
    case "cross_exam":
      return `围绕${label}“${summary}”补齐真实性、合法性、关联性三层理由。`;
    case "argument":
      return `把${label}“${summary}”对应到具体证据和法条，不要只停在结论。`;
    case "procedure_request":
      return `把${label}“${summary}”写成完整申请理由，准备接受法庭追问。`;
    case "settlement_position":
      return `围绕${label}“${summary}”明确可退与不可退项，避免临场失守。`;
    case "closing_statement":
      return `把${label}“${summary}”压成一句主结论和一句法庭请求。`;
    case "fact":
    default:
      return `围绕${label}“${summary}”补齐对应证据，避免事实孤立悬空。`;
  }
}

function buildLocalRiskFromInput(entry: SimulationUserInputEntry): string {
  const summary = summarizeLocalUserInputEntry(entry);

  switch (entry.input_type) {
    case "evidence":
      return `若“${summary}”说不清来源或形成过程，会被直接从证据三性打掉。`;
    case "argument":
    case "cross_exam":
      return `若“${summary}”没有证据或法条托底，会被法庭认定为表达空转。`;
    case "fact":
      return `若“${summary}”缺少外部印证，对方会继续围绕举证不足施压。`;
    default:
      return `你补入的“${summary}”仍需后续补强，否则会变成新的争议口。`;
  }
}

function buildLocalPositiveFactorFromInput(
  entry: SimulationUserInputEntry,
): string {
  const label = entry.label || formatLocalUserInputLabel(entry.input_type);
  return `已补入${label}：${summarizeLocalUserInputEntry(entry, 42)}`;
}

function buildLocalEvidenceGapActionFromInput(
  entry: SimulationUserInputEntry,
): string {
  const label = entry.label || formatLocalUserInputLabel(entry.input_type);
  const summary = summarizeLocalUserInputEntry(entry, 36);

  switch (entry.input_type) {
    case "evidence":
      return `补齐${label}“${summary}”的原件、截图原始载体和形成时间说明。`;
    case "cross_exam":
    case "argument":
      return `把${label}“${summary}”对应到证据编号和具体法条，再进入下一轮。`;
    default:
      return `围绕${label}“${summary}”继续补一条能落地的印证材料。`;
  }
}

function getLocalUserInputBonus(entry: SimulationUserInputEntry): number {
  switch (entry.input_type) {
    case "evidence":
      return 4;
    case "cross_exam":
    case "argument":
    case "closing_statement":
      return 3;
    case "fact":
    case "procedure_request":
      return 2;
    case "settlement_position":
      return 1;
    default:
      return 0;
  }
}

function dedupeItems(items: string[]): string[] {
  const seen = new Set<string>();
  const nextItems: string[] = [];

  for (const item of items) {
    const normalized = item.replace(/\s+/g, " ").trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }

    seen.add(normalized);
    nextItems.push(normalized);
  }

  return nextItems;
}

function mergeStringLists(primary: string[] | undefined, fallback: string[] | undefined): string[] {
  return dedupeItems([...(primary ?? []), ...(fallback ?? [])]);
}

function buildCaseTypeDefaultOpponentEvidence(caseProfile: CaseProfile): string[] {
  switch (caseProfile.case_type) {
    case "labor_dispute":
      return ["合作协议或承揽约定", "项目结算记录或转账备注", "实际用工单位派工、考勤或管理记录"];
    case "private_lending":
      return ["转账凭证及备注", "聊天记录上下文", "双方既往资金往来明细"];
    case "divorce_dispute":
      return ["财产流水与出资记录", "房车产权登记材料", "子女实际照料与支出材料"];
    case "tort_liability":
      return ["事故记录或现场照片", "监控视频或目击证言", "医疗记录、鉴定意见或维修单据"];
    default:
      return ["聊天记录", "付款备注", "内部记录"];
  }
}

function buildCaseTypeDefaultOpponentStrategies(caseProfile: CaseProfile): string[] {
  switch (caseProfile.case_type) {
    case "labor_dispute":
      return ["否认人身隶属性", "把管理行为解释为业务协作", "把付款性质解释为劳务报酬或项目结算"];
    case "private_lending":
      return ["否认借贷合意", "把转账改写为其他往来", "压低利息与违约责任范围"];
    case "divorce_dispute":
      return ["争执共同财产范围", "切割个人财产与共同财产", "把争点拉回子女利益与现实抚养安排"];
    case "tort_liability":
      return ["否认过错或因果关系", "压低损害数额", "主张原告存在共同过错或自甘风险"];
    default:
      return ["否认关键事实", "弱化因果关系", "转移举证责任"];
  }
}

function buildCaseTypeDefaultOpponentArguments(
  caseProfile: CaseProfile,
  simulationSnapshot: SimulationSnapshot,
): string[] {
  const focus =
    currentCaseFocus(caseProfile, simulationSnapshot.branch_focus) ??
    formatFocusLabel(simulationSnapshot.branch_focus);

  switch (caseProfile.case_type) {
    case "labor_dispute":
      return [
        `即便围绕“${focus}”存在一定管理安排，也不足以当然推出劳动关系成立。`,
        "双方更接近合作、承揽或劳务关系，而非受劳动法调整的劳动关系。",
        "即便存在部分报酬支付或考勤管理，也只能说明现场作业需要，不能直接证明组织隶属性与经济从属性。",
      ];
    case "private_lending":
      return [
        `围绕“${focus}”的现有材料不足以证明双方已形成明确借贷合意。`,
        "涉案转账可以解释为投资、往来款、代付款或旧账冲抵，不当然等于借款交付。",
        "即便存在资金交付，原告诉请中的利息、违约金或还款期限也缺少明确约定支撑。",
      ];
    case "divorce_dispute":
      return [
        `围绕“${focus}”的表述更多是单方陈述，尚不足以直接支持全部离婚或财产主张。`,
        "共同财产范围、贡献比例和照料安排仍需回到客观证据审查，不能仅凭情绪性叙述认定。",
        "对方会把争点拉回到证据、子女最佳利益和现实履行可能性上。",
      ];
    case "tort_liability":
      return [
        `围绕“${focus}”的证据尚不足以完整证明被告存在法定过错。`,
        "损害后果与被诉行为之间的因果关系并未形成闭环证明。",
        "即便承担责任，也应结合原告自身过错、风险参与程度和损失计算依据适当压缩责任范围。",
      ];
    default:
      return currentCaseFocusIssues(caseProfile).map((item) => `围绕“${item}”提出抗辩`);
  }
}

function buildCaseTypeLegalReferences(caseProfile: CaseProfile): string[] {
  switch (caseProfile.case_type) {
    case "labor_dispute":
      return [
        "《劳动合同法》第7条、第10条、第82条，围绕劳动关系成立、书面合同义务与双倍工资责任组织抗辩。",
        "《关于确立劳动关系有关事项的通知》关于主体资格、管理关系和报酬支付的认定规则。",
      ];
    case "private_lending":
      return [
        "《民法典》第667条、第675条，围绕借贷合意、返还义务与履行期限组织抗辩。",
        "《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》关于借贷事实、交付款项、利息和证据审查的规则。",
      ];
    case "divorce_dispute":
      return [
        "《民法典》婚姻家庭编关于离婚条件、夫妻共同财产、子女抚养与探望安排的相关规定。",
        "围绕夫妻共同财产认定、抚养安排和照料稳定性组织法律说理。",
      ];
    case "tort_liability":
      return [
        "《民法典》第1165条、第1179条等侵权责任条款，围绕过错、因果关系和赔偿范围组织抗辩。",
        "如涉及人身损害或财产损害，将进一步围绕损失计算依据、鉴定结论和责任比例展开。",
      ];
    default:
      return ["围绕争议焦点、举证责任与证明标准组织说理。"];
  }
}

function buildCaseTypeReasoningPaths(
  caseProfile: CaseProfile,
  simulationSnapshot: SimulationSnapshot,
): string[] {
  const stageLabel = formatTrialStageLabel(simulationSnapshot.current_stage);

  switch (caseProfile.case_type) {
    case "labor_dispute":
      return [
        `在${stageLabel}阶段先拆劳动关系成立要件，再把现有管理事实解释为项目协作或现场管理需要。`,
        "先否认人身、经济和组织从属性闭环，再即便存在部分管理行为，也强调不足以直接推导劳动关系。",
      ];
    case "private_lending":
      return [
        `在${stageLabel}阶段先拆借贷合意，再拆款项交付属性，最后压缩利息和违约责任范围。`,
        "通过替代资金性质解释切断“转账=借款”的单线推理。",
      ];
    case "divorce_dispute":
      return [
        `在${stageLabel}阶段把争点从情绪叙事拉回到财产来源、照料事实和证据基础上。`,
        "即便承认部分家庭矛盾存在，也主张不足以当然支持全部离婚、财产或抚养请求。",
      ];
    case "tort_liability":
      return [
        `在${stageLabel}阶段先否认过错，再否认因果关系，最后压低损失结果与责任比例。`,
        "即便责任成立，也主张原告损失计算过高或存在共同过错，应调低赔偿范围。",
      ];
    default:
      return ["先拆事实成立，再拆法律评价，最后把举证不能的风险压回原告。"];
  }
}

function buildStageDefaultCrossExaminationLines(
  caseProfile: CaseProfile,
  simulationSnapshot: SimulationSnapshot,
): string[] {
  const focus =
    currentCaseFocus(caseProfile, simulationSnapshot.branch_focus) ??
    formatFocusLabel(simulationSnapshot.branch_focus);

  switch (simulationSnapshot.current_stage) {
    case "evidence":
      return [
        `对你方围绕“${focus}”提交的证据，真实性、合法性、关联性及证明目的均不认可，请先说明原始载体、形成时间和提交主体。`,
        "即便证据形式真实，也不足以单独证明你方主张的法律评价，请结合完整证据链说明。",
      ];
    case "debate":
      return [
        `你方现在围绕“${focus}”的论证更多停留在结论，缺少逐项对应证据和法条的展开。`,
        "请你方说明，哪一组证据能够直接证明你方刚才的核心判断，而不是仅作推测。 ",
      ];
    case "investigation":
      return [
        `请你方就“${focus}”说明具体发生时间、地点、指令来源和在场人员，不要只作概括陈述。`,
      ];
    default:
      return [
        `围绕“${focus}”，对方会要求你把概括性说法进一步落到具体事实和证据编号上。`,
      ];
  }
}

function buildStageDefaultSurpriseActions(
  simulationSnapshot: SimulationSnapshot,
): string[] {
  switch (simulationSnapshot.current_stage) {
    case "prepare":
      return ["在程序确认阶段临时主张你方申请不具备必要性，试图先锁死调查边界。"];
    case "investigation":
      return ["突然要求你说明关键事实中的具体时间、地点和管理链条，逼你暴露细节摇摆。"];
    case "evidence":
      return ["当庭要求核验原始载体，指控截图、摘录或转述材料存在片段化问题。"];
    case "debate":
      return ["抓住你一句未落证据的话，反过来指称你方整体论证缺少闭环。"];
    case "final_statement":
      return ["主张最后陈述不是补证环节，要求法庭忽略你刚补入的新判断。"];
    case "mediation_or_judgment":
      return ["一边释放有限调解意愿，一边继续压你的底线，试探你是否会先松口。"];
    default:
      return [];
  }
}

function buildUserInputDrivenStableResponse(
  caseProfile: CaseProfile,
  entry: SimulationUserInputEntry,
): string {
  const summary = summarizeLocalUserInputEntry(entry, 34);

  switch (entry.input_type) {
    case "fact":
      if (caseProfile.case_type === "labor_dispute") {
        return `关于“${summary}”，我方将结合考勤、工作群指令和报酬发放记录交叉印证，证明该事实并非孤证。`;
      }
      return `关于“${summary}”，我方会把该事实落到具体时间、证据编号和证明目的上，不让它停留在概括陈述。`;
    case "evidence":
      return `对“${summary}”，我方可以继续说明来源、形成时间和原始载体，请法庭结合全案证据链综合判断证明力。`;
    case "procedure_request":
      return `就“${summary}”，相关材料掌握在对方或第三方处，我方客观上难以自行调取，请法庭依职权调查收集。`;
    case "argument":
      return `围绕“${summary}”，我方会同步指向对应证据和法条，不仅给结论，也给出论证路径。`;
    case "cross_exam":
      return `对于“${summary}”，我方将从真实性、合法性、关联性和证明目的四层继续展开，不让质证停留在态度表述。`;
    default:
      return `围绕“${summary}”，我方会补齐证据支撑和法庭表达，避免被对方抓成空口主张。`;
  }
}

function buildCaseTypeStableResponseLines(
  caseProfile: CaseProfile,
  simulationSnapshot: SimulationSnapshot,
): string[] {
  const focus =
    currentCaseFocus(caseProfile, simulationSnapshot.branch_focus) ??
    formatFocusLabel(simulationSnapshot.branch_focus);

  switch (caseProfile.case_type) {
    case "labor_dispute":
      return [
        `我方主张，虽然双方名为合作经营，但围绕“${focus}”已经出现考勤管理、工作安排和报酬取得等劳动管理特征，法庭应回到实际履行状态审查劳动关系。`,
        "对方若坚持合作关系，我方会逐项对应岗位安排、管理指令、考勤约束和报酬发放方式，证明申请人并非独立经营者。",
      ];
    case "private_lending":
      return [
        `围绕“${focus}”，我方会把借贷合意、款项交付和催收经过拆成三段陈述，避免被对方用“其他往来”一把带走。`,
        "对方若否认借款性质，我方会把转账凭证、聊天确认和还款承诺放到同一时间线上，证明资金交付系借贷而非投资或代付。",
      ];
    case "divorce_dispute":
      return [
        `围绕“${focus}”，我方会把婚姻关系、财产来源和子女照料事实分别落到证据上，不与情绪叙事混在一起。`,
        "对方若模糊共同财产范围，我方会先锁定财产形成时间、出资来源和登记状态，再进入分割方案。 ",
      ];
    case "tort_liability":
      return [
        `围绕“${focus}”，我方会先证明被告过错，再证明损害后果与被诉行为之间的因果关系，最后锁定损失金额。`,
        "对方若主张原告亦有过错，我方会要求其就具体过错事实和比例依据逐项举证，不接受空泛压责。",
      ];
    default:
      return [
        `围绕“${focus}”，我方会坚持事实、证据、法条三线并行，不让争议回到抽象判断。`,
      ];
  }
}

function buildCaseTypeFallbackResponseLines(
  caseProfile: CaseProfile,
  simulationSnapshot: SimulationSnapshot,
): string[] {
  const focus =
    currentCaseFocus(caseProfile, simulationSnapshot.branch_focus) ??
    formatFocusLabel(simulationSnapshot.branch_focus);

  switch (caseProfile.case_type) {
    case "labor_dispute":
      return [
        `即便法庭认为围绕“${focus}”的现有材料尚不足以一次性认定劳动关系，也应先准许调取考勤、社保和报酬材料后再作判断。`,
        "即便《合作经营协议》形式存在，也不能替代对实际管理关系和从属性的实体审查。",
      ];
    case "private_lending":
      return [
        `即便法庭对“${focus}”仍有疑问，也应先审查转账背景、催收记录和双方后续确认，不宜仅凭单一替代解释否定借贷关系。`,
        "即便部分利息或违约金请求需要调整，也不影响本金返还义务的独立成立。",
      ];
    case "divorce_dispute":
      return [
        `即便“${focus}”短期内难以一次性查清，也应先把无争议财产和子女现实照料安排固定下来。`,
        "即便部分主张暂时证据不足，也不影响先就已经形成闭环的事实部分请求法庭确认。",
      ];
    case "tort_liability":
      return [
        `即便“${focus}”仍需进一步核验，也应先固定事故经过、损害结果和关键责任节点，避免争议被对方整体模糊化。`,
        "即便责任比例仍有争议，也不影响先锁定基础侵权事实和主要损失项目。",
      ];
    default:
      return ["如果法庭对当前争点仍有疑问，我方至少先把无争议事实和关键证据固定下来。"];
  }
}

function buildCaseTypeLegalReasoningNotes(
  caseProfile: CaseProfile,
  simulationSnapshot: SimulationSnapshot,
): string[] {
  const focus =
    currentCaseFocus(caseProfile, simulationSnapshot.branch_focus) ??
    formatFocusLabel(simulationSnapshot.branch_focus);

  switch (caseProfile.case_type) {
    case "labor_dispute":
      return [
        `围绕“${focus}”，可先援引《劳动合同法》第7条、第10条，强调劳动关系判断要回到实际用工与管理状态，而不是协议标题。`,
        "如继续主张双倍工资，可结合《劳动合同法》第82条，说明前提是劳动关系已经成立且用人单位未依法订立书面劳动合同。",
      ];
    case "private_lending":
      return [
        `围绕“${focus}”，可援引《民法典》第667条、第675条，把借贷合意、返还义务和履行期限拆开说理。`,
        "如对方主张转账另有性质，可结合民间借贷司法解释，要求其就替代资金性质提供相应证据支持。 ",
      ];
    case "divorce_dispute":
      return [
        `围绕“${focus}”，可回到《民法典》婚姻家庭编关于离婚条件、共同财产和未成年子女利益保护的规范路径。`,
        "说理时尽量把财产形成时间、出资来源和现实照料安排与对应法条并列出现，避免只讲价值判断。 ",
      ];
    case "tort_liability":
      return [
        `围绕“${focus}”，可援引《民法典》第1165条等侵权责任条款，分开论证过错、因果关系与损失范围。`,
        "如果对方主张共同过错，应要求其对具体过错事实、因果贡献和比例基础逐项举证。 ",
      ];
    default:
      return ["法条援引应与当前争点一一对应，避免只列法条名称不写适用理由。"];
  }
}

function buildLocalCrossExaminationFromInput(
  caseProfile: CaseProfile,
  entry: SimulationUserInputEntry,
): string {
  const summary = summarizeLocalUserInputEntry(entry, 38);

  switch (entry.input_type) {
    case "evidence":
      return `对你方新补证据“${summary}”，真实性、合法性、关联性及证明目的均不认可，请说明原始载体、形成时间和保管链条。`;
    case "fact":
      if (caseProfile.case_type === "labor_dispute") {
        return `即便存在“${summary}”，也只能说明现场协作或业务管理需要，不能当然推出劳动关系中的人身隶属性与经济从属性。`;
      }
      if (caseProfile.case_type === "private_lending") {
        return `即便存在“${summary}”，也不能直接证明双方形成借贷合意，更不能当然推导款项性质。`;
      }
      return `即便存在“${summary}”，也只是单一事实片段，不足以直接证明你方主张的法律评价。`;
    case "procedure_request":
      return `你方关于“${summary}”的程序申请，缺少必要性和无法自行收集的充分说明，不应准许。`;
    case "argument":
      return `你方刚才关于“${summary}”的主张缺少证据编号与法条支撑，仍停留在结论表达。`;
    case "cross_exam":
      return `你方所谓“${summary}”只是评价意见，不是可以单独成立的事实基础。`;
    case "closing_statement":
      return `最后陈述阶段再提出“${summary}”，已经超出正常补证和补充调查范围。`;
    case "settlement_position":
      return `你方现在抛出的“${summary}”更像谈判口径，不能替代实体证明。`;
    default:
      return `对你方新增内容“${summary}”不予认可，请结合证据链完整说明。`;
  }
}

function buildLocalSurpriseActionFromInput(
  entry: SimulationUserInputEntry,
): string {
  const summary = summarizeLocalUserInputEntry(entry, 34);

  switch (entry.input_type) {
    case "evidence":
      return `围绕“${summary}”突然要求出示原始手机、原始流水或完整上下文，现场放大材料片段化问题。`;
    case "fact":
      return `抓住“${summary}”连续追问时间、地点、指令人和旁证来源，逼你承认记不清细节。`;
    case "procedure_request":
      return `反指你“${summary}”的申请逾期或无必要，要求法庭当庭驳回。`;
    case "argument":
      return `把你关于“${summary}”的主张替换成另一种更有利于己方的解释路径。`;
    default:
      return `把你新增的“${summary}”改写成一段对己方更有利的替代叙事。`;
  }
}

function currentCaseFocus(
  caseProfile: CaseProfile,
  branchFocus: string,
): string | null {
  return caseProfile.focus_issues.find((item) => item.includes(branchFocus)) ??
    caseProfile.focus_issues[0] ??
    null;
}

function currentCaseFocusIssues(caseProfile: CaseProfile): string[] {
  return caseProfile.focus_issues.length > 0
    ? caseProfile.focus_issues.slice(0, 3)
    : ["当前争议焦点"];
}

function formatReportSectionLabel(key: string): string {
  return REPORT_SECTION_LABELS[key] ?? key;
}

function looksLikeEnglishText(value: string | null | undefined): boolean {
  if (!value) {
    return false;
  }

  return ENGLISH_REPLAY_MARKERS.some((marker) => value.includes(marker));
}

function buildChineseReplayOverview(simulationSnapshot: SimulationSnapshot): string {
  const estimatedWinRate = readNumber(simulationSnapshot.analysis.estimated_win_rate);
  const stageLabel = formatTrialStageLabel(simulationSnapshot.current_stage);
  const focusLabel = formatFocusLabel(simulationSnapshot.branch_focus);
  const positiveFactor = readStringList(simulationSnapshot.analysis.positive_factors)[0];
  const negativeFactor = readStringList(simulationSnapshot.analysis.negative_factors)[0];
  const nextAction = readStringList(simulationSnapshot.analysis.recommended_next_actions)[0];

  return [
    `本轮推演已推进至${stageLabel}，主轴持续围绕“${focusLabel}”展开。`,
    estimatedWinRate !== null
      ? `当前系统估计胜诉率约为 ${Math.round(estimatedWinRate)}%。`
      : "当前系统已完成一轮局势收束，可据此继续做策略判断。",
    positiveFactor ? `当前较有利的一点是：${positiveFactor}` : null,
    negativeFactor ? `当前最需要警惕的是：${negativeFactor}` : null,
    nextAction ? `下一步建议优先处理：${nextAction}` : null,
  ]
    .filter((item): item is string => Boolean(item))
    .join(" ");
}

export function looksLikeEnglishReplayReport(
  report: ReplayReportSnapshot | null | undefined,
): boolean {
  if (!report) {
    return false;
  }

  const textPool = [
    report.report_title,
    report.report_markdown,
    ...report.report_sections.flatMap((section) => [
      section.key,
      section.title,
      ...section.items,
    ]),
  ]
    .join("\n")
    .trim();

  if (!textPool) {
    return false;
  }

  return looksLikeEnglishText(textPool);
}

export function deriveOpponentSnapshotFromSimulation(
  simulationSnapshot: SimulationSnapshot | null,
): OpponentBehaviorSnapshot | null {
  if (!simulationSnapshot) {
    return null;
  }

  const opponent = simulationSnapshot.opponent;
  const likelyArguments = readStringList(opponent?.likely_arguments);
  const likelyEvidence = readStringList(opponent?.likely_evidence);
  const likelyStrategies = readStringList(opponent?.likely_strategies);
  const likelyCrossExaminationLines = readStringList(
    opponent?.likely_cross_examination_lines,
  );
  const likelyLegalReferences = readStringList(
    opponent?.likely_legal_references,
  );
  const likelyReasoningPaths = readStringList(
    opponent?.likely_reasoning_paths,
  );
  const surpriseAttackActions = readStringList(
    opponent?.surprise_attack_actions,
  );
  const recommendedResponses = readStringList(opponent?.recommended_responses);
  const riskPoints = readStringList(opponent?.risk_points);
  const confidence = readNumber(opponent?.confidence);

  if (
    !readString(opponent?.opponent_name) &&
    !readString(opponent?.opponent_role) &&
    likelyArguments.length === 0 &&
    likelyEvidence.length === 0 &&
    likelyStrategies.length === 0 &&
    likelyCrossExaminationLines.length === 0 &&
    likelyLegalReferences.length === 0 &&
    likelyReasoningPaths.length === 0 &&
    surpriseAttackActions.length === 0 &&
    recommendedResponses.length === 0 &&
    riskPoints.length === 0 &&
    confidence === null
  ) {
    return null;
  }

  return {
    case_id: simulationSnapshot.case_id,
    simulation_id: simulationSnapshot.simulation_id,
    current_stage: simulationSnapshot.current_stage,
    opponent_name: readString(opponent?.opponent_name) ?? "对方当事人",
    opponent_role: formatPartyRoleLabel(readString(opponent?.opponent_role) ?? "defendant"),
    branch_focus:
      formatFocusLabel(readString(opponent?.branch_focus) ?? simulationSnapshot.branch_focus),
    likely_arguments: likelyArguments,
    likely_evidence: likelyEvidence,
    likely_strategies: likelyStrategies,
    likely_cross_examination_lines: likelyCrossExaminationLines,
    likely_legal_references: likelyLegalReferences,
    likely_reasoning_paths: likelyReasoningPaths,
    surprise_attack_actions: surpriseAttackActions,
    recommended_responses: recommendedResponses,
    risk_points: riskPoints,
    confidence: confidence ?? 0,
  };
}

export function normalizeOpponentSnapshot(
  snapshot: OpponentBehaviorSnapshot | null | undefined,
): OpponentBehaviorSnapshot | null {
  if (!snapshot) {
    return null;
  }

  return {
    ...snapshot,
    likely_arguments: snapshot.likely_arguments ?? [],
    likely_evidence: snapshot.likely_evidence ?? [],
    likely_strategies: snapshot.likely_strategies ?? [],
    likely_cross_examination_lines:
      snapshot.likely_cross_examination_lines ?? [],
    likely_legal_references: snapshot.likely_legal_references ?? [],
    likely_reasoning_paths: snapshot.likely_reasoning_paths ?? [],
    surprise_attack_actions: snapshot.surprise_attack_actions ?? [],
    recommended_responses: snapshot.recommended_responses ?? [],
    risk_points: snapshot.risk_points ?? [],
  };
}

export function mergeOpponentSnapshots(
  primary: OpponentBehaviorSnapshot | null | undefined,
  fallback: OpponentBehaviorSnapshot | null | undefined,
): OpponentBehaviorSnapshot | null {
  const normalizedPrimary = normalizeOpponentSnapshot(primary);
  const normalizedFallback = normalizeOpponentSnapshot(fallback);

  if (!normalizedPrimary) {
    return normalizedFallback;
  }

  if (!normalizedFallback) {
    return normalizedPrimary;
  }

  return {
    ...normalizedFallback,
    ...normalizedPrimary,
    opponent_name: normalizedPrimary.opponent_name || normalizedFallback.opponent_name,
    opponent_role: normalizedPrimary.opponent_role || normalizedFallback.opponent_role,
    branch_focus: normalizedPrimary.branch_focus || normalizedFallback.branch_focus,
    likely_arguments: mergeStringLists(
      normalizedPrimary.likely_arguments,
      normalizedFallback.likely_arguments,
    ),
    likely_evidence: mergeStringLists(
      normalizedPrimary.likely_evidence,
      normalizedFallback.likely_evidence,
    ),
    likely_strategies: mergeStringLists(
      normalizedPrimary.likely_strategies,
      normalizedFallback.likely_strategies,
    ),
    likely_cross_examination_lines: mergeStringLists(
      normalizedPrimary.likely_cross_examination_lines,
      normalizedFallback.likely_cross_examination_lines,
    ),
    likely_legal_references: mergeStringLists(
      normalizedPrimary.likely_legal_references,
      normalizedFallback.likely_legal_references,
    ),
    likely_reasoning_paths: mergeStringLists(
      normalizedPrimary.likely_reasoning_paths,
      normalizedFallback.likely_reasoning_paths,
    ),
    surprise_attack_actions: mergeStringLists(
      normalizedPrimary.surprise_attack_actions,
      normalizedFallback.surprise_attack_actions,
    ),
    recommended_responses: mergeStringLists(
      normalizedPrimary.recommended_responses,
      normalizedFallback.recommended_responses,
    ),
    risk_points: mergeStringLists(
      normalizedPrimary.risk_points,
      normalizedFallback.risk_points,
    ),
    confidence:
      normalizedPrimary.confidence > 0
        ? normalizedPrimary.confidence
        : normalizedFallback.confidence,
  };
}

export function deriveWinRateSnapshotFromSimulation(
  simulationSnapshot: SimulationSnapshot | null,
): WinRateAnalysisSnapshot | null {
  if (!simulationSnapshot) {
    return null;
  }

  const analysis = simulationSnapshot.analysis;
  const estimatedWinRate = readNumber(analysis?.estimated_win_rate);
  const confidence = readNumber(analysis?.confidence);
  const positiveFactors = readStringList(analysis?.positive_factors);
  const negativeFactors = readStringList(analysis?.negative_factors);
  const evidenceGapActions = readStringList(analysis?.evidence_gap_actions);
  const recommendedNextActions = readStringList(
    analysis?.recommended_next_actions,
  );
  const likelyOpponentLines = readStringList(analysis?.likely_opponent_lines);
  const stableResponseLines = readStringList(analysis?.stable_response_lines);
  const fallbackResponseLines = readStringList(analysis?.fallback_response_lines);
  const criticalEvidenceItems = readStringList(analysis?.critical_evidence_items);
  const legalReasoningNotes = readStringList(analysis?.legal_reasoning_notes);
  const topLossRisks = readStringList(analysis?.top_loss_risks);

  if (
    estimatedWinRate === null &&
    confidence === null &&
    positiveFactors.length === 0 &&
    negativeFactors.length === 0 &&
    evidenceGapActions.length === 0 &&
    recommendedNextActions.length === 0 &&
    likelyOpponentLines.length === 0 &&
    stableResponseLines.length === 0 &&
    fallbackResponseLines.length === 0 &&
    criticalEvidenceItems.length === 0 &&
    legalReasoningNotes.length === 0 &&
    topLossRisks.length === 0
  ) {
    return null;
  }

  return {
    case_id: simulationSnapshot.case_id,
    simulation_id: simulationSnapshot.simulation_id,
    current_stage: simulationSnapshot.current_stage,
    estimated_win_rate: estimatedWinRate ?? 0,
    confidence: confidence ?? 0,
    positive_factors: positiveFactors,
    negative_factors: negativeFactors,
    evidence_gap_actions: evidenceGapActions,
    recommended_next_actions: recommendedNextActions,
    likely_opponent_lines: likelyOpponentLines,
    stable_response_lines: stableResponseLines,
    fallback_response_lines: fallbackResponseLines,
    critical_evidence_items: criticalEvidenceItems,
    legal_reasoning_notes: legalReasoningNotes,
    top_loss_risks: topLossRisks,
  };
}

export function normalizeWinRateSnapshot(
  snapshot: WinRateAnalysisSnapshot | null | undefined,
): WinRateAnalysisSnapshot | null {
  if (!snapshot) {
    return null;
  }

  return {
    ...snapshot,
    positive_factors: snapshot.positive_factors ?? [],
    negative_factors: snapshot.negative_factors ?? [],
    evidence_gap_actions: snapshot.evidence_gap_actions ?? [],
    recommended_next_actions: snapshot.recommended_next_actions ?? [],
    likely_opponent_lines: snapshot.likely_opponent_lines ?? [],
    stable_response_lines: snapshot.stable_response_lines ?? [],
    fallback_response_lines: snapshot.fallback_response_lines ?? [],
    critical_evidence_items: snapshot.critical_evidence_items ?? [],
    legal_reasoning_notes: snapshot.legal_reasoning_notes ?? [],
    top_loss_risks: snapshot.top_loss_risks ?? [],
  };
}

export function mergeWinRateSnapshots(
  primary: WinRateAnalysisSnapshot | null | undefined,
  fallback: WinRateAnalysisSnapshot | null | undefined,
): WinRateAnalysisSnapshot | null {
  const normalizedPrimary = normalizeWinRateSnapshot(primary);
  const normalizedFallback = normalizeWinRateSnapshot(fallback);

  if (!normalizedPrimary) {
    return normalizedFallback;
  }

  if (!normalizedFallback) {
    return normalizedPrimary;
  }

  return {
    ...normalizedFallback,
    ...normalizedPrimary,
    estimated_win_rate:
      normalizedPrimary.estimated_win_rate > 0
        ? normalizedPrimary.estimated_win_rate
        : normalizedFallback.estimated_win_rate,
    confidence:
      normalizedPrimary.confidence > 0
        ? normalizedPrimary.confidence
        : normalizedFallback.confidence,
    positive_factors: mergeStringLists(
      normalizedPrimary.positive_factors,
      normalizedFallback.positive_factors,
    ),
    negative_factors: mergeStringLists(
      normalizedPrimary.negative_factors,
      normalizedFallback.negative_factors,
    ),
    evidence_gap_actions: mergeStringLists(
      normalizedPrimary.evidence_gap_actions,
      normalizedFallback.evidence_gap_actions,
    ),
    recommended_next_actions: mergeStringLists(
      normalizedPrimary.recommended_next_actions,
      normalizedFallback.recommended_next_actions,
    ),
    likely_opponent_lines: mergeStringLists(
      normalizedPrimary.likely_opponent_lines,
      normalizedFallback.likely_opponent_lines,
    ),
    stable_response_lines: mergeStringLists(
      normalizedPrimary.stable_response_lines,
      normalizedFallback.stable_response_lines,
    ),
    fallback_response_lines: mergeStringLists(
      normalizedPrimary.fallback_response_lines,
      normalizedFallback.fallback_response_lines,
    ),
    critical_evidence_items: mergeStringLists(
      normalizedPrimary.critical_evidence_items,
      normalizedFallback.critical_evidence_items,
    ),
    legal_reasoning_notes: mergeStringLists(
      normalizedPrimary.legal_reasoning_notes,
      normalizedFallback.legal_reasoning_notes,
    ),
    top_loss_risks: mergeStringLists(
      normalizedPrimary.top_loss_risks,
      normalizedFallback.top_loss_risks,
    ),
  };
}

export function deriveReplayReportFromSimulation(
  simulationSnapshot: SimulationSnapshot | null,
): ReplayReportSnapshot | null {
  if (!simulationSnapshot || simulationSnapshot.analysis.report_status !== "ready") {
    return null;
  }

  const rawReportOverview = readString(simulationSnapshot.analysis.report_overview);
  const reportOverview = looksLikeEnglishText(rawReportOverview)
    ? buildChineseReplayOverview(simulationSnapshot)
    : rawReportOverview;
  const reportSectionKeys = readStringList(
    simulationSnapshot.analysis.report_section_keys,
  );
  const stateSummaryLines = Object.entries(simulationSnapshot.hidden_state_summary).map(
    ([key, value]) => `${formatStateKeyLabel(key)}：${value}`,
  );
  const branchDecisions = [
    `当前阶段：${formatTrialStageLabel(simulationSnapshot.current_stage)}`,
    `主轴焦点：${formatFocusLabel(simulationSnapshot.branch_focus)}`,
    ...(simulationSnapshot.suggested_actions.length > 0
      ? [`建议动作：${simulationSnapshot.suggested_actions.join(" / ")}`]
      : []),
  ];
  const stagePath = [formatTrialStageLabel(simulationSnapshot.current_stage)];
  const reportSections = [
    {
      key: "overview",
      title: "复盘概览",
      items: reportOverview ? [reportOverview] : ["系统已生成复盘概览。"],
    },
    {
      key: "positive_factors",
      title: "有利因素",
      items: readStringList(simulationSnapshot.analysis.positive_factors),
    },
    {
      key: "negative_factors",
      title: "不利因素",
      items: readStringList(simulationSnapshot.analysis.negative_factors),
    },
    {
      key: "next_actions",
      title: "下一步建议",
      items: readStringList(simulationSnapshot.analysis.recommended_next_actions),
    },
  ].filter((section) => section.items.length > 0);

  return {
    case_id: simulationSnapshot.case_id,
    simulation_id: simulationSnapshot.simulation_id,
    report_title: "庭审复盘报告",
    generated_at: new Date().toISOString(),
    current_stage: simulationSnapshot.current_stage,
    stage_path: stagePath,
    branch_decisions: branchDecisions,
    state_summary: simulationSnapshot.hidden_state_summary,
    report_sections: reportSections,
    report_summary: reportOverview ?? "系统已准备复盘概览。",
    report_markdown: [
      "# 庭审复盘报告",
      "",
      reportOverview ?? "系统已准备复盘概览。",
      "",
      "## 状态摘要",
      ...(stateSummaryLines.length > 0 ? stateSummaryLines.map((item) => `- ${item}`) : ["- 暂无状态摘要"]),
      "",
      reportSectionKeys.length > 0
        ? `已生成章节：${reportSectionKeys.map(formatReportSectionLabel).join("、")}`
        : "已生成章节：概览、因素、建议",
    ].join("\n"),
  };
}

export function normalizeReplayReport(
  report: ReplayReportSnapshot | null | undefined,
): ReplayReportSnapshot | null {
  if (!report) {
    return null;
  }

  return {
    ...report,
    stage_path: report.stage_path ?? [],
    branch_decisions: report.branch_decisions ?? [],
    state_summary: report.state_summary ?? {},
    report_sections: report.report_sections ?? [],
  };
}

export function mergeReplayReports(
  primary: ReplayReportSnapshot | null | undefined,
  fallback: ReplayReportSnapshot | null | undefined,
): ReplayReportSnapshot | null {
  const normalizedPrimary = normalizeReplayReport(primary);
  const normalizedFallback = normalizeReplayReport(fallback);

  if (!normalizedPrimary) {
    return normalizedFallback;
  }

  if (!normalizedFallback) {
    return normalizedPrimary;
  }

  return {
    ...normalizedFallback,
    ...normalizedPrimary,
    stage_path:
      normalizedFallback.stage_path.length > 0
        ? normalizedFallback.stage_path
        : normalizedPrimary.stage_path,
    branch_decisions: mergeStringLists(
      normalizedPrimary.branch_decisions,
      normalizedFallback.branch_decisions,
    ),
    state_summary: {
      ...normalizedPrimary.state_summary,
      ...normalizedFallback.state_summary,
    },
    report_sections:
      normalizedFallback.report_sections.length > 0
        ? normalizedFallback.report_sections
        : normalizedPrimary.report_sections,
    report_summary:
      normalizedFallback.report_summary || normalizedPrimary.report_summary,
    report_markdown:
      normalizedFallback.report_markdown || normalizedPrimary.report_markdown,
  };
}

export function createLocalOpponentSnapshot(
  currentCase: CaseProfile,
  simulationSnapshot: SimulationSnapshot,
): OpponentBehaviorSnapshot {
  const recentUserInputs = getRecentSimulationUserInputs(simulationSnapshot);
  const defendantName =
    currentCase.opponent_profile?.display_name ??
    currentCase.parties.find((party) => party.role === "defendant")?.display_name ??
    "对方当事人";
  const inputDrivenLikelyArguments = recentUserInputs.map(
    buildLocalOpponentArgumentFromInput,
  );
  const inputDrivenLikelyEvidence = recentUserInputs
    .map(buildLocalEvidenceFocusFromInput)
    .filter((item): item is string => Boolean(item));
  const inputDrivenCrossExaminationLines = recentUserInputs.map((entry) =>
    buildLocalCrossExaminationFromInput(currentCase, entry),
  );
  const inputDrivenSurpriseActions = recentUserInputs.map(
    buildLocalSurpriseActionFromInput,
  );
  const inputDrivenResponses = recentUserInputs.map(buildLocalResponseFromInput);
  const inputDrivenRisks = recentUserInputs.map(buildLocalRiskFromInput);
  const inputDrivenConfidenceBoost = Math.min(
    recentUserInputs.reduce((total, entry) => total + getLocalUserInputBonus(entry), 0) * 0.012,
    0.12,
  );

  return {
    case_id: simulationSnapshot.case_id,
    simulation_id: simulationSnapshot.simulation_id,
    current_stage: simulationSnapshot.current_stage,
    opponent_name: defendantName,
    opponent_role: formatPartyRoleLabel("defendant"),
    branch_focus: formatFocusLabel(simulationSnapshot.branch_focus),
    likely_arguments: dedupeItems([
      ...inputDrivenLikelyArguments,
      ...(currentCase.opponent_profile?.likely_arguments.length
        ? currentCase.opponent_profile.likely_arguments
        : buildCaseTypeDefaultOpponentArguments(currentCase, simulationSnapshot)),
    ]),
    likely_evidence: dedupeItems([
      ...inputDrivenLikelyEvidence,
      ...(currentCase.opponent_profile?.likely_evidence.length
        ? currentCase.opponent_profile.likely_evidence
        : buildCaseTypeDefaultOpponentEvidence(currentCase)),
    ]),
    likely_strategies: dedupeItems([
      recentUserInputs.length > 0 ? "专盯你本轮新补材料的薄弱点施压" : "",
      ...(currentCase.opponent_profile?.likely_strategies.length
        ? currentCase.opponent_profile.likely_strategies
        : buildCaseTypeDefaultOpponentStrategies(currentCase)),
    ]),
    likely_cross_examination_lines: dedupeItems([
      ...inputDrivenCrossExaminationLines,
      ...buildStageDefaultCrossExaminationLines(currentCase, simulationSnapshot),
    ]),
    likely_legal_references: dedupeItems(
      buildCaseTypeLegalReferences(currentCase),
    ),
    likely_reasoning_paths: dedupeItems(
      buildCaseTypeReasoningPaths(currentCase, simulationSnapshot),
    ),
    surprise_attack_actions: dedupeItems([
      ...inputDrivenSurpriseActions,
      ...buildStageDefaultSurpriseActions(simulationSnapshot),
    ]),
    recommended_responses: dedupeItems([
      ...inputDrivenResponses,
      "围绕争议焦点逐项准备反驳材料。",
      "优先补齐最影响结论的证据缺口。",
      "把事实陈述压缩成时间线和证据线索两条主线。",
    ]),
    risk_points: dedupeItems([
      ...inputDrivenRisks,
      ...(currentCase.missing_evidence.length > 0
        ? currentCase.missing_evidence.slice(0, 3)
        : ["当前证据链较薄，容易被对方抓住举证不足。"]),
    ]),
    confidence: Number((0.72 + inputDrivenConfidenceBoost).toFixed(2)),
  };
}

export function createLocalWinRateSnapshot(
  currentCase: CaseProfile,
  simulationSnapshot: SimulationSnapshot,
  opponentSnapshot: OpponentBehaviorSnapshot | null,
): WinRateAnalysisSnapshot {
  const recentUserInputs = getRecentSimulationUserInputs(simulationSnapshot);
  const inputDrivenPositiveFactors = recentUserInputs.map(
    buildLocalPositiveFactorFromInput,
  );
  const inputDrivenNegativeFactors = recentUserInputs
    .filter((entry) => entry.input_type !== "evidence")
    .map(buildLocalRiskFromInput);
  const positiveFactors = dedupeItems([
    currentCase.claims[0] ? `主诉请明确：${currentCase.claims[0]}` : "主张方向较清晰。",
    currentCase.core_facts[0] ? `已有关键事实支撑：${currentCase.core_facts[0]}` : "事实主线已建立。",
    ...inputDrivenPositiveFactors,
  ]);
  const negativeFactors = dedupeItems([
    ...currentCase.missing_evidence.slice(0, 2).map((item) => `证据缺口：${item}`),
    ...(opponentSnapshot?.likely_arguments.slice(0, 1).map((item) => `对方可能抗辩：${item}`) ??
      []),
    ...inputDrivenNegativeFactors,
  ]);
  const likelyOpponentLines = dedupeItems([
    ...(opponentSnapshot?.likely_cross_examination_lines.slice(0, 2) ?? []),
    ...(opponentSnapshot?.likely_arguments.slice(0, 2) ?? []),
    ...(opponentSnapshot?.surprise_attack_actions.slice(0, 1) ?? []),
  ]);
  const stableResponseLines = dedupeItems([
    ...recentUserInputs
      .slice(-2)
      .map((entry) => buildUserInputDrivenStableResponse(currentCase, entry)),
    ...buildCaseTypeStableResponseLines(currentCase, simulationSnapshot),
  ]);
  const fallbackResponseLines = dedupeItems(
    buildCaseTypeFallbackResponseLines(currentCase, simulationSnapshot),
  );
  const criticalEvidenceItems = dedupeItems([
    ...currentCase.missing_evidence.slice(0, 4),
    ...recentUserInputs.map(buildLocalEvidenceGapActionFromInput),
  ]);
  const legalReasoningNotes = dedupeItems([
    ...buildCaseTypeLegalReasoningNotes(currentCase, simulationSnapshot),
    ...(opponentSnapshot?.likely_legal_references.slice(0, 2) ?? []),
  ]);
  const topLossRisks = dedupeItems([
    ...(opponentSnapshot?.risk_points.slice(0, 3) ?? []),
    ...inputDrivenNegativeFactors,
    ...currentCase.missing_evidence.slice(0, 2).map((item) => `若“${item}”补不上，法庭更可能认为你方举证尚未闭环。`),
  ]);

  const positiveScore = Math.min(positiveFactors.length, 3) * 8;
  const negativeScore = Math.min(negativeFactors.length, 3) * 10;
  const userInputBonus = recentUserInputs.reduce(
    (total, entry) => total + getLocalUserInputBonus(entry),
    0,
  );
  const estimated = Math.max(
    28,
    Math.min(86, 60 + positiveScore - negativeScore + userInputBonus),
  );

  return {
    case_id: simulationSnapshot.case_id,
    simulation_id: simulationSnapshot.simulation_id,
    current_stage: simulationSnapshot.current_stage,
    estimated_win_rate: estimated,
    confidence: Number(
      Math.min(0.82, 0.68 + recentUserInputs.length * 0.03).toFixed(2),
    ),
    positive_factors: positiveFactors,
    negative_factors: negativeFactors.length > 0 ? negativeFactors : ["暂无明显消极因素。"],
    evidence_gap_actions: dedupeItems([
      ...(currentCase.missing_evidence.length > 0
        ? currentCase.missing_evidence.slice(0, 3).map((item) => `尽快补齐：${item}`)
        : ["继续核实对方证据来源与证明力。"]),
      ...recentUserInputs.map(buildLocalEvidenceGapActionFromInput),
    ]),
    recommended_next_actions: dedupeItems([
      ...recentUserInputs.map(buildLocalResponseFromInput),
      "优先准备质证提纲。",
      "把关键事实按时间顺序重写成法庭陈述版本。",
      "对高风险争点预设三轮追问与回应。",
    ]),
    likely_opponent_lines:
      likelyOpponentLines.length > 0
        ? likelyOpponentLines
        : ["对方下一轮更可能继续围绕证据不足和事实闭环不完整施压。"],
    stable_response_lines:
      stableResponseLines.length > 0
        ? stableResponseLines
        : ["先把核心事实落到证据，再回应对方的法律评价。"],
    fallback_response_lines:
      fallbackResponseLines.length > 0
        ? fallbackResponseLines
        : ["即便法庭暂不完全采信现有主张，也应先固定无争议事实并继续补证。"],
    critical_evidence_items:
      criticalEvidenceItems.length > 0
        ? criticalEvidenceItems
        : ["继续补足证明链最薄弱的一环。"],
    legal_reasoning_notes:
      legalReasoningNotes.length > 0
        ? legalReasoningNotes
        : ["把法条和争议焦点逐项对应，不要只列名称。"],
    top_loss_risks:
      topLossRisks.length > 0
        ? topLossRisks
        : ["当前最大风险仍是核心事实缺少直接印证。"],
  };
}

export function createLocalReplayReport(
  currentCase: CaseProfile,
  simulationSnapshot: SimulationSnapshot,
  winRateSnapshot: WinRateAnalysisSnapshot | null,
  opponentSnapshot?: OpponentBehaviorSnapshot | null,
): ReplayReportSnapshot {
  const recentUserInputs = getRecentSimulationUserInputs(simulationSnapshot);
  const stagePath = ["案件录入", "庭审模拟", "对方推演", "胜诉率分析", "复盘报告"];
  const reportTitle = `${currentCase.title} · 庭审复盘报告`;
  const focusLabel = formatFocusLabel(simulationSnapshot.branch_focus);
  const estimatedWinRateLabel = winRateSnapshot
    ? formatPercent(winRateSnapshot.estimated_win_rate)
    : "待分析";
  const userInputSummaries = recentUserInputs.map((entry) => {
    const label = entry.label || formatLocalUserInputLabel(entry.input_type);
    return `${label}：${summarizeLocalUserInputEntry(entry, 42)}`;
  });
  const coreFact = currentCase.core_facts[0] ?? null;
  const positiveFactors = winRateSnapshot?.positive_factors.slice(0, 3) ?? [];
  const alreadyAnchoredCoreFact =
    coreFact !== null &&
    positiveFactors.some((item) => item.includes(coreFact));
  const keyObservations = dedupeItems([
    ...positiveFactors,
    ...recentUserInputs.map(buildLocalPositiveFactorFromInput),
    coreFact && !alreadyAnchoredCoreFact ? `已固定核心事实：${coreFact}` : "",
  ]);
  const pressurePoints = dedupeItems([
    ...(winRateSnapshot?.likely_opponent_lines?.slice(0, 4) ?? []),
    ...(opponentSnapshot?.surprise_attack_actions.slice(0, 2) ?? []),
    ...(winRateSnapshot?.top_loss_risks?.slice(0, 2) ?? []),
  ]);
  const evidenceChecklist = dedupeItems([
    ...(winRateSnapshot?.critical_evidence_items?.slice(0, 4) ?? []),
    ...(currentCase.missing_evidence.length > 0
      ? currentCase.missing_evidence.slice(0, 3)
      : ["继续核查现有证据的来源、时间和证明目的。"]),
  ]);
  const responseTemplates = dedupeItems([
    ...(winRateSnapshot?.stable_response_lines?.slice(0, 2) ?? []),
    ...(winRateSnapshot?.fallback_response_lines?.slice(0, 1) ?? []),
  ]);
  const primaryLegalNotes = winRateSnapshot?.legal_reasoning_notes?.slice(0, 3) ?? [];
  const legalNotes = dedupeItems([
    ...primaryLegalNotes,
    ...(primaryLegalNotes.length === 0
      ? opponentSnapshot?.likely_legal_references.slice(0, 1) ?? []
      : []),
  ]);
  const nextStepPlan = dedupeItems([
    ...(winRateSnapshot?.recommended_next_actions ?? []),
    "重新整理事实时间线。",
    "补齐关键证据。",
    "准备庭审发问与反驳稿。",
  ]);
  const stateSummary = {
    ...simulationSnapshot.hidden_state_summary,
    ...(recentUserInputs.length > 0
      ? { user_input_depth: `本轮共补入 ${simulationSnapshot.user_input_entries?.length ?? 0} 条材料` }
      : {}),
  };
  const branchDecisions = dedupeItems([
    `当前阶段：${formatTrialStageLabel(simulationSnapshot.current_stage)}`,
    `本轮焦点：${formatFocusLabel(simulationSnapshot.branch_focus)}`,
    `本轮动作池：${simulationSnapshot.available_actions.join("、") || "暂无"}`,
    ...(userInputSummaries.length > 0
      ? [`本轮新增输入：${userInputSummaries.join("；")}`]
      : []),
  ]);
  const reportSummary = [
    `本轮推演已经把争议收束到“${focusLabel}”。`,
    `当前估计胜诉率约 ${estimatedWinRateLabel}。`,
    evidenceChecklist[0] ? `下一轮最先要补的是：${evidenceChecklist[0]}。` : null,
    pressurePoints[0] ? `最需要防的压制点是：${pressurePoints[0]}。` : null,
  ]
    .filter((item): item is string => Boolean(item))
    .join("");
  const reportSections = [
    ...(userInputSummaries.length > 0
      ? [{ key: "user_inputs", title: "本轮新增材料", items: userInputSummaries }]
      : []),
    {
      key: "conclusion",
      title: "本轮结论",
      items: dedupeItems([
        `当前阶段：${formatTrialStageLabel(simulationSnapshot.current_stage)}`,
        `当前焦点：${focusLabel}`,
        `当前估计胜诉率：${estimatedWinRateLabel}`,
        ...(winRateSnapshot?.top_loss_risks?.[0]
          ? [`最大失分风险：${winRateSnapshot.top_loss_risks[0]}`]
          : []),
      ]),
    },
    { key: "effective_moves", title: "本轮有效动作", items: keyObservations },
    { key: "pressure_points", title: "对方压制点", items: pressurePoints },
    { key: "evidence", title: "下次开庭前必须补齐", items: evidenceChecklist },
    { key: "response_templates", title: "建议开口模板", items: responseTemplates },
    { key: "legal_notes", title: "可援引法条与说理", items: legalNotes },
    { key: "next_step", title: "下一步计划", items: nextStepPlan },
    { key: "path", title: "阶段路径", items: stagePath },
  ].filter((section) => section.items.length > 0);

  return {
    case_id: simulationSnapshot.case_id,
    simulation_id: simulationSnapshot.simulation_id,
    report_title: reportTitle,
    generated_at: new Date().toISOString(),
    current_stage: simulationSnapshot.current_stage,
    stage_path: stagePath,
    branch_decisions: branchDecisions,
    state_summary: stateSummary,
    report_sections: reportSections,
    report_summary: reportSummary,
    report_markdown: [
      `# ${reportTitle}`,
      "",
      reportSummary,
      "",
      "## 当前结论",
      `- 当前阶段：${formatTrialStageLabel(simulationSnapshot.current_stage)}`,
      `- 当前焦点：${focusLabel}`,
      `- 估计胜诉率：${estimatedWinRateLabel}`,
      "",
      "## 分支选择",
      ...branchDecisions.map((item) => `- ${item}`),
      ...(userInputSummaries.length > 0
        ? ["", "## 本轮新增材料", ...userInputSummaries.map((item) => `- ${item}`)]
        : []),
      "",
      "## 局面状态",
      ...Object.entries(stateSummary).map(([key, value]) => `- ${formatStateKeyLabel(key)}：${value}`),
      "",
      "## 关键观察",
      ...keyObservations.map((item) => `- ${item}`),
      "",
      "## 对方压制点",
      ...pressurePoints.map((item) => `- ${item}`),
      "",
      "## 证据补强清单",
      ...evidenceChecklist.map((item) => `- ${item}`),
      "",
      "## 建议开口模板",
      ...responseTemplates.map((item) => `- ${item}`),
      "",
      "## 可援引法条与说理",
      ...legalNotes.map((item) => `- ${item}`),
      "",
      "## 下一步计划",
      ...nextStepPlan.map((item) => `- ${item}`),
    ].join("\n"),
  };
}

export function parseStoredWorkspaceState(
  raw: string | null,
): PersistedWorkspaceState | null {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;

    return {
      draft: normalizeDraft(parsed.draft),
      currentCase: (parsed.currentCase as CaseProfile | null) ?? null,
      simulationSnapshot:
        (parsed.simulationSnapshot as SimulationSnapshot | null) ?? null,
      opponentSnapshot:
        (parsed.opponentSnapshot as OpponentBehaviorSnapshot | null) ?? null,
      winRateSnapshot:
        (parsed.winRateSnapshot as WinRateAnalysisSnapshot | null) ?? null,
      replayReport: (parsed.replayReport as ReplayReportSnapshot | null) ?? null,
      activeStage: isWorkspaceStage(parsed.activeStage) ? parsed.activeStage : "intake",
      sessionCases: Array.isArray(parsed.sessionCases)
        ? (parsed.sessionCases as SessionCaseRecord[])
        : [],
      isMockMode: Boolean(parsed.isMockMode),
    };
  } catch {
    return null;
  }
}

function normalizeDraft(value: unknown): CaseIntakeDraft {
  const base = createEmptyCaseIntakeDraft();
  const record = isRecord(value) ? value : {};

  return {
    domain: isCaseDomain(record.domain) ? record.domain : base.domain,
    case_type: isCaseType(record.case_type) ? record.case_type : base.case_type,
    title: typeof record.title === "string" ? record.title : base.title,
    summary: typeof record.summary === "string" ? record.summary : base.summary,
    user_perspective_role: isPerspectiveRole(record.user_perspective_role)
      ? record.user_perspective_role
      : base.user_perspective_role,
    user_goals: Array.isArray(record.user_goals)
      ? record.user_goals.filter(isUserGoal)
      : base.user_goals,
    plaintiff_name:
      typeof record.plaintiff_name === "string" ? record.plaintiff_name : base.plaintiff_name,
    defendant_name:
      typeof record.defendant_name === "string" ? record.defendant_name : base.defendant_name,
    claims_text: typeof record.claims_text === "string" ? record.claims_text : base.claims_text,
    core_facts_text:
      typeof record.core_facts_text === "string" ? record.core_facts_text : base.core_facts_text,
    focus_issues_text:
      typeof record.focus_issues_text === "string"
        ? record.focus_issues_text
        : base.focus_issues_text,
    missing_evidence_text:
      typeof record.missing_evidence_text === "string"
        ? record.missing_evidence_text
        : base.missing_evidence_text,
    notes: typeof record.notes === "string" ? record.notes : base.notes,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isWorkspaceStage(value: unknown): value is WorkspaceStage {
  return (
    value === "intake" ||
    value === "simulation" ||
    value === "opponent" ||
    value === "win_rate" ||
    value === "replay"
  );
}

function isCaseDomain(value: unknown): value is CaseDomain {
  return value === "civil" || value === "criminal" || value === "administrative";
}

function isCaseType(value: unknown): value is CaseType {
  return (
    value === "private_lending" ||
    value === "labor_dispute" ||
    value === "divorce_dispute" ||
    value === "tort_liability"
  );
}

function isPerspectiveRole(value: unknown): value is UserPerspectiveRole {
  return (
    value === "claimant_side" ||
    value === "respondent_side" ||
    value === "neutral_observer" ||
    value === "learner" ||
    value === "other"
  );
}

function isUserGoal(value: unknown): value is UserGoal {
  return (
    value === "simulate_trial" ||
    value === "analyze_win_rate" ||
    value === "prepare_checklist" ||
    value === "review_evidence"
  );
}
