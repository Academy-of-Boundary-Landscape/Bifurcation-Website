# CI/CD 优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给现有 GitHub Actions 流水线加后端 pytest 门槛、Docker 层缓存、阿里云 ACR 可配置占位（非破坏），以及 Docker Hub 镜像加速器文档。

**Architecture:** 改 `.github/workflows/ci.yml` 的 backend job（测试门槛 + 缓存 + 多仓库推送）、参数化 `docker-compose.yml` 的镜像、加 dev 依赖与部署文档。ACR 全部走 GitHub `vars`/`secrets`，未配置时退回 GHCR，行为等同现状。

**Tech Stack:** GitHub Actions、docker/build-push-action（gha cache + multi-registry）、pytest、阿里云 ACR / 镜像加速器。

参考 spec：`docs/superpowers/specs/2026-06-03-cicd-optimization-design.md`

---

## 文件结构

- Create `backend/requirements-dev.txt` — 测试依赖（生产依赖超集）
- Modify `.github/workflows/ci.yml` — backend job：dev 依赖 + pytest 步骤 + 缓存 + ACR 条件登录 + tag 计算 + 多仓库推送
- Modify `docker-compose.yml` — backend `image` 参数化为 `${BACKEND_IMAGE:-<GHCR 默认>}`
- Create `deploy/daemon.json` — 阿里云 Docker Hub 镜像加速器示例
- Modify `docs/deployment.md` — 新增 ACR 配置节 + daemon.json 加速器节

---

## Task 1: 后端 pytest 门槛

**Files:**
- Create: `backend/requirements-dev.txt`
- Modify: `.github/workflows/ci.yml`（backend job 的 "Install dependencies"；在 "Import check" 后新增 "Run tests"）

- [ ] **Step 1: 创建 dev 依赖文件**

创建 `backend/requirements-dev.txt`：
```
-r requirements.txt
pytest>=8
pytest-asyncio>=0.23
```

- [ ] **Step 2: 本地验证 dev 依赖能跑通测试**

Run:
```bash
cd backend && venv/bin/pip install -r requirements-dev.txt --quiet && APP_ENV=dev venv/bin/python -m pytest -q
```
Expected: `40 passed`（确认 `requirements-dev.txt` 可解析、测试可在 dev/SQLite 下跑）。

- [ ] **Step 3: CI 安装步骤改用 dev 依赖**

在 `.github/workflows/ci.yml` 的 backend job 里，把 "Install dependencies" 步骤：
```yaml
      - name: Install dependencies
        run: |
          python -m venv venv
          ./venv/bin/pip install -r requirements.txt --quiet
```
改为：
```yaml
      - name: Install dependencies
        run: |
          python -m venv venv
          ./venv/bin/pip install -r requirements-dev.txt --quiet
```

- [ ] **Step 4: 新增 "Run tests" 步骤（排在 Import check 之后、Log in to GHCR 之前）**

在 `.github/workflows/ci.yml` 的 "Import check" 步骤之后插入：
```yaml
      - name: Run tests
        run: APP_ENV=dev ./venv/bin/python -m pytest -q
```
（backend job 默认 `working-directory: backend`，故 pytest 从 `backend/` 跑；测试红 → job 失败 → 后续构建步骤不执行、`deploy` job 不触发。）

- [ ] **Step 5: 校验 workflow YAML 合法**

Run:
```bash
cd /data/sunyunbo/www/Bifurcation-Website && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML OK')"
command -v actionlint >/dev/null && actionlint .github/workflows/ci.yml || echo "actionlint 不可用，跳过（非阻塞）"
```
Expected: `YAML OK`；actionlint 若可用应无报错。

- [ ] **Step 6: Commit**

```bash
git add backend/requirements-dev.txt .github/workflows/ci.yml
git commit -m "ci(backend): 引入 pytest 测试门槛（dev 依赖固化 + 构建前必跑）"
```

---

## Task 2: Docker 层缓存

**Files:**
- Modify: `.github/workflows/ci.yml`（backend job 的 "Build and push Docker image" 步骤）

- [ ] **Step 1: 给 build-push-action 加 gha 缓存**

在 `.github/workflows/ci.yml` 的 "Build and push Docker image" 步骤的 `with:` 块里，给现有字段追加缓存两行。该步骤当前为：
```yaml
      - name: Build and push Docker image
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        uses: docker/build-push-action@v6
        with:
          context: backend
          push: true
          tags: |
            ghcr.io/${{ env.OWNER_LC }}/bifurcation-backend:latest
            ghcr.io/${{ env.OWNER_LC }}/bifurcation-backend:${{ github.sha }}
```
改为（仅在 `tags:` 块之后追加 `cache-from`/`cache-to`）：
```yaml
      - name: Build and push Docker image
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        uses: docker/build-push-action@v6
        with:
          context: backend
          push: true
          tags: |
            ghcr.io/${{ env.OWNER_LC }}/bifurcation-backend:latest
            ghcr.io/${{ env.OWNER_LC }}/bifurcation-backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

- [ ] **Step 2: 校验 YAML**

Run:
```bash
cd /data/sunyunbo/www/Bifurcation-Website && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML OK')"
```
Expected: `YAML OK`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci(backend): Docker 构建启用 gha 层缓存"
```

