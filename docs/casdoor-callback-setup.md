# Casdoor Callback URL 配置

## 1. 先说结论

这个项目当前应该这样配置：

- Casdoor 应用里的 `Redirect URL`
  - 填你网站前端的回调页
  - 生产环境示例：`https://你的前端域名/auth/callback`
  - 本地开发示例：`http://localhost:5173/auth/callback`
- 后端 `.env` 里的 `CASDOOR_REDIRECT_URI`
  - 必须和上面这个 URL 完全一致

如果你的前端和后端分域部署，Casdoor 也应该回到前端，而不是直接回 FastAPI。

原因很简单：当前项目的 OAuth 回调页在前端路由 `/auth/callback`，前端拿到 `code` 和 `state` 之后，再调用后端 `/api/v1/auth/sso/exchange` 去换本站自己的登录态。

## 2. 项目里的实际实现

当前代码里已经固定了这条链路：

1. 前端调用 `/api/v1/auth/sso/login-url`
2. 后端把 `redirect_uri` 设为 `CASDOOR_REDIRECT_URI`
3. Casdoor 登录完成后跳回前端 `/auth/callback`
4. 前端回调页读取 `code` 和 `state`
5. 前端调用 `/api/v1/auth/sso/exchange`
6. 后端校验 Casdoor 身份后，签发本站本地 token

对应代码位置：

- 前端回调路由：`frontend/src/router/index.ts`
- 前端回调页：`frontend/src/pages/auth/AuthCallbackPage.vue`
- 后端登录地址生成：`backend/app/services/sso.py`
- 后端换码接口：`backend/app/api/v1/auth.py`

## 3. Casdoor 后台应该怎么填

在 Casdoor 后台找到你的 Application，然后设置：

- `Redirect URL`
  - 填写你网站的前端回调地址

对这个项目，推荐直接填：

```text
https://你的站点域名/auth/callback
```

如果你还在本地联调：

```text
http://localhost:5173/auth/callback
```

同时在本站后端 `.env` 中填写：

```env
CASDOOR_REDIRECT_URI=https://你的站点域名/auth/callback
```

## 4. 最容易填错的地方

最常见的错误是把两种 callback 混在一起。

### 4.1 Casdoor 回你的网站

这是你现在最关心的配置。

- 配置位置：Casdoor Application 的 `Redirect URL`
- 正确值：你的网站回调页
- 对本项目来说：`https://你的前端域名/auth/callback`

### 4.2 第三方 OAuth 提供商回 Casdoor

如果你的 Casdoor 还接了 GitHub、Google、Gitee 之类的上游登录提供商，它们后台里的授权回调地址，不是你的网站地址，而是 Casdoor 自己的 callback。

对你现在的 Casdoor 域名，应该是：

```text
https://auth.secret-sealing.club/callback
```

也就是说：

- 在 Casdoor Application 里，填你网站的 `/auth/callback`
- 在 GitHub / Google / Gitee 这类提供商后台里，填 `https://auth.secret-sealing.club/callback`

## 5. 推荐的生产配置

如果正式站点前端域名是 `https://www.example.com`，建议这样配：

```env
CASDOOR_BASE_URL=https://auth.secret-sealing.club
CASDOOR_REDIRECT_URI=https://www.example.com/auth/callback
```

Casdoor Application：

```text
Redirect URL = https://www.example.com/auth/callback
```

如果 Casdoor 上游还接了第三方登录：

```text
Provider callback URL = https://auth.secret-sealing.club/callback
```

## 6. 自检清单

出现“登录后跳不回来”或“授权码换 token 失败”时，优先检查：

1. Casdoor Application 的 `Redirect URL` 是否就是前端 `/auth/callback`
2. `CASDOOR_REDIRECT_URI` 是否和 Casdoor 后台完全一致
3. 前端访问域名是否和你填写的绝对 URL 一致
4. 是否错误地把 FastAPI 地址填成了 callback
5. 如果使用 GitHub / Google 等上游登录，是否把它们的 callback 配成了 `https://auth.secret-sealing.club/callback`

## 7. 参考

- Casdoor 官方文档：Application configuration
  - https://casdoor.org/docs/application/config/
