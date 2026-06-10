#!/usr/bin/env bash
# Bifurcation Docker 部署脚本
# 用法：bash deploy/deploy.sh
#
# CI 已完成：Docker 镜像构建推送到 GHCR，前端 dist/ 已 rsync 到位。
# 本脚本负责：备份数据库 → 拉取新镜像 → 重启容器 → 健康检查。

set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT_ROOT="$(pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
HEALTH_URL="http://127.0.0.1:8057/health"
HEALTH_TIMEOUT=10
# 20×3s=60s 窗口：给冷启动期（auto_migrate + uvicorn 启动）留余地
HEALTH_RETRIES=20

# ── 工具函数 ──

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
fail() { echo "[$(date '+%H:%M:%S')] FATAL: $*" >&2; exit 1; }

# 真回滚：用部署前抓住的旧镜像 ID 拉起上一版本，再做一次健康检查。
# PREV_IMAGE_ID 在拉新镜像前由主流程捕获（见下方 [2/4] 之前）。
rollback() {
    if [ -z "${PREV_IMAGE_ID:-}" ]; then
        fail "Deploy failed and no previous image to roll back to (first deploy?). Check: docker compose logs backend"
    fi
    log "Rolling back to previous image ${PREV_IMAGE_ID:0:19}..."
    docker tag "$PREV_IMAGE_ID" bifurcation-backend:rollback || \
        fail "Cannot tag previous image ${PREV_IMAGE_ID:0:19} for rollback — may have been GC'd"
    BACKEND_IMAGE=bifurcation-backend:rollback docker compose up -d || \
        fail "Rollback failed to start previous image. Check: docker compose logs backend"
    if health_check; then
        log "Rolled back to previous version successfully (service restored)."
        fail "Deploy failed but previous version restored. Investigate the new image."
    fi
    fail "Deploy failed AND rollback health check failed — service may be down. Check: docker compose logs backend"
}

health_check() {
    log "Running health check ($HEALTH_RETRIES attempts)..."
    for i in $(seq 1 "$HEALTH_RETRIES"); do
        if curl -sf --max-time "$HEALTH_TIMEOUT" "$HEALTH_URL" > /dev/null 2>&1; then
            log "  Health check passed (attempt $i)"
            return 0
        fi
        log "  attempt $i/$HEALTH_RETRIES failed, waiting 3s..."
        sleep 3
    done
    return 1
}

echo "===================================="
echo "  Bifurcation Deploy (Docker)"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "===================================="

# ── 0. 环境校验 ──
log "[0/4] Validating environment..."
[ -f "$PROJECT_ROOT/.env" ] || fail ".env not found (copy from backend/.env.example)"
command -v docker >/dev/null 2>&1    || fail "docker not installed"
docker compose version >/dev/null 2>&1 || fail "docker compose plugin not installed"

# 拒绝默认/危险 SECRET_KEY
if grep -qE '^SECRET_KEY=(change_me|sunyunboniubi|GANGWAY|)$' "$PROJECT_ROOT/.env"; then
    fail "SECRET_KEY 未设置或仍是默认/弱值，请用 python -c 'import secrets; print(secrets.token_hex(64))' 生成新值"
fi

# ── 1. 备份数据库 ──
log "[1/4] Backing up database..."
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

if docker compose ps -q postgres 2>/dev/null | grep -q .; then
    docker compose exec -T postgres pg_dump -U bifurcation bifurcation_db \
        > "$BACKUP_DIR/bifurcation_${TIMESTAMP}.sql" 2>/dev/null \
        && log "  Backed up to backups/bifurcation_${TIMESTAMP}.sql" \
        || log "  Warning: pg_dump failed, continuing without backup"
    # 保留最近 10 个备份
    ls -t "$BACKUP_DIR"/bifurcation_*.sql 2>/dev/null | tail -n +11 | xargs -r rm --
else
    log "  PostgreSQL not running, skipping backup (first deploy?)"
fi

# ── 2. 拉取新镜像 ──
# 只拉 backend：postgres 使用本地已有的镜像，避免 Docker Hub 抽风时卡死整个部署。
# 如需升级 postgres，手动 `docker compose pull postgres && docker compose up -d postgres`。
# 先抓住当前运行容器的镜像 ID：pull 会顶掉 latest tag，但旧镜像 ID 仍在本地，
# 抓住引用即可在失败时回滚（真回滚依赖这一步）。
PREV_IMAGE_ID=$(docker inspect --format='{{.Image}}' bifurcation-backend 2>/dev/null || echo "")
log "[2/4] Pulling latest backend image (prev=${PREV_IMAGE_ID:0:19})..."
docker compose pull backend || rollback

# ── 3. 重启容器 ──
log "[3/4] Starting containers..."
docker compose up -d || rollback

# ── 4. 健康检查 ──
log "[4/4] Waiting for backend to be ready..."
sleep 3
if ! health_check; then
    log "Health check failed after deploy"
    rollback
fi

NEW_IMAGE=$(docker inspect --format='{{.Image}}' bifurcation-backend 2>/dev/null | cut -c8-19)
echo ""
echo "===================================="
echo "  Deploy complete!"
echo "  Image:   ${NEW_IMAGE:-unknown}"
echo "  Logs:    docker compose logs -f backend"
echo "  Backup:  backups/bifurcation_${TIMESTAMP}.sql"
echo "===================================="
