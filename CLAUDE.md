# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

本文件是 Claude Code 在本仓库工作时的纪律与核心约定。**优先级高于默认行为，低于用户的当场指令。**

---

## 0. 开工前必读：用好 Superpowers 技能

本环境装有 superpowers 插件技能。**任何任务开始前，先判断有没有可用技能，命中就必须用。**

- **创造性工作前**（新功能 / 新组件 / 改行为）→ 先 `superpowers:brainstorming`
- **写功能或修 bug 前** → `superpowers:test-driven-development`
- **遇到 bug / 测试失败 / 异常行为** → `superpowers:systematic-debugging`（先于任何修复猜测）
- **有 2 个以上彼此独立的任务** → `superpowers:dispatching-parallel-agents`
- **执行写好的实施计划** → `superpowers:executing-plans` / `superpowers:subagent-driven-development`
- **声称"做完 / 修好 / 通过"之前** → `superpowers:verification-before-completion`（先跑命令拿证据，再下结论）
- **前端页面 / 组件设计** → `frontend-design`


---

## 1. 项目概况

"树状结构"小说续写平台。读者沿着故事树的分支阅读，并在任意节点续写新分支，经审核后并入世界线。

- 前端：`/frontend` — Vue 3 + TypeScript + Vite + Pinia + Vue Router + TanStack Vue Query + Naive UI + UnoCSS
- 后端：`/backend` — FastAPI + SQLAlchemy 2.0(async) + Casdoor(SSO) + 本地 JWT 会话（schema 走启动时 `create_all`，**不是** alembic——见 §1.5）
- 文档：`/docs` — **唯一**正式文档目录，以源码为准

### 目录里的历史噪声
根目录的 `cline.md`、`frontend-temp/`、各子目录散落的旧 markdown 多已过期。**审阅与开发时忽略它们**；需要写文档一律进 `/docs`。

---

## 1.5 架构大图（Big Picture）

跨多个文件才能看清、动手前要先建立的结构。

### 故事树是核心数据模型（`backend/app/models/story.py`）
`StoryNode` 自引用 `parent_id` 构成树，`root_id` 指向树根（建首节点时先 insert、再回填 `root_id = self.id`，见 `services/story_nodes.py`）。节点有三个**正交**状态维度：
- `status`：`pending → published / archived`——读者续写的新分支要经管理员审核（`services/story_nodes.py:audit_*`）才进世界线。
- `visibility`：`public / unlisted / private`（注意：`unlisted` 读路径尚未实现，见 `docs/followups.md`）。
- `zone`：`long / short`。

去规范化计数 `likes_count / comments_count / children_count` 用**原子 SQL** 维护（`x = x ± 1`，减法用 `case` 防负），漂移时用对账脚本 `backend/scripts/recount.py` 重算。树的读取在 `api/v1/story.py` 的 `build_memory_tree`：一次查出可见节点、在内存里建树，并把"父节点被过滤掉但自身仍可见"的节点提升为局部 root，避免子树整片消失。

### 请求生命周期（后端，薄路由 + 厚 service）
`main.py`（仓库根，建 FastAPI app、挂 CORS / 限流 / 异常处理）→ `app/api/api.py`（聚合 v1 路由）→ `app/api/v1/*.py`（路由，按资源分 `auth/story/users/interaction/admin/discovery/upload`，保持薄）→ `app/services/*.py`（业务逻辑与事务）→ `app/models`（SQLAlchemy）。依赖注入集中在 `app/api/deps.py`（DB session、当前用户、管理员守卫）。列表端点返回**裸 `List` + `X-Total-Count` 响应头**给真实总数（辅助见 `app/api/pagination.py`，CORS 已 expose 该头）。

### 认证：Casdoor 登录 + 本地 JWT 会话
Casdoor 只做登录鉴别（OAuth2 授权码）。换码在 `services/sso.py:exchange_sso_code`（校验 id_token / userinfo，**首登自动建本地用户**），随后本站签发**本地 JWT** 作为会话凭证。此后所有请求只认本地 JWT（`core/security.py` + `deps.get_current_user`），与 Casdoor 无关。

### Schema 与迁移（重要——没有 alembic 流程）
`alembic/versions/` 是空的。schema 演进靠容器启动时 `scripts/auto_migrate.py` 跑 `Base.metadata.create_all`（**只增不毁**）。新增表/字段：重启容器即可；**改字段类型 / 加索引 / 删列**：`create_all` 不处理，要手写迁移。`init_database.py` 会 `drop_all`，**只用于全新库**，生产入口 `entrypoint.sh` 绝不调它。

### 运行时拓扑
生产用 docker-compose（`postgres` + `backend`），后端容器 `entrypoint.sh` 先 auto_migrate（重试 5 次）再起 `uvicorn main:app --workers ${UVICORN_WORKERS:-2}`。nginx 反代 `127.0.0.1:8057` 并 serve 前端 `dist/`，把真实 IP 写进 `X-Real-IP`。
- ⚠️ **默认 2 个 worker**：进程内状态（如 slowapi 内存限流计数）会**各算各的**，按进程计数的机制在多 worker 下阈值实际翻倍；要全局一致需换共享存储（Redis）。
- 开发用 SQLite（`APP_ENV=dev` → `dev.db`），生产用 Postgres（`DATABASE_URL`）。

---

## 2. 环境与构建

