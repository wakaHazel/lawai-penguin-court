import type {
  CaseDomain,
  CaseType,
  UserGoal,
  UserPerspectiveRole,
} from "../../types/case";

export interface SelectOption<T extends string> {
  value: T;
  label: string;
  hint?: string;
  disabled?: boolean;
}

export const domainOptions: SelectOption<CaseDomain>[] = [
  {
    value: "civil",
    label: "民事案件",
    hint: "当前框架优先支持民间借贷、劳动争议、离婚纠纷、侵权责任。",
  },
  {
    value: "criminal",
    label: "刑事案件",
    hint: "该方向暂未开放，先保留在规划中。",
    disabled: true,
  },
  {
    value: "administrative",
    label: "行政案件",
    hint: "该方向暂未开放，先保留在规划中。",
    disabled: true,
  },
];

export const caseTypeOptionsByDomain: Record<
  CaseDomain,
  SelectOption<CaseType>[]
> = {
  civil: [
    { value: "private_lending", label: "民间借贷" },
    { value: "labor_dispute", label: "劳动争议" },
    { value: "divorce_dispute", label: "离婚纠纷" },
    { value: "tort_liability", label: "侵权责任" },
  ],
  criminal: [],
  administrative: [],
};

export const userPerspectiveOptions: SelectOption<UserPerspectiveRole>[] = [
  { value: "claimant_side", label: "主张方视角" },
  { value: "respondent_side", label: "对方视角" },
  { value: "neutral_observer", label: "中立观察" },
  { value: "learner", label: "学习训练" },
  { value: "other", label: "其他" },
];

export const userGoalOptions: SelectOption<UserGoal>[] = [
  { value: "simulate_trial", label: "进行庭审模拟" },
  { value: "analyze_win_rate", label: "评估胜诉率" },
  { value: "prepare_checklist", label: "生成备战清单" },
  { value: "review_evidence", label: "梳理证据薄弱点" },
];
