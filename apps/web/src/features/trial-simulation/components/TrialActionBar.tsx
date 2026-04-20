import type { MouseEvent } from "react";
import type { SimulationActionCard } from "../../../types/turn";

interface TrialActionBarProps {
  actionCards?: SimulationActionCard[];
  actions: string[];
  secondaryActions?: string[];
  choicePrompt?: string | null;
  isLoading: boolean;
  canAdvance: boolean;
  onActionSelect: (action: string, choiceId?: string | null) => void;
}

const DEFAULT_CHOICE_PROMPT = "选择一个动作，推进这一轮。";

function normalizeChoicePrompt(value: string | null | undefined): string {
  if (!value) {
    return DEFAULT_CHOICE_PROMPT;
  }

  const normalized = value.trim();
  if (!normalized) {
    return DEFAULT_CHOICE_PROMPT;
  }

  const wrappedMatch = normalized.match(/^【(.+)】$/);
  return wrappedMatch ? wrappedMatch[1].trim() : normalized;
}

function cleanActionCopy(
  value: string | null | undefined,
  fallback: string,
): string {
  const normalized = (value ?? "")
    .replace(/\s+/g, " ")
    .replace(/当前动作[:：][^。！？!?]+[。！？!?]?/g, "")
    .replace(/动作[“"][^”"]+[”"]需要[^。！？!?]+[。！？!?]?/g, "")
    .replace(/风险提示[:：]?/g, "")
    .trim();

  if (!normalized) {
    return fallback;
  }

  const firstSentence = normalized.match(/^[^。！？!?]+[。！？!?]?/);
  const compact = (firstSentence?.[0] ?? normalized).trim();
  return compact.length > 44 ? `${compact.slice(0, 44).trim()}…` : compact;
}

export function TrialActionBar({
  actionCards = [],
  actions,
  secondaryActions = [],
  choicePrompt,
  isLoading,
  canAdvance,
  onActionSelect,
}: TrialActionBarProps): JSX.Element {
  function handleActionButtonClick(event: MouseEvent<HTMLButtonElement>): void {
    const selectedAction = event.currentTarget.dataset.action;
    const selectedChoiceId = event.currentTarget.dataset.choiceId;
    if (selectedAction) {
      onActionSelect(selectedAction, selectedChoiceId || null);
    }
  }

  const hasActions = actionCards.length > 0 || actions.length > 0 || secondaryActions.length > 0;
  const visibleCards: SimulationActionCard[] =
    actionCards.length > 0
      ? actionCards
      : actions.map((action, index) => ({
          choice_id: null,
          action,
          intent: index === 0 ? "优先推进当前回合主应对。" : "作为本轮替代策略选择。",
          risk_tip: "请结合当前证据与法庭反应判断节奏。",
          emphasis: index === 0 ? "critical" : "steady",
        }));
  const normalizedPrompt = normalizeChoicePrompt(choicePrompt);
  const shouldRenderPrompt = normalizedPrompt !== DEFAULT_CHOICE_PROMPT;
  const shouldRenderHeader = shouldRenderPrompt;

  return (
    <section className="trial-action-bar" aria-label="庭审动作区">
      {shouldRenderHeader ? (
        <div className="trial-action-bar__header">
          <p className="trial-action-bar__prompt">{normalizedPrompt}</p>
        </div>
      ) : null}

      {visibleCards.length > 0 ? (
        <div className="trial-action-bar__actions">
          {visibleCards.map((card, index) => (
            <button
              key={card.action}
              type="button"
              className={[
                "trial-action-bar__card",
                index === 0 ? "is-primary" : "",
                card.emphasis ? `is-${card.emphasis}` : "",
              ]
                .filter(Boolean)
                .join(" ")}
              data-action={card.action}
              data-choice-id={card.choice_id ?? undefined}
              disabled={isLoading || !canAdvance}
              onClick={handleActionButtonClick}
            >
              <div className="trial-action-bar__card-head">
                <span className="trial-action-bar__button-index">0{index + 1}</span>
                <strong className="trial-action-bar__card-title">{card.action}</strong>
              </div>
              <p className="trial-action-bar__card-intent">
                {cleanActionCopy(
                  card.intent || card.risk_tip,
                  "选择这一步后，法庭会据此推进下一轮变化。",
                )}
              </p>
            </button>
          ))}
        </div>
      ) : null}

      {secondaryActions.length > 0 ? (
        <div className="trial-action-bar__secondary">
          <span className="trial-action-bar__secondary-label">更多动作</span>
          <div className="trial-action-bar__secondary-list">
            {secondaryActions.map((action) => (
              <button
                key={action}
                type="button"
                className="trial-action-bar__secondary-chip"
                data-action={action}
                disabled={isLoading || !canAdvance}
                onClick={handleActionButtonClick}
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {!hasActions ? (
        <p className="trial-action-bar__empty">
          当前没有可选动作。
        </p>
      ) : null}

      {isLoading ? (
        <div className="trial-action-bar__loading-mask" aria-live="polite">
          <strong>正在生成下一轮庭审变化…</strong>
        </div>
      ) : null}
    </section>
  );
}
