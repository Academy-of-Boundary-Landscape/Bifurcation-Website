# CI/CD 安全扫描 + 流水线稳健性 — 设计

- 日期：2026-06-11
- 状态：已确认，待实施
- 关联：`docs/superpowers/specs/2026-06-03-cicd-optimization-design.md`（上一轮 CI/CD 优化，已落地）

## 背景

上一轮 CI/CD 优化（2026-06-03）已落地后端 pytest 门槛、Docker 层缓存、多仓库推送、参数化 compose、部署文档。当前 `ci.yml` 三个 job 骨架完整（backend 检查+构建、frontend 检查+构建、deploy SSH 部署+健康检查），但仍缺：

- **安全扫描**：无依赖漏洞扫描、无镜像 CVE 扫描、无密钥扫描——这是当前 CI 最大的安全空洞。
- **pip 缓存**：前端有 npm 缓存，后端每次重装依赖。
- **部署并发**：无并发锁，两次 push 可能并发部署打架。
- **失败回滚**：`deploy.sh` 的 `rollback()` 是假回滚——`docker compose pull` 覆盖本地 `latest` tag 后，它只是 `docker compose up -d` 重启**同一个刚拉下来的坏镜像**，无法回到旧版本。

本设计补齐这五件事。前后端 lint 本轮明确不做（用户决策）。

## 决策（已确认）

- **扫描门槛**：所有扫描**只报告不拦截**——结果上传/打印，但永不让 job 失败、不挡部署。先建立可见性。
- **依赖扫描触发时机**：`push` + `pull_request` + **每周定时**（cron），定时扫能发现依赖未变期间新披露的 CVE。
- **工具选型**：依赖用 `pip-audit`（后端）+ `npm audit`（前端）；镜像用 Trivy；密钥用 gitleaks。

## 总体结构

- **新增 `.github/workflows/security.yml`**：放依赖扫描 + 密钥扫描，独立触发器（含 schedule）。独立 workflow 避免 schedule 触发器误触发 `ci.yml` 的构建/部署 job。
- **改 `.github/workflows/ci.yml`**：3 处——backend job 加 Trivy 镜像扫描 + pip 缓存，deploy job 加并发锁。
- **改 `deploy/deploy.sh`**：把假回滚改成真回滚。

不碰其他文件。

## 详细设计

### ① 依赖漏洞扫描 → `security.yml`（新文件）

- 触发器：
  ```yaml
  on:
    push:
      branches: [main]
    pull_request:
      branches: [main]
    schedule:
      - cron: '0 3 * * 1'   # 每周一 03:00 UTC
  ```
- 后端步骤：`pip-audit --requirement backend/requirements.txt`
- 前端步骤：`npm audit --audit-level=high`（在 `frontend/` 下）
- **只报告**：步骤加 `continue-on-error: true`；结果写进 `$GITHUB_STEP_SUMMARY`。job 整体不因漏洞而失败。

### ② 镜像漏洞扫描 → `ci.yml` backend job

- 位置：`Build and push Docker image` step **之后**（镜像已推到 registry）。
- 用 `aquasecurity/trivy-action`，`image-ref: ghcr.io/${OWNER_LC}/bifurcation-backend:${{ github.sha }}`，扫基础镜像 `python:3.13-slim` 的系统层 CVE。
- **只报告**：`exit-code: '0'`（永不 fail）；`format: sarif` + `output: trivy-results.sarif`，用 `github/codeql-action/upload-sarif` 传到 GitHub Security 页。
- 仅在 push main 构建镜像后跑（与 build-push step 同样的 `if` 条件）。

### ③ 密钥扫描 → `security.yml`

- 用 `gitleaks/gitleaks-action`，扫提交内容。
- **只报告**：`continue-on-error: true`。
- 设计标注：密钥泄露比 CVE 严重，日后想升级为"发现即拦截"只需去掉 `continue-on-error`。本轮按统一的"只报告"策略起步。

### ④ pip 缓存 → `ci.yml` backend job

- `actions/setup-python@v5` 加：
  ```yaml
  with:
    python-version: '3.13'
    cache: 'pip'
    cache-dependency-path: backend/requirements-dev.txt
  ```
- 缓存 pip 下载目录（`~/.cache/pip`），加速每次的依赖安装。前端 npm 缓存已有，无需改动。

### ⑤ 部署并发锁 → `ci.yml` deploy job

- 在 **deploy job 上**（不是 workflow 顶层）加：
  ```yaml
  concurrency:
    group: production-deploy
    cancel-in-progress: false
  ```
- 效果：两次 push 时当前部署跑完、下一次排队（不取消在途部署，避免半截状态）。放 job 级别，不影响 PR 的测试并行。

### ⑥ 真·失败自动回滚 → `deploy/deploy.sh`

把现有假回滚改为真回滚：

1. **拉新镜像之前**抓住当前运行容器的镜像 ID：
   ```bash
   PREV_IMAGE_ID=$(docker inspect --format='{{.Image}}' bifurcation-backend 2>/dev/null || echo "")
   ```
   即便随后 `docker compose pull` 把 `latest` tag 顶到新镜像，旧镜像的 sha256 ID 仍在本地，抓住引用就不会被回收。
2. 任一环节失败（`pull` / `up` / 健康检查失败）触发回滚 `restore_previous()`：
   - 若 `PREV_IMAGE_ID` 非空：`docker tag "$PREV_IMAGE_ID" bifurcation-backend:rollback`，然后 `BACKEND_IMAGE=bifurcation-backend:rollback docker compose up -d`，**再跑一次 `health_check`**。
     - 旧版本起来了 → 打印"已回滚到上一版本"，进程**以非 0 退出**（CI 标红提示部署失败，但线上已恢复）。
     - 旧版本也起不来 → 大声 `fail`。
   - 若 `PREV_IMAGE_ID` 为空（首次部署，无旧镜像）→ 无法回滚，直接 `fail`。
3. compose 第 26 行 `image: ${BACKEND_IMAGE:-...latest}` 已支持覆盖，机制现成。回滚是临时的：下次正常部署不带 `BACKEND_IMAGE`，照常拉 latest。

## 影响文件

| 文件 | 改动 |
|------|------|
| `.github/workflows/security.yml` | 新增：依赖扫描（pip-audit + npm audit）+ 密钥扫描（gitleaks），push/PR/weekly |
| `.github/workflows/ci.yml` | backend job 加 Trivy 镜像扫描 + pip 缓存；deploy job 加并发锁 |
| `deploy/deploy.sh` | 假回滚改真回滚（抓旧镜像 ID → 失败时恢复 + 二次健康检查） |

## 验证方式

- `security.yml`：可用 `act` 本地跑或 push 到分支后在 Actions 页看 job summary 是否产出扫描结果、是否绿（report-only 不应 fail）。
- `ci.yml` 改动：YAML 语法校验；push 分支观察 Trivy step 跑通、SARIF 上传、pip 缓存命中、deploy job 的 concurrency 生效。
- `deploy.sh` 回滚：本地用一个故意起不来的镜像（如错误 entrypoint）模拟健康检查失败，确认脚本能 `docker tag` 旧镜像并拉起、二次健康检查通过、以非 0 退出。

## 不在本轮范围

- 前后端 lint（ruff / eslint）——用户明确不做。
- 部署失败通知（钉钉/Slack）、前后端版本一致性标记——本轮未选。
- mypy 静态类型、监控（Sentry）、多 worker 限流 Redis、异地备份——属运维/后端，另行排期。
