from __future__ import annotations

import os
from pathlib import Path

from ..database import get_static_cg_library_dir
from ..schemas.case import CaseProfile
from ..schemas.turn import SimulationCgScene, SimulationSnapshot


_DEFAULT_LIBRARY_DIR = get_static_cg_library_dir() / "cartoon-court"
_DEFAULT_MODE = "static"

_STAGE_IMAGE_MAP = {
    "prepare": "stage_prepare.png",
    "investigation": "stage_investigation.png",
    "evidence": "stage_evidence.png",
    "debate": "stage_debate.png",
    "final_statement": "stage_final_statement.png",
    "mediation_or_judgment": "stage_mediation_or_judgment.png",
    "report_ready": "stage_report_ready.png",
}


class StaticCgLibrary:
    def __init__(self, *, library_dir: Path = _DEFAULT_LIBRARY_DIR, mode: str = _DEFAULT_MODE) -> None:
        self.library_dir = library_dir
        self.mode = (mode or _DEFAULT_MODE).strip().lower()

    @classmethod
    def from_env(cls) -> "StaticCgLibrary":
        configured_dir = os.getenv("PENGUIN_CG_LIBRARY_DIR", "").strip()
        configured_mode = os.getenv("PENGUIN_CG_MODE", _DEFAULT_MODE)
        library_dir = Path(configured_dir) if configured_dir else _DEFAULT_LIBRARY_DIR
        return cls(library_dir=library_dir, mode=configured_mode)

    def is_enabled(self) -> bool:
        return self.mode in {"static", "hybrid"} and self.library_dir.exists()

    def apply_to_snapshot(
        self,
        *,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
    ) -> SimulationSnapshot:
        if not self.is_enabled():
            return snapshot

        filename = _STAGE_IMAGE_MAP.get(snapshot.current_stage.value)
        if not filename:
            return snapshot

        image_path = self.library_dir / filename
        if not image_path.exists():
            return snapshot

        cg_scene = (snapshot.cg_scene or SimulationCgScene()).model_copy(
            update={
                "image_url": f"/generated-cg-library/cartoon-court/{filename}",
                "image_prompt": None,
                "image_model": "static_cartoon_library",
                "title": (snapshot.cg_scene.title if snapshot.cg_scene else "") or snapshot.scene_title,
                "caption": (snapshot.cg_scene.caption if snapshot.cg_scene else "") or snapshot.cg_caption,
            }
        )

        return snapshot.model_copy(
            update={
                "cg_scene": cg_scene,
            }
        )
