# 后端测试说明

## 1. 当前测试策略

后端测试当前优先采用“离线单元测试”：

- 不连接真实 Casdoor
- 不依赖真实数据库服务
- 通过 mock Casdoor 返回的 claims 和 token 交换结果，验证本站自己的用户映射、权限同步和审核逻辑

这样做的目的很明确：

- 测试更稳定
- 本地开发和 CI 都不需要真实 SSO 环境
- 能直接覆盖最关键的业务判断

## 2. 测试环境里的 Casdoor 用户怎么办

答案是：**不要在自动化测试里使用真实 Casdoor 用户。**

自动化测试里应当把 Casdoor 当成“外部身份提供者”，只模拟它最终会给本站后端什么信息，例如：

- `sub`
- `email`
- `roles`

例如管理员场景，只需要在测试里构造：

```python
claims = {
    "sub": "casdoor-admin-001",
    "email": "admin@example.com",
    "roles": ["admin"],
}
```

然后验证：

- 本地用户是否被创建
- 是否映射到正确的 `auth_provider + auth_subject`
- 是否被赋成 `admin`
- `banned` 是否仍然保留为本地控制

## 3. 什么时候才需要真实 Casdoor

真实 Casdoor 更适合放在“手工联调 / 冒烟测试”里，而不是单元测试里。

适合手工联调验证的内容：

- Casdoor Application 的 `Redirect URL` 配置
- `CASDOOR_REDIRECT_URI` 是否一致
- 前端 `/auth/callback` 是否能正确换本站本地 token
- 跨域、回调域名、state、issuer、audience 是否配置正确

## 4. 当前已补的测试重点

目前 `backend/tests/` 已覆盖的重点包括：

- SSO 换码后创建本地用户
- Casdoor 管理员 claim 的角色同步
- `banned` 用户不会被 SSO 自动解封
- 邮箱自动绑定冲突
- 待审核节点的可见性
- 普通用户不能在未发布父节点后续写
- 管理员审核通过时的状态变更与通知发送

## 5. 运行方式

当前可直接在后端虚拟环境里运行：

```bash
cd backend
source venv/bin/activate
python -m unittest discover -s tests -v
```

## 6. SQLite 集成测试

目前 `backend/tests/` 里已经补了一层基于 SQLite 的 HTTP 集成测试。它的目标不是替代 PostgreSQL 真集成，而是先验证这些真实链路：

- FastAPI 路由挂载是否正常
- `Depends(get_db)` 的依赖覆盖是否可靠
- JWT 鉴权是否真的能驱动 `/auth/me`、审核接口等受保护路由
- 评论、点赞、审核这类写操作是否真实落库

实现方式：

- 使用临时 SQLite 文件数据库
- 用同步 SQLAlchemy `Session` 建表和写入测试数据
- 在测试里把同步 session 包装成 async-compatible adapter
- 通过 `app.dependency_overrides[get_db]` 覆盖 FastAPI 默认数据库依赖
- 用 `TestClient` 直接请求真实 `/api/v1/*` 路由

这一层特别适合当前项目，因为它可以绕开当前环境里不稳定的 `aiosqlite`，但依然能把“真正的 HTTP + 真实 SQL 提交”主链路测住。
