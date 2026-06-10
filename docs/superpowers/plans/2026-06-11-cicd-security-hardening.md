# CI/CD 安全加固 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 CI/CD 补上依赖/镜像/密钥安全扫描（只报告不拦截）、pip 缓存、部署并发锁，并把 `deploy.sh` 的假回滚改成真·失败自动回滚。

**Architecture:** 新增独立 `security.yml`（依赖+密钥扫描，含每周定时触发器，避免 schedule 误触发构建/部署）；`ci.yml` 改 3 处（Trivy 镜像扫描、pip 缓存、deploy 并发锁）；`deploy.sh` 重写回滚逻辑（拉新镜像前抓住旧镜像 ID，失败时恢复并二次健康检查）。

**Tech Stack:** GitHub Actions、pip-audit、npm audit、Trivy（aquasecurity/trivy-action）、gitleaks（gitleaks/gitleaks-action）、Docker Compose、Bash。

**关联：** 设计见 `docs/superpowers/specs/2026-06-11-cicd-security-hardening-design.md`。分支：`chore/cicd-security-hardening`（已存在）。

**通用验证命令：**
- workflow YAML 合法性：`python3 -c "import yaml; yaml.safe_load(open('PATH'))" && echo OK`
- shell 语法：`bash -n deploy/deploy.sh && echo OK`

---

### Task 1: 新增 `security.yml` — 依赖 + 密钥扫描

**Files:**
- Create: `.github/workflows/security.yml`

- [ ] **Step 1: 写 workflow 文件**

创建 `.github/workflows/security.yml`，完整内容：

```yaml
name: Security Scan

# 只报告不拦截：所有扫描步骤 continue-on-error，永不挡部署。
# 依赖扫描触发：push/PR + 每周定时（依赖未变期间新披露的 CVE）。
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 3 * * 1'   # 每周一 03:00 UTC

permissions:
  contents: read

jobs:
  dependency-scan:
    name: Dependency Vulnerability Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install pip-audit
        run: pip install pip-audit --quiet

      # 后端：审计 requirements.txt；markdown 结果写进 job summary
      - name: Audit backend dependencies (pip-audit)
        continue-on-error: true
        run: |
          echo "## Backend pip-audit" >> "$GITHUB_STEP_SUMMARY"
          pip-audit --requirement backend/requirements.txt --format markdown >> "$GITHUB_STEP_SUMMARY" || true

      - uses: actions/setup-node@v4
        with:
          node-version: '22'

      # 前端：npm audit（high 及以上）
      - name: Audit frontend dependencies (npm audit)
        continue-on-error: true
        working-directory: frontend
        run: |
          echo "## Frontend npm audit" >> "$GITHUB_STEP_SUMMARY"
          npm audit --audit-level=high >> "$GITHUB_STEP_SUMMARY" 2>&1 || true

  secret-scan:
    name: Secret Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # gitleaks 需要完整历史才能扫提交

      # 只报告：发现密钥不 fail。日后升级为拦截：去掉 continue-on-error。
      - name: Run gitleaks
        continue-on-error: true
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 2: 校验 YAML 合法**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/security.yml'))" && echo OK`
Expected: 输出 `OK`，无异常。

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/security.yml
git commit -m "ci: 新增 security.yml — 依赖(pip-audit/npm audit)+密钥(gitleaks)扫描，只报告不拦截

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: `ci.yml` — backend job 加 Trivy 镜像扫描

**Files:**
- Modify: `.github/workflows/ci.yml`（backend job，`Build and push Docker image` step 之后）

- [ ] **Step 1: 在 build-push step 后插入 Trivy step**

在 `ci.yml` 中 `Build and push Docker image` step（以 `cache-to: type=gha,mode=max` 结尾）之后、`frontend:` job 之前，插入两个 step：

```yaml
      # 镜像 CVE 扫描（只报告）：扫刚推上去的 SHA 镜像基础层漏洞，永不 fail
      - name: Scan image with Trivy
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/${{ env.OWNER_LC }}/bifurcation-backend:${{ github.sha }}
          format: sarif
          output: trivy-results.sarif
          exit-code: '0'        # 只报告，不让 job 失败
          severity: HIGH,CRITICAL

      - name: Upload Trivy results to Security tab
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        continue-on-error: true
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif
```

