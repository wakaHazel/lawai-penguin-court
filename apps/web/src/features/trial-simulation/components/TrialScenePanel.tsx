import type { CSSProperties } from "react";
import type {
  SimulationCgBackgroundId,
  SimulationCgCharacterId,
  SimulationCgEmotion,
  SimulationCgShotType,
  SimulationCgTargetId,
  SimulationSnapshot,
} from "../../../types/turn";
import type { TrialNarrativeBeat } from "../narrative";
import {
  formatCgCharacterLabel,
  formatCgTargetLabel,
  formatFocusLabel,
} from "../../../types/display";
import {
  pickNarrative,
  readNarrative,
  unwrapBracketLabel,
} from "../narrative";

interface TrialScenePanelProps {
  snapshot: SimulationSnapshot | null;
  currentStageLabel: string;
  currentTask: string;
  degradedFlags?: string[];
  visibleBeats?: TrialNarrativeBeat[];
  revealState?: "idle" | "revealing" | "ready";
  showTaskPanel?: boolean;
}

const DEGRADED_FLAG_LABELS: Record<string, string> = {
  deli_call_failed: "法律检索接口未返回，当前依据为本地兜底推演。",
  gemini_cg_failed: "插画分镜生成失败，已切回基础庭审场景。",
};

function resolveBackendAssetUrl(value: string | undefined | null): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }

  const normalized = value.trim();
  if (!normalized) {
    return undefined;
  }

  if (/^https?:\/\//i.test(normalized)) {
    return normalized;
  }

  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  const backendOrigin = configuredBaseUrl
    ? configuredBaseUrl.replace(/\/+$/, "")
    : "";

  if (normalized.startsWith("/")) {
    return backendOrigin ? `${backendOrigin}${normalized}` : normalized;
  }

  const relativePath = normalized.replace(/^\/+/, "");
  return backendOrigin ? `${backendOrigin}/${relativePath}` : `/${relativePath}`;
}

