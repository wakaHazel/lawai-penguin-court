from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_DEFAULT_BASE_URL = "https://openapi.delilegal.com"
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_WORKFLOW_EXPORT_ROOT_ENV = "DELILEGAL_WORKFLOW_EXPORT_ROOT"


class DeliClientError(RuntimeError):
    pass


class DeliClient:
    def __init__(
        self,
        *,
        app_id: str | None,
        secret: str | None,
        base_url: str = _DEFAULT_BASE_URL,
        timeout_seconds: int = 20,
        transport: Callable[[Request, int], dict[str, Any]] | None = None,
    ) -> None:
        self.app_id = (app_id or "").strip()
        self.secret = (secret or "").strip()
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._transport = transport or _default_transport

    @classmethod
    def from_env(cls) -> "DeliClient":
        app_id = os.getenv("DELILEGAL_APP_ID")
        secret = os.getenv("DELILEGAL_SECRET")
        if not app_id or not secret:
            discovered_app_id, discovered_secret = _discover_deli_credentials()
            app_id = app_id or discovered_app_id
            secret = secret or discovered_secret

        return cls(
            app_id=app_id,
            secret=secret,
            base_url=os.getenv("DELILEGAL_BASE_URL", _DEFAULT_BASE_URL),
            timeout_seconds=int(os.getenv("DELILEGAL_TIMEOUT_SECONDS", "20")),
        )

    def is_enabled(self) -> bool:
        return bool(self.app_id and self.secret)

    def query_laws(self, keyword: str, *, page_size: int = 3) -> list[dict[str, Any]]:
        payload = {
            "pageNo": 1,
            "pageSize": page_size,
            "sortField": "correlation",
            "sortOrder": "desc",
            "condition": {
                "keywords": [keyword],
                "fieldName": "semantic",
            },
        }
        response = self._request(
            method="POST",
            path="/api/qa/v3/search/queryListLaw",
            payload=payload,
        )
        return self._extract_result_items(response)

    def query_cases(self, keyword: str, *, page_size: int = 3) -> list[dict[str, Any]]:
        payload = {
            "pageNo": 1,
            "pageSize": page_size,
            "sortField": "correlation",
            "sortOrder": "desc",
            "condition": {"keywordArr": [keyword]},
        }
        response = self._request(
            method="POST",
            path="/api/qa/v3/search/queryListCase",
            payload=payload,
        )
        return self._extract_result_items(response)

    def get_law_info(self, law_id: str) -> dict[str, Any]:
        response = self._request(
            method="GET",
            path="/api/qa/v3/search/lawInfo",
            query={"lawId": law_id, "merge": "true"},
        )
        if isinstance(response, dict):
            data = response.get("data")
            if isinstance(data, dict):
                return data
        return response if isinstance(response, dict) else {}

    def _request(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if not self.is_enabled():
            raise DeliClientError("deli_not_configured")

        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"

        body: bytes | None = None
        headers = {
            "appid": self.app_id,
            "secret": self.secret,
            "Content-Type": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        request = Request(
            url,
            data=body,
            headers=headers,
            method=method,
        )

        try:
            return self._transport(request, self.timeout_seconds)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise DeliClientError("deli_request_failed") from exc

    def _extract_result_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        found = _find_first_list(payload)
        return [item for item in found if isinstance(item, dict)]


def _default_transport(request: Request, timeout_seconds: int) -> dict[str, Any]:
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _find_first_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return []

    for key in ("records", "rows", "list", "items", "result", "data"):
        child = value.get(key)
        found = _find_first_list(child)
        if found:
            return found

    for child in value.values():
        found = _find_first_list(child)
        if found:
            return found

    return []


@lru_cache(maxsize=1)
def _discover_deli_credentials() -> tuple[str | None, str | None]:
    for root in _candidate_workflow_roots():
        if not root.exists():
            continue

        workflow_paths = sorted(
            root.rglob("*workflow.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for workflow_path in workflow_paths:
            credentials = _extract_credentials_from_workflow_export(workflow_path)
            if credentials is not None:
                return credentials
    return None, None


def _candidate_workflow_roots() -> list[Path]:
    configured_root = (os.getenv(_WORKFLOW_EXPORT_ROOT_ENV) or "").strip()
    roots: list[Path] = []
    if configured_root:
        roots.append(Path(configured_root))
    roots.append(_PROJECT_ROOT / "tmp")
    return roots


def _extract_credentials_from_workflow_export(
    workflow_path: Path,
) -> tuple[str, str] | None:
    try:
        payload = json.loads(workflow_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    return _find_deli_credentials(payload)


def _find_deli_credentials(value: Any) -> tuple[str, str] | None:
    if isinstance(value, dict):
        api_config = value.get("API")
        header_config = value.get("Header")
        if isinstance(api_config, dict) and isinstance(header_config, list):
            api_url = str(api_config.get("URL") or "").strip()
            if _is_deli_search_api(api_url):
                app_id = _extract_header_value(header_config, "appid")
                secret = _extract_header_value(header_config, "secret")
                if app_id and secret:
                    return app_id, secret

        for child in value.values():
            credentials = _find_deli_credentials(child)
            if credentials is not None:
                return credentials
        return None

    if isinstance(value, list):
        for item in value:
            credentials = _find_deli_credentials(item)
            if credentials is not None:
                return credentials

    return None


def _is_deli_search_api(api_url: str) -> bool:
    return api_url.startswith(_DEFAULT_BASE_URL) and (
        "queryListLaw" in api_url or "queryListCase" in api_url
    )


def _extract_header_value(headers: list[Any], param_name: str) -> str | None:
    for item in headers:
        if not isinstance(item, dict):
            continue
        if str(item.get("ParamName") or "").strip().lower() != param_name.lower():
            continue
        input_payload = item.get("Input")
        if not isinstance(input_payload, dict):
            continue
        user_input = input_payload.get("UserInputValue")
        if not isinstance(user_input, dict):
            continue
        values = user_input.get("Values")
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None
