# 代码评审：互动 / 通知 / 认证 / 用户

评审范围：评论组件、通知页、登录/回调、个人中心、认证 store、interaction/user 数据层、`http.ts`。
评审基准：`docs/frontend/visual-style.md`、`docs/frontend/data-layer.md`、`docs/backend/casdoor-callback.md`、`docs/followups.md`。
评审性质：只读评审，未改动源代码。

---

## 概览

整体认证链路（SSO 登录 → 回调换码 → 本地会话）逻辑清楚，state 防 CSRF、回调参数兜底、登录后角色诊断日志都做得不错；评论与通知已基本收口到 `features/interaction/*` 统一数据层，无限滚动、缓存失效粒度（按 `nodeId` / `notificationsRoot` / `unreadCount`）都符合 data-layer.md 的约定。XSS 方面安全：评论、通知、用户资料全部走 `{{ }}` 插值，未发现任何 `v-html`，无注入面。

主要问题集中在三类：
1. **认证安全与会话健壮性**：token 存 localStorage（XSS 可窃取）、无过期/刷新机制、401 静默登出无跳转无提示、`JSON.parse(localStorage)` 无 try/catch 可致整站白屏。
2. **错误反馈缺口**：`CommentForm` 提交失败完全静默；全局 `handleError` 用 `window.alert`，与"叙事观测终端"冷峻风格严重冲突。
3. **死代码 / 残留**：`http.ts` 误导性 import `useMessage`；两个 misc 页 import 错误组件且未注册 `NButton`；ProfilePage 页面级直写 `authStore.currentUser`（已知残留，现状确认仍在）。

---

## 发现

### 【高】localStorage 中损坏的 user JSON 会让整站启动即崩溃
文件：`frontend/src/stores/auth.ts:35-36`
```ts
const savedUser = localStorage.getItem(USER_KEY)
const currentUser = ref<User | null>(savedUser ? JSON.parse(savedUser) : null)
```
`JSON.parse` 没有 try/catch。一旦 `auth_user` 被写坏（手动篡改、旧版本格式不兼容、写入被打断），store 初始化即抛异常，而 store 又被 router 守卫、http 拦截器、几乎所有页面依赖，结果是整站白屏且用户无法自行恢复（连登出按钮都渲染不出来）。
建议：包一层 try/catch，解析失败时静默清掉 `USER_KEY` 并降级为未登录。

### 【高】401 静默登出，无跳转、无任何用户反馈
文件：`frontend/src/services/http.ts:36-39`
```ts
if (error.response?.status === 401) {
  const authStore = useAuthStore()
  authStore.logout()
}
```
token 过期或失效时只清空状态，但：(1) 不跳转到登录页，用户停留在一个突然"全部 401"的页面上；(2) 没有任何提示，用户不知道自己被登出了；(3) `logout()` 不会触发当前页的重新守卫，`requiresAuth` 页面要等下次导航才会被踢走。
建议：401 时除 `logout()` 外，给一次性提示（如"登录已过期，请重新登录"），并 `router.replace({ name: 'login', query: { redirect: 当前路径 } })`。注意去抖，避免一个页面多请求同时 401 时弹多次。

### 【高】Token 长期存放在 localStorage（XSS 窃取面）
文件：`frontend/src/stores/auth.ts:7,34,46`、`docs/followups.md` 未覆盖此项
`auth_access_token` 持久化在 localStorage，任何 XSS（含三方脚本）都能读取并外带。当前模板全用插值、暂无 `v-html`，注入面较小，但这是结构性安全弱点。
建议（按成本排序）：短期至少在文档里标注风险并确认后端 token TTL 足够短；中期考虑 httpOnly cookie + 后端会话刷新，让前端不直接持有长期 token。属于 followups 未记录的新发现，建议补进安全护栏章节。

### 【高】缺少 token 过期/刷新机制
文件：`frontend/src/stores/auth.ts`（整体）、`frontend/src/services/http.ts`
`exchangeSsoCode` 只保存 `access_token`，没有 refresh token、没有过期时间记录、没有刷新逻辑。用户会在 token 到期的瞬间被动 401（见上一条），中途正在填写的评论/资料表单内容会随登出丢失。
建议：若后端支持刷新，加入静默刷新；若不支持，至少记录 token 过期时间，在临近过期时主动提示并保护未提交的表单数据。

### 【中】CommentForm 提交失败完全静默
文件：`frontend/src/components/interaction/CommentForm.vue:17-28`
```ts
submitComment({ ... }, { onSuccess: (data) => { ... } })
```
只有 `onSuccess`，没有 `onError`。评论失败（网络、被 ban、内容超长、429 限流）时用户没有任何反馈：按钮 loading 结束、输入框内容仍在，看起来像"没点中"，用户会反复重试。配合 followups 3.1 的限流计划，429 会高频出现，这个缺口会更明显。
建议：补 `onError`，用 `useMessage().error(...)` 给出明确原因（复用 `error-handler` 的 `resolveErrorMessage` 提取后端 detail）。

