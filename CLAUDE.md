# CLAUDE.md

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

红旗思维（出现就停下来想想是不是在偷懒）："这只是个简单问题""先看看代码再说""这个不值得正式上技能"。

---

## 1. 项目概况

"树状结构"小说续写平台。读者沿着故事树的分支阅读，并在任意节点续写新分支，经审核后并入世界线。

- 前端：`/frontend` — Vue 3 + TypeScript + Vite + Pinia + Vue Router + TanStack Vue Query + Naive UI + UnoCSS
- 后端：`/backend` — FastAPI + SQLAlchemy(async) + Alembic + Casdoor(SSO) + 本地 JWT 会话
- 文档：`/docs` — **唯一**正式文档目录，以源码为准

### 目录里的历史噪声
根目录的 `cline.md`、`frontend-temp/`、各子目录散落的旧 markdown 多已过期。**审阅与开发时忽略它们**；需要写文档一律进 `/docs`。

---

## 2. 环境与构建

### 后端
```bash
cd backend
source venv/bin/activate     # 必须在 /backend/venv 虚拟环境里开发
python main.py               # 启动服务
pytest                       # 跑测试
```

### 前端
```bash
cd frontend
npm install                  # 依赖在 /frontend/node_modules
npm run dev                  # 开发
npm run type-check           # vue-tsc 类型检查（提交前必跑）
npm run build                # 构建（含 type-check）
```

---

## 3. 工作纪律

1. **先梳理后动手**：改之前先看清已有模块结构，不要重复造轮子、不要制造冲突。
2. **大改动先计划**：较大改动先给计划再动手；**不要随意做整体性重构**。
3. **维护 changelog**：每次有意义的改动写入 `docs/changelog.md`（改了什么 + 为什么）。
4. **完成即清理 followups**：动手做 `docs/followups.md` 里的项时移到 in_progress，做完从该文件移到 changelog。
5. **证据优先**：说"通过/修好"之前先实际运行验证命令，贴输出，不要凭感觉下结论。

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
