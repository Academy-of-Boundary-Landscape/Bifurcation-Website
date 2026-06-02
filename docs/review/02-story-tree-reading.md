# 评审 02 · 故事树体验 / 阅读

> 范围：故事树画布、节点卡片、检视器、面包屑/路径、创建确认弹窗、节点正文页、连续阅读页、书册详情（导航台）、书册列表。
> 评审基准：`docs/frontend/visual-style.md`、`docs/frontend/tree-experience.md`、`docs/frontend/data-layer.md`。只读评审，未改动源码。

## 概览

整体方向是对的：`BookDetailPage` 已经按 `tree-experience.md` 演化成「主画布 + 右侧检视器」的导航台，路径降亮（方案 1）和面包屑（方案 2）都有落地，节点卡片走了黑底/细边框/目标框的语言，`StoryCreateConfirmModal`、`StoryTreeInspector`、书册列表等都已经收口到统一的 `ui-shell-*` token 体系，数据层也基本对齐 `features/story/queries.ts`。这几页的「世界线观测台」气质基本成立。

但有两块明显的「半成品 / 风格回潮」：

1. **`StoryNodePage` 的面包屑组件实际没渲染**——`<story-branch-path>` 既没 import 也没全局注册，正文页顶部的「当前位置」路径条是失效的（静默不显示）。这是本轮最实在的功能 bug。
2. **`StoryLineagePage`（连续阅读页）和 `StoryBranchPath`、`StoryTreePanel` 三个文件还停留在旧风格**：紫色 `#8b5cf6`、emoji（👍📖❌）、`ring-purple`、`scale` 弹跳、硬编码 `#1a1a1a/#2a2a2a`，与视觉规范和其余页面完全脱节。连续阅读页恰恰是「正文页应比树图更沉静」的核心承载页，目前却是最花的一页。

另外发现一处生产环境会持续打印的 `console.info`（每次树数据刷新）、节点卡片大量发光阴影与规范「克制发光」的张力、以及若干状态标签 i18n 不一致（直接渲染英文 `status`）。

---

## 发现

### 【严重】StoryNodePage 的面包屑 `story-branch-path` 未注册，正文页路径条静默失效
- `frontend/src/pages/story/StoryNodePage.vue:192` 使用 `<story-branch-path :path="path" />`
- 但该文件 `2-22` 行的 import 里**没有** `StoryBranchPath`，项目 `main.ts:10-16` 也未做全局组件注册，`vite.config` 无 `unplugin-vue-components` 自动导入（已确认 `components.d.ts` 不存在）。
- 结果：Vue 把它当未知元素，运行时只在 console 报 warning，**正文页顶部的「当前位置 / 父链」面包屑根本不渲染**。这直接违背 `tree-experience.md`「正在阅读的用户最怕迷路…当前路径高亮是必须项」。
- 建议：在 `StoryNodePage` 补 `import StoryBranchPath from '@/components/story/StoryBranchPath.vue'`；但见下一条——`StoryBranchPath` 本身风格也要先修。

### 【严重】StoryLineagePage 整页违背视觉规范（紫色 + emoji + 弹跳 + 硬编码色）
- `frontend/src/pages/story/StoryLineagePage.vue`
- 紫色文学链接：`67`（`text-#8b5cf6`）、`84-86`（当前节点 `ring-2 ring-#8b5cf6 scale-[1.02]`）。规范明确「选中=目标锁定（冷白/低饱和蓝白）」「不要紫色泛滥的通用 AI 科技风」。
- emoji 噪声：`122`（`👍 赞`）、`139`（`📖`）。规范「少使用卡通感反馈」「角标/目标框这类界面语言而非插画」。
- 弹跳动效：`84` 的 `scale-[1.02]` + `hover:shadow-lg`，违背「不建议弹跳 / 过厚阴影」。
- 硬编码颜色：`60/85/120` 的 `#1a1a1a/#2a2a2a/#3a3a3a`、`93/108-110` 的 `#666666`、`115` 的 `#d9d9d9`，全部绕开了 `--text-*`/`--line-*`/`ui-shell-*` token。
- 影响最大的点：这是「正文连续阅读页」，规范要求它**比树图页更沉静**，目前却是全站最花的一页。
- 建议：整页迁移到 `ui-shell-panel` / `--text-*` token，去 emoji，当前节点改用 `StoryTreeFlowNode` 同款「目标锁定」描边而非紫环+放大；点赞按钮复用 `StoryNodePage` 已有的 `♥/♡` 心型按钮样式。

