import type { ResponseEnvelope } from "../../types/case";

export class ApiRequestError extends Error {
  status: number;
  errorCode: string | null;

  constructor(message: string, status: number, errorCode: string | null) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

export interface ApiClientConfig {
  baseUrl?: string;
  timeoutMs?: number;
}

function readRuntimeOrigin(): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.location.origin;
}

function isLikelyStandaloneFrontendOrigin(origin: string): boolean {
  if (!origin) {
    return false;
  }

  try {
    const url = new URL(origin);
    return (
      (url.hostname === "127.0.0.1" || url.hostname === "localhost") &&
      ["4173", "4174", "4175", "5173"].includes(url.port)
    );
  } catch {
    return false;
  }
}

function isGitHubPagesOrigin(origin: string): boolean {
  if (!origin) {
    return false;
  }

  try {
    const url = new URL(origin);
    return url.hostname.endsWith(".github.io");
  } catch {
    return false;
  }
}

function resolveDefaultBaseUrl(): string | null {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configuredBaseUrl) {
    return configuredBaseUrl.replace(/\/+$/, "");
  }

  const runtimeOrigin = readRuntimeOrigin();
  if (
    isLikelyStandaloneFrontendOrigin(runtimeOrigin) ||
    isGitHubPagesOrigin(runtimeOrigin)
  ) {
    return null;
  }

  // When frontend and backend are deployed on the same origin, the safest
  // default is using relative API paths instead of requiring extra config.
  return "";
}

const DEFAULT_TIMEOUT_MS = 15000;

export async function requestEnvelope<T>(
  path: string,
  init?: RequestInit,
  config?: ApiClientConfig,
): Promise<ResponseEnvelope<T>> {
  const resolvedBaseUrl =
    config?.baseUrl?.replace(/\/+$/, "") ?? resolveDefaultBaseUrl();
  if (resolvedBaseUrl === null) {
    throw new ApiRequestError(
      "当前未配置后端服务地址，已跳过 API 请求。",
      0,
      "api_unconfigured",
    );
  }
  const controller = new AbortController();
  const timeout = globalThis.setTimeout(
    () => controller.abort(),
    config?.timeoutMs ?? DEFAULT_TIMEOUT_MS,
  );

  try {
    const response = await fetch(`${resolvedBaseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      ...init,
      signal: init?.signal ?? controller.signal,
    });

    const body = await parseEnvelopeBody<T>(response);
    if (!response.ok || !body.success) {
      throw new ApiRequestError(
        body.message || "API request failed.",
        response.status,
        body.error_code,
      );
    }

    return body;
  } catch (error) {
    if (error instanceof ApiRequestError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiRequestError("API request timed out.", 408, "request_timeout");
    }

    throw new ApiRequestError(
      "无法连接后端服务，请确认前端与后端都已启动。",
      0,
      "network_error",
    );
  } finally {
    globalThis.clearTimeout(timeout);
  }
}

async function parseEnvelopeBody<T>(
  response: Response,
): Promise<ResponseEnvelope<T>> {
  const rawText = await response.text();
  if (!rawText.trim()) {
    return {
      success: response.ok,
      message: response.ok ? "ok" : "Empty response body.",
      data: null,
      error_code: response.ok ? null : "empty_response_body",
    };
  }

  try {
    return JSON.parse(rawText) as ResponseEnvelope<T>;
  } catch {
    throw new ApiRequestError(
      "API returned malformed JSON.",
      response.status,
      "invalid_json_response",
    );
  }
}
