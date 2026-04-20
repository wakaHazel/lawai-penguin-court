import { startTransition, useEffect, useState } from "react";

import type { CaseProfile } from "../../types/case";
import type {
  SimulationActionCard,
  SimulationCgScene,
  SimulationCheckpoint,
  SimulationHistoryItem,
  SimulationSnapshot,
  SimulationUserInputEntry,
  SimulationUserInputType,
  TrialStage,
} from "../../types/turn";
import {
  advanceSimulationTurn,
  getCaseDetail,
  getLatestSimulation,
  getSimulationCheckpoints,
  getSimulationHistory,
  resumeSimulationFromCheckpoint,
  startSimulation,
} from "../../services/api/cases";
import { ApiRequestError } from "../../services/api/client";
import {
  buildSimulationTurnRequest,
  buildTrialSimulationPageState,
  createEmptyTrialSimulationPageState,
  createIdleTrialSimulationPageState,
  type TrialSimulationPageState,
} from "./state";
import { getTrialStageMeta } from "./stage-meta";
import {
  formatSimulationUserInputTypeLabel,
  summarizeSimulationUserInputEntry,
} from "./supplemental-inputs";

export interface UseTrialSimulationControllerOptions {
  caseId: string;
  autoStart?: boolean;
  initialSnapshot?: SimulationSnapshot | null;
  initialCaseProfile?: CaseProfile | null;
  preferMock?: boolean;
}

export interface TrialSimulationControllerResult {
  pageState: TrialSimulationPageState;
  isLoading: boolean;
  errorMessage: string | null;
  startSimulationSession: () => Promise<void>;
  advanceWithAction: (
    selectedAction: string,
    selectedChoiceId?: string | null,
    pendingInput?: {
      inputType: SimulationUserInputType;
      content: string;
    } | null,
  ) => Promise<void>;
  resumeFromCheckpoint: (checkpointId: string) => Promise<void>;
  reloadCase: () => Promise<void>;
  saveSupplementInput: (
    inputType: SimulationUserInputType,
    content: string,
  ) => void;
  removeSupplementInput: (entryId: string) => void;
}

const MOCK_STAGE_ORDER: TrialStage[] = [
  "prepare",
  "investigation",
  "evidence",
  "debate",
  "final_statement",
  "mediation_or_judgment",
  "report_ready",
];

const autoStartInFlightByCaseId = new Map<string, Promise<SimulationSnapshot>>();

const MOCK_STAGE_ACTIONS: Record<TrialStage, string[]> = {
  prepare: ["申请法庭明确争议焦点", "按时间线重述案件主线", "申请调取关键材料"],
  investigation: ["先讲核心事实再锁争点", "请求法官围绕关键关系发问", "针对对方版本逐点追问"],
  evidence: ["对对方证据提出三性质疑", "申请核验原始载体", "补强证据之间的对应关系"],
  debate: ["按构成要件展开论证", "逐项反驳对方抗辩", "压成结论+证据+法条"],
  final_statement: ["用一句话重申诉请", "强调最关键证据链", "提醒法庭先处理核心争点"],
  mediation_or_judgment: ["明确是否接受调解", "提出可接受边界", "请求依法尽快作出判断"],
  report_ready: [],
};

const MOCK_SUGGESTED_ACTIONS: Record<TrialStage, string[]> = {
  prepare: ["先让法官记住本案真正要先回答的问题", "不要一开口就把事实和评价混在一起"],
  investigation: ["每说一个事实，都预留给法官追问的空间", "优先说能直接改变心证的事实节点"],
  evidence: ["所有材料都按来源、形成时间、证明目的说清", "不要让任何一份证据孤零零悬在半空"],
  debate: ["每一轮反驳都回到证据和法条，不打空论", "宁可少讲一点，也要把主线守牢"],
  final_statement: ["最后陈述只保留主请求和最强支撑", "此时不再横向扩题"],
  mediation_or_judgment: ["先分清哪些条件能谈，哪些条件不能退", "别为了快速收束先把核心利益让掉"],
  report_ready: [],
};