### 【严重】StoryBranchPath 组件本身也是旧风格 + 含死代码
- `frontend/src/components/story/StoryBranchPath.vue`
- 紫色：`38/47`（`text-#8b5cf6`）；硬编码：`30`（`#1a1a1a/#2a2a2a`）、`31/64`（`#666666`）；箭头 `→` 直接用文本。与 `BookDetailPage` 已经做好的 `.tree-lineage` 面包屑（`BookDetailPage.vue:324-418`，纯 token、ROOT/L1 等级标签、终端感）是两套审美。
- 死代码：`15-21` 的 `handleCurrentClick()` 是空逻辑（只 `return`），`1` 行 import 了 `NAvatar/NButton/NSpace` 全未使用，`route`/`currentId`（`11-12`）也只服务那个空函数。
- 建议：要么直接复用 `BookDetailPage` 里那套 `.tree-lineage` 样式（最好抽成共享组件，正文页和导航台共用），要么重写本组件对齐 token；清掉未用 import 和空函数。

### 【重要】StoryTreePanel 是死代码且风格陈旧
- `frontend/src/components/story/StoryTreePanel.vue`
- 全仓库已无任何地方引用它（grep `story-tree-panel`/`StoryTreePanel` 仅命中自身定义）。`tree-experience.md:216-217` 说它「可作为后续辅助目录区」，但当前导航台用的是 `StoryTreeFlow`，此组件处于悬空状态。
- 同时它也带旧风格：`64`（`bg-#1a1a1a border-#2a2a2a`）、`67`（`text-white`）、`80`（`text-#666666`），且 `NTree` 用的是 Naive 默认皮肤，与黑白终端风不搭。
- 建议：明确取舍——要么删除（推荐，减少风格回潮入口），要么在做「侧栏目录树筛选」时重写并对齐 token。保留现状只会让后续维护者复制错样式。

### 【重要】生产环境每次树刷新都打印 console.info
- `frontend/src/pages/books/BookDetailPage.vue:112-121`
- `watch(() => tree.value, ...)` 里 `console.info('[StoryTree] tree payload received', {...})` 在每次树数据变化（含缓存刷新、失效重取）时执行，且会 `flattenTree` 整棵树两次（`120` 行又算一遍 `totalNodes`）仅为打日志。
- 建议：删除该调试日志，或包到 `import.meta.env.DEV` 判断里。顺带 `totalNodes`（`53`）已经有计算属性，日志里重复 flatten 是多余开销。

### 【重要】大/深树无虚拟化，全部节点与边都渲染为 DOM/SVG
- `frontend/src/components/story/StoryTreeFlow.vue:421-447`（每个节点一个 `<button>` + 内含 `StoryTreeFlowNode`，含 halo/双 ring/tooltip 多层 DOM）、`395-418`（每条边一个 `<path>` + 一个 `<circle>`，且都挂 `filter="url(#story-flow-edge-glow)"` 高斯模糊）。
- 没有可视区剔除/虚拟化：N 个节点 = N 个带阴影+多层伪元素的 DOM + N 条带模糊滤镜的 SVG path。`tree-experience.md` 把「大树性能」列为第四期目标，但当前每条边都套高斯模糊 filter 会在百节点量级明显掉帧（SVG filter 是已知的性能热点）。
- 另外布局算法 `convertToFlowData`（`74-144`）是递归手写坐标，`tree-experience.md:256-262` 已建议迁 `d3-hierarchy`；当前 `deep: true` 的 `watch(() => props.tree)`（`307-314`）配合 `computed(flowData)` 在大树上每次都会重算整棵布局。
- 建议（短期）：把边的高斯模糊 filter 改为只在 `--on-path` 边上加，或干脆去掉（描边加粗已足够「亮起来」）；（中期）按 `tree-experience.md` 引入 d3-tree + 视口剔除。