---

## Task 3: 阿里云 ACR 条件式多仓库推送

**Files:**
- Modify: `.github/workflows/ci.yml`（新增条件式 ACR 登录 + "Compute image tags" 步骤；build-push 改用计算出的 tags）

> 全程基于 `vars.ACR_REGISTRY`：未设置时，ACR 登录步骤 skip、tag 列表只含 GHCR → 行为等同现状（非破坏）。`vars.ACR_REGISTRY`/`vars.ACR_NAMESPACE` 是仓库变量；`secrets.ACR_USERNAME`/`secrets.ACR_PASSWORD` 是 secrets。

- [ ] **Step 1: 新增条件式 ACR 登录步骤（紧跟 "Log in to GHCR" 之后）**

在 `.github/workflows/ci.yml` 的 "Log in to GHCR" 步骤之后插入：
```yaml
      - name: Log in to Aliyun ACR
        if: github.ref == 'refs/heads/main' && github.event_name == 'push' && vars.ACR_REGISTRY != ''
        uses: docker/login-action@v3
        with:
          registry: ${{ vars.ACR_REGISTRY }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
```

- [ ] **Step 2: 新增 "Compute image tags" 步骤（紧跟 "Lowercase owner name" 之后）**

"Lowercase owner name" 步骤把 `OWNER_LC` 写入 `$GITHUB_ENV`。在其之后插入：
```yaml
      - name: Compute image tags
        id: meta
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: |
          {
            echo "tags<<EOF"
            echo "ghcr.io/${OWNER_LC}/bifurcation-backend:latest"
            echo "ghcr.io/${OWNER_LC}/bifurcation-backend:${{ github.sha }}"
            if [ -n "${{ vars.ACR_REGISTRY }}" ]; then
              echo "${{ vars.ACR_REGISTRY }}/${{ vars.ACR_NAMESPACE }}/bifurcation-backend:latest"
              echo "${{ vars.ACR_REGISTRY }}/${{ vars.ACR_NAMESPACE }}/bifurcation-backend:${{ github.sha }}"
            fi
            echo "EOF"
          } >> "$GITHUB_OUTPUT"
```

- [ ] **Step 3: build-push 改用计算出的 tags**

把 "Build and push Docker image" 步骤里的：
```yaml
          tags: |
            ghcr.io/${{ env.OWNER_LC }}/bifurcation-backend:latest
            ghcr.io/${{ env.OWNER_LC }}/bifurcation-backend:${{ github.sha }}
```
替换为：
```yaml
          tags: ${{ steps.meta.outputs.tags }}
```
（`cache-from`/`cache-to` 两行保持不变。最终该步骤 `with:` 为 `context` / `push` / `tags` / `cache-from` / `cache-to`。）

- [ ] **Step 4: 校验 YAML + 非破坏性推演**

Run:
```bash
cd /data/sunyunbo/www/Bifurcation-Website && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML OK')"
```
Expected: `YAML OK`。
推演确认（写进 commit message 或自检）：未设 `vars.ACR_REGISTRY` 时 → "Log in to Aliyun ACR" 的 `if` 为 false 跳过；"Compute image tags" 的 `if [ -n "" ]` 为 false → tags 只含两条 GHCR → 仅推 GHCR，等同现状。

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci(backend): 阿里云 ACR 条件式多仓库推送（未配置则退回 GHCR）"
```

---

## Task 4: 参数化 compose 镜像

**Files:**
- Modify: `docker-compose.yml`（backend 服务 `image:`，当前在第 26 行）

- [ ] **Step 1: 把 backend image 改为可被 .env 覆盖**

把 `docker-compose.yml` 的：
```yaml
    image: ghcr.io/academy-of-boundary-landscape/bifurcation-backend:latest  # GHCR 要求全小写
```
改为：
```yaml
    image: ${BACKEND_IMAGE:-ghcr.io/academy-of-boundary-landscape/bifurcation-backend:latest}  # 默认 GHCR；ACR 就绪后在服务器 .env 设 BACKEND_IMAGE 覆盖
```

- [ ] **Step 2: 验证默认回退正确**

Run（本机有 docker 则用 compose config 实测；没有则用 YAML 解析兜底）：
```bash
cd /data/sunyunbo/www/Bifurcation-Website
if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
  docker compose config 2>/dev/null | grep -A1 "bifurcation-backend" | grep "image:" || docker compose config 2>/dev/null | grep "image:"
else
  python3 -c "import yaml; d=yaml.safe_load(open('docker-compose.yml')); print(d['services']['backend']['image'])"
fi
```
Expected: 未设 `BACKEND_IMAGE` 时镜像解析为 `ghcr.io/academy-of-boundary-landscape/bifurcation-backend:latest`（compose 实测会展开默认值；YAML 兜底会打印 `${BACKEND_IMAGE:-ghcr.io/...latest}` 字面量，二者均说明默认回退就位）。

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "chore(deploy): backend 镜像参数化（BACKEND_IMAGE，默认 GHCR）"
```

