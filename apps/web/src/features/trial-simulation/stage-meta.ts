import type { TrialStage } from "../../types/turn";

export interface TrialStageMeta {
  stage: TrialStage;
  label: string;
  description: string;
}

export const TRIAL_STAGE_META: TrialStageMeta[] = [
  {
    stage: "prepare",
    label: "开庭准备",
    description: "确认到庭情况、程序权利和庭前策略，为正式进入庭审建立主动节奏。",
  },
  {
    stage: "investigation",
    label: "法庭调查",
    description: "围绕案件事实、争议焦点和举证基础展开问答，逐步固定关键叙事。",
  },
  {
    stage: "evidence",
    label: "举证质证",
    description: "对证据的真实性、合法性、关联性逐项攻防，决定证明力能否站稳。",
  },
  {
    stage: "debate",
    label: "法庭辩论",
    description: "把事实、证据与法理压缩成清晰论证，争夺法官对主轴的认定方向。",
  },
  {
    stage: "final_statement",
    label: "最后陈述",
    description: "收束全场重点，用最简洁的表达确认诉请、风险点与裁判期待。",
  },
  {
    stage: "mediation_or_judgment",
    label: "调解 / 判决",
    description: "根据当前局势进入调解博弈或裁判落点判断，观察案件可能收束的方式。",
  },
  {
    stage: "report_ready",
    label: "复盘就绪",
    description: "本轮推演已经收束，可以整理关键转折、证据短板与下一步备战动作。",
  },
];

export function getTrialStageMeta(stage: TrialStage): TrialStageMeta {
  return TRIAL_STAGE_META.find((item) => item.stage === stage) ?? TRIAL_STAGE_META[0];
}
