from __future__ import annotations

import os

from ..repositories.trial_run_repository import list_simulation_turns_for_run


class YuanqiContextStore:
    """Builds cross-turn textual context for W00 and downstream hint payloads."""

    def build_historical_dialogs(self, simulation_id: str) -> str:
        turns = list_simulation_turns_for_run(simulation_id)
        if not turns:
            return ""

        turn_limit = max(1, int(os.getenv("PENGUIN_YUANQI_HISTORY_TURN_LIMIT", "6")))
        char_limit = max(200, int(os.getenv("PENGUIN_YUANQI_HISTORY_CHAR_LIMIT", "1200")))
        recent_turns = turns[-turn_limit:]
        lines: list[str] = []
        seen_entry_ids: set[str] = set()

        for turn in recent_turns:
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

        if not lines:
            return ""

        compact_lines: list[str] = []
        total_length = 0
        for line in reversed(lines):
            extra = len(line) + (1 if compact_lines else 0)
            if compact_lines and total_length + extra > char_limit:
                break
            compact_lines.append(line)
            total_length += extra

        return "\n".join(reversed(compact_lines))

    def build_simulation_timeline(self, simulation_id: str) -> str:
        return self.build_historical_dialogs(simulation_id)
