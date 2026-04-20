import { useEffect, useMemo, useRef, useState } from "react";

import {
  buildTrialNarrativeFlow,
  getNarrativeBeatDelay,
  TrialActionBar,
  TrialCaseSidebar,
  TrialReplayPanel,
  TrialScenePanel,
  TrialSupplementInputPanel,
  TrialSimulationErrorBoundary,
  useTrialSimulationController,
} from "../features/trial-simulation";
import {
  getStageSimulationUserInputs,
  getTrialSupplementPresets,
} from "../features/trial-simulation/supplemental-inputs";
import type { CaseProfile } from "../types/case";
import type {
  SimulationSnapshot,
  SimulationUserInputType,
} from "../types/turn";

interface TrialSimulationPageProps {
  caseId: string;
  autoStart?: boolean;
  initialSnapshot?: SimulationSnapshot | null;
  initialCaseProfile?: CaseProfile | null;
  preferMock?: boolean;
  onSnapshotUpdate?: (snapshot: SimulationSnapshot | null) => void;
  embedded?: boolean;
}

export function TrialSimulationPage({
  caseId,
  autoStart = true,
  initialSnapshot = null,
  initialCaseProfile = null,
  preferMock = false,
  onSnapshotUpdate,
  embedded = false,
}: TrialSimulationPageProps): JSX.Element {
  const latestSnapshotCallbackRef = useRef(onSnapshotUpdate);
  const lastNotifiedSnapshotKeyRef = useRef<string | null>(null);
  const [isCaseDrawerOpen, setIsCaseDrawerOpen] = useState(false);
  const [isHistoryDrawerOpen, setIsHistoryDrawerOpen] = useState(false);
  const [visibleBeatCount, setVisibleBeatCount] = useState(0);
  const [selectedInputType, setSelectedInputType] =
    useState<SimulationUserInputType | null>(null);
  const [supplementDraft, setSupplementDraft] = useState("");

  const {
    pageState,
    isLoading,
    errorMessage,
    startSimulationSession,
    advanceWithAction,
    resumeFromCheckpoint,
    reloadCase,
    saveSupplementInput,
    removeSupplementInput,
  } = useTrialSimulationController({
    caseId,
    autoStart,
    initialSnapshot,
    initialCaseProfile,
    preferMock,
  });

  useEffect(() => {
    latestSnapshotCallbackRef.current = onSnapshotUpdate;
  }, [onSnapshotUpdate]);

  useEffect(() => {
    if (!pageState.snapshot && initialSnapshot) {
      return;
    }

    const latestEntryId =
      pageState.snapshot?.user_input_entries?.[
        (pageState.snapshot.user_input_entries?.length ?? 0) - 1
      ]?.entry_id ?? "none";
    const snapshotKey = pageState.snapshot
      ? [
          caseId,
          pageState.snapshot.simulation_id,
          pageState.snapshot.current_stage,
          pageState.snapshot.turn_index,
          pageState.snapshot.node_id,
          pageState.snapshot.user_input_entries?.length ?? 0,
          latestEntryId,
        ].join(":")
      : `${caseId}:null`;

    if (lastNotifiedSnapshotKeyRef.current === snapshotKey) {
      return;
    }

    lastNotifiedSnapshotKeyRef.current = snapshotKey;
    latestSnapshotCallbackRef.current?.(pageState.snapshot);
  }, [caseId, initialSnapshot, pageState.snapshot]);

  function handleReloadClick(): void {
    void reloadCase();
  }

  function handleRestartClick(): void {
    void startSimulationSession();
  }

  function handleActionSelect(action: string, choiceId?: string | null): void {
    const normalizedDraft = supplementDraft.trim();
    const pendingInput =
      normalizedDraft && selectedInputType
        ? {
            inputType: selectedInputType,
            content: normalizedDraft,
          }
        : null;

    void advanceWithAction(action, choiceId, pendingInput);
  }

  function handleResumeCheckpoint(checkpointId: string): void {
    void resumeFromCheckpoint(checkpointId);
  }

  const roundKey = pageState.snapshot
    ? `${pageState.snapshot.simulation_id}:${pageState.snapshot.turn_index}:${pageState.snapshot.node_id}`
    : "idle";
  const stagePresets = useMemo(
    () => getTrialSupplementPresets(pageState.snapshot?.current_stage),
    [pageState.snapshot?.current_stage],
  );
  const currentStageEntries = useMemo(
    () =>
      getStageSimulationUserInputs(
        pageState.snapshot?.user_input_entries,
        pageState.snapshot?.current_stage,
      ),
    [pageState.snapshot?.current_stage, pageState.snapshot?.user_input_entries],
  );
  const narrativeBeats = useMemo(
    () => buildTrialNarrativeFlow(pageState.snapshot).beats,
    [pageState.snapshot],
  );
  const hasActionChoices =
    pageState.actionCards.length > 0 ||
    pageState.primaryActions.length > 0 ||
    pageState.secondaryActions.length > 0;

  useEffect(() => {
    if (narrativeBeats.length === 0) {
      setVisibleBeatCount(0);
      return;
    }

    setVisibleBeatCount(1);
  }, [roundKey, narrativeBeats.length]);

  useEffect(() => {
    setSupplementDraft("");
    setSelectedInputType((currentType) => {
      if (
        currentType &&
        stagePresets.some((preset) => preset.type === currentType)
      ) {
        return currentType;
      }

      return stagePresets[0]?.type ?? null;
    });
  }, [roundKey, stagePresets]);

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (narrativeBeats.length === 0) {
      return;
    }

    if (visibleBeatCount >= narrativeBeats.length) {
      return;
    }

    const activeBeat = narrativeBeats[Math.max(0, visibleBeatCount - 1)];
    const timerId = window.setTimeout(() => {
      setVisibleBeatCount((current) =>
        Math.min(narrativeBeats.length, current + 1),
      );
    }, getNarrativeBeatDelay(activeBeat));

    return () => {
      window.clearTimeout(timerId);
    };
  }, [isLoading, narrativeBeats, visibleBeatCount]);

  const revealState =
    narrativeBeats.length === 0
      ? "idle"
      : visibleBeatCount >= narrativeBeats.length
        ? "ready"
        : "revealing";
  const maxVisibleNarrativeBeats = 4;
  const visibleNarrativeBeats = narrativeBeats.slice(
    Math.max(0, visibleBeatCount - maxVisibleNarrativeBeats),
    Math.max(visibleBeatCount, 0),
  );
  const isInteractionReady =
    revealState === "ready" &&
    pageState.canAdvance &&
    hasActionChoices;
  const shouldRevealFollowupPanels =
    !isLoading && (revealState === "ready" || narrativeBeats.length === 0);
  const shouldRenderActionBar = isLoading || isInteractionReady;

  function handleAddSupplementInput(): void {
    const normalizedDraft = supplementDraft.trim();
    if (!selectedInputType || !normalizedDraft) {
      return;
    }

    saveSupplementInput(selectedInputType, normalizedDraft);
    setSupplementDraft("");
  }

  return (
    <TrialSimulationErrorBoundary>
      <main
        className={
          embedded
            ? "trial-simulation-page trial-simulation-page--embedded"
            : "trial-simulation-page"
        }
      >
        {!embedded ? (
          <header className="trial-simulation-page__header">
            <div className="trial-simulation-page__header-copy">
              <p className="trial-simulation-page__eyebrow">企鹅法庭 · 当前庭次</p>
              <h1 className="trial-simulation-page__title">
                {pageState.snapshot?.scene_title ?? "沉浸式庭审推演"}
              </h1>
            </div>

            <div className="trial-simulation-page__toolbar">
              <button
                type="button"
                onClick={() => setIsCaseDrawerOpen((value) => !value)}
                disabled={!pageState.caseProfile}
              >
                {isCaseDrawerOpen ? "收起案件资料" : "案件资料"}
              </button>
              <button
                type="button"
                onClick={() => setIsHistoryDrawerOpen((value) => !value)}
                disabled={!pageState.snapshot}
              >
                {isHistoryDrawerOpen ? "收起庭审记录" : "庭审记录"}
              </button>
              <button type="button" onClick={handleReloadClick} disabled={isLoading}>
                刷新案件
              </button>
              <button type="button" onClick={handleRestartClick} disabled={isLoading}>
                重新开庭
              </button>
            </div>
          </header>
        ) : (
          <div className="trial-simulation-page__toolbar trial-simulation-page__toolbar--embedded">
            <button
              type="button"
              onClick={() => setIsCaseDrawerOpen((value) => !value)}
              disabled={!pageState.caseProfile}
            >
              {isCaseDrawerOpen ? "收起案件资料" : "案件资料"}
            </button>
            <button
              type="button"
              onClick={() => setIsHistoryDrawerOpen((value) => !value)}
              disabled={!pageState.snapshot}
            >
              {isHistoryDrawerOpen ? "收起庭审记录" : "庭审记录"}
            </button>
          </div>
        )}

        {errorMessage ? (
          <section className="trial-simulation-page__error" role="alert">
            {errorMessage}
          </section>
        ) : null}

        <div className="trial-simulation-page__layout" key={roundKey}>
          <TrialScenePanel
            snapshot={pageState.snapshot}
            currentStageLabel={pageState.currentStageLabel}
            currentTask={pageState.currentTask}
            degradedFlags={pageState.degradedFlags}
            visibleBeats={visibleNarrativeBeats}
            revealState={revealState}
            showTaskPanel={shouldRevealFollowupPanels}
          />

          {shouldRevealFollowupPanels ? (
            <TrialSupplementInputPanel
              stage={pageState.snapshot?.current_stage}
              presets={stagePresets}
              entries={currentStageEntries}
              selectedType={selectedInputType}
              draftValue={supplementDraft}
              isLoading={isLoading}
              onSelectType={setSelectedInputType}
              onDraftValueChange={setSupplementDraft}
              onAddEntry={handleAddSupplementInput}
              onRemoveEntry={removeSupplementInput}
            />
          ) : null}
        </div>

        {isCaseDrawerOpen ? (
          <TrialCaseSidebar
            caseProfile={pageState.caseProfile}
            snapshot={pageState.snapshot}
          />
        ) : null}

        {isHistoryDrawerOpen ? (
          <TrialReplayPanel
            history={pageState.history}
            checkpoints={pageState.checkpoints}
            currentTurnIndex={pageState.snapshot?.turn_index ?? null}
            isLoading={isLoading}
            onResumeCheckpoint={handleResumeCheckpoint}
          />
        ) : null}

        {shouldRenderActionBar ? (
          <TrialActionBar
            key={`actions:${roundKey}`}
            actionCards={pageState.actionCards}
            actions={pageState.primaryActions}
            secondaryActions={pageState.secondaryActions}
            choicePrompt={pageState.snapshot?.choice_prompt}
            isLoading={isLoading}
            canAdvance={pageState.canAdvance}
            onActionSelect={handleActionSelect}
          />
        ) : null}
      </main>
    </TrialSimulationErrorBoundary>
  );
}
