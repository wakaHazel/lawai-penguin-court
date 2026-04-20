import type { SimulationSnapshot } from "../../types/turn";

export type TrialNarrativeBeatTone =
  | "cinematic"
  | "progress"
  | "dynamic"
  | "pressure";

export interface TrialNarrativeBeat {
  id: string;
  tone: TrialNarrativeBeatTone;
  label: string;
  text: string;
}

export interface TrialNarrativeFlow {
  beats: TrialNarrativeBeat[];
}

interface TaggedNarrativeBeat {
  label: string;
  text: string;
  tone: TrialNarrativeBeatTone;
}

const BEAT_LABELS: Record<TrialNarrativeBeatTone, string> = {
  cinematic: "镜头展开",
  progress: "法庭推进",
  dynamic: "庭上动态",
  pressure: "局势变化",
};

export function readNarrative(
  value: string | undefined | null,
  fallback: string,
): string {
  if (typeof value !== "string") {
    return fallback;
  }

  const normalized = value.trim();
  return normalized || fallback;
}

export function pickNarrative(
  ...values: Array<string | undefined | null>
): string | undefined {
  for (const value of values) {
    if (typeof value !== "string") {
      continue;
    }

    const normalized = value.trim();
    if (normalized) {
      return normalized;
    }
  }

  return undefined;
}

export function unwrapBracketLabel(
  value: string | undefined | null,
): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }

  const normalized = value.trim();
  if (!normalized) {
    return undefined;
  }

  const taggedMatch = normalized.match(/^【[^：】]+：(.+)】$/);
  if (taggedMatch) {
    return taggedMatch[1].trim();
  }

  const plainBracketMatch = normalized.match(/^【(.+)】$/);
  if (plainBracketMatch) {
    return plainBracketMatch[1].trim();
  }

  return normalized;
}

export function stripNarrativeLabel(
  value: string | undefined | null,
): string | undefined {
  const normalized = unwrapBracketLabel(value);
  if (!normalized) {
    return undefined;
  }

  return normalized
    .replace(/^当前处于/, "")
    .replace(/^法庭正式推进到/, "")
    .trim();
}

export function normalizeSceneBody(
  sceneText: string | undefined | null,
): string | undefined {
  if (typeof sceneText !== "string") {
    return undefined;
  }

  const normalized = sceneText.trim();
  if (!normalized) {
    return undefined;
  }

  const matches = Array.from(normalized.matchAll(/【([^：】]+)：([^】]+)】/g));
  if (matches.length === 0) {
    return normalized.replace(/【你准备如何应对？】/g, "").trim();
  }

  const dynamicSegment = matches.find(([, label]) => label === "庭上动态");
  if (dynamicSegment) {
    return dynamicSegment[2].trim();
  }

  const cleaned = matches
    .filter(([_, label]) => label !== "CG画面" && label !== "插画分镜")
    .map(([_, label, content]) => {
      if (label === "你准备如何应对？" || label === "请选择本轮回应策略") {
        return "";
      }

      return content.trim();
    })
    .filter(Boolean)
    .join(" ");

  return cleaned || normalized;
}

export function refineSceneBody(
  sceneBody: string | undefined,
  progressText: string,
  pressureText: string,
): string {
  if (!sceneBody) {
    return pressureText;
  }

  const normalized = collapseText(sceneBody);
  const normalizedProgress = collapseText(progressText);
  if (!normalizedProgress) {
    return normalized === pressureText ? pressureText : normalized;
  }

  const withoutProgress = normalized
    .replace(normalizedProgress, "")
    .replace(pressureText, "")
    .replace(/^[，。；、\s]+/, "")
    .trim();

  if (!withoutProgress) {
    return pressureText;
  }

  if (withoutProgress.length < 30 && withoutProgress !== pressureText) {
    return `${withoutProgress} ${pressureText}`.trim();
  }

  return withoutProgress;
}