export function useTrialSimulationController(
  options: UseTrialSimulationControllerOptions,
): TrialSimulationControllerResult {
  const [caseProfile, setCaseProfile] = useState<CaseProfile | null>(
    options.initialCaseProfile ?? null,
  );
  const [snapshot, setSnapshot] = useState<SimulationSnapshot | null>(
    options.initialSnapshot ?? null,
  );
  const [history, setHistory] = useState<SimulationHistoryItem[]>([]);
  const [checkpoints, setCheckpoints] = useState<SimulationCheckpoint[]>([]);
  const [pageState, setPageState] = useState<TrialSimulationPageState>(
    createEmptyTrialSimulationPageState(),
  );
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function initialize(): Promise<void> {
      setIsLoading(true);
      setErrorMessage(null);

      const shouldUseMock =
        options.preferMock || options.caseId.startsWith("MOCK-");
      const localCaseProfile = options.initialCaseProfile ?? null;
      const localSnapshot = options.initialSnapshot ?? null;

      if (shouldUseMock && localCaseProfile) {
        const nextSnapshot =
          localSnapshot ??
          ((options.autoStart ?? true)
            ? createMockSimulationStartSnapshot(localCaseProfile, options.caseId)
            : null);
        const nextHistory = nextSnapshot
          ? buildMockHistory([nextSnapshot])
          : [];

        if (!cancelled) {
          applyResolvedState({
            profile: localCaseProfile,
            nextSnapshot,
            nextHistory,
            nextCheckpoints: [],
            setCaseProfile,
            setSnapshot,
            setHistory,
            setCheckpoints,
            setPageState,
          });
          setIsLoading(false);
        }
        return;
      }

      try {
        const resolvedCase = localCaseProfile ?? (await getCaseDetail(options.caseId));
        if (cancelled) {
          return;
        }

        const resolvedSnapshot = await resolveInitialSnapshot({
          caseId: options.caseId,
          autoStart: options.autoStart ?? true,
          localSnapshot,
          resolvedCaseId: resolvedCase.case_id,
        });

        const artifacts = await loadRunArtifacts({
          caseId: options.caseId,
          nextSnapshot: resolvedSnapshot,
          shouldUseMock: false,
        });

        if (!cancelled) {
          applyResolvedState({
            profile: resolvedCase,
            nextSnapshot: resolvedSnapshot,
            nextHistory: artifacts.history,
            nextCheckpoints: artifacts.checkpoints,
            setCaseProfile,
            setSnapshot,
            setHistory,
            setCheckpoints,
            setPageState,
          });
        }
      } catch (error) {
        if (!cancelled && localCaseProfile) {
          const fallbackSnapshot =
            localSnapshot ??
            ((options.autoStart ?? true)
              ? createMockSimulationStartSnapshot(localCaseProfile, options.caseId)
              : null);
          const nextHistory = fallbackSnapshot
            ? buildMockHistory([fallbackSnapshot])
            : [];

          applyResolvedState({
            profile: localCaseProfile,
            nextSnapshot: fallbackSnapshot,
            nextHistory,
            nextCheckpoints: [],
            setCaseProfile,
            setSnapshot,
            setHistory,
            setCheckpoints,
            setPageState,
          });
        } else if (!cancelled) {
          setCaseProfile(null);
          setSnapshot(null);
          setHistory([]);
          setCheckpoints([]);
          startTransition(() => {
            setPageState(createEmptyTrialSimulationPageState());
          });
          setErrorMessage(getErrorMessage(error));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void initialize();

    return () => {
      cancelled = true;
    };
  }, [
    options.autoStart,
    options.caseId,
    options.initialCaseProfile,
    options.initialSnapshot,
    options.preferMock,
  ]);

  async function reloadCase(): Promise<void> {
    setIsLoading(true);
    setErrorMessage(null);

    const shouldUseMock =
      options.preferMock ||
      options.caseId.startsWith("MOCK-") ||
      caseProfile?.case_id?.startsWith("MOCK-") === true;

    try {
      const loadedCase = caseProfile ?? (await getCaseDetail(options.caseId));
      const nextSnapshot = shouldUseMock
        ? snapshot
        : await resolveInitialSnapshot({
            caseId: options.caseId,
            autoStart: options.autoStart ?? true,
            localSnapshot: snapshot,
            resolvedCaseId: loadedCase.case_id,
          });
      const artifacts = await loadRunArtifacts({
        caseId: options.caseId,
        nextSnapshot,
        shouldUseMock,
        localHistory: history,
      });

      applyResolvedState({
        profile: loadedCase,
        nextSnapshot,
        nextHistory: artifacts.history,
        nextCheckpoints: artifacts.checkpoints,
        setCaseProfile,
        setSnapshot,
        setHistory,
        setCheckpoints,
        setPageState,
      });
    } catch (error) {
      if (caseProfile) {
        applyResolvedState({
          profile: caseProfile,
          nextSnapshot: snapshot,
          nextHistory: history,
          nextCheckpoints: checkpoints,
          setCaseProfile,
          setSnapshot,
          setHistory,
          setCheckpoints,
          setPageState,
        });
      } else {
        setErrorMessage(getErrorMessage(error));
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function startSimulationSession(): Promise<void> {
    if (!caseProfile) {
      setErrorMessage("请先载入案件，再开始庭审模拟。");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    const shouldUseMock =
      options.preferMock ||
      options.caseId.startsWith("MOCK-") ||
      caseProfile.case_id?.startsWith("MOCK-") === true;

    try {
      const initialSnapshot = shouldUseMock
        ? createMockSimulationStartSnapshot(caseProfile, options.caseId)
        : await startSimulation(options.caseId);
      const artifacts = await loadRunArtifacts({
        caseId: options.caseId,
        nextSnapshot: initialSnapshot,
        shouldUseMock,
      });

      applyResolvedState({
        profile: caseProfile,
        nextSnapshot: initialSnapshot,
        nextHistory: artifacts.history,
        nextCheckpoints: artifacts.checkpoints,
        setCaseProfile,
        setSnapshot,
        setHistory,
        setCheckpoints,
        setPageState,
      });
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  async function advanceWithAction(
    selectedAction: string,
    selectedChoiceId?: string | null,
    pendingInput?: {
      inputType: SimulationUserInputType;
      content: string;
    } | null,
  ): Promise<void> {
    if (!caseProfile || !snapshot) {
      setErrorMessage("请先进入一个有效的庭审阶段。");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    const shouldUseMock =
      options.preferMock ||
      options.caseId.startsWith("MOCK-") ||
      caseProfile.case_id?.startsWith("MOCK-") === true;
    const nextUserInputEntries = appendSimulationUserInput(
      snapshot,
      pendingInput ?? null,
    );

    try {
      const nextSnapshot = shouldUseMock
        ? createNextMockSimulationSnapshot(
            caseProfile,
            snapshot,
            selectedAction,
            nextUserInputEntries,
          )
        : mergeServerUserInputState(
            await advanceSimulationTurn(
              options.caseId,
              buildSimulationTurnRequest(
                snapshot,
                selectedAction,
                selectedChoiceId,
                nextUserInputEntries,
              ),
            ),
            nextUserInputEntries,
          );
      const artifacts = await loadRunArtifacts({
        caseId: options.caseId,
        nextSnapshot,
        shouldUseMock,
        localHistory: history,
      });

      applyResolvedState({
        profile: caseProfile,
        nextSnapshot,
        nextHistory: artifacts.history,
        nextCheckpoints: artifacts.checkpoints,
        setCaseProfile,
        setSnapshot,
        setHistory,
        setCheckpoints,
        setPageState,
      });
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  async function resumeFromCheckpoint(checkpointId: string): Promise<void> {
    if (!caseProfile || !snapshot) {
      setErrorMessage("当前没有可恢复的推演会话。");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const resumedSnapshot = await resumeSimulationFromCheckpoint(
        options.caseId,
        checkpointId,
      );
      const artifacts = await loadRunArtifacts({
        caseId: options.caseId,
        nextSnapshot: resumedSnapshot,
        shouldUseMock: false,
      });

      applyResolvedState({
        profile: caseProfile,
        nextSnapshot: resumedSnapshot,
        nextHistory: artifacts.history,
        nextCheckpoints: artifacts.checkpoints,
        setCaseProfile,
        setSnapshot,
        setHistory,
        setCheckpoints,
        setPageState,
      });
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  function saveSupplementInput(
    inputType: SimulationUserInputType,
    content: string,
  ): void {
    if (!caseProfile || !snapshot) {
      setErrorMessage("请先进入一个有效的庭审阶段。");
      return;
    }

    const nextEntries = appendSimulationUserInput(snapshot, {
      inputType,
      content,
    });
    const nextSnapshot = {
      ...snapshot,
      user_input_entries: nextEntries,
      hidden_state_summary: {
        ...snapshot.hidden_state_summary,
        user_input_depth: `已写入 ${nextEntries.length} 条`,
      },
    };

    applyResolvedState({
      profile: caseProfile,
      nextSnapshot,
      nextHistory: history,
      nextCheckpoints: checkpoints,
      setCaseProfile,
      setSnapshot,
      setHistory,
      setCheckpoints,
      setPageState,
    });
  }

  function removeSupplementInput(entryId: string): void {
    if (!caseProfile || !snapshot) {
      return;
    }

    const nextEntries = (snapshot.user_input_entries ?? []).filter(
      (entry) => entry.entry_id !== entryId,
    );
    const nextSnapshot = {
      ...snapshot,
      user_input_entries: nextEntries,
      hidden_state_summary: {
        ...snapshot.hidden_state_summary,
        ...(nextEntries.length > 0
          ? { user_input_depth: `已写入 ${nextEntries.length} 条` }
          : { user_input_depth: "尚未补充" }),
      },
    };

    applyResolvedState({
      profile: caseProfile,
      nextSnapshot,
      nextHistory: history,
      nextCheckpoints: checkpoints,
      setCaseProfile,
      setSnapshot,
      setHistory,
      setCheckpoints,
      setPageState,
    });
  }

  return {
    pageState,
    isLoading,
    errorMessage,
    startSimulationSession,
    advanceWithAction,
    resumeFromCheckpoint,
    reloadCase,
    saveSupplementInput,
    removeSupplementInput,
  };
}

async function resolveInitialSnapshot(options: {
  caseId: string;
  autoStart: boolean;
  localSnapshot: SimulationSnapshot | null;
  resolvedCaseId: string | null;
}): Promise<SimulationSnapshot | null> {
  try {
    const latestSnapshot = await getLatestSimulation(options.caseId);
    if (latestSnapshot) {
      return latestSnapshot;
    }
  } catch (error) {
    if (
      !options.localSnapshot ||
      options.localSnapshot.case_id !== options.resolvedCaseId
    ) {
      throw error;
    }
  }

  if (
    options.localSnapshot &&
    options.localSnapshot.case_id === options.resolvedCaseId
  ) {
    return options.localSnapshot;
  }

  if (!options.autoStart) {
    return null;
  }

  return startSimulationOnce(options.caseId);
}

function startSimulationOnce(caseId: string): Promise<SimulationSnapshot> {
  const existingRequest = autoStartInFlightByCaseId.get(caseId);
  if (existingRequest) {
    return existingRequest;
  }

  const nextRequest = startSimulation(caseId).finally(() => {
    autoStartInFlightByCaseId.delete(caseId);
  });
  autoStartInFlightByCaseId.set(caseId, nextRequest);
  return nextRequest;
}

async function loadRunArtifacts(options: {
  caseId: string;
  nextSnapshot: SimulationSnapshot | null;
  shouldUseMock: boolean;
  localHistory?: SimulationHistoryItem[];
}): Promise<{
  history: SimulationHistoryItem[];
  checkpoints: SimulationCheckpoint[];
}> {
  if (!options.nextSnapshot) {
    return { history: [], checkpoints: [] };
  }

  if (options.shouldUseMock) {
    return {
      history: buildMockHistoryFromItems(options.localHistory, options.nextSnapshot),
      checkpoints: [],
    };
  }

  try {
    const [history, checkpoints] = await Promise.all([
      getSimulationHistory(options.caseId, options.nextSnapshot.simulation_id),
      getSimulationCheckpoints(options.caseId, options.nextSnapshot.simulation_id),
    ]);
    return { history, checkpoints };
  } catch {
    return { history: [], checkpoints: [] };
  }
}

function applyResolvedState(options: {
  profile: CaseProfile;
  nextSnapshot: SimulationSnapshot | null;
  nextHistory: SimulationHistoryItem[];
  nextCheckpoints: SimulationCheckpoint[];
  setCaseProfile: (profile: CaseProfile | null) => void;
  setSnapshot: (snapshot: SimulationSnapshot | null) => void;
  setHistory: (history: SimulationHistoryItem[]) => void;
  setCheckpoints: (checkpoints: SimulationCheckpoint[]) => void;
  setPageState: (value: TrialSimulationPageState) => void;
}): void {
  options.setCaseProfile(options.profile);
  options.setSnapshot(options.nextSnapshot);
  options.setHistory(options.nextHistory);
  options.setCheckpoints(options.nextCheckpoints);
  startTransition(() => {
    options.setPageState(
      options.nextSnapshot
        ? buildTrialSimulationPageState(
            options.profile,
            options.nextSnapshot,
            options.nextHistory,
            options.nextCheckpoints,
          )
        : createIdleTrialSimulationPageState(options.profile),
    );
  });
}

function createMockSimulationStartSnapshot(
  caseProfile: CaseProfile,
  caseId: string,
): SimulationSnapshot {
  return createMockSimulationSnapshot({
    caseProfile,
    caseId,
    stage: "prepare",
    turnIndex: 1,
    selectedAction: "开始模拟",
    userInputEntries: [],
  });
}

function createNextMockSimulationSnapshot(
  caseProfile: CaseProfile,
  currentSnapshot: SimulationSnapshot,
  selectedAction: string,
  userInputEntries: SimulationUserInputEntry[],
): SimulationSnapshot {
  const currentIndex = MOCK_STAGE_ORDER.findIndex(
    (stage) => stage === currentSnapshot.current_stage,
  );
  const nextStage =
    currentIndex >= 0 && currentIndex < MOCK_STAGE_ORDER.length - 1
      ? MOCK_STAGE_ORDER[currentIndex + 1]
      : "report_ready";

  return createMockSimulationSnapshot({
    caseProfile,
    caseId: currentSnapshot.case_id,
    simulationId: currentSnapshot.simulation_id,
    stage: nextStage,
    turnIndex: currentSnapshot.turn_index + 1,
    selectedAction,
    userInputEntries,
  });
}

function createMockSimulationSnapshot(options: {
  caseProfile: CaseProfile;
  caseId: string;
  simulationId?: string;
  stage: TrialStage;
  turnIndex: number;
  selectedAction: string;
  userInputEntries: SimulationUserInputEntry[];
}): SimulationSnapshot {
  const simulationId = options.simulationId ?? `MOCK-SIM-${Date.now()}`;
  const stageMeta = getTrialStageMeta(options.stage);
  const branchFocus = pickBranchFocus(options.caseProfile, options.turnIndex);
  const sceneTitle = `${options.caseProfile.title || "模拟案件"} · ${stageMeta.label}`;
  const speakerRole = pickSpeakerRole(options.stage);
  const cgScene = buildMockCgScene({
    caseProfile: options.caseProfile,
    stage: options.stage,
    selectedAction: options.selectedAction,
    branchFocus,
    speakerRole,
  });
  const sceneText = buildMockSceneText({
    caseProfile: options.caseProfile,
    stage: options.stage,
    selectedAction: options.selectedAction,
    branchFocus,
    userInputEntries: options.userInputEntries,
  });
  const suggestedActions = MOCK_SUGGESTED_ACTIONS[options.stage];
  const nextStageHint = getNextStageHint(options.stage);
  const baseSnapshot: SimulationSnapshot = {
    simulation_id: simulationId,
    case_id: options.caseId,
    current_stage: options.stage,
    turn_index: options.turnIndex,
    node_id: `MOCK-${options.stage.toUpperCase()}-${options.turnIndex}`,
    branch_focus: branchFocus,
    scene_title: sceneTitle,
    scene_text: sceneText,
    cg_caption: cgScene.caption ?? buildMockCgCaption(stageMeta.label, options.selectedAction),
    cg_scene: cgScene,
    court_progress: buildMockCourtProgress(options.caseProfile, options.stage, branchFocus),
    pressure_shift: buildMockPressureShift(options.stage, options.selectedAction, branchFocus),
    stage_objective: buildMockStageObjective(options.stage),
    current_task: buildMockCurrentTask({
      caseProfile: options.caseProfile,
      stage: options.stage,
      branchFocus,
      selectedAction: options.selectedAction,
    }),
    choice_prompt: buildMockChoicePrompt(options.stage),
    hidden_state_summary: {
      evidence_strength: pickEvidenceStrength(options.stage),
      procedure_control: pickProcedureControl(options.stage),
      judge_trust: pickJudgeTrust(options.stage),
      opponent_pressure: pickOpponentPressure(options.stage),
      contradiction_risk: pickContradictionRisk(options.stage),
      surprise_exposure: pickSurpriseExposure(options.stage),
      settlement_tendency: pickSettlementTendency(options.stage),
    },
    speaker_role: speakerRole,
    available_actions: MOCK_STAGE_ACTIONS[options.stage],
    action_cards: buildMockActionCards(options.stage, MOCK_STAGE_ACTIONS[options.stage]),
    suggested_actions: suggestedActions,
    next_stage_hint: nextStageHint,
    legal_support: {
      retrieval_mode: "mock-local",
      recommended_queries: buildMockQueries(options.caseProfile, branchFocus),
      focus_issues: options.caseProfile.focus_issues,
      missing_evidence: options.caseProfile.missing_evidence,
      legal_support_summary: `当前重点仍是“${branchFocus}”。本地兜底模式建议优先围绕争议焦点、诉请依据和证据缺口做法律检索准备。`,
      referenced_laws: [],
      referenced_cases: [],
    },
    opponent: {
      opponent_name: options.caseProfile.opponent_profile?.display_name ?? "对方当事人",
      opponent_role: options.caseProfile.opponent_profile?.role ?? "respondent",
      branch_focus: branchFocus,
      likely_arguments: buildMockOpponentArguments(options.caseProfile, branchFocus),
      likely_evidence: options.caseProfile.missing_evidence
        .slice(0, 2)
        .map((item) => `围绕“${item}”反向解释现有证据`),
      likely_strategies: buildMockOpponentStrategies(options.stage),
      likely_cross_examination_lines: buildMockCrossExaminationLines(
        options.caseProfile,
        options.stage,
        branchFocus,
      ),
      likely_legal_references: buildMockOpponentLegalReferences(
        options.caseProfile,
      ),
      likely_reasoning_paths: buildMockOpponentReasoningPaths(
        options.caseProfile,
        options.stage,
        branchFocus,
      ),
      surprise_attack_actions: buildMockSurpriseActions(
        options.stage,
        options.caseProfile,
        branchFocus,
      ),
      recommended_responses: suggestedActions,
      risk_points: buildMockRiskPoints(options.caseProfile),
      confidence: 0.58,
    },
    analysis: {
      estimated_win_rate: estimateMockWinRate(options.caseProfile, options.stage),
      confidence: 0.56,
      positive_factors: buildMockPositiveFactors(options.caseProfile),
      negative_factors: buildMockNegativeFactors(options.caseProfile),
      evidence_gap_actions: options.caseProfile.missing_evidence.map(
        (item) => `补强：${item}`,
      ),
      recommended_next_actions: suggestedActions,
    },
    degraded_flags: [],
    yuanqi_branch_name: null,
    workflow_hints: [
      {
        workflow_key: "courtroom_scene_generation",
        workflow_version: "mock-local-v2",
        variables: {
          current_stage: options.stage,
        selected_action: options.selectedAction,
        branch_focus: branchFocus,
        case_type: options.caseProfile.case_type,
      },
      },
      {
        workflow_key: "legal_support_retrieval",
        workflow_version: "mock-local-v2",
        variables: {
          focus_issues: options.caseProfile.focus_issues,
          claims: options.caseProfile.claims,
          missing_evidence: options.caseProfile.missing_evidence,
        },
      },
    ],
  };

  return applyUserInputDrivenEnhancements(
    baseSnapshot,
    options.caseProfile,
    options.userInputEntries,
  );
}

function buildMockSceneText(options: {
  caseProfile: CaseProfile;
  stage: TrialStage;
  selectedAction: string;
  branchFocus: string;
  userInputEntries: SimulationUserInputEntry[];
}): string {
  const latestInput = options.userInputEntries[options.userInputEntries.length - 1] ?? null;
  const judgeQuestion = enrichJudgeQuestionWithLatestInput(
    buildMockJudgeQuestion(
      options.caseProfile,
      options.stage,
      options.branchFocus,
      options.selectedAction,
    ),
    latestInput,
    options.branchFocus,
  );
  const opponentMove = enrichOpponentMoveWithLatestInput(
    buildMockOpponentCourtMove(
      options.caseProfile,
      options.stage,
      options.branchFocus,
      options.selectedAction,
    ),
    latestInput,
  );
  const actionImpact = enrichActionImpactWithLatestInput(
    buildMockActionCourtImpact(
      options.caseProfile,
      options.stage,
      options.selectedAction,
      options.branchFocus,
    ),
    latestInput,
  );

  return [
    `【庭上动态：${buildMockStageDynamicNarrative(options.caseProfile, options.stage, options.branchFocus)}】`,
    `【法官发问：${judgeQuestion}】`,
    `【对方动作：${opponentMove}】`,
    `【你的动作影响：${actionImpact}】`,
  ]
    .join("");
}

function enrichJudgeQuestionWithLatestInput(
  baseText: string,
  latestInput: SimulationUserInputEntry | null,
  branchFocus: string,
): string {
  if (!latestInput) {
    return baseText;
  }

  const summary = summarizeSimulationUserInputEntry(latestInput, 22);

  switch (latestInput.input_type) {
    case "fact":
      return `${baseText} 另外，你刚补入的事实“${summary}”请说明由谁知晓、靠什么印证，并直接对应到“${branchFocus}”。`;
    case "evidence":
      return `${baseText} 另外，你刚补入的证据“${summary}”先把来源、形成时间和证明目的说清。`;
    case "cross_exam":
      return `${baseText} 你刚补入的质证意见“${summary}”现在要明确落在真实性、合法性、关联性还是证明目的上。`;
    case "procedure_request":
      return `${baseText} 你刚补入的程序申请“${summary}”要直接说明必要性和待证事实，否则本庭不会展开。`;
    case "argument":
      return `${baseText} 你刚补入的主张“${summary}”请对应到具体证据和法条。`;
    case "closing_statement":
      return `${baseText} 你刚补入的最后陈述“${summary}”只保留最能影响裁判的一句。`;
    case "settlement_position":
      return `${baseText} 你刚补入的调解底线“${summary}”会直接影响本庭是否继续组织调解。`;
    default:
      return baseText;
  }
}

function enrichOpponentMoveWithLatestInput(
  baseText: string,
  latestInput: SimulationUserInputEntry | null,
): string {
  if (!latestInput) {
    return baseText;
  }

  const summary = summarizeSimulationUserInputEntry(latestInput, 20);

  switch (latestInput.input_type) {
    case "fact":
      return `${baseText} 对方已经表示会把你这条新事实“${summary}”解释成个别协作场景，不承认它能推出持续管理。`;
    case "evidence":
      return `${baseText} 对方马上会咬住新证据“${summary}”的形成时间、原始载体和完整性，不会让它直接并入证明链。`;
    case "cross_exam":
      return `${baseText} 对方会顺着你那条质证意见“${summary}”补解释、补备注，尽量把材料重新扶稳。`;
    case "procedure_request":
      return `${baseText} 对方会反对你这项程序申请“${summary}”，主张与你要证明的事实关联不足，或者你本可自行取得。`;
    case "argument":
      return `${baseText} 对方会抓住你新补的论点“${summary}”里证据对应还不够满的地方反打。`;
    case "closing_statement":
      return `${baseText} 对方会把你新留下的结论“${summary}”拆成一句立场表达，而不是完整证明。`;
    case "settlement_position":
      return `${baseText} 对方会把你刚露出的底线“${summary}”当成下一口试探和压价的起点。`;
    default:
      return baseText;
  }
}

function enrichActionImpactWithLatestInput(
  baseText: string,
  latestInput: SimulationUserInputEntry | null,
): string {
  if (!latestInput) {
    return baseText;
  }

  const summary = summarizeSimulationUserInputEntry(latestInput, 18);

  switch (latestInput.input_type) {
    case "evidence":
    case "cross_exam":
      return `${baseText} 你刚补入的${latestInput.label}“${summary}”已经不是备注，而是下一轮必须正面接住的证据点。`;
    case "procedure_request":
      return `${baseText} 你刚补入的程序动作“${summary}”会让庭审节奏先偏到必要性和是否准许上。`;
    default:
      return `${baseText} 你刚补入的${latestInput.label}“${summary}”也会一起进入法官这一轮的判断。`;
  }
}

function pickPreferredFocusIssue(caseProfile: CaseProfile): string | null {
  const focusIssues = caseProfile.focus_issues.filter((item) => item.trim().length > 0);
  if (focusIssues.length === 0) {
    return null;
  }

  if (caseProfile.case_type === "labor_dispute") {
    return (
      focusIssues.find((item) => item.includes("劳动关系")) ??
      focusIssues.find((item) => item.includes("劳动")) ??
      focusIssues[0]
    );
  }

  if (caseProfile.case_type === "private_lending") {
    return (
      focusIssues.find((item) => item.includes("借贷")) ??
      focusIssues.find((item) => item.includes("借款")) ??
      focusIssues[0]
    );
  }

  if (caseProfile.case_type === "divorce_dispute") {
    return (
      focusIssues.find((item) => item.includes("离婚")) ??
      focusIssues.find((item) => item.includes("抚养")) ??
      focusIssues.find((item) => item.includes("财产")) ??
      focusIssues[0]
    );
  }

  if (caseProfile.case_type === "tort_liability") {
    return (
      focusIssues.find((item) => item.includes("责任")) ??
      focusIssues.find((item) => item.includes("过错")) ??
      focusIssues.find((item) => item.includes("因果关系")) ??
      focusIssues[0]
    );
  }

  return focusIssues[0];
}

function pickBranchFocus(caseProfile: CaseProfile, _turnIndex: number): string {
  const preferredFocus = pickPreferredFocusIssue(caseProfile);
  if (preferredFocus) {
    return preferredFocus;
  }

  if (caseProfile.claims.length > 0) {
    return caseProfile.claims[0];
  }

  return "案件事实梳理";
}

function pickSpeakerRole(stage: TrialStage): SimulationSnapshot["speaker_role"] {
  switch (stage) {
    case "prepare":
      return "judge";
    case "investigation":
      return "plaintiff";
    case "evidence":
      return "plaintiff";
    case "debate":
      return "defendant";
    case "final_statement":
      return "agent";
    case "mediation_or_judgment":
      return "judge";
    case "report_ready":
      return "judge";
    default:
      return "judge";
  }
}

function buildMockStageDynamicNarrative(
  caseProfile: CaseProfile,
  stage: TrialStage,
  branchFocus: string,
): string {
  const claim = caseProfile.claims[0] ?? "当前主张";
  const keyFact = caseProfile.core_facts[0] ?? "当前关键事实";

  switch (stage) {
    case "prepare":
      return `书记员刚核对完到庭情况，审判长就把案件往“${branchFocus}”上压，明显不打算让双方继续泛讲背景。你如果此刻不先锁住诉请和事实主线，后面很容易被对方牵着走。`;
    case "investigation":
      return `法庭调查已经进入实质问答。审判长要求双方围绕“${branchFocus}”陈述，不接受大段背景铺陈，只要能被追问、能被核实的事实。`;
    case "evidence":
      if (caseProfile.case_type === "labor_dispute") {
        return `举证质证已经开始收口。审判长不再接受“综合足以证明劳动关系”这种大话，而是要求你把聊天、考勤、工资流水一份份落到管理、报酬和隶属性上。`;
      }
      return `举证质证阶段的气压明显上来了。每份材料都要说清来源、形成时间和证明目的，任何一句“综合来看”都会被法庭打断。`;
    case "debate":
      if (caseProfile.case_type === "labor_dispute") {
        return `审判长明确表示不再重复听入职经过，而是要求双方按争议焦点逐项辩论：先答“${branchFocus}”，再答未签书面合同双倍工资请求是否具备前提。对方代理人已经把“协议名称、提成结算、未缴社保”压成三点准备反击。`;
      }
      if (caseProfile.case_type === "private_lending") {
        return `法庭辩论已经进入法律适用层。审判长要求双方先围绕借贷合意和款项交付说清，再谈利息、违约责任和履行期限，不能再把事实和评价混说。`;
      }
      if (caseProfile.case_type === "divorce_dispute") {
        return `法庭辩论已经不再接受情绪表达。审判长要求双方把离婚条件、财产范围和抚养安排拆开讲，每一点都要对应材料和裁判理由。`;
      }
      if (caseProfile.case_type === "tort_liability") {
        return `法庭辩论已经压到责任结构上。审判长要求双方按过错、因果关系、损失范围依次回答，不能再把事故经过当成辩论本身。`;
      }
      return `法庭辩论已经不再听重复事实，审判长只关心“${claim}”究竟由哪组证据和哪条法理支撑。你每多说一句空话，对方就会顺手把节奏带走。`;
    case "final_statement":
      return `法庭提醒双方最后陈述不是重新举证的机会。此刻留下印象的不是话多，而是你能否把“${branchFocus}”收束成一句法官愿意写进心证的话。`;
    case "mediation_or_judgment":
      return `庭审进入收束段后，法庭开始试探双方是否愿意调解，同时也在观察谁会先暴露真实底线。这个节点一旦松错，前面争来的优势会被很快吃掉。`;
    case "report_ready":
      return `本轮推演已经收束，接下来不再是继续说，而是把“${branchFocus}”拆回事实、证据、法条和下一轮动作。`;
    default:
      return `法庭现在围绕“${branchFocus}”推进，关键是别让${keyFact}失去证明落点。`;
  }
}

function buildMockJudgeQuestion(
  caseProfile: CaseProfile,
  stage: TrialStage,
  branchFocus: string,
  selectedAction: string,
): string {
  switch (caseProfile.case_type) {
    case "labor_dispute":
      switch (stage) {
        case "prepare":
          if (selectedAction.includes("争议焦点")) {
            return "原告先明确：本案是先审劳动关系成立，还是先审未签书面合同双倍工资的适用前提？";
          }
          if (selectedAction.includes("时间线") || selectedAction.includes("主线")) {
            return "从你第一次接受工作安排开始，按时间说明谁发指令、谁记考勤、谁发报酬，不要跳着讲。";
          }
          if (selectedAction.includes("调取关键材料")) {
            return "你申请调取哪些材料？由谁控制？这些材料不进来，会直接影响哪一点认定？";
          }
          return `原告先说明，你主张劳动关系成立，眼下最先想让法庭确认的是管理安排、考勤约束，还是报酬发放方式？`;
        case "investigation":
          if (selectedAction.includes("核心事实")) {
            return "你先挑一个最能证明管理隶属性的场景说清：谁安排工作、谁验收结果、谁决定去留。";
          }
          if (selectedAction.includes("关键关系发问")) {
            return "你希望法庭先问谁控制考勤，还是先问谁决定报酬和业务分配？";
          }
          if (selectedAction.includes("逐点追问")) {
            return "你现在准备先追哪一处矛盾：协议名称、提成结算，还是公司对你日常管理的细节？";
          }
          return `请围绕“${branchFocus}”依次说明：谁安排工作、如何考勤、报酬怎么结算，不要先下评价。`;
        case "evidence":
          if (selectedAction.includes("三性质疑")) {
            return "你具体对哪份材料的真实性、合法性或关联性提出异议？理由分别是什么？";
          }
          if (selectedAction.includes("原始载体")) {
            return "你要求核验原始载体的对象是哪份电子材料？如果对方当庭出示，你准备怎么接？";
          }
          if (selectedAction.includes("对应关系")) {
            return "你方聊天记录、考勤和转账材料分别对应哪个待证事实？请不要把证明目的混在一起。";
          }
          return `你方关于工作群记录、转账记录和《合作经营协议》，各自想证明什么？原始载体是否已经带来？`;
        case "debate":
          if (selectedAction.includes("构成要件")) {
            return "你现在按人身隶属性、经济从属性、组织从属性哪个层次先讲？每一层都对应哪份证据编号？";
          }
          if (selectedAction.includes("逐项反驳")) {
            return "对方刚才补充称协议真实、提成结算自主、未缴社保系双方协商，你准备先拆哪一点？";
          }
          if (selectedAction.includes("结论+证据+法条")) {
            return "请按“结论、证据编号、法律依据”依次陈述，先答是否存在劳动关系，再答双倍工资请求为何具备前提。";
          }
          return "请按本庭归纳的争议焦点先回答是否存在劳动关系，再回答双倍工资请求是否具备前提；每一点都对应具体证据编号。";
        case "final_statement":
          return `请在最后陈述里只保留一项主请求和一条最强证据链，不要重复已经说过的内容。`;
        case "mediation_or_judgment":
          return `双方是否接受调解？如果不接受，请分别说明此刻不能让步的核心点是什么。`;
        default:
          return `请围绕“${branchFocus}”作出最简洁、最可核验的回答。`;
      }
    case "private_lending":
      switch (stage) {
        case "prepare":
          return `原告先说清，本案现在最先要确认的是借贷合意、款项交付，还是还款约定？`;
        case "investigation":
          return `请围绕“${branchFocus}”依次说明：钱是怎么交付的、双方怎么确认性质、何时催要过。`;
        case "evidence":
          return `转账凭证、聊天记录和催收材料分别证明什么？有没有能对应到同一时间线的材料？`;
        case "debate":
          return `你方具体说明，哪组材料能排除“其他往来款”这种替代解释？`;
        case "final_statement":
          return `最后只说清：本金、利息、违约责任里，哪一项最应先被支持。`;
        case "mediation_or_judgment":
          return `若进入调解，本金、利息和履行期限三项里，双方各自的边界在哪里？`;
        default:
          return `请围绕“${branchFocus}”直接回答，不要泛讲。`;
      }
    case "divorce_dispute":
      switch (stage) {
        case "prepare":
          return `原告先说明，本轮最优先要让法庭确认的是离婚条件、共同财产范围，还是子女抚养安排？`;
        case "investigation":
          return `请围绕“${branchFocus}”先陈述客观事实，再陈述你的评价。`;
        case "evidence":
          return `你方关于财产来源、照料事实和沟通记录的材料，各自证明什么？`;
        case "debate":
          return `哪一组证据能够直接支持你方关于“${branchFocus}”的法律结论？`;
        case "final_statement":
          return `最后陈述请只保留最应先被法庭记住的一点。`;
        case "mediation_or_judgment":
          return `若调解不能成立，你方希望法庭先处理的是财产、抚养还是离婚本身？`;
        default:
          return `请围绕“${branchFocus}”直接回答。`;
      }
    case "tort_liability":
      switch (stage) {
        case "prepare":
          return `原告先说明，本案眼下最需要先确认的是过错、因果关系，还是损失范围？`;
        case "investigation":
          return `请围绕“${branchFocus}”说明事故经过、责任行为和损害结果，不要跳步。`;
        case "evidence":
          return `现场材料、鉴定意见和损失票据各自证明什么？`;
        case "debate":
          return `哪组证据最能直接证明被告存在过错并应承担相应责任？`;
        case "final_statement":
          return `最后陈述请直接说清：法庭应支持哪一项责任结论。`;
        case "mediation_or_judgment":
          return `若进入调解，双方围绕责任比例和金额是否存在可谈空间？`;
        default:
          return `请围绕“${branchFocus}”直接作答。`;
      }
    default:
      return `请围绕“${branchFocus}”说明与你方主张直接相关的事实、证据和理由。`;
  }
}

function buildMockOpponentCourtMove(
  caseProfile: CaseProfile,
  stage: TrialStage,
  branchFocus: string,
  selectedAction: string,
): string {
  switch (caseProfile.case_type) {
    case "labor_dispute":
      switch (stage) {
        case "prepare":
          if (selectedAction.includes("争议焦点")) {
            return "对方立刻顺着你的框架把《合作经营协议》抬出来， insist 先把案件定成合作，再谈双倍工资请求。";
          }
          if (selectedAction.includes("时间线") || selectedAction.includes("主线")) {
            return "对方开始在时间线上塞入“自主揽客、按业绩提成、无固定底薪”这些细节，想把整条线改写成合作经营轨迹。";
          }
          if (selectedAction.includes("调取关键材料")) {
            return "对方先反对你的调查取证申请，称相关材料你本可自行准备，试图把程序申请直接压掉。";
          }
          return `对方一开口就把《合作经营协议》摆到最前面，试图先把案件定性成合作关系，而不是劳动关系。`;
        case "investigation":
          if (selectedAction.includes("核心事实")) {
            return "对方抢着解释工作群通知和日报要求只是业务协同，不是劳动管理，想把你刚说的关键场景先拆掉。";
          }
          if (selectedAction.includes("关键关系发问")) {
            return "对方提前把“提成结算、自主开发客户、无固定工资”抛到台面上，想在法官追问前先改写关键关系。";
          }
          if (selectedAction.includes("逐点追问")) {
            return "对方开始在协议、考勤和报酬三个点上来回腾挪，只承认合作安排，不正面承认管理链条。";
          }
          return `对方反复强调你有销售提成、自主开发客户，想把“管理安排”解释成业务协作，而不是用工管理。`;
        case "evidence":
          if (selectedAction.includes("三性质疑")) {
            return "对方立刻补一句聊天截图都有原机、考勤是系统导出、转账备注能对应月份，试图把被你攻击的三性重新拉稳。";
          }
          if (selectedAction.includes("原始载体")) {
            return "对方先表示可以展示手机和转账记录，但坚持这些材料最多证明业务协作，不足以证明劳动关系。";
          }
          if (selectedAction.includes("对应关系")) {
            return "对方专门拆你证据之间的连接，主张聊天归聊天、转账归转账、考勤归考勤，三者不能直接拼成劳动关系。";
          }
          return `对方盯住聊天记录、打卡痕迹和转账备注，主张这些最多只能说明项目协作，不能直接证明劳动关系。`;
        case "debate":
          if (selectedAction.includes("构成要件")) {
            return "被告代理人顺势把焦点压到“无基本工资、无社保、可自主开发客户”三点，集中攻击你的人身和经济从属性论证。";
          }
          if (selectedAction.includes("逐项反驳")) {
            return "被告代理人坚持答辩意见，补充称你是在逐句挑刺，却没有正面回答为什么《合作经营协议》不能反映双方真实关系。";
          }
          if (selectedAction.includes("结论+证据+法条")) {
            return "被告代理人紧接着用“协议名称、提成模式、无固定工时”三句短论反压，试图让法官觉得它的结构更干净。";
          }
          return "被告代理人坚持答辩和质证意见，补充称《合作经营协议》、提成结算方式以及未缴社保的处理，都说明双方按合作模式履行，不存在劳动关系。";
        case "final_statement":
          return `对方最后要求法庭先认定协议性质，再谈双倍工资，否则你的请求整体失去前提。`;
        case "mediation_or_judgment":
          return `对方口头表示可以讨论少量补偿，但坚持不承认劳动关系，希望你先在定性上退让。`;
        default:
          return `对方正在努力把“${branchFocus}”改写成对其更有利的解释路径。`;
      }
    case "private_lending":
      switch (stage) {
        case "prepare":
          return `对方先把转账背景说成朋友往来或投资，想让法庭不要一开始就按借贷审。`;
        case "investigation":
          return `对方不断追问交付款项的背景和场合，试图把借贷合意拆散。`;
        case "evidence":
          return `对方抓住聊天上下文和转账备注里的空白处，主张资金性质仍然存在其他解释。`;
        case "debate":
          return `对方把辩论焦点拉到“是否真有借贷合意”上，想顺势压掉利息和违约责任。`;
        case "final_statement":
          return `对方最后要求法庭即便支持本金，也不要支持你方过高的附随请求。`;
        case "mediation_or_judgment":
          return `对方试图把调解落点压到分期还款和缩减利息上。`;
        default:
          return `对方正在改写“${branchFocus}”的资金解释。`;
      }
    case "divorce_dispute":
      switch (stage) {
        case "prepare":
          return `对方先把情绪冲突和生活矛盾拉上来，试图稀释真正需要确认的争点。`;
        case "investigation":
          return `对方不断把叙述拉回生活细节，避免直接回应财产来源和照料安排。`;
        case "evidence":
          return `对方盯住流水、登记材料和聊天记录的片段性，主张你方证据不足以一次性支持全部主张。`;
        case "debate":
          return `对方把辩论重心拉到共同财产范围和子女现实利益上，想压缩你方请求。`;
        case "final_statement":
          return `对方最后强调即便部分事实成立，也不足以支持你方全部分割和抚养方案。`;
        case "mediation_or_judgment":
          return `对方希望先谈可以执行的分配方案，而不是先接受你方定性。`;
        default:
          return `对方正在把“${branchFocus}”往更有利于自己的生活叙事里带。`;
      }
    case "tort_liability":
      switch (stage) {
        case "prepare":
          return `对方先强调事故原因复杂，不愿让法庭过早把责任焦点锁到自己身上。`;
        case "investigation":
          return `对方不断插入原告自身行为，试图把过错和因果关系都拉成混合状态。`;
        case "evidence":
          return `对方盯住现场材料、维修单据和鉴定意见，想从链条断点处压低责任。`;
        case "debate":
          return `对方把辩论主轴压到“即便有责任也应大幅降低比例和金额”。`;
        case "final_statement":
          return `对方最后强调你方损失计算偏高，不能照单全收。`;
        case "mediation_or_judgment":
          return `对方试图把调解焦点先落到金额压缩，而不是责任承认。`;
        default:
          return `对方正在改写“${branchFocus}”的责任结构。`;
      }
    default:
      return `对方正在尝试把“${branchFocus}”改写成对其更有利的版本。`;
  }
}

function buildMockActionCourtImpact(
  caseProfile: CaseProfile,
  stage: TrialStage,
  selectedAction: string,
  branchFocus: string,
): string {
  if (caseProfile.case_type === "labor_dispute") {
    switch (stage) {
      case "prepare":
        if (selectedAction === "开始模拟") {
          return "法官还没替你决定开口顺序；你接下来第一步怎么说，直接决定本案是先锁争点，还是先被协议名称带偏。";
        }
        if (selectedAction.includes("争议焦点")) {
          return "法官会先把“是否存在劳动关系”和“能否主张双倍工资”拆成两层问题记录，本轮不会再让双方泛讲背景。";
        }
        if (selectedAction.includes("时间线") || selectedAction.includes("主线")) {
          return "法官接下来的注意力会落在入职、考勤、报酬三个时间节点，你后面每句话都得能接住细节追问。";
        }
        if (selectedAction.includes("调取关键材料")) {
          return "这一轮节奏会先转到调查取证必要性上，实体争点会暂时往后压，但法庭会立刻检验你方准备是否充分。";
        }
        break;
      case "investigation":
        if (selectedAction.includes("争议焦点")) {
          return "因为你上一轮先锁了争点，法官现在会更愿意直接追问管理、考勤和报酬，而不是陪对方空谈协议名称。";
        }
        if (selectedAction.includes("时间线") || selectedAction.includes("主线")) {
          return "因为你上一轮先铺了时间线，法官现在会顺着入职、考勤、报酬三个节点逐项追问，你不能再跳步。";
        }
        if (selectedAction.includes("调取关键材料")) {
          return "你上一轮先打了程序申请，法官现在会更敏感地看你现有事实是否已经足够支撑调查取证的必要性。";
        }
        if (selectedAction.includes("核心事实")) {
          return "法官会先盯住一个具体管理场景，看你能不能把人身隶属性讲实，而不是只喊“劳动关系成立”。";
        }
        if (selectedAction.includes("关键关系发问")) {
          return "法官的追问会更集中在谁控制考勤、谁决定报酬和工作内容，这会直接压缩对方泛化“合作关系”的空间。";
        }
        if (selectedAction.includes("逐点追问")) {
          return "只要对方版本出现前后不一致，法官就会顺着矛盾点深追，本轮节奏会明显变硬。";
        }
        break;
      case "evidence":
        if (selectedAction.includes("核心事实")) {
          return "因为你上一轮先讲了核心事实，法官现在会立刻要你拿出能落到管理链上的材料，不再接受抽象概括。";
        }
        if (selectedAction.includes("关键关系发问")) {
          return "你上一轮把问题钉在关键关系上，法官现在会重点看哪组证据真能证明谁控制工作、谁决定报酬。";
        }
        if (selectedAction.includes("逐点追问")) {
          return "你上一轮已经把对方版本逼到细节上，这一轮只要证据接得上，法官会更容易记住对方前后不一的地方。";
        }
        if (selectedAction.includes("三性质疑")) {
          return "法官会先停下来判断那份证据还能不能进入心证，对方一旦解释不清，整条抗辩线都会松。";
        }
        if (selectedAction.includes("原始载体")) {
          return "只要对方拿不出原始载体，它关于合作关系的很多说法都会失去支撑；拿得出来，你就要立刻接着拆证明目的。";
        }
        if (selectedAction.includes("对应关系")) {
          return "法官会按“聊天记录—考勤管理—转账发放”三段去看你方证明链是否闭合，论证会更像真正的举证质证。";
        }
        break;
      case "debate":
        if (selectedAction.includes("三性质疑")) {
          return "你上一轮若已经把对方证据三性打松，法官在辩论阶段会更愿意听你顺势压缩对方整套合作关系说法。";
        }
        if (selectedAction.includes("原始载体")) {
          return "你上一轮逼出了原始载体，法官现在更关注那份材料究竟证明管理隶属，还是只证明业务协作。";
        }
        if (selectedAction.includes("对应关系")) {
          return "你上一轮已经把聊天、考勤和转账勾成链条，这一轮只要法理论证跟上，法官更容易把劳动关系作为主判断方向。";
        }
        if (selectedAction.includes("构成要件")) {
          return "法官会顺着你的结构去听要件成立与否，这一轮最怕的不是说少，而是要件漏讲。";
        }
        if (selectedAction.includes("逐项反驳")) {
          return "只要你先拆掉对方最关键的一点，它后面整套“合作关系”说法都会开始发虚。";
        }
        if (selectedAction.includes("结论+证据+法条")) {
          return "法官更容易直接把你的表达记进裁判思路，但前提是结论、证据和法条三层必须一口气接上。";
        }
        break;
      case "final_statement":
        if (selectedAction.includes("构成要件")) {
          return "你上一轮如果已经把劳动关系的要件结构讲清，这一轮最后陈述只需要把最强证据链钉住，不必再全面铺开。";
        }
        if (selectedAction.includes("逐项反驳")) {
          return "你上一轮如果已经拆出对方抗辩漏洞，这一轮最后陈述要做的就是把那处漏洞固定成法官心证。";
        }
        if (selectedAction.includes("结论+证据+法条")) {
          return "你上一轮如果已经把结论、证据和法条压成一线，这一轮只需要留下那句最该被记入裁判理由的话。";
        }
        break;
      default:
        break;
    }
  }

  return `你刚选择“${selectedAction}”，下一轮围绕“${branchFocus}”的攻防会因此改线，法官的注意力也会跟着这一步走。`;
}

function buildMockStageTask(
  caseProfile: CaseProfile,
  stage: TrialStage,
  branchFocus: string,
): string {
  switch (caseProfile.case_type) {
    case "labor_dispute":
      switch (stage) {
        case "prepare":
          return `不要先讲双方矛盾和情绪。先把“谁安排工作、如何考勤、报酬如何发放”三件事排成顺序，再决定第一口怎么开。`;
        case "investigation":
          return `现在要让法官记住的是实际管理关系，不是协议标题。优先用能被追问的事实句，不要先下“劳动关系已经成立”的评价。`;
        case "evidence":
          return `这轮只做一件事：把你手上的聊天、考勤、转账材料分别对应到管理、报酬和隶属性，不要混着说。`;
        case "debate":
          return `不要再讲入职经过。先答“为什么构成劳动关系”，再答“双倍工资为何具备前提”，每一点都带证据编号和法律依据。`;
        case "final_statement":
          return `最后陈述只留主请求和最强证据链，不再扩展新问题。`;
        case "mediation_or_judgment":
          return `先判断“是否承认劳动关系”是不是绝不能退的底线，再决定要不要谈金额。`;
        default:
          return `继续围绕“${branchFocus}”收束。`;
      }
    case "private_lending":
      switch (stage) {
        case "prepare":
          return `先分清借贷合意、交付款项和还款约定三件事，不要一上来把本金、利息、违约责任全堆在一起。`;
        case "investigation":
          return `优先让法官听明白钱是怎么给的、双方如何确认性质、后续如何催要。`;
        case "evidence":
          return `把转账凭证、聊天记录和催收材料放到同一时间线上，形成可核验的闭环。`;
        case "debate":
          return `重点不是重复转账事实，而是排除“其他往来款”这种替代解释。`;
        case "final_statement":
          return `最后陈述只守住最该先支持的一项请求。`;
        case "mediation_or_judgment":
          return `先守本金，再判断利息和期限能否作为调解空间。`;
        default:
          return `继续围绕“${branchFocus}”推进。`;
      }
    case "divorce_dispute":
      switch (stage) {
        case "prepare":
          return `先决定这一轮究竟主打离婚条件、财产范围还是抚养安排，别三条线一起开。`;
        case "investigation":
          return `先说客观事实，再说评价，不要把情绪表达放在证据前面。`;
        case "evidence":
          return `把财产来源、照料事实和沟通记录分别放到对应争点下，不要混证。`;
        case "debate":
          return `把论证压回具体财产、具体安排、具体法条，不打道德判断。`;
        case "final_statement":
          return `最后只留最应先被法庭记住的一点。`;
        case "mediation_or_judgment":
          return `先区分哪些可谈，哪些不能退，别为了快结束先乱松口。`;
        default:
          return `继续围绕“${branchFocus}”推进。`;
      }
    case "tort_liability":
      switch (stage) {
        case "prepare":
          return `先锁定是争过错、因果关系，还是损失金额，别把责任结构讲乱。`;
        case "investigation":
          return `把事故经过按时间顺序说，避免事实和评价来回跳。`;
        case "evidence":
          return `让每份材料都明确证明一个节点：过错、因果关系或损失，不要贪多。`;
        case "debate":
          return `优先处理“${branchFocus}”里最能改变责任结论的一点，不要平均用力。`;
        case "final_statement":
          return `最后陈述只压住责任结论和金额落点。`;
        case "mediation_or_judgment":
          return `先看责任比例能否守住，再考虑金额是否存在可谈空间。`;
        default:
          return `继续围绕“${branchFocus}”推进。`;
      }
    default:
      return `围绕“${branchFocus}”只说能被证据和法条托住的话。`;
  }
}

function buildMockHistoryFromItems(
  localHistory: SimulationHistoryItem[] | undefined,
  snapshot: SimulationSnapshot,
): SimulationHistoryItem[] {
  const nextHistoryItem = toHistoryItem(snapshot);
  if (!localHistory || localHistory.length === 0) {
    return [nextHistoryItem];
  }

  const historyMap = new Map<string, SimulationHistoryItem>();
  for (const item of localHistory) {
    historyMap.set(`${item.simulation_id}:${item.turn_index}`, item);
  }
  historyMap.set(`${nextHistoryItem.simulation_id}:${nextHistoryItem.turn_index}`, nextHistoryItem);

  return Array.from(historyMap.values()).sort((left, right) => left.turn_index - right.turn_index);
}

function buildMockHistory(items: SimulationSnapshot[]): SimulationHistoryItem[] {
  const historyMap = new Map<string, SimulationHistoryItem>();
  for (const item of items) {
    historyMap.set(`${item.simulation_id}:${item.turn_index}`, toHistoryItem(item));
  }

  return Array.from(historyMap.values()).sort(
    (left, right) => left.turn_index - right.turn_index,
  );
}

function toHistoryItem(snapshot: SimulationSnapshot): SimulationHistoryItem {
  return {
    simulation_id: snapshot.simulation_id,
    node_id: snapshot.node_id,
    stage: snapshot.current_stage,
    turn_index: snapshot.turn_index,
    scene_title: snapshot.scene_title,
    branch_focus: snapshot.branch_focus,
  };
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError && error.message) {
    return error.message;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "庭审模拟加载失败，请稍后重试。";
}

function getNextStageHint(stage: TrialStage): string {
  const currentIndex = MOCK_STAGE_ORDER.findIndex((item) => item === stage);
  if (currentIndex < 0 || currentIndex === MOCK_STAGE_ORDER.length - 1) {
    return "report_ready";
  }

  return MOCK_STAGE_ORDER[currentIndex + 1];
}

function appendSimulationUserInput(
  snapshot: SimulationSnapshot,
  pendingInput: {
    inputType: SimulationUserInputType;
    content: string;
  } | null,
): SimulationUserInputEntry[] {
  const existingEntries = snapshot.user_input_entries ?? [];
  if (!pendingInput) {
    return existingEntries;
  }

  const normalizedContent = pendingInput.content.trim();
  if (!normalizedContent) {
    return existingEntries;
  }

  return [
    ...existingEntries,
    {
      entry_id: `input-${snapshot.simulation_id}-${Date.now()}`,
      stage: snapshot.current_stage,
      turn_index: snapshot.turn_index,
      input_type: pendingInput.inputType,
      label: formatSimulationUserInputTypeLabel(pendingInput.inputType),
      content: normalizedContent,
      created_at: new Date().toISOString(),
    },
  ];
}

function mergeServerUserInputState(
  snapshot: SimulationSnapshot,
  fallbackUserInputEntries: SimulationUserInputEntry[],
): SimulationSnapshot {
  const resolvedEntries =
    (snapshot.user_input_entries ?? []).length > 0
      ? snapshot.user_input_entries ?? []
      : fallbackUserInputEntries;

  return {
    ...snapshot,
    user_input_entries: resolvedEntries,
    hidden_state_summary: {
      ...snapshot.hidden_state_summary,
      ...(resolvedEntries.length > 0
        ? {
            user_input_depth:
              snapshot.hidden_state_summary.user_input_depth ??
              `已写入 ${resolvedEntries.length} 条`,
          }
        : {}),
    },
  };
}

function applyUserInputDrivenEnhancements(
  snapshot: SimulationSnapshot,
  caseProfile: CaseProfile,
  userInputEntries: SimulationUserInputEntry[],
): SimulationSnapshot {
  if (userInputEntries.length === 0) {
    return {
      ...snapshot,
      user_input_entries: [],
    };
  }

  const latestInput = userInputEntries[userInputEntries.length - 1];
  const latestSummary = summarizeSimulationUserInputEntry(latestInput, 48);
  const inputDrivenTaskSuffix = buildInputDrivenTaskSuffix(
    latestInput,
    caseProfile,
    snapshot,
  );
  const inputDrivenProgressSuffix = buildInputDrivenProgressSuffix(
    latestInput,
    caseProfile,
  );
  const inputDrivenAction = buildInputDrivenNextAction(
    latestInput,
    caseProfile,
    snapshot,
  );
  const inputDrivenArgument = buildInputDrivenOpponentArgument(
    latestInput,
    caseProfile,
    snapshot,
  );
  const inputDrivenRisk = buildInputDrivenRisk(
    latestInput,
    caseProfile,
    snapshot,
  );
  const winRateShift = getInputDrivenWinRateShift(latestInput, snapshot);
  const confidenceShift = getInputDrivenConfidenceShift(latestInput, snapshot);
  const currentEstimatedWinRate =
    typeof snapshot.analysis.estimated_win_rate === "number"
      ? snapshot.analysis.estimated_win_rate
      : estimateMockWinRate(caseProfile, snapshot.current_stage);
  const currentConfidence =
    typeof snapshot.analysis.confidence === "number"
      ? snapshot.analysis.confidence
      : 0.56;

  return {
    ...snapshot,
    court_progress: `${snapshot.court_progress} ${inputDrivenProgressSuffix}`,
    pressure_shift:
      latestInput.input_type === "evidence" || latestInput.input_type === "cross_exam"
        ? `对方已经开始盯住你刚补入的${latestInput.label}，会优先从证明力和逻辑一致性上施压。`
        : snapshot.pressure_shift,
    current_task: `${snapshot.current_task} ${inputDrivenTaskSuffix}`,
    hidden_state_summary: {
      ...snapshot.hidden_state_summary,
      user_input_depth: `已写入 ${userInputEntries.length} 条`,
    },
    opponent: {
      ...snapshot.opponent,
      likely_arguments: dedupeStrings([
        inputDrivenArgument,
        ...(snapshot.opponent.likely_arguments ?? []),
      ]),
      risk_points: dedupeStrings([
        inputDrivenRisk,
        ...(snapshot.opponent.risk_points ?? []),
      ]),
      recommended_responses: dedupeStrings([
        inputDrivenAction,
        ...(snapshot.opponent.recommended_responses ?? []),
      ]),
    },
    analysis: {
      ...snapshot.analysis,
      estimated_win_rate: clampNumber(
        currentEstimatedWinRate + winRateShift,
        28,
        86,
      ),
      confidence: Number(
        clampNumber(currentConfidence + confidenceShift, 0.42, 0.84).toFixed(2),
      ),
      positive_factors: dedupeStrings([
        `已补入${latestInput.label}：${latestSummary}`,
        ...(snapshot.analysis.positive_factors ?? []),
      ]),
      negative_factors: dedupeStrings(snapshot.analysis.negative_factors ?? []),
      evidence_gap_actions:
        latestInput.input_type === "evidence"
          ? dedupeStrings([
              `把你刚补入的证据“${latestSummary}”补齐来源、形成时间和证明目的。`,
              ...(snapshot.analysis.evidence_gap_actions ?? []),
            ])
          : dedupeStrings(snapshot.analysis.evidence_gap_actions ?? []),
      recommended_next_actions: dedupeStrings([
        inputDrivenAction,
        ...(snapshot.analysis.recommended_next_actions ?? []),
      ]),
      report_overview: buildInputDrivenReportOverview(snapshot, latestInput),
    },
    user_input_entries: userInputEntries,
  };
}

function buildInputDrivenTaskSuffix(
  entry: SimulationUserInputEntry,
  caseProfile: CaseProfile,
  snapshot: SimulationSnapshot,
): string {
  const summary = summarizeSimulationUserInputEntry(entry, 28);

  if (caseProfile.case_type === "labor_dispute") {
    switch (entry.input_type) {
      case "fact":
        return `同时要把这条新事实“${summary}”继续接到管理安排、考勤约束和报酬发放上。`;
      case "evidence":
        return `同时要把这份新证据“${summary}”讲到来源、形成时间和证明劳动关系的哪一层。`;
      case "argument":
        return `同时要把这条主张“${summary}”压回证据编号和法律依据。`;
      default:
        return `同时要把你刚补入的${entry.label}真正接进当前争点。`;
    }
  }

  if (caseProfile.case_type === "private_lending") {
    return `同时要把“${summary}”接回借贷合意、款项交付或催收经过中的一个节点。`;
  }

  if (caseProfile.case_type === "divorce_dispute") {
    return `同时要把“${summary}”明确归到离婚条件、财产范围或抚养安排其中一条线上。`;
  }

  if (caseProfile.case_type === "tort_liability") {
    return `同时要把“${summary}”直接落到过错、因果关系或损失金额里的一个点上。`;
  }

  return `同时要把你刚补入的${entry.label}放回${getTrialStageMeta(snapshot.current_stage).label}的主线上。`;
}

function buildInputDrivenProgressSuffix(
  entry: SimulationUserInputEntry,
  caseProfile: CaseProfile,
): string {
  const summary = summarizeSimulationUserInputEntry(entry, 24);

  if (caseProfile.case_type === "labor_dispute" && entry.input_type === "fact") {
    return `新补入的事实“${summary}”已经把法庭注意力重新拉回管理隶属性。`;
  }

  if (caseProfile.case_type === "private_lending" && entry.input_type === "fact") {
    return `新补入的事实“${summary}”已经进入借贷合意和交付经过的判断。`;
  }

  if (caseProfile.case_type === "divorce_dispute" && entry.input_type === "fact") {
    return `新补入的事实“${summary}”已经进入离婚、财产或抚养的判断主线。`;
  }

  if (caseProfile.case_type === "tort_liability" && (entry.input_type === "fact" || entry.input_type === "evidence")) {
    return `新补入的材料“${summary}”已经进入责任链条的判断。`;
  }

  return `你补入的${entry.label}“${summary}”已经进入本轮判断。`;
}

function buildMockCourtProgress(
  caseProfile: CaseProfile,
  stage: TrialStage,
  branchFocus: string,
): string {
  const stageLabel = getTrialStageMeta(stage).label;
  const claim = caseProfile.claims[0] ?? "当前请求";

  switch (stage) {
    case "prepare":
      return `当前已进入${stageLabel}，法庭先看你能否把“${claim}”和“${branchFocus}”讲成一条清楚主线。`;
    case "investigation":
      return `当前已进入${stageLabel}，法官正在根据“${branchFocus}”形成第一轮事实心证。`;
    case "evidence":
      return `当前已进入${stageLabel}，证据的来源、形成时间和证明目的开始决定“${branchFocus}”能否站住。`;
    case "debate":
      return `当前已进入${stageLabel}，双方都在争夺法官对“${branchFocus}”的最终评价方向。`;
    case "final_statement":
      return `当前已进入${stageLabel}，法庭只会记住最后留下的主请求和最强证据链。`;
    case "mediation_or_judgment":
      return `当前已进入${stageLabel}，案件正在走向调解博弈或裁判落点。`;
    case "report_ready":
      return `当前已进入复盘阶段，接下来重点是把“${branchFocus}”拆回可执行的备诉动作。`;
    default:
      return `当前已进入${stageLabel}，这一轮仍围绕“${branchFocus}”推进。`;
  }
}

function buildMockPressureShift(
  stage: TrialStage,
  selectedAction: string,
  branchFocus: string,
): string {
  switch (stage) {
    case "prepare":
      return `你刚刚选择“${selectedAction}”，这会影响法庭是先听你锁争点，还是先看你有没有完整时间线。`;
    case "investigation":
      return `你此刻选择“${selectedAction}”，会直接决定法官下一轮追问是继续压“${branchFocus}”，还是转去听对方改写版本。`;
    case "evidence":
      return `证据阶段一旦动作选错，对方就会抓住你说不清原始载体或证明目的的地方继续放大。`;
    case "debate":
      return `辩论阶段每多讲一句无证据托底的话，对方都能顺势把你的主线拆开。`;
    case "final_statement":
      return `最后陈述阶段如果扩题，法官对你前面已经建立的印象会被明显稀释。`;
    case "mediation_or_judgment":
      return `这个节点最怕先暴露底线；你现在的选择会直接影响对方下一口压价还是收口。`;
    case "report_ready":
      return `复盘不是重讲一遍庭审，而是决定下一轮到底补什么、怎么开口。`;
    default:
      return `你刚刚选择“${selectedAction}”，会直接影响下一轮“${branchFocus}”的攻防节奏。`;
  }
}

function buildMockChoicePrompt(stage: TrialStage): string {
  switch (stage) {
    case "prepare":
      return "这一轮只能先定一个开局动作。你要先锁程序与争点，还是先把事实主线端上桌？";
    case "investigation":
      return "法庭正在追问核心事实。你现在只能先把一个问题讲深，别同时铺三条线。";
    case "evidence":
      return "证据攻防已经开始。你这一口要么先拆对方证据，要么先补我方证明链。";
    case "debate":
      return "辩论阶段不比谁说得多，只比谁更能把法官带回主线。选一个主动作继续推进。";
    case "final_statement":
      return "最后陈述只留最该被记住的话。先选你这一轮要保住的那一个落点。";
    case "mediation_or_judgment":
      return "案件进入收束节点。先选你要守底线、探调解，还是直接逼近结果。";
    default:
      return "请从下面的动作里选一个，把这一轮庭审继续推下去。";
  }
}

function buildMockStageObjective(stage: TrialStage): string {
  const mapping: Record<TrialStage, string> = {
    prepare: "先把程序位置、诉请边界和表达节奏稳住，再进入正式庭审主线。",
    investigation: "围绕案件事实和争议焦点建立法官的第一轮心证。",
    evidence: "决定哪些证据真正站得住，哪些地方最容易被对方打穿。",
    debate: "把事实、证据和法理压缩成一条清晰可守的主论证线。",
    final_statement: "收束整场庭审重点，让法官记住我方最关键的一句话。",
    mediation_or_judgment: "判断案件是进入调解博弈，还是直接走向结果落点。",
    report_ready: "本轮模拟已收束，接下来重点是复盘得失和准备下一步。",
  };
  return mapping[stage];
}

function buildMockCurrentTask(options: {
  caseProfile: CaseProfile;
  stage: TrialStage;
  branchFocus: string;
  selectedAction: string;
}): string {
  const mapping: Record<TrialStage, string> = {
    prepare: buildMockStageTask(options.caseProfile, "prepare", options.branchFocus),
    investigation: buildMockStageTask(options.caseProfile, "investigation", options.branchFocus),
    evidence: buildMockStageTask(options.caseProfile, "evidence", options.branchFocus),
    debate: buildMockStageTask(options.caseProfile, "debate", options.branchFocus),
    final_statement: buildMockStageTask(options.caseProfile, "final_statement", options.branchFocus),
    mediation_or_judgment: buildMockStageTask(options.caseProfile, "mediation_or_judgment", options.branchFocus),
    report_ready: `本轮推演已结束，请围绕“${options.branchFocus}”整理复盘，并把“${options.selectedAction}”转成下一步可执行动作。`,
  };
  return mapping[options.stage];
}

function buildMockActionCards(
  stage: TrialStage,
  actions: string[],
): SimulationActionCard[] {
  return actions.map((action, index) => ({
    action,
    intent: buildMockActionIntent(stage, action),
    risk_tip: buildMockActionRisk(stage, action),
    emphasis: index === 0 && (stage === "evidence" || stage === "debate") ? "critical" : "steady",
  }));
}

function buildMockActionIntent(stage: TrialStage, action: string): string {
  if (action.includes("核心事实")) {
    return "先用一个可核验的关键场景把法官带进案情，再把争点压到这一点上。";
  }
  if (action.includes("争议焦点")) {
    return "先把法官笔录里的核心问题锁住，避免后面越打越散。";
  }
  if (action.includes("时间线") || action.includes("主线")) {
    return "把事实按顺序摆平，让法官先听懂事情是怎么发生的。";
  }
  if (action.includes("调取关键材料")) {
    return "把后面决定胜负的材料先申请进来，不给对方继续拖。";
  }
  if (action.includes("关键关系发问")) {
    return "把法官的提问方向钉在最能刺穿对方版本的关键关系上。";
  }
  if (action.includes("逐点追问")) {
    return "逼对方逐项回应自己的版本，先把最明显的前后不一致追出来。";
  }
  if (action.includes("三性质疑")) {
    return "先拆真实性、合法性、关联性，把对方证据的站立点打松。";
  }
  if (action.includes("原始载体")) {
    return "逼对方把电子证据落回原始载体，防止片段截图直接过关。";
  }
  if (action.includes("对应关系")) {
    return "把证据一份份连起来，不让任何关键事实只剩单证孤立支撑。";
  }
  if (action.includes("裁判请求")) {
    return "把最后希望法庭采纳的判断压成一句可直接记入裁判思路的话。";
  }
  if (action.includes("构成要件")) {
    return "先按要件排结构，每一点只放最能打中的那份证据。";
  }
  if (action.includes("逐项反驳")) {
    return "顺着对方刚说的顺序逐项回击，不另开新战线。";
  }
  if (action.includes("结论+证据+法条")) {
    return "先说结论，再报证据编号，再落法条，把能写进判决书的话先说出来。";
  }
  if (action.includes("重申诉请")) {
    return "最后只让法官记住你最想被支持的那一项请求。";
  }
  if (action.includes("最关键证据链")) {
    return "把全案证明力最强的一条线单独亮出来。";
  }
  if (action.includes("先处理核心争点")) {
    return "提醒法庭别被枝节问题分流，先处理真正决定结果的争点。";
  }
  if (action.includes("接受调解") || action.includes("可接受边界")) {
    return "先把能谈和不能退的边界讲清，避免被临场压价。";
  }
  if (action.includes("尽快作出判断")) {
    return "把局面往收束推进，不给对方继续拖延腾挪。";
  }

  const stagePrefix: Record<TrialStage, string> = {
    prepare: "先稳住程序和表达顺序。",
    investigation: "让法庭持续围绕核心事实推进。",
    evidence: "先处理眼前证据压力。",
    debate: "继续争夺法官心证。",
    final_statement: "把最后表达收束成结论。",
    mediation_or_judgment: "围绕收束方式做判断。",
    report_ready: "把本轮结果转成动作。",
  };
  return `${stagePrefix[stage]} 当前动作：${action}。`;
}

function buildMockActionRisk(stage: TrialStage, action: string): string {
  if (action.includes("争议焦点")) {
    return "焦点锁得太虚，后面每一轮都会被对方重新带偏。";
  }
  if (action.includes("时间线")) {
    return "时间点一旦说乱，后面每个细节都会被放大追问。";
  }
  if (action.includes("调取关键材料")) {
    return "理由讲不充分，法庭可能直接认为你方准备不足。";
  }
  if (action.includes("三性质疑")) {
    return "只表态不讲理由，法官会把你的质疑当成常规反对。";
  }
  if (action.includes("原始载体")) {
    return "一旦对方真拿出原始载体，你必须立刻接得住后续追问。";
  }
  if (action.includes("构成要件")) {
    return "要件一旦讲漏，对方会抓住缺口倒打一轮。";
  }
  if (action.includes("结论+证据+法条")) {
    return "只报结论不报证据编号或法条，法官会直接把这句话当成空论。";
  }
  if (action.includes("逐项反驳")) {
    return "反驳越多越容易失焦，只能打最要命的几处。";
  }
  if (action.includes("重申诉请") || action.includes("最关键证据链")) {
    return "最后陈述一旦扩题，前面累积的重点会被立刻冲淡。";
  }
  if (action.includes("接受调解") || action.includes("边界")) {
    return "边界说得过早或过松，前面打出来的优势会直接折价。";
  }

  const genericRisk: Record<TrialStage, string> = {
    prepare: "开局一散，后面会越来越被动。",
    investigation: "问题铺太宽，法官记不住主线。",
    evidence: "应对节奏失衡就会留下攻击口。",
    debate: "论证不收束就会继续被带偏。",
    final_statement: "此时再开新话题会稀释重点。",
    mediation_or_judgment: "方向判断失误会影响最后落点。",
    report_ready: "只做概括不转动作，复盘价值会偏弱。",
  };
  return `${genericRisk[stage]} 动作“${action}”需要控制节奏。`;
}

function buildMockCgCaption(stageLabel: string, selectedAction: string): string {
  return `【插画分镜：${stageLabel}阶段的法庭灯光压低了一层，法官抬眼示意继续。你刚刚作出“${selectedAction}”的选择，对方席位也随之出现细微反应。】`;
}

function buildMockCgScene(options: {
  caseProfile: CaseProfile;
  stage: TrialStage;
  selectedAction: string;
  branchFocus: string;
  speakerRole: SimulationSnapshot["speaker_role"];
}): SimulationCgScene {
  return {
    background_id: pickMockCgBackground(options.stage),
    shot_type: pickMockCgShotType(options.stage),
    speaker_role: options.speakerRole,
    speaker_emotion: pickMockCgEmotion(options.stage),
    left_character_id: pickMockLeftCharacter(options.speakerRole),
    right_character_id: pickMockRightCharacter(options.speakerRole),
    emphasis_target: pickMockEmphasisTarget(options.stage),
    effect_id: pickMockEffectId(options.stage),
    title: `${getTrialStageMeta(options.stage).label}分镜`,
    caption: `【插画分镜：${options.caseProfile.title}进入${getTrialStageMeta(options.stage).label}，镜头聚焦“${options.branchFocus}”，你刚刚选择“${options.selectedAction}”，庭上气压随之变化。】`,
    image_url: pickMockStageImageUrl(options.stage),
    image_model: "static_frontend_library",
  };
}

function pickMockStageImageUrl(stage: TrialStage): string {
  switch (stage) {
    case "prepare":
      return "/generated-cg-library/cartoon-court/stage_prepare.png";
    case "investigation":
      return "/generated-cg-library/cartoon-court/stage_investigation.png";
    case "evidence":
      return "/generated-cg-library/cartoon-court/stage_evidence.png";
    case "debate":
      return "/generated-cg-library/cartoon-court/stage_debate.png";
    case "final_statement":
      return "/generated-cg-library/cartoon-court/stage_final_statement.png";
    case "mediation_or_judgment":
      return "/generated-cg-library/cartoon-court/stage_mediation_or_judgment.png";
    case "report_ready":
      return "/generated-cg-library/cartoon-court/stage_report_ready.png";
    default:
      return "/generated-cg-library/cartoon-court/stage_prepare.png";
  }
}

function pickMockCgBackground(stage: TrialStage): SimulationCgScene["background_id"] {
  switch (stage) {
    case "prepare":
      return "courtroom_entry";
    case "investigation":
      return "fact_inquiry";
    case "evidence":
      return "evidence_confrontation";
    case "debate":
      return "argument_pressure";
    case "final_statement":
      return "closing_focus";
    case "mediation_or_judgment":
      return "judgment_moment";
    case "report_ready":
      return "replay_archive";
    default:
      return "courtroom_entry";
  }
}

function pickMockCgShotType(stage: TrialStage): SimulationCgScene["shot_type"] {
  switch (stage) {
    case "prepare":
      return "wide";
    case "evidence":
    case "final_statement":
      return "close";
    case "report_ready":
      return "insert";
    default:
      return "medium";
  }
}

function pickMockCgEmotion(stage: TrialStage): SimulationCgScene["speaker_emotion"] {
  switch (stage) {
    case "prepare":
    case "mediation_or_judgment":
      return "stern";
    case "debate":
      return "pressing";
    case "final_statement":
      return "reflective";
    case "report_ready":
      return "steady";
    default:
      return "calm";
  }
}

function pickMockLeftCharacter(
  speakerRole: SimulationSnapshot["speaker_role"],
): SimulationCgScene["left_character_id"] {
  switch (speakerRole) {
    case "judge":
      return "judge_penguin";
    case "plaintiff":
    case "applicant":
      return "plaintiff_penguin";
    case "agent":
      return "plaintiff_agent_penguin";
    case "defendant":
    case "respondent":
      return "defendant_penguin";
    case "witness":
      return "witness_penguin";
    default:
      return "clerk_penguin";
  }
}

function pickMockRightCharacter(
  speakerRole: SimulationSnapshot["speaker_role"],
): SimulationCgScene["right_character_id"] {
  switch (speakerRole) {
    case "judge":
      return "defendant_agent_penguin";
    case "plaintiff":
    case "applicant":
    case "agent":
    case "defendant":
    case "respondent":
    case "witness":
      return "judge_penguin";
    default:
      return "plaintiff_agent_penguin";
  }
}

function pickMockEmphasisTarget(stage: TrialStage): SimulationCgScene["emphasis_target"] {
  switch (stage) {
    case "prepare":
      return "bench";
    case "investigation":
      return "claim_sheet";
    case "evidence":
      return "evidence_screen";
    case "debate":
      return "argument_outline";
    case "final_statement":
      return "closing_notes";
    case "mediation_or_judgment":
      return "judgment_paper";
    case "report_ready":
      return "archive_scroll";
    default:
      return "bench";
  }
}

function pickMockEffectId(stage: TrialStage): SimulationCgScene["effect_id"] {
  switch (stage) {
    case "prepare":
      return "gavel_flash";
    case "evidence":
      return "evidence_flash";
    case "debate":
      return "pressure_dark";
    case "mediation_or_judgment":
      return "judgment_seal";
    case "report_ready":
      return "archive_glow";
    default:
      return "spotlight";
  }
}

function buildMockQueries(caseProfile: CaseProfile, branchFocus: string): string[] {
  const issue = caseProfile.focus_issues[0] ?? branchFocus;
  const claim = caseProfile.claims[0] ?? caseProfile.case_type;

  return [
    `${issue} 裁判规则`,
    `${claim} 类案要点`,
    `${branchFocus} 证据标准`,
  ];
}

function buildMockOpponentArguments(
  caseProfile: CaseProfile,
  branchFocus: string,
): string[] {
  if (caseProfile.opponent_profile?.likely_arguments?.length) {
    return caseProfile.opponent_profile.likely_arguments;
  }

  switch (caseProfile.case_type) {
    case "labor_dispute":
      return [
        `围绕“${branchFocus}”，对方会先强调协议名称、提成结算和相对自主性，否认劳动关系的组织与经济从属性。`,
        "对方会坚持：即便存在工作安排和业务汇报，也只能说明合作管理，不足以推出劳动法意义上的管理隶属。",
        "对方会反复把案件拉回“合作经营 / 劳务合作”框架，试图先在定性上压掉你的后续请求。",
      ];
    case "private_lending":
      return [
        `围绕“${branchFocus}”，对方会优先否认借贷合意，主张转账还有投资、代付或往来款等其他解释。`,
        "对方会把焦点拉到资金背景和聊天上下文，尽量冲淡还款承诺与催收事实。",
        "对方会即便承认部分款项往来，也主张利息、违约责任和期限约定并不成立。",
      ];
    case "divorce_dispute":
      return [
        `围绕“${branchFocus}”，对方会尽量把争点拉回模糊的家庭矛盾和生活细节，避免直接回应核心法律问题。`,
        "对方会主张财产范围、贡献比例和照料安排都不能凭单方叙述一次性认定。",
        "对方会即便承认部分事实，也尽量压缩你方关于财产或抚养的请求范围。",
      ];
    case "tort_liability":
      return [
        `围绕“${branchFocus}”，对方会先否认过错，再否认因果关系，最后压低损失金额和责任比例。`,
        "对方会不断插入原告自身行为因素，试图形成共同过错的叙事。",
        "对方会主张现有证据最多说明事故发生，不能直接推出全部赔偿责任。",
      ];
    default:
      return [
        `否认你围绕“${branchFocus}”建立的事实链条完整性。`,
        "强调现有材料不足以直接支持你的诉请。",
        "尝试把案件重心改写到对其更有利的解释路径上。",
      ];
  }
}

function buildMockOpponentStrategies(stage: TrialStage): string[] {
  switch (stage) {
    case "evidence":
      return ["打证据三性", "切断证明链", "放大证据缺口"];
    case "debate":
      return ["压缩你的论证空间", "转移法官注意点", "强化自身版本的合理性"];
    default:
      return ["拖慢你的节奏", "等待你暴露薄弱点", "择机提出程序或事实异议"];
  }
}

function buildMockCrossExaminationLines(
  caseProfile: CaseProfile,
  stage: TrialStage,
  branchFocus: string,
): string[] {
  if (stage === "evidence") {
    return [
      `对你方围绕“${branchFocus}”提交的证据，真实性、合法性、关联性及证明目的均不认可，请先说明原始载体、形成时间和提交主体。`,
      "即便材料形式真实，也不足以单独证明你方主张的法律评价，请逐项说明它与待证事实之间的对应关系。",
    ];
  }

  if (stage === "debate") {
    return [
      `你方围绕“${branchFocus}”的论证更多停留在结论，缺少逐项对应证据和法条的展开。`,
      "请你方说明，哪一组证据能够直接证明你方刚才的核心判断，而不是只是在事实片段上做延伸推测。",
    ];
  }

  if (caseProfile.case_type === "labor_dispute") {
    return [
      `即便存在围绕“${branchFocus}”的管理安排，也不能当然推出劳动关系中的人身隶属性和经济从属性。`,
      "你方如果不能把工作安排、考勤约束和报酬发放连成闭环，就不足以完成劳动关系认定。",
    ];
  }

  return [
    `围绕“${branchFocus}”，对方会持续要求你把概括性说法落到具体事实和证据编号上。`,
  ];
}

function buildMockOpponentLegalReferences(caseProfile: CaseProfile): string[] {
  switch (caseProfile.case_type) {
    case "labor_dispute":
      return [
        "《劳动合同法》第7条、第10条、第82条。",
        "《关于确立劳动关系有关事项的通知》关于劳动关系认定的规则。",
      ];
    case "private_lending":
      return [
        "《民法典》第667条、第675条。",
        "民间借贷司法解释中关于借贷合意、交付款项和利息审查的规则。",
      ];
    case "divorce_dispute":
      return [
        "《民法典》婚姻家庭编关于离婚、共同财产、子女抚养的相关规定。",
      ];
    case "tort_liability":
      return [
        "《民法典》第1165条、第1179条等侵权责任条款。",
      ];
    default:
      return ["围绕争议焦点、举证责任和证明标准组织说理。"];
  }
}

function buildMockOpponentReasoningPaths(
  caseProfile: CaseProfile,
  stage: TrialStage,
  branchFocus: string,
): string[] {
  switch (caseProfile.case_type) {
    case "labor_dispute":
      return [
        `在${getTrialStageMeta(stage).label}阶段先拆劳动关系成立要件，再把“${branchFocus}”解释为业务协作或现场管理需要。`,
        "先否认人身、经济和组织从属性闭环，再即便存在部分管理行为，也强调不足以直接推导劳动关系。",
      ];
    case "private_lending":
      return [
        `在${getTrialStageMeta(stage).label}阶段先拆借贷合意，再拆款项交付属性，最后压缩利息和违约责任范围。`,
      ];
    case "divorce_dispute":
      return [
        `在${getTrialStageMeta(stage).label}阶段把争点从情绪叙事拉回到财产来源、照料事实和证据基础上。`,
      ];
    case "tort_liability":
      return [
        `在${getTrialStageMeta(stage).label}阶段先否认过错，再否认因果关系，最后压低损失结果与责任比例。`,
      ];
    default:
      return ["先拆事实成立，再拆法律评价，最后把举证不能的风险压回对方。"];
  }
}

function buildMockSurpriseActions(
  stage: TrialStage,
  caseProfile: CaseProfile,
  branchFocus: string,
): string[] {
  switch (stage) {
    case "prepare":
      return ["在程序确认阶段临时主张你方申请不具备必要性，试图先锁死调查边界。"];
    case "investigation":
      return [
        `突然要求你说明“${branchFocus}”的具体时间、地点和指令来源，逼你暴露细节摇摆。`,
      ];
    case "evidence":
      return [
        "当庭要求核验原始载体，指控截图、摘录或转述材料存在片段化问题。",
      ];
    case "debate":
      return [
        "抓住你一句未落证据的话，反过来指称你方整体论证缺少闭环。",
      ];
    case "mediation_or_judgment":
      return [
        "一边释放有限调解意愿，一边继续压你的底线，试探你是否会先松口。",
      ];
    default:
      return caseProfile.missing_evidence.length > 0
        ? [`继续围绕“${caseProfile.missing_evidence[0]}”放大证据缺口。`]
        : [];
  }
}

function buildMockRiskPoints(caseProfile: CaseProfile): string[] {
  if (caseProfile.missing_evidence.length === 0) {
    return ["当前主要风险是叙事虽完整，但补强材料还不够扎实。"];
  }

  return caseProfile.missing_evidence
    .slice(0, 2)
    .map((item) => `如果“${item}”迟迟补不上，对方会持续围绕这一点施压。`);
}

function buildMockPositiveFactors(caseProfile: CaseProfile): string[] {
  return [
    "案件主轴已经较为明确，可以围绕单一争点持续推进。",
    caseProfile.claims[0]
      ? `你的核心诉请“${caseProfile.claims[0]}”表达清晰。`
      : "当前诉求方向相对集中。",
  ];
}

function buildMockNegativeFactors(caseProfile: CaseProfile): string[] {
  if (caseProfile.missing_evidence.length > 0) {
    return caseProfile.missing_evidence
      .slice(0, 2)
      .map((item) => `证据缺口仍集中在“${item}”。`);
  }

  return ["目前最大的风险是缺少足够强的补强动作来放大优势。"];
}

function estimateMockWinRate(caseProfile: CaseProfile, stage: TrialStage): number {
  const baseByStage: Record<TrialStage, number> = {
    prepare: 52,
    investigation: 56,
    evidence: 59,
    debate: 62,
    final_statement: 65,
    mediation_or_judgment: 67,
    report_ready: 68,
  };

  return Math.max(
    35,
    baseByStage[stage] - caseProfile.missing_evidence.length * 3,
  );
}

function pickEvidenceStrength(stage: TrialStage): string {
  switch (stage) {
    case "evidence":
    case "debate":
      return "中上";
    default:
      return "中性";
  }
}

function pickProcedureControl(stage: TrialStage): string {
  return stage === "prepare" ? "中上" : "中性";
}

function pickJudgeTrust(stage: TrialStage): string {
  return stage === "final_statement" || stage === "mediation_or_judgment"
    ? "中上"
    : "中性";
}

function pickOpponentPressure(stage: TrialStage): string {
  return stage === "evidence" || stage === "debate" ? "偏高" : "中性";
}

function pickContradictionRisk(stage: TrialStage): string {
  return stage === "investigation" ? "中上" : "中低";
}

function pickSurpriseExposure(stage: TrialStage): string {
  return stage === "evidence" ? "偏高" : "中低";
}

function pickSettlementTendency(stage: TrialStage): string {
  return stage === "mediation_or_judgment" ? "上升" : "中性";
}

function buildInputDrivenNextAction(
  entry: SimulationUserInputEntry,
  caseProfile: CaseProfile,
  snapshot: SimulationSnapshot,
): string {
  const summary = summarizeSimulationUserInputEntry(entry, 36);

  if (caseProfile.case_type === "labor_dispute") {
    switch (entry.input_type) {
      case "fact":
        return `把新事实“${summary}”接到考勤、工作群和报酬发放上，明确它证明的是管理隶属性，不是临时协作。`;
      case "evidence":
        return `把新增证据“${summary}”压成“来源、形成时间、证明劳动关系的哪一层”三句完整表达。`;
      case "cross_exam":
        return `围绕质证意见“${summary}”继续追打三性和证明目的，别让对方把合作关系解释重新扶稳。`;
      case "argument":
        return `把主张“${summary}”压成“存在劳动关系-证据编号-法条依据”两句辩论语。`;
      default:
        break;
    }
  }

  if (caseProfile.case_type === "private_lending") {
    switch (entry.input_type) {
      case "fact":
        return `把新事实“${summary}”放回借款合意、款项交付和催收经过的时间线，不要只孤立陈述。`;
      case "evidence":
        return `把新增证据“${summary}”接到转账、聊天和催款记录的同一链条上。`;
      default:
        break;
    }
  }

  if (caseProfile.case_type === "divorce_dispute") {
    if (entry.input_type === "fact") {
      return `把新事实“${summary}”明确归到离婚条件、财产范围或抚养安排其中一条主线上。`;
    }
  }

  if (caseProfile.case_type === "tort_liability") {
    if (entry.input_type === "fact" || entry.input_type === "evidence") {
      return `把“${summary}”直接接到过错、因果关系或损失金额中的一个节点，不要三头并讲。`;
    }
  }

  switch (entry.input_type) {
    case "evidence":
      return `把新增证据“${summary}”压成来源、时间、证明目的三句完整表达。`;
    case "cross_exam":
      return `围绕你刚写的质证意见“${summary}”继续补强理由和法条。`;
    case "argument":
      return `把主张“${summary}”压缩成可直接开口的两句辩论语。`;
    case "closing_statement":
      return `围绕最后陈述“${summary}”继续收束，不再横向扩题。`;
    case "procedure_request":
      return `把程序申请“${summary}”补成完整理由，避免被法庭直接略过。`;
    case "settlement_position":
      return `围绕调解底线“${summary}”明确可退与不可退的边界。`;
    case "fact":
    default:
      return `围绕你刚补入的事实“${summary}”补齐对应证据和当前${getTrialStageMeta(snapshot.current_stage).label}里的开口说法。`;
  }
}

function buildInputDrivenOpponentArgument(
  entry: SimulationUserInputEntry,
  caseProfile: CaseProfile,
  snapshot: SimulationSnapshot,
): string {
  const summary = summarizeSimulationUserInputEntry(entry, 34);

  if (caseProfile.case_type === "labor_dispute") {
    switch (entry.input_type) {
      case "fact":
        return `主张新事实“${summary}”只是业务配合要求或个别管理片段，不足以证明持续的人身隶属性。`;
      case "evidence":
        return `强调新证据“${summary}”即便真实，也最多证明合作过程中的协作安排，不能直接推出劳动关系。`;
      case "argument":
        return `把你刚抛出的论点“${summary}”改写成“合作经营中的管理便利”，继续否认劳动关系。`;
      default:
        break;
    }
  }

  if (caseProfile.case_type === "private_lending") {
    if (entry.input_type === "fact" || entry.input_type === "evidence") {
      return `主张“${summary}”只能说明资金往来背景，仍不足以排除投资、代付或其他交易关系。`;
    }
  }

  if (caseProfile.case_type === "divorce_dispute") {
    if (entry.input_type === "fact") {
      return `强调“${summary}”只是单一生活片段，不能直接推出长期感情破裂或稳定照料状态。`;
    }
  }

  if (caseProfile.case_type === "tort_liability") {
    if (entry.input_type === "fact" || entry.input_type === "evidence") {
      return `主张“${summary}”不足以单独锁定过错和因果关系，最多只能作为事故经过中的局部细节。`;
    }
  }

  switch (entry.input_type) {
    case "evidence":
      return `质疑你新补证据“${summary}”的真实性、关联性和证明目的。`;
    case "cross_exam":
      return `抓你质证意见“${summary}”里的逻辑跳跃，反过来要求你说明依据。`;
    case "argument":
      return `把你刚抛出的主张“${summary}”改写成对其有利的替代解释。`;
    case "closing_statement":
      return `主张你的最后陈述“${summary}”只是概括性表达，缺少直接支撑。`;
    case "procedure_request":
      return `反对你的程序申请“${summary}”，强调没有必要拖延或扩张调查范围。`;
    case "settlement_position":
      return `试探你围绕“${summary}”设定的底线是否可以继续下压。`;
    case "fact":
    default:
      return `否认你新补事实“${summary}”在当前${getTrialStageMeta(snapshot.current_stage).label}里的外部印证强度，要求你继续举证。`;
  }
}

function buildInputDrivenRisk(
  entry: SimulationUserInputEntry,
  caseProfile: CaseProfile,
  snapshot: SimulationSnapshot,
): string {
  const summary = summarizeSimulationUserInputEntry(entry, 34);

  if (caseProfile.case_type === "labor_dispute") {
    switch (entry.input_type) {
      case "fact":
        return `如果“${summary}”只能证明微信群报送或局部管理，仍不足以单独撑起劳动关系认定，必须继续接上考勤和报酬控制。`;
      case "evidence":
        return `如果“${summary}”说不清形成时间或原始载体，对方会立刻把它打成协作痕迹而不是劳动管理证据。`;
      case "argument":
        return `如果主张“${summary}”没有立刻落到证据编号和法条，法庭辩论阶段会被对方按“空论”处理。`;
      default:
        break;
    }
  }

  if (caseProfile.case_type === "private_lending" && entry.input_type === "fact") {
    return `如果“${summary}”没有回到借贷合意和交付节点，对方很容易把它解释成普通往来。`;
  }

  if (caseProfile.case_type === "divorce_dispute" && entry.input_type === "fact") {
    return `如果“${summary}”没有明确对应离婚、财产或抚养其中一点，法官会把它视为生活枝节。`;
  }

  if (caseProfile.case_type === "tort_liability" && (entry.input_type === "fact" || entry.input_type === "evidence")) {
    return `如果“${summary}”没有明确落到过错、因果关系或损失其中一点，责任链条仍然会断。`;
  }

  switch (entry.input_type) {
    case "evidence":
      return `如果“${summary}”的来源或形成时间说不清，对方会直接从证据三性打穿。`;
    case "cross_exam":
      return `如果质证意见“${summary}”没有对应事实和法条支撑，容易被法官认为空泛。`;
    case "argument":
      return `如果主张“${summary}”没有及时落到证据和法理，会在辩论阶段失真。`;
    default:
      return `你刚补入的“${summary}”如果没有在${getTrialStageMeta(snapshot.current_stage).label}里继续补强，会被对方当成新的攻击口。`;
  }
}

function buildInputDrivenReportOverview(
  snapshot: SimulationSnapshot,
  entry: SimulationUserInputEntry,
): string {
  const stageLabel = getTrialStageMeta(snapshot.current_stage).label;
  const summary = summarizeSimulationUserInputEntry(entry, 40);
  return `本轮已推进至${stageLabel}。你补入的${entry.label}“${summary}”已经改变本轮推演重点，后续分析将围绕这条新增材料继续收束。`;
}

function getInputDrivenWinRateShift(
  entry: SimulationUserInputEntry,
  snapshot: SimulationSnapshot,
): number {
  const isDebateLikeStage =
    snapshot.current_stage === "debate" ||
    snapshot.current_stage === "final_statement";

  switch (entry.input_type) {
    case "evidence":
      return 4;
    case "argument":
    case "cross_exam":
      return isDebateLikeStage ? 4 : 3;
    case "closing_statement":
      return isDebateLikeStage ? 4 : 3;
    case "fact":
    case "procedure_request":
      return 2;
    case "settlement_position":
      return 1;
    default:
      return 0;
  }
}

function getInputDrivenConfidenceShift(
  entry: SimulationUserInputEntry,
  snapshot: SimulationSnapshot,
): number {
  const isDebateLikeStage =
    snapshot.current_stage === "debate" ||
    snapshot.current_stage === "final_statement";

  switch (entry.input_type) {
    case "evidence":
      return 0.05;
    case "argument":
    case "cross_exam":
      return isDebateLikeStage ? 0.05 : 0.04;
    case "closing_statement":
      return isDebateLikeStage ? 0.04 : 0.02;
    default:
      return 0.02;
  }
}

function dedupeStrings(values: string[]): string[] {
  const seen = new Set<string>();
  const nextValues: string[] = [];

  for (const value of values) {
    const normalized = value.replace(/\s+/g, " ").trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }

    seen.add(normalized);
    nextValues.push(normalized);
  }

  return nextValues;
}

function clampNumber(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
