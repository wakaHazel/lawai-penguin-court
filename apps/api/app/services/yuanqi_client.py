from __future__ import annotations

import json
import os
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..schemas.yuanqi import YuanqiChatCompletionRequest, YuanqiChatCompletionResponse

_DEFAULT_ENDPOINT = "https://yuanqi.tencent.com/openapi/v1/agent/chat/completions"


class YuanqiClientError(RuntimeError):
    pass


class YuanqiClient:
    def __init__(
        self,
        *,
        api_key: str | None,
        assistant_id: str | None,
        endpoint: str = _DEFAULT_ENDPOINT,
        timeout_seconds: int = 25,
        transport: Callable[[str, bytes, dict[str, str], int], dict[str, Any]] | None = None,
    ) -> None:
        self.api_key = api_key or ""
        self.assistant_id = assistant_id or ""
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._transport = transport or _default_transport

    @classmethod
    def from_env(cls) -> "YuanqiClient":
        return cls(
            api_key=os.getenv("YUANQI_APP_KEY") or os.getenv("YUANQI_API_KEY"),
            assistant_id=os.getenv("YUANQI_APP_ID") or os.getenv("YUANQI_ASSISTANT_ID"),
            endpoint=os.getenv("YUANQI_API_URL", _DEFAULT_ENDPOINT),
            timeout_seconds=int(os.getenv("YUANQI_TIMEOUT_SECONDS", "25")),
        )

    def is_enabled(self) -> bool:
        return bool(self.api_key and self.assistant_id)

    def create_turn_completion(
        self,
        request_payload: YuanqiChatCompletionRequest,
    ) -> YuanqiChatCompletionResponse:
        if not self.is_enabled():
            raise YuanqiClientError("yuanqi_not_configured")

        payload = json.dumps(
            request_payload.model_dump(mode="json"),
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Source": "openapi",
        }

        try:
            raw_response = self._transport(
                self.endpoint,
                payload,
                headers,
                self.timeout_seconds,
            )
        except (HTTPError, URLError, TimeoutError) as exc:
            raise YuanqiClientError("yuanqi_request_failed") from exc

        return YuanqiChatCompletionResponse.model_validate(raw_response)


def _default_transport(
    endpoint: str,
    payload: bytes,
    headers: dict[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    request = Request(
        endpoint,
        data=payload,
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))
