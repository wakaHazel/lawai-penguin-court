import { useEffect, useState } from "react";

import {
  buildDraftFromCaseProfile,
  createEmptyCaseIntakeDraft,
} from "./features/case-intake/draft";
import {
  PenguinCourtWorkspacePage,
  WORKSPACE_STORAGE_KEY,
  parseStoredWorkspaceState,
  type PersistedWorkspaceState,
  type SessionCaseRecord,
} from "./pages";
import { ApiRequestError } from "./services/api/client";
import {
  getCaseList,
  getLatestOpponentBehaviorSnapshot,
  getLatestReplayReport,
  getLatestSimulation,
  getLatestWinRateAnalysis,
} from "./services/api/cases";

type AppView = "home" | "history" | "workspace";

function readWorkspaceState(): PersistedWorkspaceState | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return parseStoredWorkspaceState(
      window.localStorage.getItem(WORKSPACE_STORAGE_KEY),
    );
  } catch {
    return null;
  }
}

function writeWorkspaceState(state: PersistedWorkspaceState): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(state));
}

function sortSessionCases(records: SessionCaseRecord[]): SessionCaseRecord[] {
  return [...records].sort(
    (left, right) =>
      new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime(),
  );
}

function buildFreshWorkspaceState(
  currentState: PersistedWorkspaceState | null,
): PersistedWorkspaceState {
  return {
    draft: createEmptyCaseIntakeDraft(),
    currentCase: null,
    simulationSnapshot: null,
    opponentSnapshot: null,
    winRateSnapshot: null,
    replayReport: null,
    activeStage: "intake",
    sessionCases: currentState?.sessionCases ?? [],
    isMockMode: currentState?.isMockMode ?? false,
  };
}

function buildWorkspaceStateFromRecord(
  record: SessionCaseRecord,
  currentState: PersistedWorkspaceState | null,
): PersistedWorkspaceState {
  return {
    draft: record.draftSnapshot,
    currentCase: record.caseProfile,
    simulationSnapshot: record.simulationSnapshot,
    opponentSnapshot: record.opponentSnapshot,
    winRateSnapshot: record.winRateSnapshot,
    replayReport: record.replayReport,
    activeStage: record.lastVisitedStage,
    sessionCases: currentState?.sessionCases ?? [record],
    isMockMode: currentState?.isMockMode ?? false,
  };
}

