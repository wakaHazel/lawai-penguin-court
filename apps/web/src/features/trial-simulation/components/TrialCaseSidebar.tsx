import type { CaseProfile } from "../../../types/case";
import { formatTrialStageLabel } from "../../../types/display";
import type { SimulationSnapshot } from "../../../types/turn";

interface TrialCaseSidebarProps {
  caseProfile: CaseProfile | null;
  snapshot?: SimulationSnapshot | null;
}

const CASE_TYPE_LABELS: Record<string, string> = {
  private_lending: "民间借贷",
  labor_dispute: "劳动争议",
  divorce_dispute: "离婚纠纷",
  tort_liability: "侵权责任",
};

function getCaseTypeLabel(caseType: string | undefined): string {
  if (!caseType) {
    return "未分类";
  }

  return CASE_TYPE_LABELS[caseType] ?? caseType;
}

export function TrialCaseSidebar({
  caseProfile,
  snapshot,
}: TrialCaseSidebarProps): JSX.Element {
  return (
    <aside className="trial-case-sidebar" aria-label="案件资料抽屉">
      <section className="trial-case-sidebar__hero">
        <p className="trial-case-sidebar__eyebrow">案件资料</p>
        <h3 className="trial-case-sidebar__title">
          {caseProfile?.title ?? "尚未载入案件"}
        </h3>
        <p className="trial-case-sidebar__summary">
          {caseProfile?.summary ?? "等待案件信息载入后显示摘要。"}
        </p>
        <div className="trial-case-sidebar__chips">
          <span>{getCaseTypeLabel(caseProfile?.case_type)}</span>
          <span>回合 {snapshot?.turn_index ?? 0}</span>
          <span>{formatTrialStageLabel(snapshot?.current_stage)}</span>
        </div>
      </section>

      <section className="trial-case-sidebar__section">
        <h3 className="trial-case-sidebar__heading">本案诉求</h3>
        <ul>
          {(caseProfile?.claims ?? []).length > 0 ? (
            (caseProfile?.claims ?? []).map((claim) => <li key={claim}>{claim}</li>)
          ) : (
            <li>暂无诉求信息。</li>
          )}
        </ul>
      </section>

      <section className="trial-case-sidebar__section">
        <h3 className="trial-case-sidebar__heading">争议焦点</h3>
        <ul>
          {(caseProfile?.focus_issues ?? []).length > 0 ? (
            (caseProfile?.focus_issues ?? []).map((issue) => (
              <li key={issue}>{issue}</li>
            ))
          ) : (
            <li>暂无争点信息。</li>
          )}
        </ul>
      </section>

      <section className="trial-case-sidebar__section">
        <h3 className="trial-case-sidebar__heading">证据薄弱点</h3>
        <ul>
          {(caseProfile?.missing_evidence ?? []).length > 0 ? (
            (caseProfile?.missing_evidence ?? []).map((item) => (
              <li key={item}>{item}</li>
            ))
          ) : (
            <li>当前未标记明显缺口。</li>
          )}
        </ul>
      </section>
    </aside>
  );
}
