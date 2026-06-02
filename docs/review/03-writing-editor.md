# 创作 / 编辑器 / 草稿 —— 前端评审

范围：
- `frontend/src/pages/story/StoryWritePage.vue`
- `frontend/src/components/editor/NodeEditor.vue`
- `frontend/src/components/editor/NodeEditorToolbar.vue`
- `frontend/src/components/editor/NodePreview.vue`
- `frontend/src/components/editor/BranchTypeSelector.vue`
- `frontend/src/components/editor/DraftGuard.vue`
- `frontend/src/features/story/creation.ts`
- `frontend/src/features/story/navigation.ts`
- `frontend/src/utils/validation.ts`
- `frontend/src/utils/storage.ts`

---

## 概览

实际承载创作流程的是 `StoryWritePage.vue`，它是一个自包含的双栏工作台：左栏只读展示 parent 正文、右栏写作表单，顶部 sticky strip 承担草稿状态 / 提交 / 返回。这一页整体质量较高：

- 视觉风格与 `visual-style.md` 的“接入世界线控制面板”定位吻合——mono 字体 strip、`§WRITE` / `NODE-x` 终端语义、直角小圆角、冷色状态点（saving=暖黄、saved=冷绿），符合“黑白 / 锐利 / 极简 / 科幻”。
- 表单与“前文摘要”分区明确，提交区“强而不刺眼”，footnote 给出了 `PEND → PUB` 流程说明，待审状态在落地页 `StoryNodePage.vue:227` 也有对应提示条，端到端的“流程状态感”是完整的。
- 数据层合规：提交走 `useCreateStoryNodeMutation()`（`features/story/queries.ts:108`），失效了 storyTree / storyNode / nodePath / booksRoot，符合 `data-layer.md`，无页面级直写请求。
- 草稿自动保存（debounce 900ms）、恢复确认、`beforeunload` 兜底、提交后清除等核心逻辑都在，数据丢失风险整体可控。

但存在一类比较突出的结构问题：`components/editor/` 下的 **5 个组件全部是死代码**（无任何引用），其中还藏着真正的 bug 与风格违规；同时 `validation.ts` 这套校验工具也从未被创作页消费，实际校验是写作页里另写的一套更弱的内联逻辑。此外 `zone` 字段被硬编码、缺少 SPA 内导航离开守卫，是本轮新发现里需要优先处理的点。

followups 1.6（`top: 64px` magic number）确认仍未修复（`StoryWritePage.vue:586`、`:415` 的 `100vh - 80px` 同属硬编码）。1.4/1.5（草稿扫描）属首页范围，本轮不重复。

---

## 发现

### 【高】editor 目录 5 个组件全部为死代码，且与现行风格/逻辑冲突
- 文件：`components/editor/NodeEditor.vue`、`NodeEditorToolbar.vue`、`NodePreview.vue`、`BranchTypeSelector.vue`、`DraftGuard.vue`（整文件）
- 问题：全仓检索这 5 个组件名（`grep -rn` 排除自身目录）无任何 import/使用，创作页是完全自包含实现。它们不仅是维护负担，还都带着旧风格和缺陷：
  - `NodeEditor.vue:31` 用 `alert('内容不能为空')` 做校验反馈——阻塞式原生弹窗，与 `useMessage` 体系不一致，违反 `visual-style.md` 动效/反馈克制原则。
  - `NodeEditor.vue:43`、`NodePreview.vue:12`、`NodeEditorToolbar.vue:17` 大量硬编码 `bg-#1a1a1a / border-#2a2a2a / text-#666666 / text-yellow-400 / text-red-400`，没有走设计 token（`--bg-*` / `--state-*`），是文档明确要求先统一的“全局 token”反例。
  - `BranchTypeSelector.vue:43` 用蓝/绿高饱和色块（`#3b82f6` / `#10b981`）做区域标签，直接违反“状态色只能少量强调、不要高饱和”。
- 建议：直接删除整个 `components/editor/` 目录（连同 `NodeEditorToolbar` 里未使用的 `NIcon` import、`BranchTypeSelector` 里未使用的 `handleSelect`+`props.modelValue` 双向写法 bug 一并清掉）。若担心未来要复用预览/工具栏，应基于现行 `StoryWritePage` 的 token 体系重写，而不是保留这批旧组件。

