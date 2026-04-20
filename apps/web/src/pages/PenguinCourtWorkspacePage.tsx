import { useEffect, useMemo, useRef, useState } from "react";
import { buildCaseProfileFromDraft, createEmptyCaseIntakeDraft, type CaseIntakeDraft } from "../features/case-intake/draft";
import { FEATURED_DEMO_PRESETS } from "../features/case-intake/demo-case-presets";
import { caseTypeOptionsByDomain, domainOptions, userGoalOptions, userPerspectiveOptions } from "../features/case-intake/options";
import {
  analyzeWinRate,
  createCase,
  generateReplayReport,
  getLatestOpponentBehaviorSnapshot,
  getLatestReplayReport,
  getLatestWinRateAnalysis,
  getOpponentBehaviorSnapshot,
} from "../services/api/cases";
import type { OpponentBehaviorSnapshot, ReplayReportSnapshot, WinRateAnalysisSnapshot } from "../types/analysis";
import type { CaseDomain, CaseProfile, CaseType, UserGoal, UserPerspectiveRole } from "../types/case";
import {
  formatFocusLabel,
  formatStateKeyLabel,
  formatTrialStageLabel,
} from "../types/display";
import type { SimulationSnapshot } from "../types/turn";
import { TrialSimulationPage } from "./TrialSimulationPage";
import {
  WORKSPACE_STORAGE_KEY,
  cloneDraft,
  createLocalOpponentSnapshot,
  createLocalReplayReport,
  createLocalWinRateSnapshot,
  deriveOpponentSnapshotFromSimulation,
  deriveReplayReportFromSimulation,
  deriveWinRateSnapshotFromSimulation,
  formatDateTime,
  formatPercent,
  looksLikeEnglishReplayReport,
  mergeOpponentSnapshots,
  mergeReplayReports,
  mergeWinRateSnapshots,
  normalizeOpponentSnapshot,
  normalizeWinRateSnapshot,
  parseStoredWorkspaceState,
  validateDraft,
  type PersistedWorkspaceState,
  type SessionCaseRecord,
  type WorkspaceStage,
} from "./workspace-utils";

type BusyAction = "save_case" | "opponent" | "win_rate" | "replay" | null;

export type { PersistedWorkspaceState, SessionCaseRecord } from "./workspace-utils";
export { WORKSPACE_STORAGE_KEY, parseStoredWorkspaceState } from "./workspace-utils";

const STAGES: Array<{ key: WorkspaceStage; label: string; description: string }> = [
  { key: "intake", label: "案件录入", description: "整理标准输入，确定案件主线。" },
  { key: "simulation", label: "庭审模拟", description: "进入文游式庭审推进。" },
  { key: "opponent", label: "对方推演", description: "预判对方证据与抗辩。" },
  { key: "win_rate", label: "胜诉率分析", description: "识别优势、风险与补强点。" },
  { key: "replay", label: "复盘报告", description: "收束结论，形成复盘文本。" },
];

const CASE_TYPE_LABELS: Record<string, string> = {
  private_lending: "民间借贷",
  labor_dispute: "劳动争议",
  divorce_dispute: "离婚纠纷",
  tort_liability: "侵权责任",
};

function matchesSimulationArtifact(
  artifact: { simulation_id: string } | null | undefined,
  simulationId: string | null,
): boolean {
  return Boolean(artifact && simulationId && artifact.simulation_id === simulationId);
}

interface PenguinCourtWorkspacePageProps {
  onBack?: () => void;
  hideSessionCasesPanel?: boolean;
}

function getCaseTypeLabel(caseType: string | undefined): string {
  if (!caseType) return "未分类";
  return CASE_TYPE_LABELS[caseType] ?? caseType;
}

