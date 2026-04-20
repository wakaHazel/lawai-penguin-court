import type {
  SimulationCheckpoint,
  SimulationHistoryItem,
  TrialStage,
} from "../../../types/turn";
import { formatFocusLabel } from "../../../types/display";
import { getTrialStageMeta } from "../stage-meta";

interface TrialReplayPanelProps {
  history: SimulationHistoryItem[];
  checkpoints: SimulationCheckpoint[];
  currentTurnIndex?: number | null;
  isLoading?: boolean;
  onResumeCheckpoint: (checkpointId: string) => void;
}

const MAX_HISTORY_ITEMS = 6;
const MAX_CHECKPOINT_ITEMS = 4;

function formatStageLabel(stage: TrialStage): string {
  return getTrialStageMeta(stage).label;
}

function formatCheckpointLabel(item: SimulationCheckpoint): string {
  const normalized = item.stage_label.trim();
  if (normalized.length > 0) {
    return normalized;
  }

  return `第 ${item.turn_index} 回合`;
}

export function TrialReplayPanel({
  history,
  checkpoints,
  currentTurnIndex = null,
  isLoading = false,
  onResumeCheckpoint,
}: TrialReplayPanelProps): JSX.Element {
  const recentHistory = [...history]
    .sort((left, right) => left.turn_index - right.turn_index)
    .slice(-MAX_HISTORY_ITEMS);
  const visibleCheckpoints = [...checkpoints]
    .sort((left, right) => right.turn_index - left.turn_index)
    .slice(0, MAX_CHECKPOINT_ITEMS);

  return (
    <section className="trial-replay-panel" aria-label="庭审记录抽屉">
      <header className="trial-replay-panel__header">
        <div className="trial-replay-panel__header-copy">
          <p className="trial-replay-panel__eyebrow">庭审记录</p>
          <h3 className="trial-replay-panel__title">回合与断点</h3>
        </div>
      </header>

      <div className="trial-replay-panel__body">
        <section className="trial-replay-panel__section" aria-label="最近回合">
          <div className="trial-replay-panel__section-head">
            <strong>最近回合</strong>
          </div>

          {recentHistory.length > 0 ? (
            <ol className="trial-replay-panel__history-list">
              {recentHistory.map((item) => (
                <li key={`${item.simulation_id}:${item.turn_index}`}>
                  <article
                    className={[
                      "trial-replay-panel__history-item",
                      currentTurnIndex === item.turn_index ? "is-current" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    <span className="trial-replay-panel__turn-badge">
                      R{item.turn_index}
                    </span>
                    <div className="trial-replay-panel__history-copy">
                      <p className="trial-replay-panel__item-meta">
                        {formatStageLabel(item.stage)}
                      </p>
                      <strong className="trial-replay-panel__item-title">
                        {item.scene_title}
                      </strong>
                      <p className="trial-replay-panel__item-note">
                        焦点：{formatFocusLabel(item.branch_focus)}
                      </p>
                    </div>
                    {currentTurnIndex === item.turn_index ? (
                      <span className="trial-replay-panel__current-tag">当前</span>
                    ) : null}
                  </article>
                </li>
              ))}
            </ol>
          ) : (
            <p className="trial-replay-panel__empty">
              当前庭次还没有形成可回看的回合记录。
            </p>
          )}
        </section>

        <section className="trial-replay-panel__section" aria-label="断点恢复">
          <div className="trial-replay-panel__section-head">
            <strong>断点</strong>
          </div>

          {visibleCheckpoints.length > 0 ? (
            <div className="trial-replay-panel__checkpoint-list">
              {visibleCheckpoints.map((item) => (
                <button
                  key={item.checkpoint_id}
                  type="button"
                  className="trial-replay-panel__checkpoint"
                  disabled={isLoading}
                  onClick={() => onResumeCheckpoint(item.checkpoint_id)}
                >
                  <span className="trial-replay-panel__checkpoint-meta">
                    {formatCheckpointLabel(item)}
                  </span>
                  <strong className="trial-replay-panel__checkpoint-title">
                    回合 {item.turn_index}
                  </strong>
                  <span className="trial-replay-panel__checkpoint-action">
                    恢复到此
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <p className="trial-replay-panel__empty">
              暂无可恢复断点，继续推进后会自动沉淀。
            </p>
          )}
        </section>
      </div>
    </section>
  );
}