注意：`OWNER_LC` 由现有 `Lowercase owner name` step 写入 `$GITHUB_ENV`（在 build-push 之前），所以此处 `${{ env.OWNER_LC }}` 可用。

- [ ] **Step 2: backend job 加 security-events 写权限（SARIF 上传需要）**

把 backend job 顶部的 `permissions:` 块从：

```yaml
    permissions:
      contents: read
      packages: write
```

改为：

```yaml
    permissions:
      contents: read
      packages: write
      security-events: write   # Trivy SARIF 上传到 Security 页需要
```

- [ ] **Step 3: 校验 YAML 合法**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo OK`
Expected: 输出 `OK`。

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: backend job 加 Trivy 镜像扫描(只报告) + SARIF 上传 Security 页

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: `ci.yml` — backend job 加 pip 缓存

**Files:**
- Modify: `.github/workflows/ci.yml`（backend job 的 `setup-python` step）

- [ ] **Step 1: 给 setup-python 加缓存**

把 backend job 的：

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
```

改为：

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'
          cache-dependency-path: backend/requirements-dev.txt
```

- [ ] **Step 2: 校验 YAML 合法**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo OK`
Expected: 输出 `OK`。

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: backend job 加 pip 缓存，加速依赖安装

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: `ci.yml` — deploy job 加并发锁

**Files:**
- Modify: `.github/workflows/ci.yml`（deploy job）

- [ ] **Step 1: 给 deploy job 加 concurrency**

把 deploy job 头部：

```yaml
  deploy:
    name: Deploy
    needs: [backend, frontend]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
```

改为（在 `runs-on` 后加 `concurrency` 块）：

```yaml
  deploy:
    name: Deploy
    needs: [backend, frontend]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    # 两次 push 时让当前部署跑完、下一次排队，不取消在途部署（避免半截状态）
    concurrency:
      group: production-deploy
      cancel-in-progress: false
```

- [ ] **Step 2: 校验 YAML 合法**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo OK`
Expected: 输出 `OK`。

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: deploy job 加并发锁，串行化生产部署

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: `deploy.sh` — 假回滚改真回滚

**Files:**
- Modify: `deploy/deploy.sh`

**背景：** 现有 `rollback()`（第 23-27 行）在 `docker compose pull` 覆盖本地 `latest` tag 后，只是 `docker compose up -d` 重启同一个坏镜像，无法回到旧版本。改为：拉新镜像前抓住旧镜像 ID，失败时用临时 tag 拉起旧版本并二次健康检查。

- [ ] **Step 1: 把 `rollback()` 函数替换为真回滚**

把第 23-27 行的：

```bash
rollback() {
    log "Rolling back — restarting previous containers..."
    docker compose up -d 2>/dev/null || true
    fail "Deploy failed. Check: docker compose logs backend"
}
```

替换为：

```bash
# 真回滚：用部署前抓住的旧镜像 ID 拉起上一版本，再做一次健康检查。
# PREV_IMAGE_ID 在拉新镜像前由主流程捕获（见下方 [2/4] 之前）。
rollback() {
    if [ -z "${PREV_IMAGE_ID:-}" ]; then
        fail "Deploy failed and no previous image to roll back to (first deploy?). Check: docker compose logs backend"
    fi
    log "Rolling back to previous image ${PREV_IMAGE_ID:0:19}..."
    docker tag "$PREV_IMAGE_ID" bifurcation-backend:rollback
    BACKEND_IMAGE=bifurcation-backend:rollback docker compose up -d || \
        fail "Rollback failed to start previous image. Check: docker compose logs backend"
    if health_check; then
        log "Rolled back to previous version successfully (service restored)."
        fail "Deploy failed but previous version restored. Investigate the new image."
    fi
    fail "Deploy failed AND rollback health check failed — service may be down. Check: docker compose logs backend"
}
```

说明：`fail` 会 `exit 1`，所以即便回滚成功也以非 0 退出（CI 标红，但线上已恢复）。

- [ ] **Step 2: 在拉新镜像前捕获当前运行镜像 ID**

把第 74-78 行的：

```bash
# ── 2. 拉取新镜像 ──
# 只拉 backend：postgres 使用本地已有的镜像，避免 Docker Hub 抽风时卡死整个部署。
# 如需升级 postgres，手动 `docker compose pull postgres && docker compose up -d postgres`。
log "[2/4] Pulling latest backend image..."
docker compose pull backend || rollback
```

替换为：

```bash
# ── 2. 拉取新镜像 ──
# 只拉 backend：postgres 使用本地已有的镜像，避免 Docker Hub 抽风时卡死整个部署。
# 如需升级 postgres，手动 `docker compose pull postgres && docker compose up -d postgres`。
# 先抓住当前运行容器的镜像 ID：pull 会顶掉 latest tag，但旧镜像 ID 仍在本地，
# 抓住引用即可在失败时回滚（真回滚依赖这一步）。
PREV_IMAGE_ID=$(docker inspect --format='{{.Image}}' bifurcation-backend 2>/dev/null || echo "")
log "[2/4] Pulling latest backend image (prev=${PREV_IMAGE_ID:0:19})..."
docker compose pull backend || rollback
```

- [ ] **Step 3: 校验 shell 语法**

Run: `bash -n deploy/deploy.sh && echo OK`
Expected: 输出 `OK`，无语法错误。

- [ ] **Step 4: （可选）shellcheck 静态检查**

Run: `command -v shellcheck >/dev/null && shellcheck deploy/deploy.sh || echo "shellcheck not installed, skipped"`
Expected: 无 error 级告警（或 shellcheck 未装时跳过）。

- [ ] **Step 5: Commit**

```bash
git add deploy/deploy.sh
git commit -m "fix(deploy): 假回滚改真回滚——抓旧镜像 ID，失败时恢复上一版本并二次健康检查

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: 收尾 — followups + changelog