### 【高】DraftGuard 的 onBeforeUnmount 里弹原生 confirm —— 即便启用也是错误模式
- 文件：`components/editor/DraftGuard.vue:24-31`
- 问题：在 `onBeforeUnmount` 钩子里调用 `confirm(...)`。`onBeforeUnmount` 在 Vue 中是不可取消的——此时组件已确定要卸载，用户无论点“放弃离开”都无法阻止导航，这个“守卫”名不副实；而且 unmount 阶段同步弹原生模态会卡住卸载流程。同时模板里的 `<n-modal v-model:show="showModal">` 的 `showModal` 永远是 `false`（无处 set true），Modal 形同虚设。该组件即使被启用也无法正确守卫。
- 建议：删除（见上条）。真正需要的“离开未保存”守卫应改用 `onBeforeRouteLeave`（见下条），而不是这种实现。

### 【中】写作页缺少 SPA 内导航离开守卫，依赖隐式自动保存
- 文件：`pages/story/StoryWritePage.vue:204-214, 269-275`
- 问题：只注册了 `beforeunload`（覆盖刷新 / 关页 / 整页跳转）和 `onBeforeUnmount` 时的兜底保存。但在 SPA 内点击导航（比如点顶部 logo、点“返回”以外的链接）离开时，没有 `onBeforeRouteLeave` 守卫，也没有任何“你有未保存内容”的拦截提示。虽然 `onBeforeUnmount` 会触发一次 `saveDraftImmediately()` 兜底，但：用户没有被告知“已自动存草稿”，体验上像“内容丢了”；而真正需要数据丢失防护的恰恰是这种静默导航。
- 建议：用 `onBeforeRouteLeave` 在 `hasMeaningfulDraftContent` 为真且非提交流程时，给一个轻量确认（或至少 `message.info('已自动保存为草稿')`）。注意要排除 `handleSubmit` 成功后的 `router.push`，避免提交后还弹守卫。

### 【中】zone 区域类型被硬编码为 'short'，用户无法选择
- 文件：`pages/story/StoryWritePage.vue:48, 200`
- 问题：`formData.zone` 初始化为 `'short'`，`resetForm()` 也固定回 `'short'`，整页没有任何 UI 让用户切换 `long/short`。但 `StoryNodeCreate.zone` 是必填字段（`types/models.ts:120`），后端语义上 long/short 是有区分的（死代码 `NodeEditor.vue:88` / `BranchTypeSelector` 本来就是为选区域而写）。结果是所有续写节点一律落到 short 区，long 区无法通过 UI 产出。
- 建议：确认产品上 zone 是否仍需用户选择。若需要，在右栏补一个区域选择（沿用现行 token，不要用死代码里的高饱和标签）；若 zone 应由 parent 继承，则应从 `parentNode.zone` 派生而非写死 `'short'`，并在 root 节点给默认。

### 【中】validation.ts 的 validateStoryNode 从未被创作页使用，校验出现两套且不一致
- 文件：`utils/validation.ts:50-73` 对比 `pages/story/StoryWritePage.vue:240-248`
- 问题：`validateStoryNode` 定义了完整规则（content 50~2000、branch_name 2~50 字符），但全仓只有它自己引用（`grep` 确认无页面消费）。写作页 `handleSubmit` 另写了一套更弱的内联校验：只对空正文 `message.error` 阻断，<50 字仅 `message.warning` 但**仍放行提交**，且完全不校验 >2000 字、不校验 branch_name 长度。两套规则不一致，且强规则那套是死的。
- 建议：让写作页统一消费 `validateStoryNode`（或反过来删掉 util、把规则收进写作页），并明确 50 字 / 2000 字是硬约束还是软建议——目前 UI 文案说“建议”、`n-input` 对 content 又没设 `maxlength`，但 util 把 2000 写成 error，三处口径要对齐。content 文本域应根据决策补 `maxlength` 或在超限时禁用提交。

### 【中】恢复草稿用原生 confirm 阻塞 onMounted，且无焦点管理
- 文件：`pages/story/StoryWritePage.vue:173-191`
- 问题：`loadDraft()` 在 `onMounted` 同步调用 `globalThis.confirm(...)`。原生 confirm 会阻塞整个页面渲染线程直到用户响应，首屏体验突兀；与 `visual-style.md` 的克制反馈、终端式 UI 也不搭（其它地方都用 `useMessage` / Naive 组件）。同样地，`handleBeforeUnload` 里 `event.preventDefault()` 触发的是浏览器原生“离开确认”，无法定制文案。
- 建议：草稿恢复改用 Naive 的 `useDialog`（可定制、非阻塞、暗色 token 一致、可做焦点管理）。这也顺带解决可访问性：原生 confirm 没有进入页面后的焦点落点设计，而正文 textarea 理应在无草稿时自动聚焦。

