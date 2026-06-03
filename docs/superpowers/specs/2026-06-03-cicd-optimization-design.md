# CI/CD 优化设计 — 2026-06-03

> 目标：给现有 GitHub Actions 流水线补上**后端测试门槛**、**Docker 层缓存提速**、**阿里云 ACR 镜像加速**（可配置占位、非破坏），以及 **Docker Hub 镜像加速器**（让 postgres 拉取不卡死）。
> 来源：用户对 CI/CD 流水线的优化请求 + 现状审计（CI 完全不跑后端 pytest 是最大缺口）。

## 现状（`.github/workflows/ci.yml`）

`push main` / PR 触发三个 job：
- **backend**：装 `requirements.txt` → `py_compile` 编译检查 → import 检查 →（仅 push main）登录 GHCR + `build-push-action` 推 `:latest` / `:sha`。
- **frontend**：`npm ci` → type-check → build-only →（仅 push main）上传 `dist/` artifact。
- **deploy**（`needs: [backend, frontend]`，仅 push main）：rsync `dist/` → SSH `git pull` + `deploy/deploy.sh`（备份 PG → `docker compose pull backend` → `up -d` → 健康检查）→ 远程 health check。

部署侧：`docker-compose.yml` 的 backend `image:` 硬编码 GHCR 地址；`deploy.sh` 注释说明 postgres 走 Docker Hub、抽风会卡死，故只 `pull backend`。

## 决策摘要（用户确认）

- 范围：**(A) CI 跑后端 pytest、(B) Docker 层缓存、(C) 阿里云 ACR、(D) Docker Hub 加速器**。不做 lint / 部署真回滚 / 并发控制。
- ACR：**还没建** → workflow/compose/docs 全部写成**可配置占位**，未配置时退回 GHCR，不破坏现有流水线。
- pytest：**硬门槛**——测试不过就不构建、不部署。
- ACR 仓库名沿用 `bifurcation-backend`（与 GHCR 一致）；区域/命名空间由用户建好后填 GitHub `vars`。

---

## A. 测试门槛（CI 跑后端 pytest）

### A1. 测试依赖固化
新增 `backend/requirements-dev.txt`：
```
-r requirements.txt
pytest>=8
pytest-asyncio>=0.23
```
（测试基类是 `unittest.IsolatedAsyncioTestCase`，pytest 原生支持 unittest，`pytest-asyncio` 作为保险一并装；不污染生产 `requirements.txt`。）

### A2. backend job 增加测试步骤
- 把现有 **"Install dependencies"** 步骤的 `pip install -r requirements.txt` 改为 `pip install -r requirements-dev.txt`（dev 文件首行 `-r requirements.txt`，所以是生产依赖的超集，仍只有一步 install）。
- 在 **import 检查之后、GHCR 登录/构建之前**新增 **"Run tests"** 步骤：`APP_ENV=dev ./venv/bin/python -m pytest -q`（dev → SQLite，无需 DATABASE_URL/外部服务）。

### A3. 门槛生效方式
构建/推送步骤在同一 job 内、顺序排在 pytest 之后；pytest 失败 → job 失败 → 后续构建步骤不执行。`deploy` job `needs: [backend, frontend]`，backend 失败 → 部署不触发。**无需额外 gate 配置**，顺序即门槛。

---

## B. Docker 层缓存

`build-push-action`（backend job 的构建步骤）增加：
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```
依赖层（`pip install -r requirements.txt`）命中缓存后构建显著加速。用 GitHub Actions 自带缓存，无需额外密钥。

---

## C. 阿里云 ACR（可配置占位，非破坏）

### C1. 配置来源（不硬编码）
- **仓库变量（非敏感）**：`vars.ACR_REGISTRY`（如 `registry.cn-hangzhou.aliyuncs.com`）、`vars.ACR_NAMESPACE`。
- **secrets（敏感）**：`ACR_USERNAME`、`ACR_PASSWORD`。
- 全部未配置时，下述 ACR 步骤跳过，流水线行为与现状一致（只推 GHCR）。

### C2. CI：一次构建、多仓库推送
1. 保留现有 GHCR 登录（`docker/login-action`，always on push main）。
2. **条件式 ACR 登录**：`if: vars.ACR_REGISTRY != ''` 时 `docker/login-action` 登录 `${{ vars.ACR_REGISTRY }}`（user/password 走 secrets）。
3. **构造 tag 列表**：一个 `id: meta` 步骤，始终含两条 GHCR tag（`:latest`、`:${{ github.sha }}`）；当 `vars.ACR_REGISTRY != ''` 时追加两条 ACR tag（`${REGISTRY}/${NAMESPACE}/bifurcation-backend:latest` 与 `:${sha}`）。用 heredoc 写入 `$GITHUB_OUTPUT` 的多行 `tags`。
4. **单个 `build-push-action`** 用 `tags: ${{ steps.meta.outputs.tags }}` + B 的缓存。已登录的仓库都会被推送 → 配了 ACR 就双推，没配就只 GHCR。

> 不复制两个 build step（避免重复构建）；多 registry 推送由同一 step 完成。

### C3. 服务器拉取侧（参数化镜像）
`docker-compose.yml` 的 backend 服务：
```yaml
    image: ${BACKEND_IMAGE:-ghcr.io/academy-of-boundary-landscape/bifurcation-backend:latest}
```
- 默认仍是 GHCR → 不破坏现状。
- ACR 就绪后：服务器 `.env` 增 `BACKEND_IMAGE=<acr>/<ns>/bifurcation-backend:latest`，并 `docker login <acr> -u … -p …` 一次（拉私有库）。`deploy.sh` 的 `docker compose pull backend` 自动按 `BACKEND_IMAGE` 拉取，CI 与脚本都不用再改。

### C4. 文档（`docs/deployment.md`）
新增一节，写清：阿里云控制台建 ACR（个人版即可）+ 命名空间 + 仓库 `bifurcation-backend`；GitHub 仓库 Settings 填 `vars.ACR_REGISTRY`/`vars.ACR_NAMESPACE` 与 `secrets.ACR_USERNAME`/`ACR_PASSWORD`；服务器设 `BACKEND_IMAGE` + `docker login`。

---

## D. Docker Hub 镜像加速器（postgres 不卡死）

- 新增 `deploy/daemon.json` 示例：
```json
{
  "registry-mirrors": ["https://<your-id>.mirror.aliyuncs.com"]
}
```
- `docs/deployment.md` 一节：把它放到服务器 `/etc/docker/daemon.json`，`systemctl restart docker`，加速 Docker Hub（postgres 等）拉取。
- **明确说明**：registry-mirror 对 `ghcr.io` / 私有 ACR **无效**，只加速 Docker Hub；backend 镜像的加速靠 C 的 ACR。

---

## 验证门槛

- 后端：`cd backend && venv/bin/python -m pytest -q`（40 passed，确认 pytest 步骤本身可跑）。
- workflow：用 `actionlint`（若环境可用）校验 `ci.yml`；否则仔细审 + reviewer 子代理过一遍。
- 非破坏性推演：未设 `vars.ACR_REGISTRY` 时——ACR 登录步骤 skip、tag 列表只含 GHCR、compose 用默认 GHCR 镜像 → 行为等同现状。
- `docker-compose.yml` 改动用 `docker compose config`（若本机有 docker）确认 `image` 解析正确（无 `BACKEND_IMAGE` 时回退默认）。

## 范围外

- 后端 ruff / 前端 eslint。
- 部署真回滚（按 sha 回退上一个好镜像）、`concurrency` 防并发部署。
- 多 worker 限流共享存储（已在 `docs/followups.md` 记录，另行处理）。