### 【重要】节点卡片发光层级偏多，与「克制发光 / 黑底白字细边框」有张力
- `frontend/src/components/story/StoryTreeFlowNode.vue`
- 单个卡片叠了：`__halo` 径向光（`225-231`）+ `__ring--outer/inner` 双环（`258-266`）+ 三档 `likes` 发光阴影（`199-223`，mid/high 都带 `0 0 20~28px rgba(255,255,255,…)` 外发光）+ selected 的 `0 0 32px` 外发光（`167-174`）+ tooltip 的 `backdrop-filter: blur(10px)`（`338`）。
- 规范要求节点卡片「黑底白字细边框」「选中=边框强化+轻量外发光」「不要大面积花哨阴影/玻璃态」。当前「点赞越多越亮」属于把热度做成持续光污染，未选中节点也在发光，削弱了「选中态像目标锁定」的对比。
- 另外用形状（圆/方/六边/菱形）编码状态（`45-50`、`147-161`）信息密度高但缺图例，新读者无法解读；规范倾向「状态用细标签 + 稳定语义」。
- 建议：把 likes 发光收敛为更克制的边框/不发光，保证只有 selected/on-path 才发光；考虑在画布角落加一个小图例说明形状=状态。

### 【重要】状态标签直接渲染英文枚举，i18n 不一致
- 多处直接把 `status` 英文值塞进 UI，而非走已有的中文映射：
  - `frontend/src/components/story/StoryTreeInspector.vue:59`（`selectedNode.status`）
  - `frontend/src/pages/story/StoryNodePage.vue:213`（`{{ node.status }}`）、`258`（admin 区）、`358`（子分支 `{{ child.status }}`）
  - `frontend/src/pages/story/StoryLineagePage.vue:103`（`{{ item.status }}`）
  - `frontend/src/components/story/StoryCreateConfirmModal.vue:79`（`{{ parentNode.status }}`）
- 对比：`StoryTreeFlowNode.vue:23-41` 和 `StoryTreePanel.vue:32-37` 都已有 `published→已发布` 等中文映射函数，但没被复用。结果同一状态在树里是「已发布」、在检视器/正文页是「published」。规范明确「状态标签视觉/语义要稳定，不能今天一套明天一套」。
- 建议：把状态→中文标签抽成 `features/story` 的单一 helper，所有 status 显示统一复用。

### 【重要】节点正文页缺独立错误/空态；详情查询未取 error/isError
- `frontend/src/pages/story/StoryNodePage.vue:31`（`useNodeDetailQuery` 只解构 `data, isLoading`）
- 整页用 `n-spin :show="isLoading"` 包裹，所有内容用 `v-if="node"` 守卫。当节点不存在 / 403（pending 节点对非作者）/ 网络错误时，`node` 为空且 `isLoading=false`，**页面只剩一个空白 spin 容器**，没有任何「节点不存在 / 无权访问 / 加载失败」提示。
- `BookDetailPage.vue:31` 同样只取 `isLoading`，没有 error 分支（书不存在时整页静默空白）。对比 `BookListPage.vue:120-126` 已经做了 `error` + 空态分支，是正面样板。
- 建议：在两页补 `isError`/`error` 与「未找到」空态，至少给一个返回入口。

### 【次要】StoryLineagePage 空态判据会误伤单节点分支
- `frontend/src/pages/story/StoryLineagePage.vue:138`（`v-if="!lineage || lineage.length === 0"` 显示「暂无完整分支」）
- 对一个刚创建、只有根节点的书，lineage 可能长度为 1，此时既不是「无分支」也谈不上「完整阅读」，但文案「该节点尚未形成完整的分支路径」对单节点是成立的边界——只是 `length===0` 与 `length===1` 的体验没区分。需确认后端 lineage 对根节点返回 `[self]` 还是 `[]`；若返回 `[self]` 则当前逻辑会直接进入「阅读区」只渲染一节，文案与高亮（最后一节=当前）尚算合理，但「第 1 节」+ ring 高亮单卡略突兀。
- 建议：单节点时简化为普通正文展示，不加「第 N 节 / ring 高亮」。

### 【次要】画布键盘可达性弱，无方向键导航
- `frontend/src/components/story/StoryTreeFlow.vue:369-447`
- 画布容器是 `<div>` 仅监听 `mousedown`/`wheel`，无 `tabindex`、无键盘平移/缩放。节点本身是 `<button>`（`421-447`）可被 Tab 聚焦并回车选中，这点不错；但：聚焦节点时没有把它居中（`centerOnNode` 只在 `selectedNodeId` 程序变更时触发），Tab 到画布外的节点会聚焦到不可见区域；没有方向键在父/子/兄弟节点间移动。
- 规范虽未强制无障碍，但「世界线观测台」的键盘锁定/聚焦语义本可强化。
- 建议（可延后）：节点 `:focus-visible` 时调用 `centerOnNode`；给画布加方向键在树结构上移动选中。

