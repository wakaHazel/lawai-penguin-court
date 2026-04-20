import type { CaseIntakeDraft } from "./draft";

export type IntakeFieldControl =
  | "text"
  | "textarea"
  | "select"
  | "multiselect";

export interface IntakeFieldConfig {
  key: keyof CaseIntakeDraft;
  label: string;
  control: IntakeFieldControl;
  required: boolean;
  section: "basic" | "parties" | "dispute" | "notes";
  placeholder?: string;
  optionSource?:
    | "domainOptions"
    | "caseTypeOptionsByDomain"
    | "userPerspectiveOptions"
    | "userGoalOptions";
}

export const caseIntakeFieldConfig: IntakeFieldConfig[] = [
  {
    key: "domain",
    label: "案件领域",
    control: "select",
    required: true,
    section: "basic",
    optionSource: "domainOptions",
  },
  {
    key: "case_type",
    label: "案件类型",
    control: "select",
    required: true,
    section: "basic",
    optionSource: "caseTypeOptionsByDomain",
  },
  {
    key: "title",
    label: "案件标题",
    control: "text",
    required: true,
    section: "basic",
    placeholder: "例如：未签劳动合同双倍工资争议",
  },
  {
    key: "summary",
    label: "案件概述",
    control: "textarea",
    required: true,
    section: "basic",
    placeholder: "用 3 到 5 句话概括争议背景、关键事实和诉求方向。",
  },
  {
    key: "user_perspective_role",
    label: "使用视角",
    control: "select",
    required: true,
    section: "basic",
    optionSource: "userPerspectiveOptions",
  },
  {
    key: "user_goals",
    label: "本次目标",
    control: "multiselect",
    required: true,
    section: "basic",
    optionSource: "userGoalOptions",
  },
  {
    key: "plaintiff_name",
    label: "原告 / 申请人",
    control: "text",
    required: true,
    section: "parties",
    placeholder: "填写主张方姓名或主体名称",
  },
  {
    key: "defendant_name",
    label: "被告 / 被申请人",
    control: "text",
    required: true,
    section: "parties",
    placeholder: "填写对方姓名或主体名称",
  },
  {
    key: "claims_text",
    label: "诉讼请求",
    control: "textarea",
    required: false,
    section: "dispute",
    placeholder: "每行一条，例如：\n确认劳动关系\n支付未签劳动合同双倍工资差额",
  },
  {
    key: "core_facts_text",
    label: "核心事实",
    control: "textarea",
    required: false,
    section: "dispute",
    placeholder: "每行一条，写清时间、行为、证据线索和争议节点。",
  },
  {
    key: "focus_issues_text",
    label: "争议焦点",
    control: "textarea",
    required: false,
    section: "dispute",
    placeholder: "每行一条，例如：劳动关系是否成立",
  },
  {
    key: "missing_evidence_text",
    label: "缺口证据",
    control: "textarea",
    required: false,
    section: "dispute",
    placeholder: "每行一条，例如：工资流水、考勤记录、社保记录",
  },
  {
    key: "notes",
    label: "补充备注",
    control: "textarea",
    required: false,
    section: "notes",
    placeholder: "记录暂时无法结构化的信息、风险提醒或老师建议。",
  },
];
