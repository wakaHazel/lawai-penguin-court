from __future__ import annotations

from ..repositories.trial_run_repository import list_simulation_turns_for_run


class YuanqiContextStore:
    """Builds cross-turn textual context for W00 and downstream hint payloads."""

    def build_historical_dialogs(self, simulation_id: str) -> str:
        turns = list_simulation_turns_for_run(simulation_id)
        if not turns:
            return ""

        lines: list[str] = []
        seen_entry_ids: set[str] = set()

        for turn in turns:
            lines.append(f"[turn {turn.turn_index} | {turn.current_stage.value}] {turn.scene_title}")
            sorted_entries = sorted(
                turn.user_input_entries,
                key=lambda entry: (entry.turn_index, entry.created_at, entry.entry_id),
            )
            for entry in sorted_entries:
                if entry.entry_id in seen_entry_ids:
                    continue
                seen_entry_ids.add(entry.entry_id)
                lines.append(f"[用户{entry.label}] {entry.content}")

        return "\n".join(lines)

    def build_simulation_timeline(self, simulation_id: str) -> str:
        return self.build_historical_dialogs(simulation_id)
