# 评审 01 — 首页 / 全局布局 / 发现导航

评审范围：`HomePage.vue`、`DefaultLayout.vue`、`App.vue`、`AppFooter.vue`、`DiscoveryRail.vue`、`DiscoveryNodeCard.vue`、`components/common/*`（PageTitle / EmptyState / ErrorBlock / LoadingBlock / UserAvatar / ConfirmDialog）。
评审基准：`docs/frontend/visual-style.md`、`docs/frontend/data-layer.md`、`uno.config.ts`、`docs/followups.md`。

## 概览

整体方向是对的：首页（HomePage）和 DiscoveryRail / DiscoveryNodeCard / DefaultLayout 已经基本落地了「黑白锐利极简科幻 / 叙事观测终端」的风格——大面积黑底、mono 字体、分区编号（§00–§06）、原子化树状示意图、克制的 fade-up 动效、`prefers-reduced-motion` 兜底都做得不错。数据层方面 HomePage 也确实只组合了 `features/discovery/queries` 的四个 hook，没有散写请求，符合 data-layer.md。

但有一组**明显与风格指南冲突、且属于历史遗留**的问题集中在 `components/common/*` 七个组件和 `AppFooter.vue`：它们仍是早期 emoji + UnoCSS 硬编码色值 + `card-base` 风格，与新的 `styles.css` token 体系完全脱节。好消息是经检索这 7 个组件 + AppFooter **当前没有任何地方 import 使用**（全是死代码），坏消息是它们仍在仓库里、且违反了 visual-style 的多条硬性禁令（emoji、圆角社交卡片、与 token 不一致的配色），一旦有人复用就会破坏风格统一。

下面按主题分组列出发现。

---

## A. 死代码 / 组件复用

### A1.【严重程度: 中】`components/common/*` 七个组件 + `AppFooter.vue` 全部为死代码
- 文件：`components/common/{PageTitle,EmptyState,ErrorBlock,LoadingBlock,UserAvatar,ConfirmDialog}.vue`、`components/common/AppFooter.vue`
- 问题：全仓检索（`grep -rn` 排除自身定义与 `name:` 字段）显示这 8 个组件没有任何 import 引用。`AppFooter.vue` 与 `DefaultLayout.vue` 内联的 `<n-layout-footer>`（第 266–271 行）功能重复，footer 实际渲染走的是 DefaultLayout 那份，`AppFooter.vue` 完全未被挂载。
- 建议：直接删除这 8 个文件；如果计划复用，必须先按 A2 重写到新 token 体系再保留。保留半成品死代码会持续误导后续开发者，并让风格审计失真。

### A2.【严重程度: 高】死代码组件违反 visual-style 多条硬性禁令（若被复用即破坏风格）
- 文件 / 行号：
  - `EmptyState.vue:7`（`<div class="text-6xl mb-4">📖</div>`）、`ErrorBlock.vue:7`（`⚠️`）使用 emoji 大图标——visual-style「不应采用的方向」明确禁止二次元/插画/表情符号式装饰，且与「黑白锐利」冲突。
  - 全部 8 个组件用 UnoCSS 硬编码色值 `bg-#1a1a1a / border-#2a2a2a / text-#666666`（如 `EmptyState.vue:6`、`ErrorBlock.vue:6`、`LoadingBlock.vue:6`、`PageTitle.vue:8`、`AppFooter.vue:6`），与 `App.vue` themeOverrides（`cardColor:#101010`）和 `styles.css` 的 `--line-soft / --bg-shell` token **三套不同的灰**并存，违反 data-layer/视觉 token 单一来源原则。
  - `EmptyState/ErrorBlock` 用 `n-card`（默认 `borderRadius:8px`，见 `App.vue:48`）+ 居中大图标，是典型「圆润 SaaS 空状态卡片」，与节点页/发现页那套 `ui-status-note`（细边框、直角、mono 文案，见 `styles.css:307`）风格不一致。
- 建议：若保留，统一改用 `ui-status-note` / `ui-status-note--danger` 风格（直角 + 细边框 + mono 文案），去掉 emoji，颜色全部走 `var(--…)` token。首页 §05 搜索区已经手写了一套终端风 `STATUS: NO MATCH` 空态（`HomePage.vue:511–522`），可抽象成共享空/错状态组件，反过来淘汰 EmptyState/ErrorBlock。

