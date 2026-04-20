from __future__ import annotations

from typing import Any

from ..schemas.case import CaseProfile, EvidenceStrength
from ..schemas.common import CaseParticipantRole, CaseType
from ..schemas.trial_workflow import TrialRunSnapshot
from ..schemas.turn import (
    SimulationActionCard,
    SimulationSnapshot,
    SimulationUserInputEntry,
    TrialStage,
)
from .deli_client import DeliClient, DeliClientError

_REPORT_SECTION_KEYS = [
    "header",
    "main_axis",
    "turning_points",
    "timeline",
    "evidence_risk",
    "opponent",
    "suggestions",
    "result",
]

_STAGE_SEQUENCE = [
    TrialStage.PREPARE,
    TrialStage.INVESTIGATION,
    TrialStage.EVIDENCE,
    TrialStage.DEBATE,
    TrialStage.FINAL_STATEMENT,
    TrialStage.MEDIATION_OR_JUDGMENT,
    TrialStage.REPORT_READY,
]

_STAGE_CONFIDENCE: dict[TrialStage, float] = {
    TrialStage.PREPARE: 0.38,
    TrialStage.INVESTIGATION: 0.48,
    TrialStage.EVIDENCE: 0.6,
    TrialStage.DEBATE: 0.72,
    TrialStage.FINAL_STATEMENT: 0.8,
    TrialStage.MEDIATION_OR_JUDGMENT: 0.86,
    TrialStage.REPORT_READY: 0.9,
}

_CASE_TYPE_LABELS: dict[CaseType, str] = {
    CaseType.PRIVATE_LENDING: "民间借贷纠纷",
    CaseType.LABOR_DISPUTE: "劳动争议",
    CaseType.DIVORCE_DISPUTE: "离婚纠纷",
    CaseType.TORT_LIABILITY: "侵权责任纠纷",
}


