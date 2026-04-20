FROM node:20-bookworm-slim AS web-build

WORKDIR /build/apps/web

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY apps/web/ ./
RUN npm run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PENGUIN_RUNTIME_DATA_DIR=/app/runtime-data \
    PENGUIN_STATIC_ASSETS_DIR=/app/data

WORKDIR /app/apps/api

COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app
COPY --from=web-build /build/apps/web/dist /app/apps/web/dist

RUN mkdir -p /app/runtime-data /app/data/cg-library /app/data/generated-cg

EXPOSE 8000

CMD ["/bin/sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