### 【中】全局 handleError 使用 window.alert，违背视觉风格
文件：`frontend/src/utils/error-handler.ts:47-52`，被 `LoginPage.vue:22`、`AuthCallbackPage.vue:45` 调用
```ts
function notifyError(messageText: string) {
  console.error(messageText)
  window.alert(messageText)
}
```
`window.alert` 是浏览器原生模态弹窗，样式无法控制、阻塞交互、带浏览器 chrome，与 visual-style.md 要求的"黑白 / 锐利 / 极简 / 终端感"完全冲突，是登录失败场景下用户看到的第一个反馈。
建议：改用 Naive UI 的 `message` / `notification`（项目其它页已在用 `useMessage`），保持统一的冷峻反馈语言。注意 `useMessage` 是组件内 composable，全局 util 里需要通过 `createDiscreteApi` 或在调用处传入。

### 【中】http.ts 误导性死 import：useMessage
文件：`frontend/src/services/http.ts:3`
```ts
import { useMessage } from 'naive-ui'
```
导入后从未使用。`useMessage` 是只能在 setup/组件上下文调用的 composable，放在纯 service 模块里是个陷阱——后续维护者若真在 401 处调用它会直接报"No outer message provider"。属于 followups.md 提及的"指标说谎/死代码"同类问题。
建议：删除该 import；若要在拦截器里发消息，用 `createDiscreteApi(['message'])`。

### 【中】ProfilePage 页面级直写 authStore.currentUser（数据层残留）
文件：`frontend/src/pages/user/ProfilePage.vue:107,129`
```ts
authStore.currentUser = updatedUser
```
data-layer.md:224 明确把 ProfilePage 标为"页面级直写数据入口"残留——现状确认仍在。问题有二：(1) 直接给 store 的 `currentUser` 赋值绕过了 store 封装；(2) 更新成功后只改了 store，但 `useMyProfileQuery` 的缓存（`userProfile()` key）由 `useUpdateMyProfileMutation` 的 `onSuccess` 失效——也就是说同一份用户数据存在两条更新路径（mutation 失效 query + 页面手动写 store），容易不一致。另外 `updateUser` 走的是 `features/user` 的 mutation，而 `authStore.updateProfile`（auth.ts:155）是另一套同功能的接口，两套并存。
建议：去掉页面里的 `authStore.currentUser = ...`，让 store 通过监听 query 或 mutation 成功回调统一刷新；或收敛到 `authStore.updateProfile` 单一路径。

### 【中】头像上传进度逻辑形同虚设
文件：`frontend/src/pages/user/ProfilePage.vue:91-122,141`
`uploadProgress` 通过 `onProgress` 回调更新，但进度条 `v-if="uploadingAvatar"`（ProfilePage.vue:211）依赖的是 mutation 的 `isPending`，而 `uploadProgress` 初值 0 且上传通常很快返回，进度条往往一闪而过或停在 0。更重要的是：上传成功后 `uploadProgress` 不会被重置，下次打开仍是上次的百分比。
建议：上传开始时显式归零，结束时重置；或直接去掉进度条，用简单 loading 文案（极简风格也更契合）。

### 【中】misc 页 import 了错误组件、未注册 NButton
文件：`frontend/src/pages/misc/NotFoundPage.vue:2`、`frontend/src/pages/misc/ForbiddenPage.vue:2`
```ts
import { NCard, NSpace } from 'naive-ui'
```
两页都 import 了 `NSpace`（模板里没用到）却没 import 模板中实际使用的 `n-button`。当前能渲染只是因为项目用了 Naive UI 全局注册/自动 import 兜底，但 import 列表与实际用法完全对不上，是明显的复制粘贴遗留，且依赖隐式全局注册很脆弱。
建议：删掉未用的 `NSpace`，补上 `NButton`（或确认项目确实全局注册了再统一删 import）。

### 【中】misc 两页使用 emoji 图标，违背风格基调
文件：`frontend/src/pages/misc/NotFoundPage.vue:25`（❌）、`frontend/src/pages/misc/ForbiddenPage.vue:25`（🔐）
visual-style.md 要求黑白、锐利、终端感、避免"社交平台卡片/卡通感"。`text-9xl` 的彩色 emoji 与该基调冲突，且这两页还是裸 `bg-#0a0a0a` + 圆角阴影卡片，没有用上其它页面统一的 `ui-shell-panel` / `ui-page-stack` 设计 token，风格游离。
建议：改用线条/角标/`SIGNAL / 404` 这类终端式排版（通知页空态 `SIGNAL / 00` 是个好范例），并复用统一 shell 容器。

