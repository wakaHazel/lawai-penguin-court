import type {
  SimulationUserInputEntry,
  SimulationUserInputType,
  TrialStage,
} from "../../../types/turn";
import {
  formatSimulationUserInputTypeLabel,
  summarizeSimulationUserInputEntry,
  type TrialSupplementPreset,
} from "../supplemental-inputs";

interface TrialSupplementInputPanelProps {
  stage: TrialStage | null | undefined;
  presets: TrialSupplementPreset[];
  entries: SimulationUserInputEntry[];
  selectedType: SimulationUserInputType | null;
  draftValue: string;
  isLoading: boolean;
  onSelectType: (type: SimulationUserInputType) => void;
  onDraftValueChange: (value: string) => void;
  onAddEntry: () => void;
  onRemoveEntry: (entryId: string) => void;
}

export function TrialSupplementInputPanel({
  stage,
  presets,
  entries,
  selectedType,
  draftValue,
  isLoading,
  onSelectType,
  onDraftValueChange,
  onAddEntry,
  onRemoveEntry,
}: TrialSupplementInputPanelProps): JSX.Element | null {
  if (!stage || presets.length === 0) {
    return null;
  }

  const activePreset =
    presets.find((preset) => preset.type === selectedType) ?? presets[0];

  return (
    <section className="trial-supplement-panel" aria-label="当前回合补充输入">
      <div className="trial-supplement-panel__header">
        <div className="trial-supplement-panel__header-copy">
          <p className="trial-supplement-panel__eyebrow">当前回合补充输入</p>
          <h3 className="trial-supplement-panel__title">把新材料写进这一轮</h3>
        </div>

        <button
          type="button"
          className="workspace-button workspace-button--secondary"
          onClick={onAddEntry}
          disabled={isLoading || !draftValue.trim()}
        >
          加入本轮
        </button>
      </div>

      <div className="trial-supplement-panel__preset-list" role="tablist" aria-label="补充输入类型">
        {presets.map((preset) => (
          <button
            key={preset.type}
            type="button"
            className={[
              "trial-supplement-panel__preset-chip",
              preset.type === activePreset.type ? "is-active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onSelectType(preset.type)}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <label className="trial-supplement-panel__editor">
        <span className="trial-supplement-panel__editor-label">
          {activePreset.label}
        </span>
        <textarea
          rows={4}
          value={draftValue}
          onChange={(event) => onDraftValueChange(event.target.value)}
          placeholder={activePreset.placeholder}
          disabled={isLoading}
        />
      </label>

      {entries.length > 0 ? (
        <div className="trial-supplement-panel__entry-list">
          {entries.map((entry) => (
            <article key={entry.entry_id} className="trial-supplement-panel__entry-card">
              <div className="trial-supplement-panel__entry-head">
                <span className="trial-supplement-panel__entry-label">
                  {entry.label || formatSimulationUserInputTypeLabel(entry.input_type)}
                </span>
                <button
                  type="button"
                  className="trial-supplement-panel__remove-button"
                  onClick={() => onRemoveEntry(entry.entry_id)}
                  disabled={isLoading}
                  aria-label={`移除${entry.label}`}
                >
                  删除
                </button>
              </div>
              <p className="trial-supplement-panel__entry-text">
                {summarizeSimulationUserInputEntry(entry, 88)}
              </p>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
