#!/usr/bin/env bash
# 容器启动入口：先做安全的 schema 同步，再起 uvicorn。
# 注意：不要调用 init_database.py（它会 drop_all）。
set -euo pipefail

echo "[entrypoint] running auto_migrate..."
# PG 容器健康检查偶尔会在 bifurcation_db 完全初始化前就 ready，
# 重试 5 次让 schema 创建更稳。
for attempt in 1 2 3 4 5; do
    if python -m scripts.auto_migrate; then
        echo "[entrypoint] auto_migrate succeeded (attempt $attempt)"
        break
    fi
    if [ "$attempt" = "5" ]; then
        echo "[entrypoint] auto_migrate failed after 5 attempts, exiting"
        exit 1
    fi
    echo "[entrypoint] auto_migrate failed (attempt $attempt), retrying in 3s..."
    sleep 3
done

echo "[entrypoint] starting uvicorn..."
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "${BACKEND_PORT:-8057}" \
    --workers "${UVICORN_WORKERS:-2}"