function formatUpdatedAt(value: string): string {
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

function getStageLabel(record: SessionCaseRecord): string {
  switch (record.lastVisitedStage) {
    case "intake":
      return "案件录入";
    case "simulation":
      return "庭审模拟";
    case "opponent":
      return "对方推演";
    case "win_rate":
      return "胜诉率分析";
    case "replay":
      return "复盘报告";
    default:
      return "处理中";
  }
}

function getCaseTypeLabel(record: SessionCaseRecord): string {
  return record.caseProfile.case_type || "未分类";
}

export function App(): JSX.Element {
  const [view, setView] = useState<AppView>("home");
  const [sessionCases, setSessionCases] = useState<SessionCaseRecord[]>([]);
  const [workspaceRenderKey, setWorkspaceRenderKey] = useState(0);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [backendCaseCount, setBackendCaseCount] = useState<number | null>(null);

  function refreshSessionCases(): void {
    const workspaceState = readWorkspaceState();
    setSessionCases(sortSessionCases(workspaceState?.sessionCases ?? []));
  }

  useEffect(() => {
    refreshSessionCases();
  }, []);

  useEffect(() => {
    if (view !== "history") {
      return;
    }

    let isCancelled = false;

    async function loadHistoryFromBackend(): Promise<void> {
      setHistoryLoading(true);
      setHistoryError(null);

      try {
        const cases = await getCaseList();
        const currentState = readWorkspaceState();
        const localByCaseId = new Map(
          (currentState?.sessionCases ?? []).map((record) => [record.caseId, record]),
        );

        const remoteRecords = await Promise.all(
          cases.map(async (caseProfile) => {
            const caseId = caseProfile.case_id;
            if (!caseId) {
              return null;
            }

            const localRecord = localByCaseId.get(caseId);
            const [
              simulationSnapshot,
              opponentSnapshot,
              winRateSnapshot,
              replayReport,
            ] = await Promise.all([
              getLatestSimulation(caseId).catch((error) =>
                isNotFoundError(error)
                  ? localRecord?.simulationSnapshot ?? null
                  : Promise.reject(error),
              ),
              getLatestOpponentBehaviorSnapshot(caseId).catch((error) =>
                isNotFoundError(error)
                  ? localRecord?.opponentSnapshot ?? null
                  : Promise.reject(error),
              ),
              getLatestWinRateAnalysis(caseId).catch((error) =>
                isNotFoundError(error)
                  ? localRecord?.winRateSnapshot ?? null
                  : Promise.reject(error),
              ),
              getLatestReplayReport(caseId).catch((error) =>
                isNotFoundError(error)
                  ? localRecord?.replayReport ?? null
                  : Promise.reject(error),
              ),
            ]);

            return buildRecordFromBackend(caseProfile, {
              localRecord,
              simulationSnapshot,
              opponentSnapshot,
              winRateSnapshot,
              replayReport,
            });
          }),
        );

        if (isCancelled) {
          return;
        }

        const mergedRecords = sortSessionCases(
          remoteRecords.filter((record): record is SessionCaseRecord => record !== null),
        );

        setBackendCaseCount(cases.length);
        setSessionCases(mergedRecords);
        writeWorkspaceState({
          ...(currentState ?? buildFreshWorkspaceState(null)),
          sessionCases: mergedRecords,
        });
      } catch {
        if (!isCancelled) {
          setHistoryError("历史案件暂时无法从后端加载，当前先展示本地记录。");
          refreshSessionCases();
        }
      } finally {
        if (!isCancelled) {
          setHistoryLoading(false);
        }
      }
    }

    void loadHistoryFromBackend();

    return () => {
      isCancelled = true;
    };
  }, [view]);

  function openWorkspace(nextState: PersistedWorkspaceState): void {
    writeWorkspaceState(nextState);
    refreshSessionCases();
    setWorkspaceRenderKey((previous) => previous + 1);
    setView("workspace");
  }

  function handleCreateNewCase(): void {
    openWorkspace(buildFreshWorkspaceState(readWorkspaceState()));
  }

  function handleOpenHistory(): void {
    refreshSessionCases();
    setView("history");
  }

  function handleResumeCase(record: SessionCaseRecord): void {
    openWorkspace(buildWorkspaceStateFromRecord(record, readWorkspaceState()));
  }

  function handleBackHome(): void {
    refreshSessionCases();
    setView("home");
  }

  if (view === "workspace") {
    return (
      <PenguinCourtWorkspacePage
        key={workspaceRenderKey}
        onBack={handleBackHome}
        hideSessionCasesPanel
      />
    );
  }

  if (view === "history") {
    return (
      <main className="app-page-shell">
        <section className="app-page-panel">
          <div className="app-page-panel__header">
            <div>
              <p className="app-page-panel__eyebrow">历史案件</p>
              <h1 className="app-page-panel__title">已保存的模拟记录</h1>
            </div>
            <div className="app-page-panel__actions">
              <button
                type="button"
                className="workspace-button workspace-button--ghost"
                onClick={handleBackHome}
              >
                返回首页
              </button>
              <button
                type="button"
                className="workspace-button workspace-button--primary"
                onClick={handleCreateNewCase}
              >
                新建案件
              </button>
            </div>
          </div>

          {historyError ? (
            <section className="workspace-feedback workspace-feedback--error">
              {historyError}
            </section>
          ) : null}

          {historyLoading ? (
            <section className="app-empty-state">
              <h2>正在加载历史案件</h2>
              <p>正在读取案件记录。</p>
            </section>
          ) : sessionCases.length > 0 ? (
            <div className="history-case-list">
              {sessionCases.map((record) => (
                <article key={record.caseId} className="history-case-card">
                  <div className="history-case-card__content">
                    <div className="history-case-card__meta">
                      <span>{getCaseTypeLabel(record)}</span>
                      <span>{getStageLabel(record)}</span>
                      <span>{formatUpdatedAt(record.updatedAt)}</span>
                    </div>
                    <h2 className="history-case-card__title">{record.caseProfile.title}</h2>
                    <p className="history-case-card__summary">
                      {record.caseProfile.summary || "暂无摘要。"}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="workspace-button workspace-button--secondary"
                    onClick={() => handleResumeCase(record)}
                  >
                    继续处理
                  </button>
                </article>
              ))}
            </div>
          ) : (
            <section className="app-empty-state">
              <h2>还没有历史案件</h2>
              <p>新建案件后会自动保存到这里。</p>
              <button
                type="button"
                className="workspace-button workspace-button--primary"
                onClick={handleCreateNewCase}
              >
                去新建案件
              </button>
            </section>
          )}
        </section>
      </main>
    );
  }

  return (
    <main className="app-home">
      <section className="app-home__hero">
        <p className="app-home__eyebrow">企鹅法庭</p>
        <h1 className="app-home__title">沉浸式庭审模拟</h1>
      </section>

      <section className="app-home__entry-grid" aria-label="首页入口">
        <button
          type="button"
          className="entry-card entry-card--primary"
          onClick={handleCreateNewCase}
        >
          <span className="entry-card__eyebrow">开始主线</span>
          <strong className="entry-card__title">新建案件</strong>
        </button>

        <button
          type="button"
          className="entry-card"
          onClick={handleOpenHistory}
        >
          <span className="entry-card__eyebrow">继续案件</span>
          <strong className="entry-card__title">历史案件</strong>
          {(backendCaseCount ?? sessionCases.length) > 0 ? (
            <span className="entry-card__badge">
              {backendCaseCount ?? sessionCases.length} 个案件
            </span>
          ) : null}
        </button>
      </section>
    </main>
  );
}

function isNotFoundError(error: unknown): boolean {
  return error instanceof ApiRequestError && error.status === 404;
}

function buildRecordFromBackend(
  caseProfile: SessionCaseRecord["caseProfile"],
  options: {
    localRecord?: SessionCaseRecord;
    simulationSnapshot: SessionCaseRecord["simulationSnapshot"];
    opponentSnapshot: SessionCaseRecord["opponentSnapshot"];
    winRateSnapshot: SessionCaseRecord["winRateSnapshot"];
    replayReport: SessionCaseRecord["replayReport"];
  },
): SessionCaseRecord {
  const localRecord = options.localRecord;
  const simulationSnapshot = options.simulationSnapshot ?? localRecord?.simulationSnapshot ?? null;
  const opponentSnapshot = options.opponentSnapshot ?? localRecord?.opponentSnapshot ?? null;
  const winRateSnapshot = options.winRateSnapshot ?? localRecord?.winRateSnapshot ?? null;
  const replayReport = options.replayReport ?? localRecord?.replayReport ?? null;
  const draftSnapshot = localRecord?.draftSnapshot ?? buildDraftFromCaseProfile(caseProfile);
  const updatedAt =
    replayReport?.generated_at ??
    localRecord?.updatedAt ??
    new Date().toISOString();

  return {
    caseId: caseProfile.case_id ?? localRecord?.caseId ?? `case-${Date.now()}`,
    caseProfile,
    draftSnapshot,
    simulationSnapshot,
    opponentSnapshot,
    winRateSnapshot,
    replayReport,
    lastVisitedStage: resolveLastVisitedStage({
      simulationSnapshot,
      opponentSnapshot,
      winRateSnapshot,
      replayReport,
      localRecord,
    }),
    updatedAt,
  };
}

function resolveLastVisitedStage(options: {
  simulationSnapshot: SessionCaseRecord["simulationSnapshot"];
  opponentSnapshot: SessionCaseRecord["opponentSnapshot"];
  winRateSnapshot: SessionCaseRecord["winRateSnapshot"];
  replayReport: SessionCaseRecord["replayReport"];
  localRecord?: SessionCaseRecord;
}): SessionCaseRecord["lastVisitedStage"] {
  const hasDerivedReplay =
    options.simulationSnapshot?.analysis?.report_status === "ready";
  const hasDerivedWinRate =
    typeof options.simulationSnapshot?.analysis?.estimated_win_rate === "number";
  const hasDerivedOpponent =
    Array.isArray(options.simulationSnapshot?.opponent?.likely_arguments) &&
    options.simulationSnapshot.opponent.likely_arguments.length > 0;

  if (options.localRecord?.lastVisitedStage) {
    return options.localRecord.lastVisitedStage;
  }

  if (options.replayReport || hasDerivedReplay) {
    return "replay";
  }

  if (options.winRateSnapshot || hasDerivedWinRate) {
    return "win_rate";
  }

  if (options.opponentSnapshot || hasDerivedOpponent) {
    return "opponent";
  }

  if (options.simulationSnapshot) {
    return "simulation";
  }

  return "intake";
}