function joinClassNames(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

function toModifier(value: string | null | undefined): string | undefined {
  if (!value) {
    return undefined;
  }

  return `is-${value.replace(/_/g, "-")}`;
}

function fallbackBackground(stage: SimulationSnapshot["current_stage"] | undefined): SimulationCgBackgroundId {
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

function fallbackShot(stage: SimulationSnapshot["current_stage"] | undefined): SimulationCgShotType {
  switch (stage) {
    case "prepare":
    case "investigation":
      return "medium";
    case "evidence":
    case "debate":
      return "close";
    case "final_statement":
      return "medium";
    case "mediation_or_judgment":
    case "report_ready":
      return "wide";
    default:
      return "medium";
  }
}

function fallbackEmotion(stage: SimulationSnapshot["current_stage"] | undefined): SimulationCgEmotion {
  switch (stage) {
    case "evidence":
    case "debate":
      return "pressing";
    case "mediation_or_judgment":
      return "stern";
    case "report_ready":
      return "reflective";
    default:
      return "steady";
  }
}

function fallbackTarget(stage: SimulationSnapshot["current_stage"] | undefined): SimulationCgTargetId {
  switch (stage) {
    case "prepare":
      return "claim_sheet";
    case "investigation":
      return "bench";
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

function fallbackStageImageUrl(
  stage: SimulationSnapshot["current_stage"] | undefined,
): string | undefined {
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
      return undefined;
  }
}

function pickSpeakerCharacter(
  role: SimulationSnapshot["speaker_role"] | undefined,
): SimulationCgCharacterId {
  switch (role) {
    case "judge":
      return "judge_penguin";
    case "plaintiff":
    case "applicant":
      return "plaintiff_penguin";
    case "defendant":
    case "respondent":
      return "defendant_penguin";
    case "agent":
      return "plaintiff_agent_penguin";
    case "witness":
      return "witness_penguin";
    default:
      return "clerk_penguin";
  }
}

function fallbackLeftCharacter(
  snapshot: SimulationSnapshot | null,
): SimulationCgCharacterId | null {
  if (!snapshot) {
    return null;
  }

  if (snapshot.speaker_role === "judge") {
    return "judge_penguin";
  }

  return "judge_penguin";
}

function fallbackRightCharacter(
  snapshot: SimulationSnapshot | null,
): SimulationCgCharacterId | null {
  if (!snapshot) {
    return null;
  }

  if (snapshot.speaker_role === "judge") {
    return "plaintiff_agent_penguin";
  }

  return pickSpeakerCharacter(snapshot.speaker_role);
}

export function TrialScenePanel({
  snapshot,
  currentStageLabel,
  currentTask,
  degradedFlags = [],
  visibleBeats = [],
  revealState = "idle",
  showTaskPanel = true,
}: TrialScenePanelProps): JSX.Element {
  const cgScene = snapshot?.cg_scene ?? null;
  const cgBackground =
    cgScene?.background_id ?? fallbackBackground(snapshot?.current_stage);
  const cgShot = cgScene?.shot_type ?? fallbackShot(snapshot?.current_stage);
  const cgEmotion =
    cgScene?.speaker_emotion ?? fallbackEmotion(snapshot?.current_stage);
  const cgTarget =
    cgScene?.emphasis_target ?? fallbackTarget(snapshot?.current_stage);
  const cgLeftCharacter =
    cgScene?.left_character_id ?? fallbackLeftCharacter(snapshot);
  const cgRightCharacter =
    cgScene?.right_character_id ?? fallbackRightCharacter(snapshot);
  const speakerCharacter = pickSpeakerCharacter(snapshot?.speaker_role);
  const cinematicCaption = readNarrative(
    unwrapBracketLabel(pickNarrative(cgScene?.caption, snapshot?.cg_caption)),
    "法庭镜头仍在等待你推动下一步动作。",
  );
  const cinematicImageUrl = resolveBackendAssetUrl(
    pickNarrative(cgScene?.image_url) ??
      fallbackStageImageUrl(snapshot?.current_stage),
  );
  const visibleFlags = degradedFlags
    .filter((flag) => flag !== "static_cg_applied")
    .map((flag) => DEGRADED_FLAG_LABELS[flag] ?? flag)
    .filter((flag) => flag.trim().length > 0);
  const visibleNarrativeBeats = visibleBeats.length > 0
    ? visibleBeats
    : [
        {
          id: "fallback-beat",
          tone: "dynamic" as const,
          label: "庭上动态",
          text: "当前还没有可展示的庭审叙事，请先进入案件并推动第一轮动作。",
        },
      ];

  return (
    <section className="trial-scene-panel" aria-live="polite">
      <header className="trial-scene-panel__header">
        <div className="trial-scene-panel__header-copy">
          <p className="trial-scene-panel__eyebrow">{currentStageLabel}</p>
          <h2 className="trial-scene-panel__title">
            {snapshot?.scene_title ?? "庭审场景尚未展开"}
          </h2>
        </div>
      </header>

      <section className="trial-scene-panel__narrative">
        <div className="trial-scene-panel__cinematic-block">
          <div
            className={joinClassNames(
              "trial-scene-panel__cg-stage",
              cinematicImageUrl && "is-rendered-image",
              toModifier(cgBackground),
              toModifier(`shot-${cgShot}`),
              toModifier(`emotion-${cgEmotion}`),
            )}
            aria-label="文游分镜画面"
          >
            {cinematicImageUrl ? (
              <img
                className="trial-scene-panel__cg-image"
                src={cinematicImageUrl}
                alt={cinematicCaption}
              />
            ) : null}

            <div className="trial-scene-panel__cg-bench" aria-hidden="true">
              <span className="trial-scene-panel__cg-bench-label">审判席</span>
            </div>

            {cgLeftCharacter ? (
              <article
                className={joinClassNames(
                  "trial-scene-panel__cg-character",
                  "trial-scene-panel__cg-character--left",
                  toModifier(cgLeftCharacter),
                  cgLeftCharacter === speakerCharacter &&
                    "trial-scene-panel__cg-character--speaker",
                )}
              >
                <div
                  className="trial-scene-panel__cg-character-figure"
                  aria-hidden="true"
                >
                  <span className="trial-scene-panel__cg-character-head" />
                  <span className="trial-scene-panel__cg-character-body" />
                  <span className="trial-scene-panel__cg-character-belly" />
                  <span className="trial-scene-panel__cg-character-beak" />
                  <span className="trial-scene-panel__cg-character-trim" />
                </div>
                <span className="trial-scene-panel__cg-character-name">
                  {formatCgCharacterLabel(cgLeftCharacter)}
                </span>
              </article>
            ) : null}

            <div
              className={joinClassNames(
                "trial-scene-panel__cg-focus",
                toModifier(cgTarget),
              )}
            >
              <span className="trial-scene-panel__cg-focus-label">
                {formatCgTargetLabel(cgTarget)}
              </span>
              <strong className="trial-scene-panel__cg-focus-value">
                {readNarrative(
                  snapshot?.branch_focus
                    ? formatFocusLabel(snapshot.branch_focus)
                    : undefined,
                  "当前争点尚未生成",
                )}
              </strong>
            </div>

            {cgRightCharacter ? (
              <article
                className={joinClassNames(
                  "trial-scene-panel__cg-character",
                  "trial-scene-panel__cg-character--right",
                  toModifier(cgRightCharacter),
                  cgRightCharacter === speakerCharacter &&
                    "trial-scene-panel__cg-character--speaker",
                )}
              >
                <div
                  className="trial-scene-panel__cg-character-figure"
                  aria-hidden="true"
                >
                  <span className="trial-scene-panel__cg-character-head" />
                  <span className="trial-scene-panel__cg-character-body" />
                  <span className="trial-scene-panel__cg-character-belly" />
                  <span className="trial-scene-panel__cg-character-beak" />
                  <span className="trial-scene-panel__cg-character-trim" />
                </div>
                <span className="trial-scene-panel__cg-character-name">
                  {formatCgCharacterLabel(cgRightCharacter)}
                </span>
              </article>
            ) : null}

            {cgScene?.effect_id ? (
              <div
                className={joinClassNames(
                  "trial-scene-panel__cg-effect",
                  toModifier(cgScene.effect_id),
                )}
                aria-hidden="true"
              />
            ) : null}
          </div>

        </div>

        <div className="trial-scene-panel__storyline" aria-label="当前庭审叙事流">
          {visibleNarrativeBeats.map((beat, index) => (
            <article
              key={beat.id}
              className={[
                "trial-scene-panel__beat",
                `is-${beat.tone}`,
              ].join(" ")}
              style={
                {
                  "--beat-order": `${index}`,
                } as CSSProperties
              }
            >
              <p className="trial-scene-panel__beat-label">{beat.label}</p>
              <p className="trial-scene-panel__text">{beat.text}</p>
            </article>
          ))}

          {revealState === "revealing" ? (
            <div
              className="trial-scene-panel__story-cursor"
              aria-label="法庭叙事仍在继续"
            >
              <span />
              <span />
              <span />
            </div>
          ) : null}
        </div>
      </section>

      {showTaskPanel ? (
        <section className="trial-scene-panel__task-panel" aria-label="当前任务">
          <div className="trial-scene-panel__task-copy">
            <p className="trial-scene-panel__task-label">当前任务</p>
            <h3 className="trial-scene-panel__task-title">
              {readNarrative(currentTask, "等待当前回合任务生成。")}
            </h3>
          </div>
        </section>
      ) : null}

      {visibleFlags.length > 0 ? (
        <p className="trial-scene-panel__warning" aria-label="执行提醒">
          {visibleFlags.join(" ")}
        </p>
      ) : null}
    </section>
  );
}
