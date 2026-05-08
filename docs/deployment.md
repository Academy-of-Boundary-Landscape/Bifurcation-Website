# 部署清单（傻瓜式）

从零开始，把 Bifurcation 部署到生产服务器的完整步骤。**按顺序执行，每一步都验证再进入下一步。**

> 阅读时间约 15 分钟，实际操作 30~60 分钟。
>
> 假设你已经有：
> - 一个域名（本文档以 `bifurcation.secret-sealing.club` 为例，按实际改）
> - 一台 Linux 服务器（root 或 sudo 权限）
> - 一个 GitHub 仓库（含本项目代码）
> - 一个 Casdoor 实例（已部署可访问）

每个命令块顶部会标注 **[在哪台机器]** 和 **[什么用户身份]**，避免操作错地方。涉及到的机器有：

- **dev 机器**：你写代码、`git push` 的地方（也可能是这台 Claude Code 所在的机器）
- **生产服务器**：跑 Docker 容器的地方
- **浏览器**：GitHub / Casdoor 后台

---

## 目录

- [概览：三把 SSH key 心智模型](#概览三把-ssh-key-心智模型)
- [Part 1：生产服务器准备](#part-1生产服务器准备)
- [Part 2：浏览器侧配置（GitHub + Casdoor）](#part-2浏览器侧配置github--casdoor)
- [Part 3：写 .env 与首次部署](#part-3写-env-与首次部署)
- [Part 4：Nginx 反向代理 + HTTPS](#part-4nginx-反向代理--https)
- [Part 5：验证 CI 自动部署](#part-5验证-ci-自动部署)
- [Part 6：故障排查与运维](#part-6故障排查与运维)
- [附：完成度自检清单](#附完成度自检清单)

---

## 概览：SSH key 心智模型

整套流程涉及**最多三把不同方向的 SSH key**——但**第三把只在仓库 private 时才需要**：

| key | 私钥在哪 | 公钥在哪 | 干什么 | 哪一步配 |
|---|---|---|---|---|
| **个人 GitHub key** | 你 dev 机器 `~/.ssh/` | 你的 GitHub user 账号 | `git push` 提交代码 | 你早就配好了，本文档不涉及 |
| **GitHub Actions → 生产机** | GitHub Secrets `DEPLOY_KEY` | 生产机 deploy 用户 `~/.ssh/authorized_keys` | runner 跑完构建后 SSH 进生产机执行 `deploy.sh` | [Part 1.4](#14-生成-github-actions--生产机的-ssh-key) → [Part 2.1](#21-在-github-仓库添加-secrets) |
| **生产机 → GitHub**（**仅 private 仓库**） | 生产机 deploy 用户 `~/.ssh/bifurcation_github` | GitHub 仓库 Settings → Deploy keys | 生产机 `git pull` 拉代码 | [Part 1.5](#15-private-仓库才需要配置生产机--github-的-deploy-key) |

> 第一把和第二把是必备的。第三把仅在仓库 private 时需要——public 仓库 `git clone https://...` / `git pull` 都不需要任何认证。

整套流程的全局图：

```
[dev 机器]                      [GitHub]                   [生产服务器]
   |                                |                           |
   | (1) 准备生产机：建用户、装 Docker、                         |
   |     生成 2 把 SSH key、clone 仓库  ───────────────────→     |
   |                                |                           |
   |                          (2) 浏览器：填 Secrets、Casdoor    |
   |                                ↓                           |
   |                                |                           |
   | (3) git push  ───→ Actions 构建镜像推 GHCR ─→ docker pull ─→|
   |                                |                           |
   | (4) 配 nginx + HTTPS  ─────────────────────────────────→   |
   |                                |                           |
   | (5) 测试 CI 自动部署            |                           |
```

---

## Part 1：生产服务器准备

> 这一部分**全部在生产服务器上**完成。SSH 进去之后从头跑到尾，出来时手里会握着两段密钥/公钥，给 Part 2 用。

### 1.1 创建 deploy 用户

**[在生产服务器] [以 root 或 sudo 用户]**

```bash
# 创建 deploy 用户（带 home 目录）
sudo useradd -m -s /bin/bash deploy
```

### 1.2 安装 Docker

**[在生产服务器] [以 root 或 sudo 用户]**

```bash
# Ubuntu/Debian 一键脚本
curl -fsSL https://get.docker.com | sudo sh

# 把 deploy 加进 docker 组（这样不用 sudo 也能 docker）
sudo usermod -aG docker deploy

# 验证
docker --version
docker compose version
```

### 1.3 切到 deploy 用户继续操作

**[在生产服务器]**

```bash
# 切换到 deploy 用户身份。docker 组生效需要重新登录一次
sudo su - deploy

# 验证 docker 不需要 sudo
docker ps
# 报权限错误就 exit 出去再 ssh 重连一次让组生效
```

> 后续 1.x 步骤都以 deploy 用户身份执行，除非另有说明。

### 1.4 生成 "GitHub Actions → 生产机" 的 SSH key

**[在生产服务器] [以 deploy 用户]**

这把 key 让 GitHub Actions 的 runner 能 SSH 进来跑 `deploy.sh`。

```bash
# 1. 生成 key 对（无密码短语）
ssh-keygen -t ed25519 \
    -C "github-actions@bifurcation" \
    -f ~/.ssh/bifurcation_deploy -N ""

# 2. 把公钥追加到 authorized_keys（让带这把私钥的人能 SSH 进来）
cat ~/.ssh/bifurcation_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 3. 输出私钥，等会儿 Part 2.1 要复制到 GitHub Secrets
cat ~/.ssh/bifurcation_deploy
```

把 **私钥整段**（含 `-----BEGIN OPENSSH PRIVATE KEY-----` 和 `-----END OPENSSH PRIVATE KEY-----` 两行）复制到剪贴板**或者临时记下**，Part 2.1 要粘进 GitHub Secrets。

### 1.5 [private 仓库才需要] 配置 "生产机 → GitHub" 的 Deploy Key

> **如果你的仓库是 public，跳过这一节直接看 [1.6](#16-clone-仓库到-deploy-用户家目录)。**
>
> 仓库是 private 才需要这把 key——让生产机能 `git pull` 拉本仓库的代码。它跟 1.4 那把方向**完全相反**：1.4 让 GitHub 进生产机，这把让生产机进 GitHub。一个仓库一把 key，权限只读，最小化暴露面。

**[在生产服务器] [以 deploy 用户]**

```bash
# 1. 生成另一把 key
ssh-keygen -t ed25519 \
    -C "github-deploy@bifurcation-prod" \
    -f ~/.ssh/bifurcation_github -N ""

# 2. 配置 SSH alias，让 git 拉这个仓库时自动用这把 key
# 用 github-bifurcation 别名跟其他仓库的 deploy key 隔离
cat >> ~/.ssh/config <<'EOF'

Host github-bifurcation
    HostName github.com
    User git
    IdentityFile ~/.ssh/bifurcation_github
    IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config

# 3. 输出公钥，等会儿 Part 2.2 要粘到仓库 Deploy keys
cat ~/.ssh/bifurcation_github.pub
```

记下这段公钥（一行，通常以 `ssh-ed25519 ...` 开头）。

### 1.6 clone 仓库到 deploy 用户家目录

**[在生产服务器] [以 deploy 用户]**

根据仓库可见性二选一：

**A) 仓库 public**：用 **HTTPS URL** clone，无需认证：

```bash
cd /home/deploy

# ⚠️ 必须是 https://github.com/... 不能是 git@github.com:...
# 后者是 SSH URL，就算仓库 public 也要 SSH key 认证
git clone https://github.com/<your-github-username>/Bifurcation-Website.git
cd Bifurcation-Website
git pull   # 验证能拉
```

> GitHub 仓库页面默认复制的是 SSH URL。点页面上 **HTTPS** 那个 tab 切换一下，再复制。

**B) 仓库 private**：先做完 [Part 2.2](#22-private-仓库才需要-把生产机公钥挂到仓库-deploy-keys) 把公钥挂到 GitHub，再回来这里 clone：

```bash
cd /home/deploy

# URL 用 1.5 配的 SSH 别名 github-bifurcation: 而不是 github.com:
git clone github-bifurcation:<your-github-username>/Bifurcation-Website.git
cd Bifurcation-Website
git pull   # 验证能拉
```

clone 失败说明 1.5 的 SSH config 或 2.2 的 Deploy key 哪里没配对，回头查。

### 1.7 创建运行时目录 + 修正所有权

**[在生产服务器] [以 deploy 用户]**

```bash
cd /home/deploy/Bifurcation-Website
mkdir -p backups frontend/dist backend/static/uploads
```

**[在生产服务器] [以 root 或 sudo 用户]**

如果你前面是用 root 或别的用户 clone 的仓库，**整个项目目录的所有权都得交给 deploy**——否则 CI rsync 推前端 dist 时会报 `Permission denied`：

```bash
# 把整个项目目录的所有权归还给 deploy
sudo chown -R deploy:deploy /home/deploy/Bifurcation-Website

# docker 容器内进程默认以 UID:GID 1000:1000 跑，
# deploy 用户通常就是 1000:1000，所以上面那行已够。
# 如果 deploy 不是 1000:1000（id deploy 自查），再单独 chown：
# sudo chown -R 1000:1000 backend/static/uploads backups
```

> 验证：`ls -la /home/deploy/Bifurcation-Website` 第一列里所有项的 owner 都应该是 `deploy`，不是 `root`。

完成 Part 1 之后，你应该手里有：
- ✅ 生产机 `~/.ssh/bifurcation_deploy`（私钥，要给 GitHub Secrets）
- ✅ 生产机 `~/.ssh/bifurcation_github.pub`（公钥，要给 GitHub Deploy keys）
- ✅ Docker 装好了
- ✅ 仓库准备 clone（Part 2.2 之后）

---

## Part 2：浏览器侧配置（GitHub + Casdoor）

> 全部在浏览器里完成，没有命令。

### 2.1 在 GitHub 仓库添加 Secrets

**[浏览器]** 打开仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**，添加 3 个：

| Secret 名 | 值 |
|---|---|
| `DEPLOY_HOST` | 生产服务器 IP 或域名（如 `123.45.67.89`） |
| `DEPLOY_USER` | `deploy` |
| `DEPLOY_KEY` | Part 1.4 第 3 步 `cat` 出来的**整段私钥**（含 `-----BEGIN .. -----END-----` 两行） |

> ⚠️ 私钥的开头和结尾两行必须包含，否则 GitHub Actions 会报 "Error loading key"。

### 2.2 [private 仓库才需要] 把生产机公钥挂到仓库 Deploy keys

> **public 仓库跳过。** 这一步是给 [Part 1.5](#15-private-仓库才需要-配置生产机--github-的-deploy-key) 那把 key 在 GitHub 端授权用的。

**[浏览器]** 打开仓库 → **Settings** → **Deploy keys** → **Add deploy key**：

- **Title**：`prod-server`（任何能识别身份的名字）
- **Key**：粘贴 Part 1.5 第 3 步 `cat` 出来的**整段公钥**
- **Allow write access**：⚠️ **不要勾**（生产机只 pull 不 push）
- 点 **Add key**

加完之后回到 [Part 1.6](#16-clone-仓库到-deploy-用户家目录) 完成 clone。

### 2.3 开启 Workflow 的写权限（让 CI 推镜像）

**[浏览器]** 仓库 → **Settings** → **Actions** → **General** → 滚到底部 **Workflow permissions**：

- ✅ 选 **Read and write permissions**
- 保存

> 这是为了让 CI 用 `${{ secrets.GITHUB_TOKEN }}` 把镜像推到 GHCR（GitHub Container Registry）。不开就推不上去。

### 2.4 Casdoor：添加 Redirect URL

**[浏览器]** Casdoor 管理面板 → **Applications** → 找到本应用（如 `bifurcation`）→ 编辑：

- **Redirect URLs** 字段添加：
  ```
  https://bifurcation.secret-sealing.club/auth/callback
  ```
- 保存

### 2.5 Casdoor：给管理员用户分配 admin 角色

**[浏览器]** Casdoor 管理面板 → **Roles**（如果没有 admin role）→ **Add**：

- **Name**: `admin`
- **Display name**: 管理员
- **Owner**: 你的组织
- 保存

然后 **Users** → 找到管理员账号 → 编辑 → **Roles** 字段添加 `admin` → 保存。

### 2.6 Casdoor：记下连接信息

**[浏览器]** 回 **Applications** → 你的应用，复制下面这些值，等下写 `.env` 用：

- `Client ID`
- `Client Secret`
- `Organization`
- `Application name`
- Casdoor 自身 URL（如 `https://auth.secret-sealing.club`）

---

## Part 3：写 .env 与首次部署

> 这一部分回到生产服务器。前提：Part 1.6 的 `git clone` 已经完成。

### 3.1 写 .env

**[在生产服务器] [以 deploy 用户]**

```bash
cd /home/deploy/Bifurcation-Website
cp backend/.env.example .env

# 生成强随机 SECRET_KEY，复制输出待会儿粘进 .env
python3 -c "import secrets; print(secrets.token_hex(64))"

nano .env
```

**最少要改这些字段**（Casdoor 系列的值来自 [Part 2.6](#26-casdoor记下连接信息)）：

```env
APP_ENV=prod

# 上面 python 命令的输出
SECRET_KEY=<刚生成的 64 字节十六进制>

# Docker 模式 host 必须是 postgres（compose 内部服务名）
DATABASE_URL=postgresql+asyncpg://bifurcation:<你定义的PG密码>@postgres:5432/bifurcation_db
PG_PASSWORD=<上面 DATABASE_URL 里的同一个密码>

CORS_ORIGINS=https://bifurcation.secret-sealing.club

CASDOOR_BASE_URL=https://auth.secret-sealing.club
CASDOOR_CLIENT_ID=<Part 2.6 复制的>
CASDOOR_CLIENT_SECRET=<Part 2.6 复制的>
CASDOOR_ORGANIZATION_NAME=<Part 2.6 复制的>
CASDOOR_APPLICATION_NAME=<Part 2.6 复制的>
CASDOOR_REDIRECT_URI=https://bifurcation.secret-sealing.club/auth/callback
CASDOOR_ISSUER=https://auth.secret-sealing.club
CASDOOR_AUDIENCE=<同 CASDOOR_CLIENT_ID>
CASDOOR_SCOPE=openid profile email role roles

SSO_ADMIN_CLAIM_KEYS=roles,role
SSO_ADMIN_MATCH_VALUES=admin,administrator
```

保存退出（Ctrl+O Enter Ctrl+X）。

> ⚠️ **注意**：`.env` 必须在**项目根目录**（`/home/deploy/Bifurcation-Website/.env`），不是 `backend/.env`——docker-compose 是从根目录读这个文件的。

### 3.2 dev 机器：commit 并 push

**[在 dev 机器] [以你自己的 GitHub 身份]**

回到 dev 机器（这台 Claude Code 所在的机器，或者你写代码的笔记本）：

```bash
cd /data/sunyunbo/www/Bifurcation-Website   # 按实际路径

# 如果有未提交的改动，commit 一下
git status
git push origin main
```

去 GitHub 仓库 → **Actions** 看 workflow 跑：

- `backend` job：编译检查 + 构建 Docker 镜像 + 推 GHCR ← **这一步必须绿**
- `frontend` job：type check + 构建 + 上传 dist 产物 ← 绿
- `deploy` job：rsync 前端 + SSH 进生产机跑 `deploy.sh` ← **可能红**，下面解释

`deploy` 红了不要慌——这是首次部署，生产机上还没跑过任何 docker 容器，可能撞到这些点：
- 镜像默认在 GHCR 是 private，生产机 docker 没登录
- 或者生产机本地代码版本还没追上 main

我们下一步**手动**首次部署，跑通之后 CI 才能接管。

> 验证镜像确实推到 GHCR 了：仓库 → 右侧 **Packages** 区域，应该能看到 `bifurcation-backend`。

### 3.3 GHCR 镜像可见性（二选一）

GHCR 默认 private，生产机要拉镜像需要先登录。两条路：

**选项 A（推荐）：把镜像设为 public**

**[浏览器]** 你的 GitHub Profile → **Packages** → `bifurcation-backend` → **Package settings** → 滚到底 **Change visibility** → 选 **Public** → 输入包名确认 → 保存。

镜像本来就是无密资源，public 没风险。

**选项 B：生产机登录 GHCR**

如果就是想保持 private，需要在生产机用一个有 read:packages 权限的 PAT 登录：

**[在生产服务器] [以 deploy 用户]**

```bash
# 先在浏览器去 GitHub Settings → Developer settings → Personal access tokens
# → Generate new token (classic) → 勾 read:packages → 生成
echo "<刚生成的 PAT>" | docker login ghcr.io -u <你的 GitHub 用户名> --password-stdin
```

### 3.4 服务器手动首次部署

**[在生产服务器] [以 deploy 用户]**

```bash
cd /home/deploy/Bifurcation-Website

# 把 Part 3.2 push 的最新代码拉下来（包括 docker-compose.yml、deploy.sh）
git pull origin main

# 拉镜像
docker compose pull

# 启动所有服务（postgres + backend）
docker compose up -d

# 看后端启动日志
docker compose logs -f backend
```

应该看到：

```
[entrypoint] running auto_migrate...
[entrypoint] auto_migrate succeeded (attempt 1)
[entrypoint] starting uvicorn...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8057
```

Ctrl+C 退出 logs。

### 3.5 验证后端

**[在生产服务器] [以 deploy 用户]**

```bash
curl http://127.0.0.1:8057/health
# 期望返回：{"status":"ok","service":"Bifurcation"}
```

返回正确就说明后端起来了。**这时只是端口通了，还没接 nginx 也没 HTTPS**——下一步配。

---

## Part 4：Nginx 反向代理 + HTTPS

### 4.1 装 Nginx + Certbot

**[在生产服务器] [以 root 或 sudo 用户]**

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

### 4.2 写 nginx 配置

**[在生产服务器] [以 root 或 sudo 用户]**

仓库自带模板 `deploy/nginx.conf`，复制改域名：

```bash
sudo cp /home/deploy/Bifurcation-Website/deploy/nginx.conf \
        /etc/nginx/sites-available/bifurcation

sudo nano /etc/nginx/sites-available/bifurcation
# 把所有 bifurcation.secret-sealing.club 改成你的实际域名
# 确认 root 路径指向 /home/deploy/Bifurcation-Website/frontend/dist
```

启用：

```bash
sudo ln -s /etc/nginx/sites-available/bifurcation /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t   # 配置语法校验
sudo systemctl reload nginx
```

### 4.3 申请 HTTPS 证书

**[在生产服务器] [以 root 或 sudo 用户]**

```bash
sudo certbot --nginx -d bifurcation.secret-sealing.club
# 提示：填邮箱、同意 TOS、是否强制 HTTPS 选 Yes
```

certbot 会自动改 nginx 配置启用 SSL，并设好定时续期（无需手动 cron）。

### 4.4 验证 HTTPS

**[浏览器]** 打开 `https://bifurcation.secret-sealing.club`，应该看到前端页面。

但此时前端 `dist/` 目录还是空的（因为 CI 的 deploy 步骤刚才失败了）。手动从仓库 build 也行，但更省事的是直接走下一步——让 CI 自动部署一次。

---

## Part 5：验证 CI 自动部署

到这里所有的"配置"都做完了，剩下就是把 CI 自动化跑通。

### 5.1 触发一次自动部署

**[在 dev 机器]**

随便改个文件 push 一次（比如 `docs/deployment.md` 加个空格也行）：

```bash
git commit --allow-empty -m "ci: trigger first auto deploy"
git push origin main
```

### 5.2 看 Actions 跑通

**[浏览器]** 仓库 → **Actions**：

- `backend` job → ✅ 绿
- `frontend` job → ✅ 绿
- `deploy` job：
  - rsync frontend → 把 dist 推到 `/home/deploy/Bifurcation-Website/frontend/dist/`
  - SSH 进生产机跑 `deploy.sh`：备份 PG → pull 新镜像 → up -d → 健康检查
  - 远程 `curl /health` 通过

全绿就成功了。

### 5.3 浏览器全流程验证

**[浏览器]** 打开 `https://bifurcation.secret-sealing.club`：

1. 看到前端页面（说明 nginx + dist 都对了）
2. 点登录 → 跳到 Casdoor → 用管理员账号登录
3. 跳回 callback → 进入站内
4. 检查能否进入管理员页面/看到管理员标识

如果"登录成功但不是管理员"，看 [Part 6.1](#61-验证管理员同步) 排查。

---

## Part 6：故障排查与运维

### 6.1 验证管理员同步

**[在生产服务器] [以 deploy 用户]**

```bash
cd /home/deploy/Bifurcation-Website
docker compose logs backend | grep -i "SSO admin role sync"
```

应该看到：

```
SSO admin role sync inspecting claim: key=roles values=['admin']
SSO admin role sync matched admin claim: key=roles value=admin
```

如果看到的是 `SSO admin role sync no match`，看 `available_claim_keys=...` 那一行——它列出了 Casdoor 实际返回了哪些 claim 字段。对照 `.env` 里的 `SSO_ADMIN_CLAIM_KEYS` 调整。

### 6.2 常见问题排查表

| 现象 | 原因 | 解决 |
|---|---|---|
| `docker compose pull` 报 `denied` | GHCR 镜像 private，生产机没登录 | [Part 3.3](#33-ghcr-镜像可见性二选一) 选 A 或 B |
| 健康检查超时 / 容器反复重启 | `.env` 配错（DB 密码、Casdoor 必填项缺失） | `docker compose logs backend` 看具体报错 |
| Casdoor 登录报"重定向 URI...在许可跳转列表中未找到" | Casdoor 没加 redirect URL | 重做 [Part 2.4](#24-casdoor添加-redirect-url) |
| 登录成功但不是管理员 | Casdoor 用户没分配 admin role，或 claim 字段不匹配 | 看 [6.1](#61-验证管理员同步) + [Part 2.5](#25-casdoor给管理员用户分配-admin-角色) |
| nginx 502 | 后端没起来 | 服务器跑 `curl http://127.0.0.1:8057/health`，再看 `docker compose logs backend` |
| GitHub Actions deploy 步骤超时 | `DEPLOY_HOST` / `DEPLOY_KEY` 配错 | 在生产机本地 `ssh -i ~/.ssh/bifurcation_deploy deploy@127.0.0.1` 自测；或检查 GitHub Secrets 私钥粘贴是否完整 |
| 前端请求 404 | rsync 没推上去，或 nginx root 路径错 | `ls /home/deploy/Bifurcation-Website/frontend/dist/`；`sudo nginx -T \| grep root` |
| Actions deploy 步骤 rsync 报 `Permission denied (13)` / `Operation not permitted` | 项目目录是 root（或其他用户）clone 的，deploy 不是 owner | `sudo chown -R deploy:deploy /home/deploy/Bifurcation-Website` |
| Actions deploy 报 `git@github.com: Permission denied (publickey)` 后接 `bash: deploy/deploy.sh: No such file or directory` | 仓库是 public 但用 SSH URL clone 的，deploy 用户没 GitHub 认证 | `git remote set-url origin https://github.com/<owner>/<repo>.git` |
| 前端请求走 localhost:8057 而非相对路径 | 构建时 `VITE_API_BASE_URL` 被注入 | 仓库 `frontend/src/services/http.ts` 已硬编码 `/api/v1`，重新 push 触发构建 |
| `git pull` 在生产机上报 permission denied | 生产机没用别名 `github-bifurcation:` clone，或 Deploy key 公钥粘错 | 重做 [Part 1.5](#15-配置生产机--github-的-deploy-key) + [Part 2.2](#22-把生产机公钥挂到仓库-deploy-keys) |

### 6.3 常用运维命令

**[在生产服务器] [以 deploy 用户]**

```bash
cd /home/deploy/Bifurcation-Website

# 看后端实时日志
docker compose logs -f backend

# 手动拉新镜像 + 滚动重启（一般不需要，CI 会做）
docker compose pull backend && docker compose up -d

# 进容器调试
docker compose exec backend bash

# 进 PG 调试
docker compose exec postgres psql -U bifurcation bifurcation_db

# 手动备份数据库
docker compose exec -T postgres pg_dump -U bifurcation bifurcation_db \
    > backups/manual_$(date +%Y%m%d_%H%M%S).sql

# 看磁盘 / 容器状态
docker compose ps
docker system df
```

### 6.4 回滚到上一个版本

CI 每次部署都会推一个带 commit SHA 的镜像 tag（如 `bifurcation-backend:a1b2c3d`），出问题了可以回滚：

**[在生产服务器] [以 deploy 用户]**

```bash
# 1. 查可用镜像
docker images ghcr.io/<owner>/bifurcation-backend

# 2. 编辑 docker-compose.yml，把 image 行的 :latest 改成 :<上一个 sha>
nano docker-compose.yml

# 3. 应用
docker compose up -d
```

---

## 附：完成度自检清单

按顺序勾选，全部勾完就部署完了：

**Part 1（生产服务器）**
- [ ] deploy 用户已创建
- [ ] Docker + Compose 装好，`docker ps` 不需要 sudo
- [ ] 生成 `~/.ssh/bifurcation_deploy`（GitHub Actions → 生产机）
- [ ] 公钥追加到 `~/.ssh/authorized_keys`
- [ ] **[private 仓库]** 生成 `~/.ssh/bifurcation_github`（生产机 → GitHub）
- [ ] **[private 仓库]** `~/.ssh/config` 里加了 `github-bifurcation` 别名
- [ ] 仓库 clone 到 `/home/deploy/Bifurcation-Website`，`git pull` 跑通（public 用 HTTPS / private 用别名）
- [ ] 创建了 `backups/` `frontend/dist/` `backend/static/uploads/`

**Part 2（浏览器）**
- [ ] GitHub Secrets：`DEPLOY_HOST` / `DEPLOY_USER` / `DEPLOY_KEY` 加齐
- [ ] **[private 仓库]** Deploy keys 里挂了生产机的公钥（不勾 write）
- [ ] GitHub Actions Workflow permissions 设为 Read and write
- [ ] Casdoor Application 加了 redirect URL
- [ ] Casdoor 管理员用户分配了 admin role
- [ ] 记下了 Casdoor 的 Client ID / Secret / Org / App / URL

**Part 3（首次部署）**
- [ ] `.env` 在项目根目录 `/home/deploy/Bifurcation-Website/.env`
- [ ] `SECRET_KEY` 是 64 字节强随机十六进制
- [ ] `DATABASE_URL` host 是 `postgres`（不是 `localhost`）
- [ ] `PG_PASSWORD` 跟 `DATABASE_URL` 里的密码一致
- [ ] GHCR 镜像设为 public 或生产机已 `docker login ghcr.io`
- [ ] `docker compose up -d` 起来，`/health` 返回 ok

**Part 4（Nginx + HTTPS）**
- [ ] nginx 配置启用，`nginx -t` 通过
- [ ] certbot 签发了 Let's Encrypt 证书
- [ ] 浏览器打开 `https://<域名>` 看到前端

**Part 5（自动化）**
- [ ] 一次空 commit push 到 main
- [ ] Actions 三个 job 全绿
- [ ] 浏览器登录全流程跑通，admin 身份正确同步

全打钩就完事了。