### A3.【严重程度: 高】`ConfirmDialog.vue:9` 模板插值写在 HTML 属性里，title 永远是字面量
- 文件：`ConfirmDialog.vue:9` — `title="{{ title }}"`
- 问题：Vue 不会解析 attribute 值里的 `{{ }}`，这里 title 会被原样渲染成字符串 `"{{ title }}"`。应是 `:title="title"`。这是一个真实 bug（虽然组件未被使用）。
- 建议：删除该组件（见 A1）；若保留则改为 `:title="title"`。

### A4.【严重程度: 低】`ConfirmDialog.vue` 同时用 `preset="dialog"` 自带按钮 + 自定义 `#action` 插槽，按钮会重复
- 文件：`ConfirmDialog.vue:6–18`
- 问题：`preset="dialog"` 已生成确认/取消按钮，再加 `#action` 插槽会渲染两组按钮。又一个组件从未被验证过的迹象。
- 建议：随 A1 删除，或二选一。

---

## B. HomePage.vue

### B1.【严重程度: 中】§05 搜索无防抖，每次按键都触发查询
- 文件：`HomePage.vue:95–105`、`features/discovery/queries.ts:27–33`
- 问题：`searchKeyword` 直接驱动 `useDiscoverySearchQuery`，query key 随每个字符变化，逐字符发请求（虽有 TanStack 缓存，但无 debounce）。中文输入法组合期间也会触发。
- 建议：用 VueUse `refDebounced(normalizedSearchKeyword, 300)` 作为传给 hook 的 keyword 源；或在 hook 内做 debounce。

### B2.【严重程度: 中】hero telemetry「数字」会误导，且文案与实际语义勉强
- 文件：`HomePage.vue:111–119, 297–312`
- 问题：`totalFeatured/totalLatest/totalTrending` 取的是 `query.length`，被各自 `limit`（4/4/4）截断，并非站点真实总数。代码注释已自承「不是真实总数」，并把标签改成了 `SHOWN · …` 试图缓解，但终端/档案语境下展示 `04 / 04 / 04` 三个被 limit 夹死的等值数字，信息价值近乎为零，反而像「说谎指标」（followups.md §1 刚修过同类问题）。
- 建议：要么后端补 count 接口给真实总数，要么直接移除 telemetry 这一行，避免无意义/误导性数据展示。

### B3.【严重程度: 中】§05 搜索区没有复用 DiscoveryRail，重复实现 loading/empty/error 三态
- 文件：`HomePage.vue:511–534`（手写 loading/error/empty/results）vs `DiscoveryRail.vue:35–50`
- 问题：搜索结果用 `DiscoveryNodeCard` 网格 + 自写三态；而 §01/§02/§04 用 `DiscoveryRail`（内含三态）。同一页两套三态逻辑与样式，违反组件复用。两套空态文案风格也不同（Rail 是中文「暂无…」，搜索是 mono `STATUS: NO MATCH`）。
- 建议：让 DiscoveryRail 支持「自定义终端风三态」或把搜索结果也走 DiscoveryRail；至少把搜索三态抽成共享小组件。

### B4.【严重程度: 低】DiscoveryRail 的 `kicker`/`title` 与外层 `section-divider` 文案重复
- 文件：`HomePage.vue:384–400`（§01 divider 写 `§01 / SELECTION INDEX` + `编辑标记节点`，Rail 又传 `kicker="§01 / Selection index"` + `title="编辑标记节点"`），§02、§04 同样
- 问题：编号与标题在 divider 和 Rail header 各出现一次，视觉上重复，且大小写不一致（`SELECTION INDEX` vs `Selection index`）。
- 建议：二选一展示来源；若保留 divider 做章节锚，则 Rail 不再重复 kicker。

### B5.【严重程度: 低】草稿扫描的两个已知问题仍未修（followups §1.4 / §1.5）
- 文件：`HomePage.vue:36–71`（mount 时全表扫 localStorage）、`onMounted`（只在 mount 跑一次）
- 问题：followups.md 已登记——SPA 内提交/清除草稿后回首页 banner 仍显示旧草稿直到刷新；localStorage 全表遍历。当前仍是这个实现，未改为 `useDraftStore`。
- 建议：按 followups 既定方案做（pinia draft store + `store.refresh()`）。此处仅记录「仍未修」，不重复展开。

