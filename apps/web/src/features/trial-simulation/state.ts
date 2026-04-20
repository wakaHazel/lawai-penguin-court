import type { CaseProfile } from "../../types/case";
import type {
  SimulationActionCard,
  SimulationCheckpoint,
  SimulationHistoryItem,
  SimulationSnapshot,
  SimulationUserInputEntry,
  SimulationTurnRequest,
} from "../../types/turn";
import { getTrialStageMeta, TRIAL_STAGE_META } from "./stage-meta";

export interface TrialSimulationPageState {
  caseProfile: CaseProfile | null;
  snapshot: SimulationSnapshot | null;
  currentStageLabel: string;
  progressItems: Array<{
    stage: string;
    label: string;
    isCurrent: boolean;
    isCompleted: boolean;
  }>;
  history: SimulationHistoryItem[];
  checkpoints: SimulationCheckpoint[];
  hiddenStateSummary: Record<string, string>;
  currentTask: string;
  historyCount: number;
  actionCards: SimulationActionCard[];
  primaryActions: string[];
  secondaryActions: string[];
  suggestedActions: string[];
  nextStageHint: string | null;
  degradedFlags: string[];
  canAdvance: boolean;
}

export function createEmptyTrialSimulationPageState(): TrialSimulationPageState {
  return {
    caseProfile: null,
    snapshot: null,
    currentStageLabel: "尚未开始",
    progressItems: TRIAL_STAGE_META.map((item) => ({
      stage: item.stage,
      label: item.label,
      isCurrent: false,
      isCompleted: false,
    })),
    history: [],
    checkpoints: [],
    hiddenStateSummary: {},
    currentTask: "",
    historyCount: 0,
    actionCards: [],
    primaryActions: [],
    secondaryActions: [],
    suggestedActions: [],
    nextStageHint: null,
    degradedFlags: [],
    canAdvance: false,
  };
}

export function createIdleTrialSimulationPageState(
  caseProfile: CaseProfile,
): TrialSimulationPageState {
  return {
    ...createEmptyTrialSimulationPageState(),
    caseProfile,
  };
}

export function buildTrialSimulationPageState(
  caseProfile: CaseProfile,
  snapshot: SimulationSnapshot,
  history: SimulationHistoryItem[] = [],
  checkpoints: SimulationCheckpoint[] = [],
): TrialSimulationPageState {
  const currentMeta = getTrialStageMeta(snapshot.current_stage);
  const currentIndex = TRIAL_STAGE_META.findIndex(
    (item) => item.stage === snapshot.current_stage,
  );
  const availableActions = sanitizeTextList(snapshot.available_actions);
  const suggestedActions = sanitizeTextList(snapshot.suggested_actions);
  const actionPool = availableActions.length > 0 ? availableActions : suggestedActions;
  const primaryActions =
    snapshot.current_stage === "report_ready" ? [] : actionPool.slice(0, 3);
  const secondaryActions =
    snapshot.current_stage === "report_ready" ? [] : actionPool.slice(3);
  const nextStageHint = normalizeText(snapshot.next_stage_hint);
  const actionCards =
    Array.isArray(snapshot.action_cards) && snapshot.action_cards.length > 0
      ? snapshot.action_cards.filter((card) => card.action.trim().length > 0)
      : primaryActions.map((action, index) => ({
          action,
          intent: suggestedActions[index] ?? "",
          risk_tip: "",
          emphasis: index === 0 ? "critical" : "steady",
        }));

  return {
    caseProfile,
    snapshot,
    currentStageLabel: currentMeta.label,
    progressItems: TRIAL_STAGE_META.map((item, index) => ({
      stage: item.stage,
      label: item.label,
      isCurrent: item.stage === snapshot.current_stage,
      isCompleted: index < currentIndex,
    })),
    history,
    checkpoints,
    hiddenStateSummary: snapshot.hidden_state_summary,
    currentTask:
      normalizeText(snapshot.current_task) ??
      normalizeText(snapshot.choice_prompt) ??
      "当前回合尚未生成明确任务，请继续推进模拟。",
    historyCount: history.length,
    actionCards,
    primaryActions,
    secondaryActions,
    suggestedActions,
    nextStageHint,
    degradedFlags: sanitizeTextList(snapshot.degraded_flags),
    canAdvance:
      snapshot.current_stage !== "report_ready" &&
      actionPool.length > 0,
  };
}

export function buildSimulationTurnRequest(
  snapshot: SimulationSnapshot,
  selectedAction: string,
  selectedChoiceId?: string | null,
  userInputEntries: SimulationUserInputEntry[] = [],
): SimulationTurnRequest {
  return {
    simulation_id: snapshot.simulation_id,
    current_stage: snapshot.current_stage,
    turn_index: snapshot.turn_index,
    selected_action: selectedAction,
    selected_choice_id: selectedChoiceId ?? null,
    user_input_entries: userInputEntries,
  };
}

function sanitizeTextList(items: string[] | undefined): string[] {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function normalizeText(value: string | null | undefined): string | null {
  if (typeof value !== "string") {
    return null;
  }

  const normalized = value.trim();
  return normalized.length > 0 ? normalized : null;
}
