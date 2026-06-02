# 项目文档

文档统一维护在 `/docs`，以源码为准，不以历史导出文档为准。

## 后端

- [`backend/overview.md`](backend/overview.md) — 模块结构、分层职责、认证边界
- [`backend/setup.md`](backend/setup.md) — 环境变量、数据库初始化、SSO 配置、测试环境启动
- [`backend/api.md`](backend/api.md) — FastAPI 路由总览与说明
- [`backend/features.md`](backend/features.md) — 业务规则、权限模型、故事树与审核机制
- [`backend/testing.md`](backend/testing.md) — 后端测试组织方式，如何处理 Casdoor mock
- [`backend/casdoor-callback.md`](backend/casdoor-callback.md) — Casdoor Redirect URL 的正确填法

## 前端

- [`frontend/data-layer.md`](frontend/data-layer.md) — feature 层 API 调用、query key 规范
- [`frontend/visual-style.md`](frontend/visual-style.md) — 视觉风格、设计系统语义类
- [`frontend/tree-experience.md`](frontend/tree-experience.md) — 树状阅读视图方案
- [`frontend/discovery-rail.md`](frontend/discovery-rail.md) — 发现栏组件与后端接口契约

## 部署 / 运维

- [`deployment.md`](deployment.md) — **从零开始的部署清单**（GitHub / Casdoor / 服务器 Docker / Nginx + HTTPS）

## 审阅

- [`review/00-overview.md`](review/00-overview.md) — **前端审阅总览（2026-06-02）**：跨册共性主题与落地优先级
- `review/01`~`06` — 按页面/横切分册的详细审阅意见
- [`backend-review/00-overview.md`](backend-review/00-overview.md) — **后端审阅总览（2026-06-02）**：「指标说谎」与前后端协同、优化顺序
- [`backend-review/02-frontend-needs-and-metric-lying.md`](backend-review/02-frontend-needs-and-metric-lying.md) — 前端指标真实/说谎/缺失分类
- [`backend-review/03-backend-core-correctness.md`](backend-review/03-backend-core-correctness.md) — 后端计数完整性、trending、聚合一致性

## 记录

- [`changelog.md`](changelog.md) — 改造记录
- [`followups.md`](followups.md) — **未完成的优化点清单**（代码债、互动功能补全、安全护栏、运维）

## 文档原则

- 优先以当前源码为准，不以历史导出文档为准
- 规则和边界优先，避免写容易过时的实现样例
- SSO 相关：Casdoor 只负责登录鉴别，本站用本地 JWT 做会话鉴权

## 部署说明

快速上手、开发/测试/生产部署见根目录 [`README.md`](../README.md)。