### 【低】sticky / 高度 magic number（followups 1.6 未修 + 新增一处）
- 文件：`pages/story/StoryWritePage.vue:586`（`top: 64px`）、`:587`（`100vh - 64px - 80px`）、`:415`（`100vh - 80px`）
- 问题：左栏 sticky 偏移与高度都基于“顶部 strip 恒为 64px、外层 header 恒为 80px”的假设。strip 本身 `flex-wrap: wrap`（`:442`），窄屏或元数据变多时会换行撑高，sticky 顶部就会错位/被遮挡。followups 1.6 已登记 `top:64px`，本轮确认仍在，且发现 `100vh - 80px` 是同源 magic number。
- 建议：按 followups 建议用 `useElementSize` 测真实高度写入 CSS variable；至少把 64/80 抽成共享 token，避免散落三处各自维护。

### 【低】parentId 解析分支冗余 + 草稿 key 不随登录用户隔离
- 文件：`pages/story/StoryWritePage.vue:22-27, 36-38`
- 问题：(a) `parentId` 解析里 `typeof normalizedValue === 'string' ? Number(...) : Number(...)` 两个分支完全相同，是冗余三元。(b) 草稿 key `story_node_draft:${bookId}:parent:${parent}` 不含用户标识——同一浏览器换账号登录后，会读到上一个账号在同一 parent 下的草稿。共享设备场景下属于轻度数据串台。
- 建议：化简三元；草稿 key 拼上当前 userId（从 auth store 取），并在登出时清理 `bifurcation_*draft*`（`StorageManager.clearAll` 已有，登出流程可复用）。

### 【低】预览缺失（新建链路无独立预览），与死 NodePreview 功能脱节
- 文件：`pages/story/StoryWritePage.vue`（整页）
- 问题：现行写作页没有“预览”能力——正文是纯 `whitespace: pre-wrap` 文本，提交即跳转。死代码 `NodePreview.vue` / `NodeEditorToolbar.vue`（带 preview 事件）本是为此设计但未接入。由于正文不渲染 markdown（落地页 `StoryNodePage` 也是纯文本展示，提交前后一致），预览“保真度”问题当前不严重，但等同于功能缺口。
- 建议：若产品确认正文永远是纯文本，则无需预览，明确删掉死的 NodePreview；若未来要支持 markdown/排版，预览必须与落地页用同一渲染管线以保证保真。

### 【低】双重提交防护与网络错误恢复尚可，但提交期 content 仍可编辑
- 文件：`pages/story/StoryWritePage.vue:240-260, 306-315`
- 问题：双击提交已由 `:disabled="isCreating ..."` 与 `:loading` 防住（`useMutation` 的 `isPending` 串联），空提交也被 `content.trim()` 拦住，错误路径有 `message.error` + 保留草稿（未 clearDraft），这些都正确。小问题是提交 loading 期间正文 textarea 没有 disabled，用户仍可改字，但提交用的是发起时的 `formData.value`（引用），edge case 下提交内容与界面内容可能不一致。
- 建议：提交期间对正文/标题输入做 `:disabled="isCreating"`，让“正在接入世界线”的状态更明确，也避免提交内容与可见内容漂移。

---

## 优先级建议（前 3）

1. **清理 `components/editor/` 整个目录（5 个死组件）+ 收口校验**。这批组件无引用、带 `alert` 阻塞反馈、高饱和违规色、`onBeforeUnmount` 假守卫、双向绑定 bug，留着只会误导后续维护；同时让写作页统一消费 `validation.ts` 或删除该 util，消灭“两套不一致校验”。对应发现【高】×2、【中】（validation）。

2. **补 SPA 内导航离开守卫 + 把 zone 变成真实可控字段**。`onBeforeRouteLeave` 给未保存内容兜底提示，消除“静默离开像丢内容”的体验；同时让 zone 可选或从 parent 继承，避免所有续写都被写死成 short 区。对应发现【中】×2。

3. **把原生 confirm/alert 换成 Naive Dialog/Message，并处理硬编码高度**。草稿恢复改 `useDialog`（非阻塞、token 一致、可做焦点管理），顺带补正文自动聚焦；sticky 的 64/80 用 `useElementSize` 或共享 token 替换，修掉 followups 1.6。对应发现【中】（confirm）、【低】（magic number）。