export function buildTrialNarrativeFlow(
  snapshot: SimulationSnapshot | null,
): TrialNarrativeFlow {
  if (!snapshot) {
    return { beats: [] };
  }

  const choicePrompt = normalizeChoicePrompt(snapshot.choice_prompt);
  const candidateBeats: TrialNarrativeBeat[] = [];
  const seen = new Set<string>();

  const addBeat = (
    tone: TrialNarrativeBeatTone,
    rawText: string | undefined | null,
    suffix?: string,
    labelOverride?: string,
  ): void => {
    const text = normalizeNarrativeText(rawText);
    if (!text) {
      return;
    }

    const collapsed = collapseText(text);
    if (!collapsed || collapsed === choicePrompt || seen.has(collapsed)) {
      return;
    }

    seen.add(collapsed);
    candidateBeats.push({
      id: `${tone}-${suffix ?? candidateBeats.length}`,
      tone,
      label: labelOverride ?? BEAT_LABELS[tone],
      text,
    });
  };

  addBeat("cinematic", unwrapBracketLabel(snapshot.cg_caption));
  const taggedBeats = extractTaggedNarrativeBeats(
    snapshot.scene_text,
    choicePrompt,
  );

  if (taggedBeats.length > 0) {
    taggedBeats.forEach((beat, index) => {
      addBeat(beat.tone, beat.text, `tagged-${index}`, beat.label);
    });
  } else {
    addBeat("progress", stripNarrativeLabel(snapshot.court_progress));
    const sceneBody = normalizeSceneBody(snapshot.scene_text);
    const pressureText = readNarrative(
      stripNarrativeLabel(snapshot.pressure_shift),
      "",
    );
    const progressText = readNarrative(
      stripNarrativeLabel(snapshot.court_progress),
      "",
    );
    addBeat("dynamic", refineSceneBody(sceneBody, progressText, pressureText));
    addBeat("pressure", stripNarrativeLabel(snapshot.pressure_shift));
  }

  if (candidateBeats.length === 0) {
    addBeat("dynamic", snapshot.scene_text || snapshot.scene_title);
  }

  return { beats: candidateBeats };
}

export function getNarrativeBeatDelay(beat: TrialNarrativeBeat): number {
  const baseline =
    beat.tone === "cinematic"
      ? 760
      : beat.tone === "pressure"
        ? 900
        : 820;
  const scaled = beat.text.length * 26;
  return Math.min(2200, Math.max(baseline, scaled));
}

function normalizeChoicePrompt(value: string | null | undefined): string {
  const unwrapped = unwrapBracketLabel(value);
  return collapseText(unwrapped ?? "");
}

function extractTaggedNarrativeBeats(
  sceneText: string | undefined | null,
  choicePrompt: string,
): TaggedNarrativeBeat[] {
  if (typeof sceneText !== "string") {
    return [];
  }

  const normalized = sceneText.trim();
  if (!normalized) {
    return [];
  }

  const taggedSegments = Array.from(normalized.matchAll(/【([^：】]+)：([^】]+)】/g));
  if (taggedSegments.length === 0) {
    return [];
  }

  return taggedSegments
    .filter(([, label]) => {
      return ![
        "CG画面",
        "插画分镜",
        "法庭进程",
        "局势变化",
        "你准备如何应对？",
        "请选择本轮回应策略",
      ].includes(label);
    })
    .map(([, label, content]) => {
      const text = normalizeNarrativeText(content);
      if (!text || collapseText(text) === choicePrompt) {
        return null;
      }

      return {
        label: label.trim(),
        text,
        tone: mapNarrativeLabelToTone(label.trim()),
      } satisfies TaggedNarrativeBeat;
    })
    .filter((value): value is TaggedNarrativeBeat => Boolean(value));
}

function mapNarrativeLabelToTone(label: string): TrialNarrativeBeatTone {
  switch (label) {
    case "法官发问":
      return "progress";
    case "对方动作":
      return "pressure";
    case "你的动作影响":
    case "你刚补入":
      return "progress";
    case "庭上动态":
    default:
      return "dynamic";
  }
}

function normalizeNarrativeText(value: string | undefined | null): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }

  const normalized = value
    .replace(/【你准备如何应对？】/g, "")
    .replace(/【请选择本轮回应策略】/g, "")
    .replace(/\s+/g, " ")
    .trim();

  return normalized || undefined;
}

function collapseText(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}
