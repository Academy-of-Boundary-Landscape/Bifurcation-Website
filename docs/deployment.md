# 部署清单（傻瓜式）

从零开始，把 Bifurcation 部署到生产服务器的完整步骤。**按顺序执行，每一步都验证再进入下一步。**

> 阅读时间约 15 分钟，实际操作 30~60 分钟。
>
> 假设你已经有：
> - 一个域名（本文档以 `bifurcation.secret-sealing.club` 为例，按实际改）
> - 一台 Linux 服务器（root 或 sudo 权限）
> - 一个 GitHub 仓库（含本项目代码）
> - 一个 Casdoor 实例（已部署可访问）

---

## 目录

- [Part A：GitHub 仓库配置](#part-agithub-仓库配置)
- [Part B：Casdoor 配置](#part-bcasdoor-配置)
- [Part C：服务器初始化](#part-c服务器初始化)
- [Part D：首次部署](#part-d首次部署)
- [Part E：Nginx 反向代理 + HTTPS](#part-enginx-反向代理--https)
- [Part F：验证 & 故障排查](#part-f验证--故障排查)

---

## Part A：GitHub 仓库配置

### A.1 创建部署用 SSH 密钥对

**在你的本地电脑**执行：

```bash
ssh-keygen -t ed25519 -C "github-deploy@bifurcation" -f ~/.ssh/bifurcation_deploy -N ""
```

会生成两个文件：

- `~/.ssh/bifurcation_deploy`（私钥，待会儿放进 GitHub Secrets）
- `~/.ssh/bifurcation_deploy.pub`（公钥，待会儿放进服务器）

### A.2 在 GitHub 仓库添加 Secrets

打开 GitHub 仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**，依次添加 3 个：

| Secret 名 | 值 | 说明 |
|---|---|---|
| `DEPLOY_HOST` | 服务器 IP 或域名 | 例如 `123.45.67.89` |
| `DEPLOY_USER` | SSH 登录用户名 | 推荐 `deploy`（下文会创建） |
| `DEPLOY_KEY` | 私钥**全文** | 把 `~/.ssh/bifurcation_deploy` 文件内容（含 `-----BEGIN ... -----END-----`）整个粘贴进去 |

> ⚠️ 私钥要包含开头和结尾的 `-----BEGIN OPENSSH PRIVATE KEY-----` / `-----END OPENSSH PRIVATE KEY-----` 这两行，不要漏。

### A.3 启用 GHCR（GitHub Container Registry）

默认就启用了，无需操作。CI 会用 `${{ secrets.GITHUB_TOKEN }}` 自动登录推送镜像，不用你管。

**唯一要确认的一点**：仓库 → **Settings** → **Actions** → **General** → 滚到底 **Workflow permissions**，选择：

- ✅ **Read and write permissions**（这样 CI 才能推镜像到 GHCR）

---

## Part B：Casdoor 配置

### B.1 添加重定向 URL

Casdoor 管理面板 → **Applications** → 找到你的应用（如 `bifurcation`）→ 编辑：

- **Redirect URLs** 字段填入：
  ```
  https://bifurcation.secret-sealing.club/auth/callback
  ```
- 保存

### B.2 给管理员用户分配 admin 角色

Casdoor 管理面板 → **Roles** → **Add**（如果没有 admin role）：

- **Name**: `admin`
- **Display name**: 管理员
- **Owner**: 你的组织
- 保存

然后 **Users** → 找到你这个管理员账号 → 编辑 → **Roles** 字段添加 `admin` → 保存。

### B.3 记录 Client ID / Secret

回到 **Applications** → 你的应用，记下：

- `Client ID`
- `Client Secret`
- `Organization`
- `Application name`
- Casdoor 自身的 URL（如 `https://auth.secret-sealing.club`）

这些待会儿要写进服务器的 `.env`。

---

## Part C：服务器初始化

### C.1 创建 deploy 用户

**SSH 登录服务器**（用 root 或 sudo），执行：

```bash
# 1. 创建 deploy 用户
sudo useradd -m -s /bin/bash deploy

# 2. 把 deploy 加进 docker 组（先装 Docker 再做这步也行）
sudo usermod -aG docker deploy
```

### C.2 安装公钥

把 [A.1 步骤] 生成的**公钥**装到 deploy 用户：

```bash
sudo mkdir -p /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh

# 把 ~/.ssh/bifurcation_deploy.pub 内容粘贴进去
sudo nano /home/deploy/.ssh/authorized_keys
# 粘贴公钥（一行），保存退出（Ctrl+O Enter Ctrl+X）

sudo chmod 600 /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh
```

### C.3 验证 SSH 能登录

**在你的本地电脑**：

```bash
ssh -i ~/.ssh/bifurcation_deploy deploy@<DEPLOY_HOST>
```

能直接登录、不要密码，即成功。

### C.4 安装 Docker

**切换回 deploy 用户**（如果还没），或在 root 下：

```bash
# 一键脚本（适用 Ubuntu/Debian）
curl -fsSL https://get.docker.com | sudo sh

# 验证
docker --version
docker compose version
```

### C.5 让 deploy 用户能直接用 docker（不用 sudo）

```bash
sudo usermod -aG docker deploy
# 用 deploy 重新登录一次让组生效
exit
ssh -i ~/.ssh/bifurcation_deploy deploy@<DEPLOY_HOST>
docker ps   # 不报权限错误就 OK
```

### C.6 克隆仓库

**以 deploy 身份**：

```bash
cd /home/deploy
git clone https://github.com/<your-github-username>/Bifurcation-Website.git
cd Bifurcation-Website
```

> 如果仓库是 private，得先在服务器配 GitHub deploy key 或用 PAT。最简单做法：把仓库设为 public，或者只 clone 一次手动用 `git pull` 维护。

### C.7 配置 `.env`

```bash
cd /home/deploy/Bifurcation-Website
cp backend/.env.example .env
nano .env
```

**至少要改这些**（其余按需）：

```env
APP_ENV=prod

# 强随机密钥：python -c "import secrets; print(secrets.token_hex(64))" 生成
SECRET_KEY=<粘贴上面命令的输出>

# Docker 模式 host 写 postgres（compose 内部服务名）
DATABASE_URL=postgresql+asyncpg://bifurcation:<PG密码>@postgres:5432/bifurcation_db
PG_PASSWORD=<PG密码>   # 与上面 DATABASE_URL 里的密码一致

CORS_ORIGINS=["https://bifurcation.secret-sealing.club"]

# 来自 Part B
CASDOOR_BASE_URL=https://auth.secret-sealing.club
CASDOOR_CLIENT_ID=<Part B.3 记录的>
CASDOOR_CLIENT_SECRET=<Part B.3 记录的>
CASDOOR_ORGANIZATION_NAME=<Part B.3 记录的>
CASDOOR_APPLICATION_NAME=<Part B.3 记录的>
CASDOOR_REDIRECT_URI=https://bifurcation.secret-sealing.club/auth/callback
CASDOOR_ISSUER=https://auth.secret-sealing.club
CASDOOR_AUDIENCE=<同 CASDOOR_CLIENT_ID>
CASDOOR_SCOPE=openid profile email role roles

SSO_ADMIN_CLAIM_KEYS=roles,role
SSO_ADMIN_MATCH_VALUES=admin,administrator
```

保存退出。

### C.8 创建必要目录并设权限

```bash
mkdir -p backups frontend/dist backend/static/uploads
# 让 docker 容器内的 UID:GID（默认 1000:1000）能写入
sudo chown -R 1000:1000 backend/static/uploads backups
```

---

## Part D：首次部署

### D.1 触发 CI 构建镜像

**在你本地**：

```bash
git add .
git commit -m "chore: enable CI/CD"
git push origin main
```

去 GitHub 仓库 → **Actions** 标签页看 workflow 跑。**第一次 push 会失败**——因为镜像还没构建出来，服务器拉不到。这正常，让它先走完构建步骤把镜像推到 GHCR。

去 GitHub 仓库 → **Packages** 标签页（或个人 profile → Packages）确认 `bifurcation-backend` 镜像出现了。

### D.2 服务器手动拉镜像 + 启动

**SSH 进服务器**，以 deploy 身份：

```bash
cd /home/deploy/Bifurcation-Website

# 公开镜像直接拉，私有镜像需先登录 GHCR：
# echo "<github-PAT>" | docker login ghcr.io -u <your-github-user> --password-stdin

docker compose pull
docker compose up -d

# 看日志，确认起来了
docker compose logs -f backend
```

看到 `[entrypoint] starting uvicorn` 和 `Application startup complete` 就成功了。Ctrl+C 退出 logs。

### D.3 测试后端

```bash
curl http://127.0.0.1:8057/health
# 期望返回：{"status":"ok","service":"Bifurcation"}
```

返回正确即后端 OK。

### D.4 测试 GitHub Actions 自动部署

之后每次 push main，GitHub Actions 会：

1. 构建镜像 → 推 GHCR
2. 构建前端 → 上传产物
3. SSH 到服务器跑 `bash deploy/deploy.sh`（自动 pull + up + 健康检查）
4. rsync 前端 dist 到 `/home/deploy/Bifurcation-Website/frontend/dist/`

随便改个文件 push 一次试试，去 Actions 看是否绿。

---

## Part E：Nginx 反向代理 + HTTPS

### E.1 安装 Nginx + Certbot

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

### E.2 写 nginx 配置

**项目仓库已有模板** `deploy/nginx.conf`，复制并改成你的域名：

```bash
sudo cp /home/deploy/Bifurcation-Website/deploy/nginx.conf /etc/nginx/sites-available/bifurcation
sudo nano /etc/nginx/sites-available/bifurcation
# 把所有 bifurcation.secret-sealing.club 改成你的域名
# 把 root 路径确认指向 /home/deploy/Bifurcation-Website/frontend/dist
```

```bash
sudo ln -s /etc/nginx/sites-available/bifurcation /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t   # 配置语法校验
sudo systemctl reload nginx
```

### E.3 申请 HTTPS 证书

```bash
sudo certbot --nginx -d bifurcation.secret-sealing.club
# 跟着提示走：填邮箱、同意 TOS、是否强制 HTTPS 选 Yes
```

certbot 会自动改 nginx 配置启用 SSL，并设好定时续期。

### E.4 验证 HTTPS

浏览器打开 `https://bifurcation.secret-sealing.club`，应该看到前端页面。

---

## Part F：验证 & 故障排查

### F.1 完整链路测试

1. 浏览器打开 `https://bifurcation.secret-sealing.club`
2. 点击登录 → 跳转到 Casdoor → 用 admin 用户登录
3. 跳转回 callback URL → 进入站内
4. 检查右上角是否显示管理员标识/能进入管理员页面

### F.2 验证管理员同步

服务器看后端日志：

```bash
cd /home/deploy/Bifurcation-Website
docker compose logs backend | grep -i "SSO admin role sync"
```

应该看到类似：

```
SSO admin role sync inspecting claim: key=roles values=['admin']
SSO admin role sync matched admin claim: key=roles value=admin
```

如果是 `SSO admin role sync no match`，看 `available_claim_keys=...` 这一行，对照 `SSO_ADMIN_CLAIM_KEYS` 调整 `.env`。

### F.3 常见问题

| 现象 | 原因 | 解决 |
|------|------|------|
| `docker compose pull` 报 `denied` | 镜像是 private，没登录 GHCR | `echo "<PAT>" \| docker login ghcr.io -u <user> --password-stdin`；或把镜像设为 public（GitHub → Packages → Settings） |
| 健康检查超时 | `.env` 配错了，容器起不来 | `docker compose logs backend` 看具体报错 |
| Casdoor 登录报 "重定向 URI...在许可跳转列表中未找到" | Casdoor 没加白名单 | 重做 Part B.1 |
| 登录成功但不是管理员 | Casdoor 没分配 admin role，或 claim 字段不匹配 | 看 F.2，Part B.2 |
| nginx 502 | 后端没起来，或端口配错 | `curl http://127.0.0.1:8057/health` 排查 |
| GitHub Actions deploy 步骤超时 | SSH 密钥不对，或 `DEPLOY_HOST` 错 | 在本地 `ssh -i ~/.ssh/bifurcation_deploy deploy@<HOST>` 自测 |
| 前端请求 404 | rsync 没把 dist 推上去，或 nginx root 路径错 | `ls /home/deploy/Bifurcation-Website/frontend/dist/`，`sudo nginx -T \| grep root` |
| 前端请求走 localhost | 构建时 `VITE_API_BASE_URL` 被覆盖 | 已在 `http.ts` 硬编码 `/api/v1`，重新 push 触发构建 |

### F.4 常用运维命令

```bash
# 看后端日志
docker compose logs -f backend

# 重启后端（新镜像）
docker compose pull backend && docker compose up -d

# 进容器调试
docker compose exec backend bash

# 进 PG 调试
docker compose exec postgres psql -U bifurcation bifurcation_db

# 手动备份数据库
docker compose exec -T postgres pg_dump -U bifurcation bifurcation_db > backups/manual_$(date +%Y%m%d_%H%M%S).sql

# 看磁盘占用
docker system df
docker compose ps
```

### F.5 回滚到上一个版本

```bash
cd /home/deploy/Bifurcation-Website
# 找上一个镜像 SHA（用 sha 标签的那个）
docker images ghcr.io/<owner>/bifurcation-backend
# 在 docker-compose.yml 里把 :latest 改成 :<上一个 sha>
nano docker-compose.yml
docker compose up -d
```

---

## 附：完成度自检清单

- [ ] GitHub Secrets：`DEPLOY_HOST` / `DEPLOY_USER` / `DEPLOY_KEY` 已加
- [ ] GitHub 仓库 Workflow permissions 设为 Read and write
- [ ] Casdoor Application 的 Redirect URLs 已加
- [ ] Casdoor admin 用户分配了 admin role
- [ ] 服务器创建了 deploy 用户、装好了 SSH key、能本机免密 SSH
- [ ] 服务器装了 Docker + Compose
- [ ] 仓库克隆到 `/home/deploy/Bifurcation-Website`
- [ ] `.env` 在项目根目录，`SECRET_KEY` 是强随机值
- [ ] `docker compose up -d` 正常启动，`/health` 返回 ok
- [ ] Nginx + HTTPS 配置完成
- [ ] push main 触发 Actions，绿色完成
- [ ] 浏览器登录全流程跑通，admin 身份正确同步

全打钩就完事了。