class BackendOrchestrator:
    def __init__(self, deli_client: DeliClient | None = None) -> None:
        self._deli_client = deli_client or DeliClient.from_env()

    def enrich_snapshot(
        self,
        *,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
        run: TrialRunSnapshot,
        selected_action: str,
        historical_dialogs: str,
        preserve_existing: bool = True,
    ) -> SimulationSnapshot:
        legal_support, legal_flags = self._build_legal_support(case_profile, snapshot)
        opponent = self._build_opponent(case_profile, snapshot, run, selected_action)
        analysis = self._build_analysis(
            case_profile=case_profile,
            snapshot=snapshot,
            run=run,
            historical_dialogs=historical_dialogs,
        )

        suggested_actions = self._merge_list(
            snapshot.suggested_actions,
            self._build_suggested_actions(snapshot, analysis),
            preserve_existing=preserve_existing,
        )
        stage_objective = self._merge_scalar(
            snapshot.stage_objective,
            self._build_stage_objective(snapshot.current_stage),
            preserve_existing=preserve_existing,
        )
        current_task = self._merge_scalar(
            snapshot.current_task,
            self._build_current_task(case_profile, snapshot, run),
            preserve_existing=preserve_existing,
        )
        action_cards = self._merge_action_cards(
            snapshot.action_cards,
            self._build_action_cards(snapshot),
            preserve_existing=preserve_existing,
        )
        hidden_state_summary = self._merge_dict(
            snapshot.hidden_state_summary,
            self._build_user_input_hidden_state(snapshot),
            preserve_existing=preserve_existing,
        )
        next_stage_hint = self._merge_scalar(
            snapshot.next_stage_hint,
            self._infer_next_stage_hint(snapshot.current_stage),
            preserve_existing=preserve_existing,
        )
        degraded_flags = _append_unique(snapshot.degraded_flags, legal_flags)

        return snapshot.model_copy(
            update={
                "suggested_actions": suggested_actions,
                "stage_objective": stage_objective,
                "current_task": current_task,
                "action_cards": action_cards,
                "hidden_state_summary": hidden_state_summary,
                "next_stage_hint": next_stage_hint,
                "legal_support": self._merge_dict(
                    snapshot.legal_support,
                    legal_support,
                    preserve_existing=preserve_existing,
                ),
                "opponent": self._merge_dict(
                    snapshot.opponent,
                    opponent,
                    preserve_existing=preserve_existing,
                ),
                "analysis": self._merge_dict(
                    snapshot.analysis,
                    analysis,
                    preserve_existing=preserve_existing,
                ),
                "degraded_flags": degraded_flags,
            }
        )

    def _build_legal_support(
        self,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
    ) -> tuple[dict[str, Any], list[str]]:
        queries = self._build_recommended_queries(case_profile, snapshot)
        payload: dict[str, Any] = {
            "retrieval_mode": "fallback",
            "recommended_queries": queries,
            "focus_issues": _clean_list(case_profile.focus_issues),
            "missing_evidence": _clean_list(case_profile.missing_evidence),
            "legal_support_summary": self._build_legal_support_summary(
                case_profile,
                snapshot,
                [],
                [],
            ),
            "referenced_laws": [],
            "referenced_cases": [],
        }

        if not self._deli_client.is_enabled():
            return payload, []

        try:
            laws: list[dict[str, Any]] = []
            cases: list[dict[str, Any]] = []
            for query in queries[:2]:
                laws.extend(self._normalize_search_results(self._deli_client.query_laws(query), "law"))
                cases.extend(self._normalize_search_results(self._deli_client.query_cases(query), "case"))
            payload.update(
                {
                    "retrieval_mode": "direct_api",
                    "referenced_laws": self._dedupe_result_items(laws)[:3],
                    "referenced_cases": self._dedupe_result_items(cases)[:3],
                }
            )
            payload["legal_support_summary"] = self._build_legal_support_summary(
                case_profile,
                snapshot,
                payload["referenced_laws"],
                payload["referenced_cases"],
            )
            return payload, []
        except DeliClientError:
            return payload, ["deli_call_failed"]

    def _build_opponent(
        self,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
        run: TrialRunSnapshot,
        selected_action: str,
    ) -> dict[str, Any]:
        opponent_name, opponent_role = self._resolve_opponent_identity(case_profile)
        likely_arguments = self._infer_opponent_arguments(case_profile)
        likely_evidence = self._infer_opponent_evidence(case_profile)
        likely_strategies = self._infer_opponent_strategies(case_profile, snapshot)
        risk_points = self._build_risk_points(case_profile, run)
        recommended_responses = self._build_recommended_responses(
            case_profile=case_profile,
            snapshot=snapshot,
            selected_action=selected_action,
            likely_arguments=likely_arguments,
        )
        return {
            "opponent_name": opponent_name,
            "opponent_role": opponent_role,
            "branch_focus": snapshot.branch_focus,
            "likely_arguments": likely_arguments,
            "likely_evidence": likely_evidence,
            "likely_strategies": likely_strategies,
            "recommended_responses": recommended_responses,
            "risk_points": risk_points,
            "confidence": self._build_confidence(snapshot.current_stage, run.turn_index),
        }

    def _build_analysis(
        self,
        *,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
        run: TrialRunSnapshot,
        historical_dialogs: str,
    ) -> dict[str, Any]:
        latest_user_input = self._get_latest_user_input(snapshot)
        estimated_win_rate = self._estimate_win_rate(
            case_profile,
            snapshot,
            run,
            latest_user_input,
        )
        recommended_next_actions = self._build_next_actions(
            snapshot,
            case_profile,
            latest_user_input,
        )
        positive_factors = self._build_positive_factors(
            case_profile,
            run,
            latest_user_input,
        )
        negative_factors = self._build_negative_factors(case_profile, run)
        evidence_gap_actions = self._build_evidence_gap_actions(case_profile)

        payload: dict[str, Any] = {
            "estimated_win_rate": estimated_win_rate,
            "confidence": self._build_confidence(snapshot.current_stage, run.turn_index),
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "evidence_gap_actions": evidence_gap_actions,
            "recommended_next_actions": recommended_next_actions,
        }

        if snapshot.current_stage == TrialStage.REPORT_READY:
            payload.update(
                {
                    "report_status": "ready",
                    "report_section_keys": list(_REPORT_SECTION_KEYS),
                    "report_overview": self._build_report_overview(
                        case_profile=case_profile,
                        snapshot=snapshot,
                        estimated_win_rate=estimated_win_rate,
                        historical_dialogs=historical_dialogs,
                    ),
                }
            )

        return payload

    def _build_recommended_queries(
        self,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
    ) -> list[str]:
        latest_user_input = self._get_latest_user_input(snapshot)
        raw_queries = [
            *_clean_list(case_profile.focus_issues),
            *(
                [f"{latest_user_input.label} {latest_user_input.content}"]
                if latest_user_input is not None
                else []
            ),
            *_clean_list(case_profile.claims)[:2],
            f"{_CASE_TYPE_LABELS.get(case_profile.case_type, case_profile.case_type.value)} {snapshot.branch_focus}",
            *_clean_list(case_profile.missing_evidence)[:2],
        ]
        deduped = _dedupe_preserve_order(raw_queries)
        return deduped[:5] or [case_profile.summary]

    def _build_legal_support_summary(
        self,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
        laws: list[dict[str, Any]],
        cases: list[dict[str, Any]],
    ) -> str:
        focus = _clean_list(case_profile.focus_issues)
        missing = _clean_list(case_profile.missing_evidence)
        law_hint = ""
        if laws or cases:
            law_hint = f" 当前已直连检索到 {len(laws)} 条法律线索、{len(cases)} 条类案线索。"
        focus_text = focus[0] if focus else snapshot.branch_focus
        missing_text = missing[0] if missing else "当前证据链中的薄弱环节"
        return (
            f"当前阶段的主轴聚焦于“{focus_text}”。"
            f" 优先把现有诉请、已有证据与“{missing_text}”这一补强方向重新对齐。{law_hint}"
        ).strip()

    def _normalize_search_results(
        self,
        items: list[dict[str, Any]],
        result_type: str,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in items:
            title = self._pick_first_text(
                item,
                "title",
                "name",
                "caseTitle",
                "lawName",
                "fullName",
            )
            if not title:
                continue
            normalized.append(
                {
                    "type": result_type,
                    "title": title,
                    "id": self._pick_first_text(item, "id", "lawId", "caseId", "docId"),
                    "summary": self._pick_first_text(
                        item,
                        "summary",
                        "digest",
                        "content",
                        "snippet",
                    ),
                }
            )
        return normalized

    def _dedupe_result_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ordered: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in items:
            marker = (str(item.get("type") or ""), str(item.get("title") or ""))
            if marker in seen:
                continue
            seen.add(marker)
            ordered.append(item)
        return ordered

    def _resolve_opponent_identity(self, case_profile: CaseProfile) -> tuple[str, str]:
        if case_profile.opponent_profile is not None:
            return (
                case_profile.opponent_profile.display_name,
                case_profile.opponent_profile.role.value,
            )

        for party in case_profile.parties:
            if party.role in {CaseParticipantRole.DEFENDANT, CaseParticipantRole.RESPONDENT}:
                return party.display_name, party.role.value

        for party in case_profile.parties:
            if party.role not in {CaseParticipantRole.PLAINTIFF, CaseParticipantRole.APPLICANT}:
                return party.display_name, party.role.value

        return "对方当事人", CaseParticipantRole.OTHER.value

    def _infer_opponent_arguments(self, case_profile: CaseProfile) -> list[str]:
        if case_profile.opponent_profile and _clean_list(case_profile.opponent_profile.likely_arguments):
            return _clean_list(case_profile.opponent_profile.likely_arguments)

        focus = _clean_list(case_profile.focus_issues)
        missing = _clean_list(case_profile.missing_evidence)
        arguments = []
        if focus:
            arguments.append(f"围绕“{focus[0]}”提出针对性反驳。")
        if missing:
            arguments.append(f"抓住“{missing[0]}”尚未补齐这一点，主张本方证明不足。")
        arguments.append("切断事实、证据与诉请结果之间的因果和证明联系。")
        return arguments

    def _infer_opponent_evidence(self, case_profile: CaseProfile) -> list[str]:
        if case_profile.opponent_profile and _clean_list(case_profile.opponent_profile.likely_evidence):
            return _clean_list(case_profile.opponent_profile.likely_evidence)

        defaults: dict[CaseType, list[str]] = {
            CaseType.LABOR_DISPUTE: [
                "项目合作或外包往来记录",
                "转账备注、结算说明等辅助材料",
            ],
            CaseType.PRIVATE_LENDING: [
                "否认借贷关系的聊天记录",
                "用于解释转账性质的其他往来材料",
            ],
            CaseType.DIVORCE_DISPUTE: [
                "财产出资与形成过程材料",
                "家庭共同支出或生活安排证明",
            ],
            CaseType.TORT_LIABILITY: [
                "事故责任划分相关材料",
                "用于质疑因果关系的反向证据",
            ],
        }
        return defaults.get(case_profile.case_type, ["对方事先准备的反向证明材料"])

    def _infer_opponent_strategies(
        self,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
    ) -> list[str]:
        if case_profile.opponent_profile and _clean_list(case_profile.opponent_profile.likely_strategies):
            return _clean_list(case_profile.opponent_profile.likely_strategies)

        strategies = [
            "把争议压缩到我方证明链最薄弱的那个点上。",
            "通过替代解释或重新定性，削弱我方关键证据的说服力。",
        ]
        if snapshot.current_stage in {TrialStage.EVIDENCE, TrialStage.DEBATE}:
            strategies.append("在举证或辩论阶段增加突袭细节与程序阻力。")
        return strategies

    def _build_recommended_responses(
        self,
        *,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
        selected_action: str,
        likely_arguments: list[str],
    ) -> list[str]:
        responses = []
        if selected_action and not selected_action.startswith("__"):
            responses.append(f"我方回应应继续围绕已选动作推进：{selected_action}。")
        if likely_arguments:
            responses.append(f"针对对方首要抗辩逐点准备回应：{likely_arguments[0]}")
        responses.extend(self._build_evidence_gap_actions(case_profile)[:2])
        if snapshot.available_actions:
            responses.append(f"下一轮优先补强这一步：{snapshot.available_actions[0]}。")
        return _dedupe_preserve_order(responses)

    def _build_risk_points(
        self,
        case_profile: CaseProfile,
        run: TrialRunSnapshot,
    ) -> list[str]:
        risk_points = []
        for item in _clean_list(case_profile.missing_evidence)[:2]:
            risk_points.append(f"证据缺口仍可能被对方追打：{item}。")
        if run.state.contradiction_risk >= 50:
            risk_points.append("当前矛盾风险偏高，法官追问时容易削弱整体可信度。")
        if run.state.surprise_exposure >= 45:
            risk_points.append("当前路径对突袭证据和未预判事实仍有较高暴露。")
        if not risk_points:
            risk_points.append("当前最大风险是叙事推进过快，但证明链补强还不够。")
        return risk_points

    def _estimate_win_rate(
        self,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
        run: TrialRunSnapshot,
        latest_user_input: SimulationUserInputEntry | None,
    ) -> int:
        strong = sum(1 for item in case_profile.evidence_items if item.strength == EvidenceStrength.STRONG)
        medium = sum(1 for item in case_profile.evidence_items if item.strength == EvidenceStrength.MEDIUM)
        weak = sum(1 for item in case_profile.evidence_items if item.strength == EvidenceStrength.WEAK)
        missing = len(_clean_list(case_profile.missing_evidence))

        raw_score = 50
        raw_score += strong * 8
        raw_score += medium * 4
        raw_score -= weak * 4
        raw_score -= missing * 6
        raw_score += max(-8, min(12, (run.state.evidence_strength - 50) // 4))
        raw_score += max(-6, min(10, (run.state.judge_trust - 50) // 5))
        raw_score += max(-4, min(6, (run.state.procedure_control - 50) // 6))
        raw_score -= max(0, (run.state.contradiction_risk - 45) // 4)
        raw_score -= max(0, (run.state.surprise_exposure - 35) // 5)
        raw_score += self._stage_score(snapshot.current_stage)
        raw_score += self._user_input_win_rate_bonus(latest_user_input)

        return max(15, min(92, int(raw_score)))

    def _build_positive_factors(
        self,
        case_profile: CaseProfile,
        run: TrialRunSnapshot,
        latest_user_input: SimulationUserInputEntry | None,
    ) -> list[str]:
        factors = []
        strong = sum(1 for item in case_profile.evidence_items if item.strength == EvidenceStrength.STRONG)
        medium = sum(1 for item in case_profile.evidence_items if item.strength == EvidenceStrength.MEDIUM)
        if strong:
            factors.append(f"我方已掌握 {strong} 项强证明力证据。")
        if medium:
            factors.append(f"当前还有 {medium} 项中等证明力材料可继续整合放大。")
        if latest_user_input is not None:
            factors.append(f"已新增{latest_user_input.label}：{latest_user_input.content}")
        if run.state.judge_trust >= 55:
            factors.append("当前法官信任度已高于中性基线。")
        if run.state.procedure_control >= 55:
            factors.append("当前程序节奏总体稳定，我方仍掌握一定主动性。")
        return factors or ["当前局面仍可推进，关键在于把证明链整理得更紧。"]

    def _build_negative_factors(
        self,
        case_profile: CaseProfile,
        run: TrialRunSnapshot,
    ) -> list[str]:
        factors = []
        missing = _clean_list(case_profile.missing_evidence)
        if missing:
            factors.append(f"证据链尚未闭合，首先卡在“{missing[0]}”。")
        if run.state.contradiction_risk >= 45:
            factors.append("当前论证线里仍存在可被放大的矛盾风险。")
        if run.state.opponent_pressure >= 55:
            factors.append("对方压迫感较强，要求我方回应更克制、更成体系。")
        return factors or ["暂未暴露决定性弱点，但未经证据支撑的推断仍有风险。"]

    def _build_evidence_gap_actions(self, case_profile: CaseProfile) -> list[str]:
        missing = _clean_list(case_profile.missing_evidence)
        if not missing:
            return ["下一轮前重新梳理现有证据链，并标记最薄弱的证明环节。"]
        return [f"尽快补齐或固定：{item}。" for item in missing]

    def _build_next_actions(
        self,
        snapshot: SimulationSnapshot,
        case_profile: CaseProfile,
        latest_user_input: SimulationUserInputEntry | None,
    ) -> list[str]:
        if snapshot.current_stage == TrialStage.REPORT_READY:
            actions = [
                "把本轮复盘整理成正式的庭审备战清单。",
                "优先针对最薄弱的证据环节做定向补强。",
                "围绕对方最强抗辩准备一版精简回应口径。",
            ]
            if latest_user_input is not None:
                actions.insert(
                    0,
                    f"把这条{latest_user_input.label}“{latest_user_input.content}”整理进复盘主轴。",
                )
            return _dedupe_preserve_order(actions)

        actions = []
        if latest_user_input is not None:
            actions.append(
                f"优先把这条{latest_user_input.label}“{latest_user_input.content}”接入本轮论证。"
            )
        if snapshot.available_actions:
            actions.extend(f"下一步可优先考虑：{item}。" for item in snapshot.available_actions[:2])
        actions.extend(self._build_evidence_gap_actions(case_profile)[:2])
        return _dedupe_preserve_order(actions)

    def _build_suggested_actions(
        self,
        snapshot: SimulationSnapshot,
        analysis: dict[str, Any],
    ) -> list[str]:
        if snapshot.available_actions:
            return snapshot.available_actions[:3]
        next_actions = analysis.get("recommended_next_actions")
        if isinstance(next_actions, list):
            return [str(item) for item in next_actions[:3]]
        return []

    def _build_stage_objective(self, current_stage: TrialStage) -> str:
        objectives = {
            TrialStage.PREPARE: "先把程序位置、诉请边界和表达节奏稳住，再进入正式庭审主线。",
            TrialStage.INVESTIGATION: "围绕核心事实与争议焦点建立法官的第一轮心证。",
            TrialStage.EVIDENCE: "决定哪些证据能真正站住，哪些地方最容易被对方打穿。",
            TrialStage.DEBATE: "把事实、证据和法理压缩成一条能说服法官的主论证线。",
            TrialStage.FINAL_STATEMENT: "收束整场庭审重点，让法官记住最关键的一句话。",
            TrialStage.MEDIATION_OR_JUDGMENT: "判断案件是否进入调解博弈，还是直接走向裁判落点。",
            TrialStage.REPORT_READY: "本轮庭审已经落定，接下来重点是复盘和备战。",
        }
        return objectives[current_stage]

    def _build_current_task(
        self,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
        run: TrialRunSnapshot,
    ) -> str:
        focus = _clean_list(case_profile.focus_issues)
        focus_text = focus[0] if focus else snapshot.branch_focus
        action = snapshot.available_actions[0] if snapshot.available_actions else "整理下一步应对"

        if snapshot.current_stage == TrialStage.PREPARE:
            return f"围绕“{focus_text}”先稳住程序节奏，并判断本轮应先如何进入主线。"
        if snapshot.current_stage == TrialStage.INVESTIGATION:
            return f"在事实调查阶段，你需要让“{focus_text}”成为法官此刻最清楚的问题。"
        if snapshot.current_stage == TrialStage.EVIDENCE:
            return f"证据攻防正在升温，你要决定先如何回应眼前的证据压力，再推进“{focus_text}”。"
        if snapshot.current_stage == TrialStage.DEBATE:
            return f"辩论已进入高压阶段，你要用最少的话守住“{focus_text}”这条主轴。"
        if snapshot.current_stage == TrialStage.FINAL_STATEMENT:
            return "现在不是扩展新问题的时候，而是把整场庭审压缩成最能留下印象的结论。"
        if snapshot.current_stage == TrialStage.MEDIATION_OR_JUDGMENT:
            if run.state.settlement_tendency >= 55:
                return "法官已经在试探收束方式，你需要判断此刻是否值得进入调解博弈。"
            return "案件已接近结果出口，你需要决定是守住裁判主张，还是为收束留出空间。"
        return f"本轮模拟已完成，接下来请围绕“{focus_text}”整理复盘并准备下一步：{action}。"

    def _build_action_cards(self, snapshot: SimulationSnapshot) -> list[SimulationActionCard]:
        cards: list[SimulationActionCard] = []
        for index, action in enumerate(snapshot.available_actions):
            intent, risk_tip = self._describe_action_card(snapshot.current_stage, action, index)
            cards.append(
                SimulationActionCard(
                    action=action,
                    intent=intent,
                    risk_tip=risk_tip,
                    emphasis="critical" if index == 0 and snapshot.current_stage in {TrialStage.EVIDENCE, TrialStage.DEBATE} else "steady",
                )
            )
        return cards

    def _describe_action_card(
        self,
        current_stage: TrialStage,
        action: str,
        index: int,
    ) -> tuple[str, str]:
        common_pairs = {
            "请求法庭先确认争议焦点与举证期限": ("先把审理顺序、证明对象和举证窗口框住。", "如果程序抓手不够清楚，法官会要求你先回到实体陈述。"),
            "先由我方概括诉请与裁判请求": ("先让法庭知道我方到底要求什么以及结果要落到哪里。", "若事实铺垫太薄，对方会反指你先下结论。"),
            "逐项确认对方明确否认哪些事实": ("把对方不能回避的事实先钉住，后面质证才有抓手。", "追问得不够准时，容易在程序环节耗掉时间。"),
            "先说明本案核心法律关系与认定标准": ("先把法庭拉到正确的法律评价框架里。", "如果标准讲得太虚，后面事实承接会显得发空。"),
            "按时间线陈述关键事实与经过": ("让法官先建立完整时间线，再进入争点。", "时间线过长会让对方借细节打断主线。"),
            "围绕核心争点直接提出证明命题": ("一开始就把法庭目光拉到最关键的问题上。", "如果底层事实交代不足，会显得跳结论。"),
            "抓住答辩中的自认与前后矛盾": ("提前锁定对方说漏或说不圆的地方。", "暴露得太早会给对方修补空间。"),
            "要求其明确否认哪些具体事实": ("把笼统否认拆成可处理的具体争议。", "如果你逼得不够准，法官不一定会继续追问。"),
            "推动法庭把争点压缩到一项核心问题": ("把后续举证和辩论都压到最关键的一点上。", "压得过窄时，补位论点也会被一起挤掉。"),
            "保留第二争点，防止对方转移责任": ("不让案件被偷换成单线争议，给后面责任分配留支点。", "争点保留太多会显得不够收束。"),
            "先上基础事实证据，再用补强材料闭合证明链": ("先把事实、关系和时间线搭牢，再完成闭环。", "节奏更稳，但对法官的即时冲击力偏弱。"),
            "先打决定性证据，直接建立法官心证": ("先用最重的一锤改写法官注意力。", "其他支撑跟不上时，会被反打成只重一点。"),
            "针对真实性、合法性、关联性分别提出异议": ("先拆三性，迫使对方说明证据为何能被采信。", "异议理由不够具体时会被视为拖延。"),
            "承认材料形式存在，但限缩其证明对象": ("不与明显存在的材料硬碰，而是压窄它能证明什么。", "限缩边界说松后，对方会把局部材料膨胀成整体证明。"),
            "申请给予质证准备时间并补充反证": ("先争取缓冲，再准备针对性反证和说明。", "补充理由太虚时，法官可能只给极短时间甚至驳回。"),
            "请求围绕核心证明对象重新聚焦质证": ("把法庭重新拉回最该证明的事实上。", "如果主线没搭稳，只回焦点会显得心虚。"),
            "顺势补齐我方最薄弱的证明环节": ("利用程序停顿先堵住证据链缺口。", "补强方向抓错时，反而会暴露真正短板。"),
            "按法律构成要件逐项对应事实与证据": ("让法官看到每一项要件都有证据落点。", "体系完整，但在高压阶段不如单点猛攻有穿透力。"),
            "围绕最能改写结果的一项争点集中猛攻": ("把全部论证都汇到最关键的一点上。", "若法官同时关心配套问题，追问会来得更凶。"),
            "逐点拆解其抗辩前提和证据来源": ("不跟着对方结论跑，先拆它赖以成立的前提。", "若我方底层事实仍有漏洞，只拆逻辑未必足够。"),
            "承认边缘事实，守住核心法律评价": ("把不影响结果的小口子让出去，集中保护决定性判断。", "边缘事实判断失误时，会被包装成整体退让。"),
            "把关键举证责任重新压回对方": ("提醒法官谁主张例外事实，谁就该承担更重的说明义务。", "责任分配本身不清时，会显得像在回避回答。"),
            "直接回答法官最关心的证明断点": ("把最危险的问题正面接住，争取可信度。", "细节准备不足时会当庭暴露新矛盾。"),
            "先界定问题范围，再给出限缩回答": ("先把问题压缩到可控范围，再稳住风险。", "界定过窄时，法官会直接感到你在回避。"),
            "用一句结论加三句理由完成收束": ("把整场庭审压成法官最容易记住的结论格式。", "结论过硬时，会压缩后续调解空间。"),
            "保留调解窗口，但不松核心请求": ("给法官留出收束空间，但底线和主张仍明确。", "信号放得含糊时，对方会不断试探底线。"),
            "试探对方底线，争取可接受收束": ("先摸清对方和法官愿意接受的落点。", "如果对方并无和解诚意，我方会显得先松动。"),
            "明确请求依法判决，不再实质让步": ("把案件重新推回裁判逻辑，不让结果靠试探漂移。", "若整体优势没坐稳，可能错失更平稳的落点。"),
        }
        if action in common_pairs:
            return common_pairs[action]

        stage_defaults = {
            TrialStage.PREPARE: ("优先稳住开局表达。", "如果表达结构不清，后续节奏会更被动。"),
            TrialStage.INVESTIGATION: ("围绕事实和争点推进这一轮调查。", "如果问题铺得太散，法官不容易抓住主线。"),
            TrialStage.EVIDENCE: ("围绕当前证据压力作出第一反应。", "应对过急或过缓都可能被对方利用。"),
            TrialStage.DEBATE: ("用这一动作继续争夺法官心证。", "如果论证不够收束，反而会削弱重点。"),
            TrialStage.FINAL_STATEMENT: ("把最后陈述继续压缩和收束。", "此时再开新话题会稀释重点。"),
            TrialStage.MEDIATION_OR_JUDGMENT: ("围绕最终收束方式做选择。", "选择方向失误会影响最终落点。"),
            TrialStage.REPORT_READY: ("把当前结果整理成可执行的下一步。", "如果只停留在概括层，复盘价值会偏弱。"),
        }
        intent, risk_tip = stage_defaults[current_stage]
        if index == 0:
            return intent, risk_tip
        return f"继续推进：{action}。", risk_tip

    def _infer_next_stage_hint(self, current_stage: TrialStage) -> str:
        try:
            current_index = _STAGE_SEQUENCE.index(current_stage)
        except ValueError:
            return current_stage.value
        if current_index == len(_STAGE_SEQUENCE) - 1:
            return current_stage.value
        return _STAGE_SEQUENCE[current_index + 1].value

    def _build_report_overview(
        self,
        *,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
        estimated_win_rate: int,
        historical_dialogs: str,
    ) -> str:
        focus = _clean_list(case_profile.focus_issues)
        focus_text = focus[0] if focus else snapshot.branch_focus
        history_line_count = len([line for line in historical_dialogs.splitlines() if line.strip()])
        return (
            f"本轮《{case_profile.title}》的庭审推演已完成收束。"
            f" 主轴持续围绕“{focus_text}”展开，当前后端估算胜诉率约为 {estimated_win_rate}%。"
            f" 本次复盘共纳入 {history_line_count} 条轮次记录，可直接用于回看关键分叉、证据风险与下一步补强方向。"
        )

    def _build_confidence(self, current_stage: TrialStage, turn_index: int) -> float:
        baseline = _STAGE_CONFIDENCE[current_stage]
        return min(0.95, round(baseline + min(0.08, max(0, turn_index - 1) * 0.02), 2))

    def _stage_score(self, current_stage: TrialStage) -> int:
        scores = {
            TrialStage.PREPARE: -4,
            TrialStage.INVESTIGATION: -1,
            TrialStage.EVIDENCE: 3,
            TrialStage.DEBATE: 6,
            TrialStage.FINAL_STATEMENT: 8,
            TrialStage.MEDIATION_OR_JUDGMENT: 10,
            TrialStage.REPORT_READY: 12,
        }
        return scores[current_stage]

    def _merge_dict(
        self,
        existing: dict[str, Any],
        generated: dict[str, Any],
        *,
        preserve_existing: bool,
    ) -> dict[str, Any]:
        if not preserve_existing:
            return {**existing, **generated}

        result = dict(existing)
        for key, value in generated.items():
            if key not in result:
                result[key] = value
                continue

            current_value = result[key]
            if isinstance(current_value, dict) and isinstance(value, dict):
                result[key] = self._merge_dict(
                    current_value,
                    value,
                    preserve_existing=True,
                )
            elif not _has_value(current_value):
                result[key] = value
        return result

    def _merge_list(
        self,
        existing: list[str],
        generated: list[str],
        *,
        preserve_existing: bool,
    ) -> list[str]:
        if preserve_existing and existing:
            return list(existing)
        return list(generated)

    def _merge_scalar(
        self,
        existing: str,
        generated: str,
        *,
        preserve_existing: bool,
    ) -> str:
        if preserve_existing and _has_value(existing):
            return existing
        return generated

    def _merge_action_cards(
        self,
        existing: list[SimulationActionCard],
        generated: list[SimulationActionCard],
        *,
        preserve_existing: bool,
    ) -> list[SimulationActionCard]:
        if preserve_existing and existing:
            return list(existing)
        return list(generated)

    def _pick_first_text(self, payload: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _get_latest_user_input(
        self,
        snapshot: SimulationSnapshot,
    ) -> SimulationUserInputEntry | None:
        if not snapshot.user_input_entries:
            return None
        return sorted(
            snapshot.user_input_entries,
            key=lambda entry: (entry.turn_index, entry.created_at, entry.entry_id),
        )[-1]

    def _build_user_input_hidden_state(
        self,
        snapshot: SimulationSnapshot,
    ) -> dict[str, str]:
        latest_user_input = self._get_latest_user_input(snapshot)
        if latest_user_input is None:
            return {}
        return {
            "user_input_depth": f"已写入 {len(snapshot.user_input_entries)} 条",
            "latest_user_input": f"最新输入｜{latest_user_input.label}：{latest_user_input.content}",
        }

    def _user_input_win_rate_bonus(
        self,
        latest_user_input: SimulationUserInputEntry | None,
    ) -> int:
        if latest_user_input is None:
            return 0
        if latest_user_input.input_type.value == "evidence":
            return 4
        if latest_user_input.input_type.value in {"argument", "cross_exam", "closing_statement"}:
            return 3
        return 2


def _clean_list(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item and item.strip()]


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in _clean_list(items):
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    merged = list(existing)
    for item in additions:
        if item not in merged:
            merged.append(item)
    return merged


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True