### B6.【严重程度: 低】§05 文案「区分大小写不敏感」表述拗口
- 文件：`HomePage.vue:497`
- 问题：「区分大小写不敏感」语义自相矛盾，应为「大小写不敏感」。
- 建议：改为「大小写不敏感；暂不支持作者名搜索」。

### B7.【严重程度: 低】`formatDate` 与 `formatDraftTime` 各写一份日期格式化
- 文件：`HomePage.vue:73–82, 121–125`，另 `todayStamp`（108–109）又内联一份同样的 `YYYY.MM.DD` 拼接
- 问题：同一 `YYYY.MM.DD` 逻辑在本文件出现三处。
- 建议：抽到 `utils/date.ts` 复用（项目其他页大概率也需要）。

---

## C. DefaultLayout.vue

### C1.【严重程度: 中】头像 `n-avatar` 缺少 alt / 无障碍名称
- 文件：`DefaultLayout.vue:229–235`（用户头像 `:src` 无 alt）
- 问题：头像图片没有可访问文本；屏幕阅读器只能读到下拉触发按钮无明确标签。visual-style 之外，可访问性应补。
- 建议：给 `app-user-zone__trigger` 加 `:aria-label="用户菜单 · ${username}"`，头像作纯装饰可 `aria-hidden`。

### C2.【严重程度: 中】「菜单」下拉按钮在桌面端隐藏，移动端才出现，但导航项有限时移动端体验割裂
- 文件：`DefaultLayout.vue:181–190`（菜单触发 `.app-header__menu-trigger { display:none }`，`@media(max-width:960px)` 才 `display:inline-flex`）、`538–557`
- 问题：≤960px 时整个 `app-header__center`（含主导航和 section 状态）被隐藏，仅靠「菜单」下拉；同时 `app-utility-link`（通知/管理台/节点）也 `display:none`。移动端登录用户要看「通知未读数」徽标（`198`）会丢失——徽标只挂在被隐藏的 `app-utility-link` 上，移动端下拉菜单项「通知中心」无未读数显示。
- 建议：移动端下拉的「通知中心」项加未读数，或保留一个常驻的通知图标按钮（带 badge）在移动端 header。

### C3.【严重程度: 低】`<main>` 与 `n-layout` / footer 结构语义可优化，且自定义 footer 与 AppFooter 重复
- 文件：`DefaultLayout.vue:260–271`
- 问题：footer 直接内联在 layout 中（合理），但与死代码 `AppFooter.vue` 形成两份 footer 实现（见 A1）。另外 `currentSectionLabel` 默认值「叙事终端」（`59`）与 footer「Worldline Observation Interface」「分岔视界」品牌名（DefaultLayout `268` / AppFooter `8`）三处英文副标题不完全统一。
- 建议：删 AppFooter；统一品牌副标题文案来源（常量）。

### C4.【严重程度: 低】`app-shell__backdrop` 用了两层 radial/linear 渐变光晕
- 文件：`DefaultLayout.vue:283–291`
- 问题：visual-style 要求「稀疏但精准的光效」「不要大片高饱和光污染」。当前白色 5% radial + 2% linear 很克制，基本可接受，但 `--glow-focus`（`0 0 28px`）用在 nav link hover（`411`）、user trigger hover（`461`）、archive card hover（styles.css `243`）多处叠加，整体「轻微发光」点偏多，接近 visual-style 想克制的方向。
- 建议：保留 backdrop；评估是否把 hover glow 收敛为仅边框增亮（visual-style 对次级控件建议「以边框增亮为主」）。

---

## D. App.vue / 设计 token

### D1.【严重程度: 中】`uno.config.ts:53` 紫色 `accent:#8b5cf6` 仍在 token 表中（与风格冲突的陷阱）
- 文件：`uno.config.ts:53`
- 问题：visual-style 与本次评审任务都点名「`accent:#8b5cf6` 紫色与风格冲突」。经检索该 token 当前未被任何组件用作 `text-accent/bg-accent/...`（无实际引用，属潜在地雷），但留在配置里随时可能被误用，且 uno.config 的 `card-base/bg-card/text-primary` 等 shortcut（`28, 31–41`）与 `styles.css` 的 token 体系、`App.vue` themeOverrides 是**三套并存**的色值来源，违反「设计 token 单一来源」。
- 建议：删除 `accent:#8b5cf6`（或改为中性/冷蓝白选中色 `#e9eef2`，与 styles.css `--accent-focus` 对齐）；长期应将 uno.config 颜色 token 与 `styles.css` CSS 变量收敛为单一来源，避免 `#1a1a1a/#2a2a2a/#101010/--bg-shell` 多套深灰。