### 后端（在 `backend/venv` 里开发；venv 需装 `pytest` + `pytest-asyncio`）
```bash
cd backend
source venv/bin/activate                  # 或直接用 venv/bin/python 前缀
python main.py                            # 启动服务（读 BACKEND_HOST/BACKEND_PORT，默认 0.0.0.0:8057）
venv/bin/python -m pytest -q              # 跑全部测试
venv/bin/python -m pytest tests/test_metrics_integrity.py -q                                 # 单个文件
venv/bin/python -m pytest tests/test_rate_limit.py::TestCommentRateLimit -v                  # 单个类
venv/bin/python -m pytest tests/test_rate_limit.py::TestRateLimitKeys::test_user_key_prefers_user_then_ip -v   # 单个用例
venv/bin/python -m scripts.recount       # 计数对账（漂移时重算 likes/comments/children）
```
测试两种基类（共享工具在 `tests/test_support.py`）：`SQLiteIntegrationTestCase`（真 aiosqlite 库 + httpx 打 ASGI app，端到端）、`BackendAsyncTestCase`（mock execute 结果，单元）。

### 前端
```bash
cd frontend
npm install                  # 依赖在 /frontend/node_modules
npm run dev                  # 开发
npm run type-check           # vue-tsc 类型检查（提交前必跑）
npm run build                # 构建（含 type-check）
# 提交门槛（与 §3.5 一致，最干净的一次过）：
npx vue-tsc --build --force && npm run build-only
```

---

## 3. 工作纪律

1. **先梳理后动手**：改之前先看清已有模块结构，不要重复造轮子、不要制造冲突。
2. **大改动先计划**：较大改动先给计划再动手；**不要随意做整体性重构**。
3. **维护 changelog**：每次有意义的改动写入 `docs/changelog.md`（改了什么 + 为什么）。
4. **完成即清理 followups**：动手做 `docs/followups.md` 里的项时移到 in_progress，做完从该文件移到 changelog。
5. **证据优先**：说"通过/修好"之前先实际运行验证命令，贴输出，不要凭感觉下结论。

---

## 3.5 Git 工作流（合并 / 推送到 main 的标准流程）

**默认在分支上工作，main 始终保持可部署。** `push` 到 `origin/main` 会触发自动部署（CI 见 `.github/workflows/ci.yml`，`on: push: branches: [main]`）。

标准节奏（每次成规模改动）：

1. **开分支**：从 main 切 `chore/...`、`fix/...`、`feat/...`（不在 main 上直接改）。
2. **分阶段提交**：按逻辑拆分提交；每个提交前先过验证门槛：
   - 前端：`cd frontend && npx vue-tsc --build --force && npm run build-only`
   - 后端：`cd backend && venv/bin/python -m pytest -q`（venv 需有 pytest/pytest-asyncio）
3. **审阅**：合并前派一个 reviewer 子代理审 `git diff main..HEAD`（让它自己跑两套件复核）；修掉 Critical/Important。
4. **合并**：`git checkout main && git merge --ff-only <branch>`（优先 fast-forward，保持线性历史）。
5. **推送**：`git push origin main`（此步触发部署）。
6. **清理**：`git branch -d <branch>`。

纪律：
- `commit`可以自主决策，但**只有用户明确要求才  `push`**；，每次合并/推送前确认。
- **提交信息**：沿用历史风格（`type(scope): 摘要`，可带 gitmoji），正文说清"做了什么 + 为什么"，结尾固定 trailer：
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- 合并前确认 `git status` 干净、与 `origin/main` 关系清楚（`git log --oneline origin/main..HEAD`）；推送后确认 `## main...origin/main` 已同步。
- 注意 CI 范围（`.github/workflows/ci.yml`）：后端只做 `py_compile` 导入检查 + 镜像构建/推送，前端做 type-check + build——**两边都不跑后端 pytest**。所以后端运行时风险要靠本地 `pytest` + 审阅把关；push main 还会触发 SSH 部署。

---

## 4. 前端核心约定（务必遵守）

### 4.1 数据层分层（见 `docs/frontend/data-layer.md`）
- `services/http.ts` — 唯一 HTTP 入口；统一 baseURL、token 注入、401 登出。**业务层不要手拼 `/api/v1`**。
- `features/*/api.ts` — 资源级接口路径，同一资源只保留一套正式路径。
- `features/*/queries.ts` — query / mutation 与缓存失效策略。
- `features/queryKeys.ts` — **唯一** query key 来源，不要在页面里散写字符串 key。
- `pages/*` / `components/*` — **只组合 feature 能力 + 管界面状态**，不自创接口协议、不自创 key、不直接 `get/post/put/del` 业务请求。

领域划分：`story`=故事资源，`interaction`=互动资源，`admin`=后台资源，`discovery`=发现资源。

### 4.2 视觉风格（见 `docs/frontend/visual-style.md`）
定位："叙事观测终端"，不是内容社区。
- **黑白灰主导**，状态色仅做少量强调（成功冷绿 / 警告冷黄 / 错误冷红）。
- **锐利几何**，小圆角甚至直角；细边框；克制阴影。
- **极简有秩序**，留白服务层次；动效克制，语义是"扫描 / 锁定 / 聚焦 / 切换"。
- **明确禁止**：紫色泛滥的通用 AI 科技风、赛博霓虹、社交卡片堆叠、二次元梦幻发光、花哨大屏可视化、过圆的消费级 SaaS 风。
  - ⚠️ 注意：`uno.config.ts` 现有 `accent: '#8b5cf6'`（紫）与本风格冲突，新代码不要依赖它。
- 设计 token 走 `uno.config.ts` 的 shortcuts（`card-base`、`text-primary` 等），不要到处硬编码颜色。

---

## 5. 文档约定

- 正式文档只在 `/docs`，以当前源码为准，规则与边界优先于易过时的实现样例。
- SSO：Casdoor 只负责登录鉴别，本站用本地 JWT 做会话鉴权。
- 索引见 `docs/README.md`；改造记录见 `docs/changelog.md`；待办见 `docs/followups.md`。
