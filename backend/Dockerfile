FROM python:3.13-slim

# curl 用于 HEALTHCHECK；libpq5 是 asyncpg 等 PG 驱动的运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 非 root 用户
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# 先装依赖（利用 Docker 层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ app/
COPY scripts/ scripts/
COPY alembic/ alembic/
COPY alembic.ini main.py entrypoint.sh ./

# 确保 entrypoint 可执行（COPY 不一定保留执行位）
# static/uploads 通过 volume 挂载，这里只建骨架
RUN chmod +x /app/entrypoint.sh \
    && mkdir -p static/uploads \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8057

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -sf http://127.0.0.1:8057/health || exit 1

CMD ["/app/entrypoint.sh"]
