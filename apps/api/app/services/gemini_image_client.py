from __future__ import annotations

import base64
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from openai import OpenAI

from ..schemas.case import CaseProfile
from ..schemas.turn import SimulationCgScene, SimulationSnapshot

_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_DEFAULT_MODEL = "gemini-2.5-flash-image-preview"
_DEFAULT_TIMEOUT_SECONDS = 45
_DEFAULT_IMAGE_SIZE = "1536x1024"
_V3CM_DEFAULT_MODEL = "gemini-3-pro-image-preview-2k"
_V3CM_DEFAULT_IMAGE_SIZE = "2752x1536"


class GeminiImageClientError(RuntimeError):
    pass


class GeminiImageClient:
    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str = _DEFAULT_BASE_URL,
        model: str = _DEFAULT_MODEL,
        timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
        api_style: str = "auto",
        image_size: str = _DEFAULT_IMAGE_SIZE,
        output_dir: Path | None = None,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.base_url = base_url.rstrip("/")
        self.model = model.strip() or _DEFAULT_MODEL
        self.timeout_seconds = timeout_seconds
        self.api_style = (api_style or "auto").strip().lower()
        self.image_size = image_size.strip() or _DEFAULT_IMAGE_SIZE
        self.output_dir = output_dir or Path(__file__).resolve().parents[4] / "data" / "generated-cg"

    @classmethod
    def from_env(cls) -> "GeminiImageClient":
        base_url = (
            os.getenv("GEMINI_BASE_URL")
            or os.getenv("V3CM_BASE_URL")
            or _DEFAULT_BASE_URL
        )
        hostname = (urlparse(base_url).hostname or "").lower()
        is_vapi_provider = hostname in {"api.v3.cm", "api.gpt.ge"}
        model = os.getenv("GEMINI_IMAGE_MODEL")
        image_size = os.getenv("GEMINI_IMAGE_SIZE")
        api_style = os.getenv("GEMINI_API_STYLE")

        return cls(
            api_key=(
                os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
                or os.getenv("V3CM_API_KEY")
            ),
            base_url=base_url,
            model=model or (_V3CM_DEFAULT_MODEL if is_vapi_provider else _DEFAULT_MODEL),
            timeout_seconds=int(os.getenv("GEMINI_TIMEOUT_SECONDS", str(_DEFAULT_TIMEOUT_SECONDS))),
            api_style=api_style or ("openai_compatible" if is_vapi_provider else "auto"),
            image_size=image_size or (_V3CM_DEFAULT_IMAGE_SIZE if is_vapi_provider else _DEFAULT_IMAGE_SIZE),
        )

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def render_snapshot(
        self,
        *,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
    ) -> SimulationSnapshot:
        if not self.is_enabled():
            raise GeminiImageClientError("gemini_not_configured")

        prompt = self._build_prompt(case_profile=case_profile, snapshot=snapshot)
        image_bytes, mime_type = self._generate_image(prompt)
        image_url = self._persist_image(
            case_id=snapshot.case_id,
            simulation_id=snapshot.simulation_id,
            turn_index=snapshot.turn_index,
            image_bytes=image_bytes,
            mime_type=mime_type,
        )

        cg_scene = (snapshot.cg_scene or SimulationCgScene()).model_copy(
            update={
                "image_url": image_url,
                "image_prompt": prompt,
                "image_model": self.model,
            }
        )
        return snapshot.model_copy(update={"cg_scene": cg_scene})

    def _build_prompt(
        self,
        *,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
    ) -> str:
        cg_scene = snapshot.cg_scene or SimulationCgScene()
        focus_issues = "、".join(case_profile.focus_issues[:2]) or snapshot.branch_focus or "案件核心争点"
        claims = "、".join(case_profile.claims[:2]) or "当前诉请"
        scene_text = (snapshot.scene_text or "").strip()
        opponent_name = (
            case_profile.opponent_profile.display_name
            if case_profile.opponent_profile is not None
            else "对方当事人"
        )
        return (
            "请生成一张高质量中文法律题材叙事插画，用于“企鹅法庭”沉浸式庭审模拟系统。\n"
            "风格要求：CG 插画、电影感、叙事性强、光影克制、细节精致、写实与拟人结合、无 UI、无分镜框、无水印、无文字。\n"
            "人物设定：拟人化企鹅法官、企鹅当事人、企鹅代理人，服装与法庭角色对应，整体庄重但有轻微文游戏剧张力。\n"
            "场景要求：中华人民共和国民事法庭语境，法槌、审判席、证据材料、法庭灯光与空间层次明确。\n"
            f"案件标题：{case_profile.title}\n"
            f"案件类型：{case_profile.case_type.value}\n"
            f"当前阶段：{snapshot.current_stage.value}\n"
            f"当前场景标题：{snapshot.scene_title}\n"
            f"分镜标题：{cg_scene.title or snapshot.scene_title}\n"
            f"分镜说明：{cg_scene.caption or snapshot.cg_caption or snapshot.scene_text}\n"
            f"发言角色：{snapshot.speaker_role.value}\n"
            f"镜头类型：{cg_scene.shot_type or 'medium'}\n"
            f"情绪：{cg_scene.speaker_emotion or 'steady'}\n"
            f"背景标识：{cg_scene.background_id or 'courtroom_entry'}\n"
            f"强调对象：{cg_scene.emphasis_target or 'bench'}\n"
            f"争议焦点：{focus_issues}\n"
            f"当前诉请：{claims}\n"
            f"对方角色：{opponent_name}\n"
            f"案件摘要：{case_profile.summary}\n"
            f"庭上叙事：{scene_text[:900]}\n"
            "必须体现：当前这一回合正在发生的法庭推进感、对方席位的反应、法官关注点集中、镜头聚焦于当前争点。\n"
            "构图要求：单张横版场景图，适合网页首屏展示，主体清晰，前中后景层次明显。"
        )

    def _generate_image(self, prompt: str) -> tuple[bytes, str]:
        if self._use_openai_compatible_api():
            return self._generate_image_openai_compatible(prompt)
        return self._generate_image_google_native(prompt)

    def _generate_image_google_native(self, prompt: str) -> tuple[bytes, str]:
        endpoint = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = json.dumps(
            {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"],
                },
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise GeminiImageClientError("gemini_request_failed") from exc

        candidates = raw.get("candidates") or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            for part in content.get("parts") or []:
                inline = part.get("inlineData") or part.get("inline_data")
                if not isinstance(inline, dict):
                    continue
                data = inline.get("data")
                mime_type = str(inline.get("mimeType") or inline.get("mime_type") or "image/png")
                if not data:
                    continue
                try:
                    return base64.b64decode(data), mime_type
                except ValueError as exc:
                    raise GeminiImageClientError("gemini_invalid_image_data") from exc

        raise GeminiImageClientError("gemini_image_missing")

    def _generate_image_openai_compatible(self, prompt: str) -> tuple[bytes, str]:
        model = self._resolve_openai_compatible_model()
        size = self._resolve_openai_sdk_size()
        base_url = self._resolve_openai_sdk_base_url()
        client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
            timeout=self.timeout_seconds,
        )

        try:
            response = client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size=size,
                response_format="b64_json",
            )
        except Exception as exc:
            raise GeminiImageClientError("gemini_request_failed") from exc

        data_items = getattr(response, "data", None) or []
        for item in data_items:
            b64_json = getattr(item, "b64_json", None)
            if isinstance(b64_json, str) and b64_json.strip():
                try:
                    return base64.b64decode(b64_json), "image/png"
                except ValueError as exc:
                    raise GeminiImageClientError("gemini_invalid_image_data") from exc
            image_url = getattr(item, "url", None)
            if isinstance(image_url, str) and image_url.strip():
                return self._download_image_from_url(image_url.strip())

        raise GeminiImageClientError("gemini_image_missing")

    def _download_image_from_url(self, image_url: str) -> tuple[bytes, str]:
        request = Request(image_url, method="GET")
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                mime_type = str(response.headers.get_content_type() or "image/png")
                return response.read(), mime_type
        except (HTTPError, URLError, TimeoutError) as exc:
            raise GeminiImageClientError("gemini_image_download_failed") from exc

    def _use_openai_compatible_api(self) -> bool:
        if self.api_style == "openai_compatible":
            return True
        if self.api_style == "google_native":
            return False
        normalized = self.base_url.lower()
        return "generativelanguage.googleapis.com" not in normalized

    def _resolve_openai_sdk_base_url(self) -> str:
        parsed = urlparse(self.base_url)
        base_path = parsed.path.rstrip("/")
        if base_path.endswith("/v1"):
            return self.base_url
        return f"{self.base_url}/v1"

    def _resolve_openai_compatible_model(self) -> str:
        if not self._is_vapi_provider():
            return self.model

        aliases = {
            "gemini-2.5-flash-image-preview": "nano-banana",
            "gemini-2.5-flash-image": "nano-banana",
            "gemini-3-pro-image-preview": "nano-banana-pro",
        }
        return aliases.get(self.model, self.model)

    def _resolve_openai_compatible_size(self) -> str:
        if not self._is_vapi_provider():
            return self.image_size

        parsed = self._parse_size_pair(self.image_size)
        if parsed is None:
            return self.image_size
        width, height = parsed
        divisor = math.gcd(width, height)
        return f"{width // divisor}:{height // divisor}"

    def _resolve_openai_sdk_size(self) -> str:
        if self._is_vapi_provider():
            return self.image_size
        return self._resolve_openai_compatible_size()

    def _parse_size_pair(self, value: str) -> tuple[int, int] | None:
        text = value.strip().lower()
        if "x" not in text:
            return None
        left, right = text.split("x", 1)
        if not left.isdigit() or not right.isdigit():
            return None
        width = int(left)
        height = int(right)
        if width <= 0 or height <= 0:
            return None
        return width, height

    def _is_vapi_provider(self) -> bool:
        hostname = (urlparse(self.base_url).hostname or "").lower()
        return hostname in {"api.v3.cm", "api.gpt.ge"}

    def _persist_image(
        self,
        *,
        case_id: str,
        simulation_id: str,
        turn_index: int,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        ext = ".png"
        if "jpeg" in mime_type or "jpg" in mime_type:
            ext = ".jpg"
        digest = hashlib.sha1(image_bytes).hexdigest()[:12]
        case_dir = self.output_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{simulation_id}_turn_{turn_index:02d}_{digest}{ext}"
        file_path = case_dir / filename
        file_path.write_bytes(image_bytes)
        return f"/generated-cg/{case_id}/{filename}"