**Files:**
- Modify: `docs/changelog.md`
- Modify: `docs/followups.md`（如有对应项移除）

- [ ] **Step 1: 写 changelog**

在 `docs/changelog.md` 顶部加一条（沿用文件现有格式）：

```markdown
- CI/CD 安全加固：新增 `security.yml`（pip-audit + npm audit + gitleaks，只报告不拦截，依赖扫 push/PR + 每周定时）；`ci.yml` backend job 加 Trivy 镜像扫描（SARIF 上传 Security 页）与 pip 缓存，deploy job 加并发锁串行化部署；`deploy.sh` 假回滚改真回滚（抓旧镜像 ID，失败时恢复上一版本并二次健康检查）。设计见 `docs/superpowers/specs/2026-06-11-cicd-security-hardening-design.md`。
```

- [ ] **Step 2: followups.md 标注**

`followups.md` 当前 §4 只有 chunk size(4.1) 与 alembic(4.2)，本轮 CI/CD 安全项不在其列表内，无需移除。确认无遗漏即可（如发现相关条目则移到 changelog）。

- [ ] **Step 3: Commit**

```bash
git add docs/changelog.md docs/followups.md
git commit -m "docs: changelog 记录 CI/CD 安全加固

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage：**
- ① 依赖扫描（pip-audit + npm audit，push/PR+weekly，只报告）→ Task 1 ✅
- ② 镜像扫描（Trivy，只报告，SARIF）→ Task 2 ✅
- ③ 密钥扫描（gitleaks，只报告）→ Task 1 ✅
- ④ pip 缓存 → Task 3 ✅
- ⑤ 部署并发锁 → Task 4 ✅
- ⑥ 真回滚 → Task 5 ✅
- 收尾文档 → Task 6 ✅

**Placeholder scan：** 无 TBD/TODO；每个改动都给了确切 YAML/bash 内容与精确替换锚点。

**一致性：** `PREV_IMAGE_ID` 在 Task 5 Step 2 定义、Step 1 的 `rollback()` 引用，名称一致；`OWNER_LC` 复用 ci.yml 现有 step 写入的 env，时序正确（Lowercase owner name → build-push → Trivy 都在 push main 条件下）。`bifurcation-backend:rollback` 临时 tag 与 compose `BACKEND_IMAGE` 覆盖机制对齐。

**风险提示：** Trivy `image-ref` 用 `${{ env.OWNER_LC }}`，仅在 push main 时镜像已推送、env 已写入——已用相同 `if` 条件守住。gitleaks-action 对个人/公开仓库免费，无需 license secret。
