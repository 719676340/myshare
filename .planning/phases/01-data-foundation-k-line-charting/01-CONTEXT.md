# Phase 1: Data Foundation + K-Line Charting - Context

**Gathered:** 2026-05-05
**Status:** Ready for planning

<domain>
## Phase Boundary

用户可以通过代码/名称搜索A股股票，在TradingView风格深色主题界面上查看带成交量柱的交互式K线图，叠加MA5/MA10/MA20/MA60均线。图表支持十字光标、缩放、拖拽平移、OHLCV悬浮显示。

</domain>

<decisions>
## Implementation Decisions

### 页面布局与导航
- **D-01:** 单页布局，顶部水平导航栏切换三大模块（策略分析、交易练习、自动回测）
- **D-02:** 股票搜索框放在图表上方工具栏中（非导航栏中），与图表参数控制（周期、指标开关等）同栏
- **D-03:** 初次打开应用时显示引导页，提示用户搜索股票，图表区域显示占位内容

### 股票搜索交互
- **D-04:** 实时自动补全下拉框，输入时即时显示匹配结果
- **D-05:** 搜索结果每行显示：股票代码 + 股票名称（简洁明了）
- **D-06:** 搜索输入 300ms 防抖，减少无效查询
- **D-07:** 选中新股票直接替换当前图表，不保留旧股票

### 图表布局与默认值
- **D-08:** K线图占 75%，成交量柱状图占 25%（上下布局）
- **D-09:** 默认显示最近 120 个交易日数据，用户可通过缩放调整
- **D-10:** MA均线传统配色：MA5=白色、MA10=黄色、MA20=紫色、MA60=绿色
- **D-11:** MA图例显示在K线图左上角，包含线名和当前值

### 数据拉取与缓存
- **D-12:** 首次选择股票时从 tushare 拉取该股票全部历史日K数据，存入 SQLite
- **D-13:** 缓存策略：首次拉取后全部缓存，后续打开直接读本地；显示最后更新时间，用户可手动刷新
- **D-14:** 数据加载时显示进度条，让用户感知加载进度
- **D-15:** tushare API 失败时显示错误提示 + 重试按钮

### Claude's Discretion
- 图表工具栏具体包含哪些按钮（缩放、全屏等）
- 引导页的具体文案和视觉设计
- 进度条的具体样式和精度
- 错误提示的具体措辞
- 深色主题的精确色值（遵循 TradingView 风格即可）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目规划与技术栈
- `CLAUDE.md` — 完整技术栈版本、项目结构、关键决策
- `.planning/PROJECT.md` — 项目愿景、核心价值、约束条件、已确定的关键决策
- `.planning/REQUIREMENTS.md` — 需求清单，Phase 1 涉及：DATA-01, DATA-02, CHART-01~05, INDIC-05
- `.planning/ROADMAP.md` — Phase 1 目标、成功标准、需求映射

### 用户笔记（量价分析理论参考）
- `笔记/第06章_K线图与量价分析.md` — K线图相关理论，理解图表展示需求
- `笔记/第02章_为何成交量如此重要.md` — 成交量展示的理论基础

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 无现有代码 — 这是一个全新项目（greenfield）

### Established Patterns
- 技术栈已确定：Vue 3 + ECharts 6 + FastAPI + SQLite + Element Plus + Pinia
- 所有版本号在 CLAUDE.md 中锁定

### Integration Points
- 前端：Vue Router 路由（三大模块）、Pinia 状态管理（股票数据共享）、vue-echarts 图表组件
- 后端：FastAPI REST API + SQLAlchemy 2.0 + aiosqlite
- 数据：tushare Pro API（需 token）→ SQLite 缓存

</code_context>

<specifics>
## Specific Ideas

- 页面布局参考 TradingView 风格：顶部导航 + 工具栏 + 图表占满主区域
- A股颜色惯例：红涨绿跌（与美股相反）
- 股票列表需预加载到 SQLite 以支持模糊搜索（代码/名称匹配）

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-data-foundation-k-line-charting*
*Context gathered: 2026-05-05*