### D2.【严重程度: 低】Card 圆角 token 不统一（8px vs 4px vs 2px）
- 文件：`App.vue:27`（`borderRadius:4px`）、`App.vue:48`（`Card.borderRadius:8px`）、`HomePage.vue` 多处按钮 `border-radius:2px`
- 问题：visual-style 要求「卡片小圆角或接近直角」。`Card 8px` 偏圆，与首页 `ui-archive-card`（styles.css 实际用细边框直角风）和 2px 按钮不一致。
- 建议：把 `Card.borderRadius` 降到 4px 或更小，与全局节奏统一。

---

## E. DiscoveryRail.vue / DiscoveryNodeCard.vue

### E1.【严重程度: 中】DiscoveryRail loading 态用 `n-spin` 大转圈，与终端风不符且无骨架
- 文件：`DiscoveryRail.vue:35–37`、`55–59`
- 问题：visual-style 动效关键词是「扫描/锁定/聚焦」，不建议旋转娱乐动画。大 `n-spin` 居中转圈是通用 SaaS loading；首页 §05 搜索 loading 用的是 mono `QUERYING…` 文案（`HomePage.vue:514–516`），两种 loading 风格不一致。
- 建议：Rail 改用占位骨架（细边框灰块）或 mono「LOADING / SCANNING…」状态文案，与搜索区统一。

### E2.【严重程度: 低】DiscoveryNodeCard 命名混用 `ui-archive-card__*` 与 `discovery-node-card__*` 两套前缀
- 文件：`DiscoveryNodeCard.vue:22–66`（结构用全局 `ui-archive-card`/`ui-panel-section`，metrics/hint/actions 又用局部 `discovery-node-card__*`）
- 问题：同一卡片两套 BEM 前缀，metrics/secondary 样式 scoped 在组件里，archive 主体样式在 styles.css。维护时容易找不到样式归属。
- 建议：统一前缀，或把 metrics/hint/actions 也并入 `ui-archive-card__*` 共享样式，便于 BookListPage 等其它档案卡复用。

### E3.【严重程度: 低】DiscoveryNodeCard 主操作 `n-button type="primary"` 在卡片密集时偏「实心填充按钮堆叠」
- 文件：`DiscoveryNodeCard.vue:62`
- 问题：visual-style 卡片建议「次按钮边框优先，不要太多彩色填充按钮」。这里 primary 已被 themeOverrides 改成近白填充（非彩色，尚可），但每张卡一个高对比实心按钮，在 §01/§02/§04 多 rail 多卡时视觉重，接近「社交卡片堆叠」。
- 建议：考虑主操作改边框/幽灵按钮，仅在 hover 或选中卡时强化；与节点页「锁定」语义呼应。

### E4.【严重程度: 低】`DiscoveryRailItem` 的可点击区域仅按钮，整卡不可点
- 文件：`DiscoveryNodeCard.vue:11–18`（仅按钮 `@click` 跳转）
- 问题：档案/清单语境下用户常期望点整卡进入；当前只能点小按钮，移动端命中区域小。
- 建议：把整卡做成可点（保留按钮做次级语义），或加大按钮触达区。注意整卡可点时 secondary「续写」按钮要 `@click.stop`。

---

## 优先级建议（前 3 项）

1. **清理死代码并消除风格地雷（A1 + A2 + A3 + D1）**：删除未被引用的 `components/common/*` 7 个组件与 `AppFooter.vue`（其中 ConfirmDialog 还有 `title="{{ title }}"` 真 bug、含 emoji、含硬编码灰），并删除/中性化 `uno.config.ts` 的紫色 `accent:#8b5cf6`。这一步成本低、直接消除「emoji + 圆角社交卡 + 三套灰 + 紫色」对 visual-style 的硬性违反。

2. **搜索区收口（B1 + B3）**：给 §05 搜索加防抖（300ms），并把搜索结果三态与 DiscoveryRail/共享空错组件统一，消除一页两套三态逻辑与文案风格分裂。

3. **指标与移动端可达性（B2 + C2）**：移除或用真实 count 替换 hero telemetry 的「被 limit 夹死的等值数字」（避免说谎指标）；并修复移动端隐藏 `app-utility-link` 后通知未读数徽标丢失的问题（下拉「通知中心」补 badge 或保留常驻通知图标）。
