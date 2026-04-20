import type { CaseIntakeDraft } from "./draft";
import { findDemoCaseById } from "./demo-case-library";

export interface DemoCasePreset {
  id: string;
  label: string;
  description: string;
  draft: CaseIntakeDraft;
}

const FEATURED_PRESET_CONFIG = [
  {
    id: "demo-labor_dispute-01",
    label: "劳动争议示例",
    description: "适合演示劳动关系确认、工资差额与证据缺口梳理。",
  },
  {
    id: "demo-private_lending-01",
    label: "民间借贷示例",
    description: "适合演示借贷关系认定、还款事实与抗辩策略。",
  },
  {
    id: "demo-divorce_dispute-01",
    label: "离婚纠纷示例",
    description: "适合演示婚姻关系、财产分割与子女抚养争点。",
  },
  {
    id: "demo-tort_liability-01",
    label: "侵权责任示例",
    description: "适合演示责任构成、损害后果与赔偿范围推演。",
  },
] as const;

function getPresetDraft(id: string): CaseIntakeDraft {
  const demoCase = findDemoCaseById(id);
  if (!demoCase?.draft) {
    throw new Error(`Featured demo case "${id}" is unavailable.`);
  }

  return {
    ...demoCase.draft,
    user_goals: [...demoCase.draft.user_goals],
  };
}

export const FEATURED_DEMO_PRESETS: DemoCasePreset[] = FEATURED_PRESET_CONFIG.map(
  (preset) => ({
    ...preset,
    draft: getPresetDraft(preset.id),
  }),
);
