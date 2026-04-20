import type { SimulationSnapshot } from "../../types/turn";

type WorkflowHint = SimulationSnapshot["workflow_hints"][number];
type WorkflowKey = WorkflowHint["workflow_key"];

interface WorkflowMeta {
  label: string;
  description: string;
}

export const WORKFLOW_META: Record<WorkflowKey, WorkflowMeta> = {
  courtroom_scene_generation: {
    label: "庭审场景生成",
    description: "按当前阶段生成法庭叙事、发言角色与下一步互动动作。",
  },
  legal_support_retrieval: {
    label: "法律支持检索",
    description: "围绕争议焦点、诉请和证据缺口补充法条与案例支持。",
  },
  opponent_behavior_simulation: {
    label: "对方行为模拟",
    description: "预测对方最可能提出的抗辩、证据和应对策略。",
  },
  outcome_analysis_report: {
    label: "结果分析报告",
    description: "基于推演轨迹输出胜诉率判断、风险解释和复盘结论。",
  },
};

export const WORKFLOW_VARIABLE_LABELS: Record<string, string> = {
  case_id: "案件 ID",
  case_type: "案件类型",
  current_stage: "当前阶段",
  turn_index: "轮次",
  selected_action: "所选动作",
  next_stage: "下一阶段",
  branch_focus: "本轮焦点",
  focus_issues: "争议焦点",
  claims: "诉讼请求",
  fact_keywords: "事实关键词",
  missing_evidence: "缺口证据",
  likely_arguments: "可能抗辩",
  likely_evidence: "可能证据",
  likely_strategies: "可能策略",
  opponent_role: "对方角色",
  opponent_name: "对方名称",
  opponent_arguments: "对方观点",
  v_case_type: "案件类型",
  v_case_title: "案件标题",
  v_case_summary: "案件概述",
  v_focus_issues: "争议焦点",
  v_claims: "诉讼请求",
  v_missing_evidence: "缺口证据",
  v_notes: "备注",
};

export function getWorkflowLabel(workflowKey: WorkflowKey): string {
  return WORKFLOW_META[workflowKey]?.label ?? workflowKey;
}

export function getWorkflowDescription(workflowKey: WorkflowKey): string {
  return WORKFLOW_META[workflowKey]?.description ?? "暂无工作流说明。";
}

export function getWorkflowVariableLabel(variableKey: string): string {
  return WORKFLOW_VARIABLE_LABELS[variableKey] ?? variableKey;
}

export function formatWorkflowVariableValue(
  value: string | number | string[],
): string {
  if (Array.isArray(value)) {
    return value.length > 0 ? value.join("、") : "未提供";
  }

  if (typeof value === "number") {
    return String(value);
  }

  const normalized = value.trim();
  return normalized || "未提供";
}