export function PenguinCourtWorkspacePage({ onBack, hideSessionCasesPanel = false }: PenguinCourtWorkspacePageProps): JSX.Element {
  const [draft, setDraft] = useState<CaseIntakeDraft>(createEmptyCaseIntakeDraft());
  const [currentCase, setCurrentCase] = useState<CaseProfile | null>(null);
  const [simulationSnapshot, setSimulationSnapshot] = useState<SimulationSnapshot | null>(null);
  const [opponentSnapshot, setOpponentSnapshot] = useState<OpponentBehaviorSnapshot | null>(null);
  const [winRateSnapshot, setWinRateSnapshot] = useState<WinRateAnalysisSnapshot | null>(null);
  const [replayReport, setReplayReport] = useState<ReplayReportSnapshot | null>(null);
  const [activeStage, setActiveStage] = useState<WorkspaceStage>("intake");
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [sessionCases, setSessionCases] = useState<SessionCaseRecord[]>([]);
  const [isMockMode, setIsMockMode] = useState(false);
  const [hasRestoredWorkspace, setHasRestoredWorkspace] = useState(false);
  const latestSimulationIdRef = useRef<string | null>(null);

  const currentCaseId = currentCase?.case_id ?? null;
  const currentSimulationId = simulationSnapshot?.simulation_id ?? null;
  const caseTypeOptions = caseTypeOptionsByDomain[draft.domain];
  const simulationUsesMock = isMockMode || Boolean(currentCaseId?.startsWith("MOCK-"));
  const showMockBadge =
    simulationUsesMock &&
    Boolean(currentCase) &&
    Boolean(simulationSnapshot || opponentSnapshot || winRateSnapshot || replayReport);
  const activeStageMeta = useMemo(() => STAGES.find((stage) => stage.key === activeStage) ?? STAGES[0], [activeStage]);
  const isSimulationStage = activeStage === "simulation";
  const derivedOpponentSnapshot = useMemo(
    () => deriveOpponentSnapshotFromSimulation(simulationSnapshot),
    [simulationSnapshot],
  );
  const localOpponentSnapshot = useMemo(
    () =>
      currentCase && simulationSnapshot
        ? createLocalOpponentSnapshot(currentCase, simulationSnapshot)
        : null,
    [currentCase, simulationSnapshot],
  );
  const effectiveOpponentSnapshot = useMemo(() => {
    if (simulationUsesMock) {
      if (!opponentSnapshot) {
        return null;
      }

      return mergeOpponentSnapshots(opponentSnapshot, localOpponentSnapshot);
    }

    return normalizeOpponentSnapshot(opponentSnapshot ?? derivedOpponentSnapshot);
  }, [
    derivedOpponentSnapshot,
    localOpponentSnapshot,
    opponentSnapshot,
    simulationUsesMock,
  ]);
  const derivedWinRateSnapshot = useMemo(
    () => deriveWinRateSnapshotFromSimulation(simulationSnapshot),
    [simulationSnapshot],
  );
  const localWinRateSnapshot = useMemo(
    () =>
      currentCase && simulationSnapshot
        ? createLocalWinRateSnapshot(
            currentCase,
            simulationSnapshot,
            effectiveOpponentSnapshot,
          )
        : null,
    [currentCase, effectiveOpponentSnapshot, simulationSnapshot],
  );
  const effectiveWinRateSnapshot = useMemo(() => {
    if (simulationUsesMock) {
      if (!winRateSnapshot) {
        return null;
      }

      return mergeWinRateSnapshots(winRateSnapshot, localWinRateSnapshot);
    }

    return normalizeWinRateSnapshot(winRateSnapshot ?? derivedWinRateSnapshot);
  }, [
    derivedWinRateSnapshot,
    localWinRateSnapshot,
    simulationUsesMock,
    winRateSnapshot,
  ]);
  const derivedReplayReport = useMemo(
    () => deriveReplayReportFromSimulation(simulationSnapshot),
    [simulationSnapshot],
  );
  const localReplayReport = useMemo(
    () =>
      currentCase && simulationSnapshot
        ? createLocalReplayReport(
            currentCase,
            simulationSnapshot,
            effectiveWinRateSnapshot,
            effectiveOpponentSnapshot,
          )
        : null,
    [
      currentCase,
      effectiveOpponentSnapshot,
      effectiveWinRateSnapshot,
      simulationSnapshot,
    ],
  );
  const replayReportNeedsChineseFallback = looksLikeEnglishReplayReport(replayReport);
  const effectiveReplayReport = useMemo(() => {
    if (simulationUsesMock) {
      if (!replayReport) {
        return null;
      }

      return mergeReplayReports(replayReport, localReplayReport);
    }

    return replayReport && !replayReportNeedsChineseFallback
      ? mergeReplayReports(replayReport, derivedReplayReport)
      : mergeReplayReports(derivedReplayReport ?? replayReport, null);
  }, [
    derivedReplayReport,
    localReplayReport,
    replayReport,
    replayReportNeedsChineseFallback,
    simulationUsesMock,
  ]);

  useEffect(() => {
    if (typeof window === "undefined") {
      setHasRestoredWorkspace(true);
      return;
    }
    const restored = parseStoredWorkspaceState(window.localStorage.getItem(WORKSPACE_STORAGE_KEY));
    if (restored) {
      latestSimulationIdRef.current = restored.simulationSnapshot?.simulation_id ?? null;
      setDraft(cloneDraft(restored.draft));
      setCurrentCase(restored.currentCase);
      setSimulationSnapshot(restored.simulationSnapshot);
      setOpponentSnapshot(restored.opponentSnapshot);
      setWinRateSnapshot(restored.winRateSnapshot);
      setReplayReport(restored.replayReport);
      setActiveStage(restored.activeStage);
      setSessionCases(restored.sessionCases);
      setIsMockMode(restored.isMockMode);
    }
    setHasRestoredWorkspace(true);
  }, []);

  useEffect(() => {
    if (!hasRestoredWorkspace || typeof window === "undefined") return;
    const nextState: PersistedWorkspaceState = { draft: cloneDraft(draft), currentCase, simulationSnapshot, opponentSnapshot: effectiveOpponentSnapshot, winRateSnapshot: effectiveWinRateSnapshot, replayReport: effectiveReplayReport, activeStage, sessionCases, isMockMode };
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(nextState));
  }, [activeStage, currentCase, draft, effectiveOpponentSnapshot, effectiveReplayReport, effectiveWinRateSnapshot, hasRestoredWorkspace, isMockMode, sessionCases, simulationSnapshot]);

  useEffect(() => {
    if (
      !hasRestoredWorkspace ||
      !currentCaseId ||
      !currentSimulationId ||
      simulationUsesMock
    ) {
      return;
    }

    const resolvedCaseId = currentCaseId;
    const resolvedSimulationId = currentSimulationId;

    const needsOpponentHydration = !matchesSimulationArtifact(
      opponentSnapshot,
      resolvedSimulationId,
    );
    const needsWinRateHydration = !matchesSimulationArtifact(
      winRateSnapshot,
      resolvedSimulationId,
    );
    const needsReplayHydration = !matchesSimulationArtifact(
      replayReport,
      resolvedSimulationId,
    ) || looksLikeEnglishReplayReport(replayReport);

    if (
      !needsOpponentHydration &&
      !needsWinRateHydration &&
      !needsReplayHydration
    ) {
      return;
    }

    let cancelled = false;

    async function hydrateLatestArtifacts(): Promise<void> {
      const [opponentResult, winRateResult, replayResult] =
        await Promise.allSettled([
          needsOpponentHydration
            ? getLatestOpponentBehaviorSnapshot(resolvedCaseId)
            : Promise.resolve(null),
          needsWinRateHydration
            ? getLatestWinRateAnalysis(resolvedCaseId)
            : Promise.resolve(null),
          needsReplayHydration
            ? getLatestReplayReport(resolvedCaseId)
            : Promise.resolve(null),
        ]);

      if (cancelled) {
        return;
      }

      if (
        opponentResult.status === "fulfilled" &&
        opponentResult.value &&
        opponentResult.value.simulation_id === resolvedSimulationId
      ) {
        setOpponentSnapshot(opponentResult.value);
      }

      if (
        winRateResult.status === "fulfilled" &&
        winRateResult.value &&
        winRateResult.value.simulation_id === resolvedSimulationId
      ) {
        setWinRateSnapshot(winRateResult.value);
      }

      if (
        replayResult.status === "fulfilled" &&
        replayResult.value &&
        replayResult.value.simulation_id === resolvedSimulationId &&
        !looksLikeEnglishReplayReport(replayResult.value)
      ) {
        setReplayReport(replayResult.value);
      }
    }

    void hydrateLatestArtifacts();

    return () => {
      cancelled = true;
    };
  }, [
    currentCaseId,
    currentSimulationId,
    hasRestoredWorkspace,
    opponentSnapshot,
    replayReport,
    simulationUsesMock,
    winRateSnapshot,
  ]);

  useEffect(() => {
    if (!currentCase || !currentCase.case_id) {
      return;
    }

    upsertSessionCaseRecord({
      caseId: currentCase.case_id,
      caseProfile: currentCase,
      draftSnapshot: cloneDraft(draft),
      simulationSnapshot,
      opponentSnapshot: effectiveOpponentSnapshot,
      winRateSnapshot: effectiveWinRateSnapshot,
      replayReport: effectiveReplayReport,
      lastVisitedStage: activeStage,
    });
  }, [
    activeStage,
    currentCase,
    draft,
    effectiveOpponentSnapshot,
    effectiveReplayReport,
    effectiveWinRateSnapshot,
    simulationSnapshot,
  ]);

  const stageEnabled: Record<WorkspaceStage, boolean> = {
    intake: true,
    simulation: Boolean(currentCaseId),
    opponent: Boolean(currentSimulationId),
    win_rate: Boolean(currentSimulationId),
    replay: Boolean(currentSimulationId),
  };
  const stageComplete: Record<WorkspaceStage, boolean> = {
    intake: Boolean(currentCaseId),
    simulation: Boolean(currentSimulationId),
    opponent: Boolean(effectiveOpponentSnapshot),
    win_rate: Boolean(effectiveWinRateSnapshot),
    replay: Boolean(effectiveReplayReport),
  };
  const showSimulationCompletionRail =
    activeStage === "simulation" &&
    simulationSnapshot?.current_stage === "report_ready";

  function setFeedback(error: string | null, success: string | null): void {
    setErrorMessage(error);
    setSuccessMessage(success);
  }

  function resetGeneratedState(nextStage: WorkspaceStage): void {
    latestSimulationIdRef.current = null;
    setSimulationSnapshot(null);
    setOpponentSnapshot(null);
    setWinRateSnapshot(null);
    setReplayReport(null);
    setActiveStage(nextStage);
  }

  function upsertSessionCaseRecord(record: Omit<SessionCaseRecord, "updatedAt">): void {
    setSessionCases((previous) => [{ ...record, updatedAt: new Date().toISOString() }, ...previous.filter((item) => item.caseId !== record.caseId)]);
  }

  async function handleCreateCase(): Promise<void> {
    const validationError = validateDraft(draft);
    if (validationError) {
      setFeedback(validationError, null);
      return;
    }
    setBusyAction("save_case");
    setFeedback(null, null);
    const nextProfile = buildCaseProfileFromDraft(draft);
    try {
      try {
        const createdCase = await createCase(nextProfile);
        const resolvedCase = { ...createdCase, case_id: createdCase.case_id ?? `CASE-${Date.now()}` };
        setCurrentCase(resolvedCase);
        setIsMockMode(false);
        resetGeneratedState("simulation");
        upsertSessionCaseRecord({ caseId: resolvedCase.case_id!, caseProfile: resolvedCase, draftSnapshot: cloneDraft(draft), simulationSnapshot: null, opponentSnapshot: null, winRateSnapshot: null, replayReport: null, lastVisitedStage: "simulation" });
        setFeedback(null, "案件已创建，现在可以进入庭审模拟。");
      } catch {
        const fallbackCase: CaseProfile = { ...nextProfile, case_id: `MOCK-${Date.now()}` };
        setCurrentCase(fallbackCase);
        setIsMockMode(true);
        resetGeneratedState("simulation");
        upsertSessionCaseRecord({ caseId: fallbackCase.case_id!, caseProfile: fallbackCase, draftSnapshot: cloneDraft(draft), simulationSnapshot: null, opponentSnapshot: null, winRateSnapshot: null, replayReport: null, lastVisitedStage: "simulation" });
        setFeedback(null, "后端暂未连通，已切换为演示数据模式。");
      }
    } finally {
      setBusyAction(null);
    }
  }

  function handleSimulationSnapshotUpdate(nextSnapshot: SimulationSnapshot | null): void {
    setSimulationSnapshot(nextSnapshot);
    if (!nextSnapshot || !currentCase || !currentCase.case_id) return;
    if (latestSimulationIdRef.current !== nextSnapshot.simulation_id) {
      setOpponentSnapshot(null);
      setWinRateSnapshot(null);
      setReplayReport(null);
    }
    latestSimulationIdRef.current = nextSnapshot.simulation_id;
    setActiveStage("simulation");
    upsertSessionCaseRecord({ caseId: currentCase.case_id, caseProfile: currentCase, draftSnapshot: cloneDraft(draft), simulationSnapshot: nextSnapshot, opponentSnapshot: null, winRateSnapshot: null, replayReport: null, lastVisitedStage: "simulation" });
  }

  async function handleGenerateOpponent(): Promise<void> {
    if (!currentCase || !simulationSnapshot || !currentCaseId || !currentSimulationId) {
      setFeedback("请先完成案件创建与庭审模拟。", null);
      return;
    }
    setBusyAction("opponent");
    try {
      const snapshot = simulationUsesMock ? createLocalOpponentSnapshot(currentCase, simulationSnapshot) : await getOpponentBehaviorSnapshot(currentCaseId, currentSimulationId).catch(() => createLocalOpponentSnapshot(currentCase, simulationSnapshot));
      setOpponentSnapshot(snapshot);
      setActiveStage("opponent");
      setFeedback(null, "对方推演已生成。");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleGenerateWinRate(): Promise<void> {
    if (!currentCase || !simulationSnapshot || !currentCaseId || !currentSimulationId) {
      setFeedback("请先完成案件创建与庭审模拟。", null);
      return;
    }
    if (!effectiveOpponentSnapshot) {
      setFeedback("请先生成对方推演。", null);
      return;
    }
    setBusyAction("win_rate");
    try {
      const snapshot = simulationUsesMock ? createLocalWinRateSnapshot(currentCase, simulationSnapshot, effectiveOpponentSnapshot) : await analyzeWinRate(currentCaseId, currentSimulationId).catch(() => createLocalWinRateSnapshot(currentCase, simulationSnapshot, effectiveOpponentSnapshot));
      setWinRateSnapshot(snapshot);
      setActiveStage("win_rate");
      setFeedback(null, "胜诉率分析已生成。");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleGenerateReplay(): Promise<void> {
    if (!currentCase || !simulationSnapshot || !currentCaseId || !currentSimulationId) {
      setFeedback("请先完成案件创建与庭审模拟。", null);
      return;
    }
    if (!effectiveWinRateSnapshot) {
      setFeedback("请先生成胜诉率分析。", null);
      return;
    }
    setBusyAction("replay");
    try {
      const report = simulationUsesMock ? createLocalReplayReport(currentCase, simulationSnapshot, effectiveWinRateSnapshot, effectiveOpponentSnapshot) : await generateReplayReport(currentCaseId, currentSimulationId).catch(() => createLocalReplayReport(currentCase, simulationSnapshot, effectiveWinRateSnapshot, effectiveOpponentSnapshot));
      setReplayReport(report);
      setActiveStage("replay");
      setFeedback(null, "复盘报告已生成。");
    } finally {
      setBusyAction(null);
    }
  }

  function handleGoalToggle(goal: UserGoal): void {
    setDraft((previous) => ({ ...previous, user_goals: previous.user_goals.includes(goal) ? previous.user_goals.filter((item) => item !== goal) : [...previous.user_goals, goal] }));
  }

  return (
    <main
      className={[
        "workspace-shell",
        isSimulationStage ? "workspace-shell--simulation-mode" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="workspace-topbar" hidden={isSimulationStage}>
        <div className="workspace-topbar__lead">
          {onBack ? (
            <button type="button" className="workspace-button workspace-button--ghost" onClick={onBack}>
              返回首页
            </button>
          ) : null}
          <div className="workspace-topbar__lead-copy">
            <p className="workspace-topbar__eyebrow">企鹅法庭</p>
            <h1 className="workspace-topbar__title">{currentCase?.title ?? "新建案件"}</h1>
          </div>
        </div>
        <div className="workspace-topbar__status-group">
          <span className="workspace-topbar__status workspace-topbar__status--stage">{activeStageMeta.label}</span>
          {currentCase ? <span className="workspace-topbar__status">{getCaseTypeLabel(currentCase.case_type)}</span> : null}
          {showMockBadge ? (
            <span className="workspace-topbar__status workspace-topbar__status--mock">本地演示</span>
          ) : null}
        </div>
      </div>

      <nav
        className="workspace-stage-strip"
        aria-label="工作台阶段"
        hidden={isSimulationStage}
      >
        {STAGES.map((stage, index) => (
          <button
            key={stage.key}
            type="button"
            className={[
              "workspace-stage-pill",
              activeStage === stage.key ? "is-current" : "",
              stageComplete[stage.key] ? "is-completed" : "",
              !stageEnabled[stage.key] ? "is-locked" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            disabled={!stageEnabled[stage.key]}
            onClick={() => setActiveStage(stage.key)}
          >
            <span className="workspace-stage-pill__index">0{index + 1}</span>
            <span className="workspace-stage-pill__content">
              <strong>{stage.label}</strong>
            </span>
          </button>
        ))}
      </nav>

      <div className="workspace-body">
        <section className="workspace-main">
          {errorMessage ? <section className="workspace-feedback workspace-feedback--error">{errorMessage}</section> : null}
          {successMessage && !isSimulationStage ? (
            <section className="workspace-feedback workspace-feedback--success">
              {successMessage}
            </section>
          ) : null}

          <section className="workspace-stage-panel" hidden={activeStage !== "intake"}>
            <header className="workspace-stage-panel__header workspace-stage-panel__header--compact">
              <div>
                <p className="workspace-stage-panel__eyebrow">阶段 01</p>
                <h2 className="workspace-stage-panel__title">案件录入</h2>
              </div>
            </header>

            <div className="intake-block-list">
              <section className="intake-block intake-block--template">
                <div className="intake-block__header intake-block__header--inline">
                  <div>
                    <p className="intake-block__eyebrow">快速开始</p>
                    <h3 className="intake-block__title">示例模板</h3>
                  </div>
                  <div className="intake-template-bar__actions">
                    {FEATURED_DEMO_PRESETS.map((preset) => (
                      <button
                        key={preset.id}
                        type="button"
                        className="workspace-button workspace-button--secondary"
                        onClick={() => setDraft(cloneDraft(preset.draft))}
                      >
                        {preset.label}
                      </button>
                    ))}
                    <button
                      type="button"
                      className="workspace-button workspace-button--ghost"
                      onClick={() => {
                        setDraft(createEmptyCaseIntakeDraft());
                        setCurrentCase(null);
                        setIsMockMode(false);
                        resetGeneratedState("intake");
                      }}
                    >
                      清空表单
                    </button>
                  </div>
                </div>
              </section>

              <section className="intake-block">
                <div className="intake-block__header">
                  <p className="intake-block__eyebrow">基础信息</p>
                  <h3 className="intake-block__title">案件信息</h3>
                </div>
                <div className="intake-grid">
                  <label className="intake-field">
                    <span className="intake-field__label">案件领域</span>
                    <select
                      value={draft.domain}
                      onChange={(event) =>
                        setDraft((previous) => ({
                          ...previous,
                          domain: event.target.value as CaseDomain,
                          case_type:
                            caseTypeOptionsByDomain[event.target.value as CaseDomain][0]?.value ?? "private_lending",
                        }))
                      }
                    >
                      {domainOptions.map((option) => (
                        <option key={option.value} value={option.value} disabled={option.disabled}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="intake-field">
                    <span className="intake-field__label">案件类型</span>
                    <select
                      value={draft.case_type}
                      onChange={(event) =>
                        setDraft((previous) => ({ ...previous, case_type: event.target.value as CaseType }))
                      }
                    >
                      {caseTypeOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="intake-field is-wide">
                    <span className="intake-field__label">案件标题</span>
                    <input
                      value={draft.title}
                      onChange={(event) => setDraft((previous) => ({ ...previous, title: event.target.value }))}
                      placeholder="例如：未签劳动合同双倍工资争议"
                    />
                  </label>

                  <label className="intake-field is-wide">
                    <span className="intake-field__label">案件概述</span>
                    <textarea
                      rows={4}
                      value={draft.summary}
                      onChange={(event) => setDraft((previous) => ({ ...previous, summary: event.target.value }))}
                      placeholder="概括争议背景、关键事实与主要诉求。"
                    />
                  </label>
                </div>
              </section>

              <section className="intake-block">
                <div className="intake-block__header">
                  <p className="intake-block__eyebrow">策略设定</p>
                  <h3 className="intake-block__title">使用方式</h3>
                </div>
                <div className="intake-grid">
                  <label className="intake-field">
                    <span className="intake-field__label">使用视角</span>
                    <select
                      value={draft.user_perspective_role}
                      onChange={(event) =>
                        setDraft((previous) => ({
                          ...previous,
                          user_perspective_role: event.target.value as UserPerspectiveRole,
                        }))
                      }
                    >
                      {userPerspectiveOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="intake-field">
                    <span className="intake-field__label">本次目标</span>
                    <div className="goal-grid">
                      {userGoalOptions.map((option) => (
                        <label key={option.value} className="goal-option">
                          <input
                            type="checkbox"
                            checked={draft.user_goals.includes(option.value)}
                            onChange={() => handleGoalToggle(option.value)}
                          />
                          <span>{option.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </section>

              <section className="intake-block">
                <div className="intake-block__header">
                  <p className="intake-block__eyebrow">当事人与争点</p>
                  <h3 className="intake-block__title">事实与诉求</h3>
                </div>
                <div className="intake-grid">
                  <label className="intake-field">
                    <span className="intake-field__label">原告 / 申请人</span>
                    <input
                      value={draft.plaintiff_name}
                      onChange={(event) => setDraft((previous) => ({ ...previous, plaintiff_name: event.target.value }))}
                    />
                  </label>

                  <label className="intake-field">
                    <span className="intake-field__label">被告 / 被申请人</span>
                    <input
                      value={draft.defendant_name}
                      onChange={(event) => setDraft((previous) => ({ ...previous, defendant_name: event.target.value }))}
                    />
                  </label>

                  <label className="intake-field is-wide">
                    <span className="intake-field__label">诉讼请求</span>
                    <textarea
                      rows={4}
                      value={draft.claims_text}
                      onChange={(event) => setDraft((previous) => ({ ...previous, claims_text: event.target.value }))}
                    />
                  </label>

                  <label className="intake-field is-wide">
                    <span className="intake-field__label">核心事实</span>
                    <textarea
                      rows={4}
                      value={draft.core_facts_text}
                      onChange={(event) => setDraft((previous) => ({ ...previous, core_facts_text: event.target.value }))}
                    />
                  </label>

                  <label className="intake-field is-wide">
                    <span className="intake-field__label">争议焦点</span>
                    <textarea
                      rows={4}
                      value={draft.focus_issues_text}
                      onChange={(event) => setDraft((previous) => ({ ...previous, focus_issues_text: event.target.value }))}
                    />
                  </label>

                  <label className="intake-field is-wide">
                    <span className="intake-field__label">缺口证据</span>
                    <textarea
                      rows={4}
                      value={draft.missing_evidence_text}
                      onChange={(event) => setDraft((previous) => ({ ...previous, missing_evidence_text: event.target.value }))}
                    />
                  </label>

                  <label className="intake-field is-wide">
                    <span className="intake-field__label">补充备注</span>
                    <textarea
                      rows={4}
                      value={draft.notes}
                      onChange={(event) => setDraft((previous) => ({ ...previous, notes: event.target.value }))}
                    />
                  </label>
                </div>
              </section>
            </div>

            <footer className="intake-submit-bar">
              <button
                type="button"
                className="workspace-button workspace-button--primary"
                onClick={() => void handleCreateCase()}
                disabled={busyAction === "save_case"}
              >
                {busyAction === "save_case" ? "创建中..." : "创建案件"}
              </button>
            </footer>
          </section>

          <section
            className={[
              "workspace-stage-panel",
              "workspace-stage-panel--simulation",
            ].join(" ")}
            hidden={activeStage !== "simulation"}
          >

            {currentCase && currentCaseId ? (
              <>
                <TrialSimulationPage
                  caseId={currentCaseId}
                  initialSnapshot={simulationSnapshot}
                  initialCaseProfile={currentCase}
                  preferMock={simulationUsesMock}
                  onSnapshotUpdate={handleSimulationSnapshotUpdate}
                  embedded
                />
                {showSimulationCompletionRail ? (
                  <section
                    className="simulation-completion-rail"
                    aria-label="模拟结束后的下一步"
                  >
                    <div className="simulation-completion-rail__copy">
                      <p className="simulation-completion-rail__eyebrow">本轮已收束</p>
                      <h3 className="simulation-completion-rail__title">
                        庭审模拟已经结束，继续进入后续分析。
                      </h3>
                    </div>

                    <div className="simulation-completion-rail__actions">
                      <button
                        type="button"
                        className="workspace-button workspace-button--secondary"
                        onClick={() => setActiveStage("opponent")}
                      >
                        去对方推演
                      </button>
                      <button
                        type="button"
                        className="workspace-button workspace-button--secondary"
                        onClick={() => setActiveStage("win_rate")}
                      >
                        去胜诉率分析
                      </button>
                      <button
                        type="button"
                        className="workspace-button workspace-button--primary"
                        onClick={() => setActiveStage("replay")}
                      >
                        去复盘报告
                      </button>
                    </div>
                  </section>
                ) : null}
              </>
            ) : (
              <section className="stage-empty-state">
                <h3>还没有可模拟的案件</h3>
                <p>请先完成案件录入并创建案件。</p>
              </section>
            )}
          </section>

          <section className="workspace-stage-panel" hidden={activeStage !== "opponent"}>
            <header className="workspace-stage-panel__header">
              <div>
                <p className="workspace-stage-panel__eyebrow">阶段 03</p>
                <h2 className="workspace-stage-panel__title">对方推演</h2>
              </div>
              <div className="workspace-stage-panel__actions">
                <button
                  type="button"
                  className="workspace-button workspace-button--primary"
                  onClick={() => void handleGenerateOpponent()}
                  disabled={busyAction === "opponent" || !simulationSnapshot}
                >
                  {busyAction === "opponent" ? "生成中..." : "生成推演"}
                </button>
              </div>
            </header>

            {effectiveOpponentSnapshot ? (
              <div className="analysis-grid analysis-grid--balanced">
                <article className="analysis-card analysis-card--summary">
                  <h3>对方画像</h3>
                  <dl className="analysis-card__meta-list">
                    <div>
                      <dt>对方名称</dt>
                      <dd>{effectiveOpponentSnapshot.opponent_name || "未识别"}</dd>
                    </div>
                    <div>
                      <dt>对方角色</dt>
                      <dd>{effectiveOpponentSnapshot.opponent_role || "未识别"}</dd>
                    </div>
                    <div>
                      <dt>当前焦点</dt>
                      <dd>
                        {formatFocusLabel(effectiveOpponentSnapshot.branch_focus) || "未指定"}
                      </dd>
                    </div>
                    <div>
                      <dt>压制强度</dt>
                      <dd>{formatPercent(effectiveOpponentSnapshot.confidence)}</dd>
                    </div>
                  </dl>
                  <div className="analysis-card__section">
                    <h4>风险提醒</h4>
                    {renderList(effectiveOpponentSnapshot.risk_points, "暂无高风险提醒。", {
                      maxItems: 4,
                    })}
                  </div>
                  <div className="analysis-card__section">
                    <h4>突袭动作</h4>
                    {renderList(
                      effectiveOpponentSnapshot.surprise_attack_actions,
                      "暂无明显突袭动作。",
                      { maxItems: 3 },
                    )}
                  </div>
                </article>

                <article className="analysis-card">
                  <h3>预计动作</h3>
                  <div className="analysis-card__section">
                    <h4>可能抗辩</h4>
                    {renderList(effectiveOpponentSnapshot.likely_arguments, "暂无抗辩预测。", {
                      maxItems: 4,
                    })}
                  </div>
                  <div className="analysis-card__section">
                    <h4>可能证据</h4>
                    {renderList(effectiveOpponentSnapshot.likely_evidence, "暂无证据预测。", {
                      maxItems: 4,
                    })}
                  </div>
                  <div className="analysis-card__section">
                    <h4>可能策略</h4>
                    {renderList(effectiveOpponentSnapshot.likely_strategies, "暂无策略预测。", {
                      maxItems: 3,
                    })}
                  </div>
                </article>

                <article className="analysis-card">
                  <h3>法庭上的说法</h3>
                  <div className="analysis-card__section">
                    <h4>可能质证话术</h4>
                    {renderList(
                      effectiveOpponentSnapshot.likely_cross_examination_lines,
                      "暂无质证话术预测。",
                      { maxItems: 3 },
                    )}
                  </div>
                  <div className="analysis-card__section">
                    <h4>可能援引法条</h4>
                    {renderList(
                      effectiveOpponentSnapshot.likely_legal_references,
                      "暂无法条援引预测。",
                      { maxItems: 3 },
                    )}
                  </div>
                  <div className="analysis-card__section">
                    <h4>可能说理路径</h4>
                    {renderList(
                      effectiveOpponentSnapshot.likely_reasoning_paths,
                      "暂无说理路径预测。",
                      { maxItems: 3 },
                    )}
                  </div>
                </article>

                <article className="analysis-card">
                  <h3>我方应对</h3>
                  {renderList(effectiveOpponentSnapshot.recommended_responses, "暂无应对建议。", {
                    maxItems: 4,
                  })}
                </article>
              </div>
            ) : (
              <section className="stage-empty-state">
                <h3>尚未生成对方推演</h3>
                <p>点击上方生成推演。</p>
              </section>
            )}
          </section>

          <section className="workspace-stage-panel" hidden={activeStage !== "win_rate"}>
            <header className="workspace-stage-panel__header">
              <div>
                <p className="workspace-stage-panel__eyebrow">阶段 04</p>
                <h2 className="workspace-stage-panel__title">胜诉率分析</h2>
              </div>
              <div className="workspace-stage-panel__actions">
                <button
                  type="button"
                  className="workspace-button workspace-button--primary"
                  onClick={() => void handleGenerateWinRate()}
                  disabled={busyAction === "win_rate" || !simulationSnapshot || !effectiveOpponentSnapshot}
                >
                  {busyAction === "win_rate" ? "生成中..." : "生成分析"}
                </button>
              </div>
            </header>

            {effectiveWinRateSnapshot ? (
              <>
                <section className="win-rate-hero">
                  <span className="win-rate-hero__label">当前估计胜诉率</span>
                  <strong className="win-rate-hero__value">
                    {formatPercent(effectiveWinRateSnapshot.estimated_win_rate)}
                  </strong>
                  <span className="win-rate-hero__confidence">
                    置信度 {formatPercent(effectiveWinRateSnapshot.confidence)}
                  </span>
                </section>
                <div className="analysis-grid analysis-grid--balanced">
                  <article className="analysis-card analysis-card--summary">
                    <h3>当前判断</h3>
                    <dl className="analysis-card__meta-list">
                      <div>
                        <dt>当前阶段</dt>
                        <dd>{formatTrialStageLabel(effectiveWinRateSnapshot.current_stage)}</dd>
                      </div>
                      <div>
                        <dt>判断强度</dt>
                        <dd>置信度 {formatPercent(effectiveWinRateSnapshot.confidence)}</dd>
                      </div>
                    </dl>
                    <div className="analysis-card__section">
                      <h4>积极因素</h4>
                      {renderList(effectiveWinRateSnapshot.positive_factors, "暂无积极因素。")}
                    </div>
                    <div className="analysis-card__section">
                      <h4>当前最大失分风险</h4>
                      {renderList(
                        effectiveWinRateSnapshot.top_loss_risks ?? effectiveWinRateSnapshot.negative_factors,
                        "暂无明显失分风险。",
                        { maxItems: 4 },
                      )}
                    </div>
                  </article>

                  <article className="analysis-card">
                    <h3>对方下一轮最可能怎么压你</h3>
                    <div className="analysis-card__section">
                      <h4>可能说法</h4>
                      {renderList(
                        effectiveWinRateSnapshot.likely_opponent_lines ?? [],
                        "暂无具体压制路径。",
                        { maxItems: 4 },
                      )}
                    </div>
                  </article>

                  <article className="analysis-card">
                    <h3>我方回应版本</h3>
                    <div className="analysis-card__section">
                      <h4>最稳回应</h4>
                      {renderList(
                        effectiveWinRateSnapshot.stable_response_lines ?? [],
                        "暂无稳定回应版本。",
                        { maxItems: 3 },
                      )}
                    </div>
                    <div className="analysis-card__section">
                      <h4>第二回应</h4>
                      {renderList(
                        effectiveWinRateSnapshot.fallback_response_lines ?? [],
                        "暂无备选回应版本。",
                        { maxItems: 2 },
                      )}
                    </div>
                  </article>

                  <article className="analysis-card">
                    <h3>证据与法条</h3>
                    <div className="analysis-card__section">
                      <h4>最该补的证据</h4>
                      {renderList(
                        effectiveWinRateSnapshot.critical_evidence_items ?? effectiveWinRateSnapshot.evidence_gap_actions,
                        "暂无补证方向。",
                        { maxItems: 4 },
                      )}
                    </div>
                    <div className="analysis-card__section">
                      <h4>可援引法条与说理</h4>
                      {renderList(
                        effectiveWinRateSnapshot.legal_reasoning_notes ?? [],
                        "暂无法条说理建议。",
                        { maxItems: 3 },
                      )}
                    </div>
                    <div className="analysis-card__section">
                      <h4>推进顺序</h4>
                      {renderList(effectiveWinRateSnapshot.recommended_next_actions, "暂无下一步建议。", {
                        maxItems: 4,
                      })}
                    </div>
                  </article>
                </div>
              </>
            ) : (
              <section className="stage-empty-state">
                <h3>尚未生成胜诉率分析</h3>
                <p>请先完成对方推演。</p>
              </section>
            )}
          </section>

          <section className="workspace-stage-panel" hidden={activeStage !== "replay"}>
            <header className="workspace-stage-panel__header">
              <div>
                <p className="workspace-stage-panel__eyebrow">阶段 05</p>
                <h2 className="workspace-stage-panel__title">复盘报告</h2>
              </div>
              <div className="workspace-stage-panel__actions">
                <button
                  type="button"
                  className="workspace-button workspace-button--primary"
                  onClick={() => void handleGenerateReplay()}
                  disabled={busyAction === "replay" || !simulationSnapshot || !effectiveWinRateSnapshot}
                >
                  {busyAction === "replay" ? "生成中..." : "生成报告"}
                </button>
              </div>
            </header>

            {effectiveReplayReport ? (
              <>
                <section className="report-markdown-card report-markdown-card--structured">
                  <div className="report-markdown-card__header">
                    <strong>{effectiveReplayReport.report_title}</strong>
                    <span>{formatDateTime(effectiveReplayReport.generated_at)}</span>
                  </div>
                  {effectiveReplayReport.report_summary ? (
                    <p className="report-summary-card__lead">{effectiveReplayReport.report_summary}</p>
                  ) : null}
                </section>

                <div className="analysis-grid analysis-grid--balanced">
                  <article className="analysis-card analysis-card--summary">
                    <h3>本轮主轴</h3>
                    {renderList(effectiveReplayReport.branch_decisions, "暂无分支记录。", {
                      maxItems: 4,
                    })}
                    <div className="analysis-card__section">
                      <h4>局面状态</h4>
                      {renderList(
                        Object.entries(effectiveReplayReport.state_summary).map(
                          ([key, value]) => `${formatStateKeyLabel(key)}：${value}`,
                        ),
                        "暂无状态摘要。",
                        { maxItems: 6 },
                      )}
                    </div>
                  </article>

                  {effectiveReplayReport.report_sections.map((section) => (
                    <article key={section.key} className="analysis-card">
                      <h3>{section.title}</h3>
                      {renderList(section.items, "暂无内容。", {
                        maxItems: getReplaySectionMaxItems(section.key),
                      })}
                    </article>
                  ))}
                </div>
              </>
            ) : (
              <section className="stage-empty-state">
                <h3>尚未生成复盘报告</h3>
                <p>请先完成胜诉率分析。</p>
              </section>
            )}
          </section>
        </section>

        {!hideSessionCasesPanel && sessionCases.length > 0 ? (
          <aside className="workspace-aside">
            <section className="context-card">
              <p className="context-card__eyebrow">最近案件</p>
              <h3 className="context-card__title">继续未完成的模拟</h3>
              <div className="workspace-main">
                {sessionCases.map((record) => (
                  <button
                    key={record.caseId}
                    type="button"
                    className="session-case-item"
                    onClick={() => {
                      latestSimulationIdRef.current = record.simulationSnapshot?.simulation_id ?? null;
                      setDraft(cloneDraft(record.draftSnapshot));
                      setCurrentCase(record.caseProfile);
                      setSimulationSnapshot(record.simulationSnapshot);
                      setOpponentSnapshot(record.opponentSnapshot);
                      setWinRateSnapshot(record.winRateSnapshot);
                      setReplayReport(record.replayReport);
                      setActiveStage(record.lastVisitedStage);
                      setIsMockMode(record.caseProfile.case_id?.startsWith("MOCK-") === true);
                    }}
                  >
                    <strong>{record.caseProfile.title}</strong>
                    <span className="session-case-item__time">{formatDateTime(record.updatedAt)}</span>
                  </button>
                ))}
              </div>
            </section>
          </aside>
        ) : null}
      </div>
    </main>
  );
}

function getReplaySectionMaxItems(sectionKey: string): number {
  switch (sectionKey) {
    case "conclusion":
      return 4;
    case "effective_moves":
    case "pressure_points":
    case "evidence":
    case "next_step":
      return 4;
    case "response_templates":
    case "legal_notes":
      return 3;
    case "path":
      return 5;
    case "user_inputs":
      return 3;
    default:
      return 4;
  }
}

function renderList(
  items: string[],
  emptyText: string,
  options?: { maxItems?: number },
): JSX.Element {
  const visibleItems =
    options?.maxItems && options.maxItems > 0
      ? items.slice(0, options.maxItems)
      : items;

  return visibleItems.length > 0 ? (
    <ul className="analysis-list">
      {visibleItems.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  ) : (
    <p className="analysis-card__empty">{emptyText}</p>
  );
}