### 【次要】返回故事树的「自动聚焦」依赖 query，刷新/缩放状态不持久
- `StoryNodePage.vue:220` 和 `StoryLineagePage.vue:52` 用 `query: { focusNodeId }` 返回 `book-detail`，`BookDetailPage.vue:99-107` watch `focusNodeId` 设选中节点，`StoryTreeFlow` watch `selectedNodeId` 调 `centerOnNode`（`316-323`）。链路是通的，符合 `tree-experience.md`「从阅读页返回自动聚焦」。
- 但 `centerOnNode` 用当前 `zoom`（`243`）居中，若用户离开前缩到很小，回来仍很小；且 `watch(() => props.tree, …, {immediate:true})` 会先 `fitView` 再被 `selectedNodeId` 的 watch 覆盖，存在「先 fit 再跳到节点」的一帧抖动。
- 建议：返回聚焦时给一个合理默认 zoom（如 1.0）再 center；或合并两个 watch 避免双重视口写入。

### 【次要】节点详情/路径/子分支查询无 staleTime，频繁来回切换重复请求
- `frontend/src/features/story/queries.ts:40-80`（storyTree/nodePath/nodeDetail/lineage/children 均未设 `staleTime`，全仓库 `main.ts` 也未配置 `VueQueryPlugin` 默认 staleTime=默认 0）
- 结果在导航台 ↔ 正文页频繁往返时，每次进入都触发后台重取。`data-layer.md` 关注的是 key/失效精度（这块已不错），但 staleTime 缺失会放大请求量。
- 建议：给树/详情类查询设一个温和 `staleTime`（如 30s~60s），减少导航抖动重取。

### 【次要】StoryNodePage 删除/确认用原生 confirm，且子分支查询限制 5 条无「查看全部」
- `frontend/src/pages/story/StoryNodePage.vue:142`（`globalThis.confirm`）破坏黑白终端视觉一致性，应改用 `useDialog`（Naive）。
- `33` 行 `useNodeChildrenQuery(nodeId, { limit: 5 })` 只取前 5 个子分支，模板 `332-367` 标题写「子分支（{{ children.length }}）」会在子分支 >5 时显示「子分支（5）」误导真实分歧度，且无分页/「在故事树中查看全部」入口。
- 建议：子分支标题改用真实计数（如 `node.children_count`），并提供「在故事树查看全部分支」链接到 `book-detail?focusNodeId`。

### 【次要】死代码 / 未用 import 零散
- `StoryTreePanel.vue:1` import 了 `NIcon` 未使用；`StoryBranchPath.vue:1` import `NAvatar/NButton/NSpace` 全未使用（见上）；`StoryLineagePage.vue:2` import `NTimeline/NTimelineItem/NDivider` 但模板未用。
- 建议：随上面对应组件重写时一并清理。

---

## 优先级建议（前 3）

1. **修复正文页面包屑 + 统一连续阅读页风格**（合并处理三个旧风格文件）
   - 给 `StoryNodePage` 补 `StoryBranchPath` import 让面包屑真正渲染；
   - 把 `StoryLineagePage`、`StoryBranchPath` 从紫色/emoji/硬编码色全面迁到 `ui-shell-*` + `--text-*` token，去掉 `scale` 弹跳与 `👍📖`，当前节点改用「目标锁定」描边；
   - 最好把 `BookDetailPage` 已有的 `.tree-lineage` 面包屑抽成共享组件，正文页与导航台共用，彻底消灭第二套面包屑审美。

2. **状态标签统一中文映射 + 补错误/空态**
   - 抽一个 `formatNodeStatus(status, is_ending)` helper，替换 Inspector/NodePage/Lineage/ConfirmModal 里所有直出英文 `status`；
   - 给 `StoryNodePage`、`BookDetailPage` 补 `isError`/未找到/无权访问空态（参考 `BookListPage` 的 error 分支），避免静默空白页。

3. **画布性能与发光收敛**
   - 删除 `BookDetailPage` 的 `console.info` 调试日志；
   - 把边的高斯模糊 `filter` 限定到 on-path 边（或移除），节点 likes 发光收敛为仅 selected/on-path 发光，强化「选中=锁定」对比；
   - 中期按 `tree-experience.md` 引入 `d3-hierarchy` 布局 + 视口剔除，为大/深树铺路。