### 【低】回调页 console.info 在生产环境泄露 SSO 细节
文件：`frontend/src/pages/auth/AuthCallbackPage.vue:21-27`
```ts
console.info('[SSO] auth callback page loaded', { href: window.location.href, ... hasCode, hasState })
```
与 auth.ts 里受 `isDev` 守卫的 `devLog` 不同，这条 `console.info` 无条件执行，生产环境会在控制台打印完整回调 URL（含 code/state）。code 是一次性的、state 已校验，敏感度有限，但仍是不必要的信息泄露。
建议：套用 auth.ts 已有的 `isDev` 守卫模式。

### 【低】guestOnly 与 requiresAuth 守卫依赖的 isAuthenticated 只看 token 存在
文件：`frontend/src/router/index.ts:111-133`、`frontend/src/stores/auth.ts:39`
`isAuthenticated = !!accessToken.value`，只判断 token 字符串是否存在，不校验有效性。后果：token 已过期但还在 localStorage 时，`requiresAuth` 守卫放行 → 页面加载 → 接口 401 → 静默登出（且不跳转，见上文）。即"看起来登录成功，实际马上全部失败"。
建议：配合"401 跳转"修复后此问题可缓解；更彻底的做法是在守卫里对关键页面 lazy 校验 `/auth/me`。

### 【低】通知"标记已读"成功提示噪声偏大
文件：`frontend/src/pages/notification/NotificationPage.vue:131-134`
单条标记已读成功后弹 `message.success('通知状态已更新')`。批量场景或快速连点时会刷屏。卡片本身已有 `UNREAD` 状态会立即消失（缓存失效驱动），视觉上已有反馈，success toast 属冗余。
建议：单条已读去掉 success toast，仅保留 onError 提示；"全部已读"保留成功提示即可。

### 【低】CommentList 删除评论无 onError、无二次确认、无乐观反馈
文件：`frontend/src/components/interaction/CommentList.vue:44-46`、`frontend/src/features/interaction/queries.ts:78-88`
`handleDeleteComment` 直接调用 mutate，没有 `onError`（失败静默），没有删除确认对话框（误点即删），删除期间按钮无 loading/禁用，依赖 invalidate 后整列表刷新（删自己的评论时会有可感知延迟）。后端是 soft delete，但前端 UX 上看起来就是硬删。
建议：加 `NPopconfirm` 二次确认 + `onError` 提示 + 删除期间禁用按钮。

### 【低】点赞 mutation 无乐观更新，依赖整树/整节点失效
文件：`frontend/src/features/interaction/queries.ts:20-36`
`useToggleLikeMutation` onSuccess 失效 `storyNode` / `nodeComments`，无 `bookId` 时退回失效整个 `storyTreesRoot()`（与 followups 一致，缓存粒度已收紧到可接受）。但没有乐观更新：点赞后要等请求往返 + 重新拉取，按钮状态才翻转，高频切换时体感卡顿，也更容易触发 followups 3.1 担心的限流。
建议：加 `onMutate` 乐观翻转 like 状态与计数，`onError` 回滚。属增强项，非缺陷。

### 【低】notification 类型筛选在前端做，与服务端分页冲突
文件：`frontend/src/pages/notification/NotificationPage.vue:44-47`
`filteredNotifications` 在已加载页上前端过滤。配合无限滚动：选中"点赞"筛选时，若前 20 条里没有点赞类，列表显示空，用户需手动"加载更多"才可能出现——但 `hasNextPage` 判断的是总数据而非筛选后数据，空态与"加载更多"按钮的组合会让人误以为没有该类通知。
建议：要么把筛选下推到后端接口（加 `type` 参数），要么在筛选结果为空但 `hasNextPage` 为真时给出"当前页无此类，继续加载"提示。

---

## 优先级建议（前 3）

1. **修认证健壮性三连（高）**：`auth.ts:36` 的 `JSON.parse` 加 try/catch（防整站白屏）+ `http.ts:36` 的 401 增加跳转登录页与一次性提示。这三处都是用户可直接撞上的"登录看似正常实则全挂"路径，影响面最大、改动成本低。

2. **补齐互动的错误反馈（中）**：`CommentForm` 加 `onError`、`CommentList` 删除加确认+错误提示、并把全局 `handleError` 的 `window.alert` 换成 Naive UI message。这是 followups 限流落地（429 会变高频）前必须先铺好的反馈底座，否则用户只会看到"点了没反应"。

3. **清理死代码与风格游离（中/低）**：删除 `http.ts` 的 `useMessage` 死 import、修正两个 misc 页的组件 import、把 emoji/裸卡片换成统一 shell + 终端式排版、收敛 ProfilePage 的页面级直写 `authStore.currentUser`。延续上一轮"修指标说谎和死代码"的方向，巩固数据层与视觉的一致性。
