# Penguin Court API

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run

Run from `E:\lawai\apps\api`:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API now auto-loads optional env files from:

- `E:\lawai\apps\api\.env`
- `E:\lawai\apps\api\.env.local`
- `E:\lawai\.env`
- `E:\lawai\.env.local`

## Smoke Check

```powershell
curl http://127.0.0.1:8000/health
```

Expected envelope:

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "status": "healthy"
  },
  "error_code": null
}
```

## Local Integration

- Frontend dev server: `E:\lawai\apps\web`
- Frontend command: `npm run dev`
- Vite proxy already forwards `/api` and `/health` to `http://127.0.0.1:8000`

## External AI / Legal APIs

- Yuanqi main agent:
  - `YUANQI_APP_ID` or `YUANQI_ASSISTANT_ID`
  - `YUANQI_APP_KEY` or `YUANQI_API_KEY`
  - live simulation now sends Yuanqi workflow variables through official `custom_variables`
  - default live provider is Yuanqi; optional override:
    - `PENGUIN_LIVE_PROVIDER=yuanqi`
    - `PENGUIN_LIVE_PROVIDER=zhipu`
- Live simulation switch:
  - `PENGUIN_SIMULATION_MODE=local` keeps deterministic local flow
  - `PENGUIN_SIMULATION_MODE=live` enables remote workflow calls
- Zhipu courtroom generation:
  - `ZHIPU_API_KEY`
  - optional: `ZHIPU_BASE_URL` or `ZHIPU_API_URL`
  - optional: `ZHIPU_MODEL` (default: `glm-4.5-air`)
  - optional: `ZHIPU_MAX_TOKENS` (default: `1800`)
  - optional: `ZHIPU_TEMPERATURE` (default: `0.2`)
- Gemini CG image generation:
  - `GEMINI_API_KEY` or `GOOGLE_API_KEY`
  - also supported for the verified relay path: `V3CM_API_KEY`
  - optional: `GEMINI_BASE_URL` (default: `https://generativelanguage.googleapis.com/v1beta`)
  - also supported for the verified relay path: `V3CM_BASE_URL`
  - optional: `GEMINI_IMAGE_MODEL` (default: `gemini-2.5-flash-image-preview`)
  - optional: `GEMINI_TIMEOUT_SECONDS` (default: `45`)
  - optional: `GEMINI_API_STYLE` (`auto` / `google_native` / `openai_compatible`)
  - optional: `GEMINI_IMAGE_SIZE` (default: `1536x1024`)
  - note: for `api.v3.cm`-style V-API gateways, the backend now auto-maps
    to a verified default combination:
    `model=gemini-3-pro-image-preview-2k`
    `size=2752x1536`
    `api_style=openai_compatible`
- Deli legal retrieval:
  - preferred: `DELILEGAL_APP_ID` + `DELILEGAL_SECRET`
  - optional: `DELILEGAL_WORKFLOW_EXPORT_ROOT`

If `DELILEGAL_APP_ID` / `DELILEGAL_SECRET` are not set, the backend now tries to discover them
from exported Yuanqi workflow JSON files under `E:\lawai\tmp` or the custom path specified by
`DELILEGAL_WORKFLOW_EXPORT_ROOT`.

## Persistence

- SQLite database file: `E:\lawai\data\penguin_court.db`
- Generated CG image directory: `E:\lawai\data\generated-cg`
- Current persistence scope:
  - cases
  - simulations
  - replay reports

## Implemented Endpoints

- `GET /health`
- `POST /api/cases`
- `GET /api/cases`
- `GET /api/cases/{case_id}`
- `POST /api/cases/{case_id}/simulate/start`
- `GET /api/cases/{case_id}/simulate/latest`
- `POST /api/cases/{case_id}/simulate/turn`
- `POST /api/cases/{case_id}/opponent-behavior/snapshot`
- `GET /api/cases/{case_id}/opponent-behavior/latest`
- `POST /api/cases/{case_id}/win-rate/analyze`
- `GET /api/cases/{case_id}/win-rate/latest`
- `POST /api/cases/{case_id}/replay-report/generate`
- `GET /api/cases/{case_id}/replay-report/latest`
