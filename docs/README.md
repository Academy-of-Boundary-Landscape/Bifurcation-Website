# 项目文档

文档统一维护在仓库根目录的 `/docs`，不再以 `backend` 或 `frontend` 目录中的散落文档为准。

## 当前建议阅读顺序

- `backend-overview.md`
  - 后端模块结构、关键文件、认证流和数据边界
- `backend-setup.md`
  - 后端启动方式、环境变量、数据库补列脚本、SSO 联调前准备
- `backend-api.md`
  - 当前 FastAPI 路由总览，重点标出仍在使用、已废弃、以及新增的 SSO 接口
- `backend-features.md`
  - 业务规则、权限模型、故事树与审核机制
- `backend-gap-review.md`
  - 当前后端代码和文档的一致性检查，以及从功能角度看仍然缺少什么
- `casdoor-callback-setup.md`
  - Casdoor 的 `Redirect URL` / callback 该怎么填，以及和本站前端回调页的对应关系
- `casdoor-sso-migration-plan.md`
  - Casdoor 接入背景、迁移策略和后续阶段规划
- `testing-environment-setup.md`
  - 测试环境如何以 `8401` / `5174` 端口启动，以及 Casdoor callback、CORS、前端代理如何对齐
- `backend-testing-guide.md`
  - 后端自动化测试怎么组织，以及测试环境中如何处理 Casdoor 用户与真实 SSO
- `frontend-tree-experience-plan.md`
  - 树状小说前端展示方案草案，说明阅读视图、目录树、图谱视图和后续重构顺序
- `frontend-visual-style-guide.md`
  - 前端视觉风格指导，统一“黑白 + 锐利 + 极简 + 科幻”的界面语言和组件原则
- `frontend-data-layer-guide.md`
  - 前端 API 调用、query key、feature 层职责和当前一致性收口状态说明
- `discovery-rail-contract.md`
  - 发现栏通用组件、榜单/推荐区的前端展示契约，以及后端后续扩展榜单接口时建议遵守的数据结构
- `changelog.md`
  - 本轮整理与改造记录

## 文档原则

- 优先以当前源码为准，而不是历史导出的 OpenAPI 或旧说明
- 对会频繁变动的实现细节，尽量写“规则”和“边界”，少写容易过时的样例
- 对 SSO 相关内容，统一以“Casdoor 只负责登录鉴别，本站继续使用本地 token 做会话鉴权”为准
