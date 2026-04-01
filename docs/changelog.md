# Changelog

## 2026-03-26

- 新增 `docs/casdoor-sso-migration-plan.md`，审阅后端认证文档与代码，确认当前系统仍是本地 JWT + 本地密码体系。
- 记录 Casdoor SSO 的推荐迁移路线：采用“Casdoor 负责身份认证，本站保留本地用户与本地 JWT”的兼容方案，避免一次性重写全部业务鉴权。
- 标记现有后端认证文档存在过期和与代码不一致的问题，后续登录迁移应以 `/docs` 下文档为准。
- 后端新增 Casdoor SSO 第一阶段骨架：配置项、SSO 服务层、`/api/v1/auth/sso/login-url`、`/api/v1/auth/sso/exchange`，并保持业务接口继续使用本站本地 JWT。
- 本地 `users` 模型新增 SSO 映射字段，`hashed_password` 改为可空，为逐步下线本地密码登录做准备。
- 新增 `backend/scripts/migrate_add_sso_columns.py`，为已有数据库补齐 SSO 映射字段和索引，避免直接查询 `users` 时因缺列报错。
- 删除 `backend` 目录下 `docs/` 之外的旧后端文档与过期接口导出，包括旧版功能清单，避免继续误导后续开发与 SSO 迁移。
- 重写 `/docs` 下的后端文档，补充后端概览、启动配置、当前 API 与业务规则说明，并统一到新的 SSO + 本地会话模型。
- 清理后端旧认证链路：移除本地注册/密码登录/验证码重置 API，删除验证码模型与邮件验证码工具，并把鉴权依赖收口为通用 Bearer 模式。
- 调整 `init_database.py` 为全新库场景：初始化时直接创建绑定 SSO subject 的管理员账号，不再依赖本地密码引导。
- 新增基于 Casdoor claims 的新用户角色初始化规则：可通过 `.env` 配置管理员 claim 和匹配值，在首次创建本地用户时决定是否生成为 `admin`。
- 新增 `docs/casdoor-callback-setup.md`，明确 Casdoor Application `Redirect URL`、本站 `CASDOOR_REDIRECT_URI` 与上游 OAuth Provider callback 的区别，避免回调地址配置混淆。