---

## Task 5: 部署文档（ACR + Docker Hub 加速器）

**Files:**
- Create: `deploy/daemon.json`
- Modify: `docs/deployment.md`（在 "### 2.3 开启 Workflow 的写权限" 之后新增 ACR 节；并在合适位置加 daemon.json 加速器节）

- [ ] **Step 1: 创建 daemon.json 示例**

创建 `deploy/daemon.json`：
```json
{
  "registry-mirrors": ["https://<你的加速器ID>.mirror.aliyuncs.com"]
}
```

- [ ] **Step 2: deployment.md 新增 ACR 配置节**

在 `docs/deployment.md` 的 "### 2.3 开启 Workflow 的写权限（让 CI 推镜像）" 节之后，插入：
```markdown
### 2.3.1 [可选/推荐] 阿里云 ACR：加速服务器拉镜像

GHCR（`ghcr.io`）在国内服务器拉取常慢甚至卡死。把后端镜像额外推到阿里云容器镜像服务（ACR），服务器改从 ACR 拉，可大幅提速。**不配置则一切照旧走 GHCR。**

**1. 阿里云控制台**：开通「容器镜像服务（个人版即免费）」→ 创建命名空间（记下 `<namespace>`）→ 创建镜像仓库 `bifurcation-backend`。记下仓库地址前缀，形如 `registry.cn-hangzhou.aliyuncs.com`，并设置 Registry 登录密码。

**2. GitHub 仓库**：Settings → Secrets and variables → Actions：
- **Variables** 标签页新增：`ACR_REGISTRY`（如 `registry.cn-hangzhou.aliyuncs.com`）、`ACR_NAMESPACE`（你的命名空间）。
- **Secrets** 标签页新增：`ACR_USERNAME`、`ACR_PASSWORD`（阿里云 Registry 账号密码）。

配齐后，下次 push main：CI 会同时把镜像推到 GHCR 与 ACR（`<ACR_REGISTRY>/<ACR_NAMESPACE>/bifurcation-backend:latest` 及 `:<sha>`）。

**3. 生产服务器**：
```bash
# 登录 ACR（拉私有库需要，一次即可）
docker login <ACR_REGISTRY> -u <ACR_USERNAME> -p <ACR_PASSWORD>
# 在项目根 .env 增加一行，让 compose 从 ACR 拉
echo 'BACKEND_IMAGE=<ACR_REGISTRY>/<ACR_NAMESPACE>/bifurcation-backend:latest' >> .env
```
此后 `deploy/deploy.sh` 的 `docker compose pull backend` 会按 `BACKEND_IMAGE` 从 ACR 拉取，CI 与脚本都无需再改。

### 2.3.2 [可选] Docker Hub 镜像加速器（让 postgres 拉取不卡死）

postgres 镜像走 Docker Hub，国内拉取易抽风。给服务器 Docker 配阿里云镜像加速器：

```bash
# 阿里云控制台「容器镜像服务 → 镜像加速器」获取你的专属地址，填进 deploy/daemon.json 后：
sudo cp deploy/daemon.json /etc/docker/daemon.json   # 或手动编辑 /etc/docker/daemon.json
sudo systemctl restart docker
```

⚠️ 镜像加速器只对 **Docker Hub** 生效，对 `ghcr.io` 与私有 ACR **无效**——后端镜像的加速靠 2.3.1 的 ACR。
```

- [ ] **Step 3: 校验 daemon.json 合法**

Run:
```bash
cd /data/sunyunbo/www/Bifurcation-Website && python3 -c "import json; json.load(open('deploy/daemon.json')); print('JSON OK')"
```
Expected: `JSON OK`

- [ ] **Step 4: Commit**

```bash
git add deploy/daemon.json docs/deployment.md
git commit -m "docs(deploy): 阿里云 ACR 配置 + Docker Hub 镜像加速器说明"
```

---

## 最终验证门槛

- [ ] 后端测试可跑：`cd backend && APP_ENV=dev venv/bin/python -m pytest -q` → `40 passed`
- [ ] workflow 合法：`python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` 通过；有 actionlint 则无报错
- [ ] compose 默认回退正确（Task 4 Step 2）
- [ ] daemon.json 合法 JSON
- [ ] 非破坏推演：未配 ACR vars/secrets → 流水线只推 GHCR、compose 用默认 GHCR 镜像，等同现状
- [ ] `git log --oneline main..HEAD` 为本次任务提交序列；`git status` 干净

## 审阅与合并（按 CLAUDE.md §3.5）

- [ ] 派 reviewer 子代理审 `git diff main..HEAD`（重点：ci.yml 的 ACR 条件分支非破坏性、缓存/多仓库推送正确性、YAML 缩进）；修掉 Critical/Important
- [ ] 合并前确认 `git status` 干净、`git log --oneline origin/main..HEAD` 清楚
- [ ] **仅在用户明确要求后** `git checkout main && git merge --ff-only chore/ci-cd-optimization && git push origin main`（push 会触发部署，且本次 CI 第一次真正跑 pytest）
- [ ] 推送后 `git branch -d chore/ci-cd-optimization`
