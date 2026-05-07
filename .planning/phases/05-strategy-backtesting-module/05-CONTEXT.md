# Phase 5: Strategy Backtesting Module - Context

**Gathered:** 2026-05-07
**Status:** Ready for planning

<domain>
## Phase Boundary

用户通过自定义指标构建器创建指标表达式，用嵌套条件组（AND/OR）定义买入和卖出规则，对选定股票和时间范围运行自动回测。系统执行回测、计算绩效指标、展示资金曲线和K线买卖标记。

**范围扩展说明：** 原定 BACK-01（预设策略模板+调参）已扩展为「自定义指标构建+条件组合回测」。DATA-05（自定义指标构建器）从 v2 提前纳入本阶段。预设策略模板保留为快速开始选项。

</domain>

<decisions>
## Implementation Decisions

### 自定义指标构建器
- **D-01:** 用户通过文本输入框输入指标表达式，如 `VOL/MA(VOL,20)` 或 `CLOSE-MA(CLOSE,10)`。系统解析表达式并计算每日指标值
- **D-02:** 表达式支持的基础字段：OPEN、HIGH、LOW、CLOSE、VOL、AMOUNT、PRE_CLOSE、CHANGE_PCT
- **D-03:** 表达式支持的函数：MA(field, period)、EMA(field, period)、STD(field, period)、MAX(field, period)、MIN(field, period)、REF(field, n)（n日前值）、CROSS(field1, field2)（上穿判断）
- **D-04:** 表达式支持四则运算：+、-、*、/，以及括号组合

### 条件组合器
- **D-05:** 买入规则和卖出规则各一组条件，条件之间用嵌套 AND/OR 组合
- **D-06:** 每个条件项：选择指标（自定义指标或基础指标）+ 运算符 + 阈值/另一个指标
- **D-07:** 运算符集（10+）：大于（>）、小于（<）、大于等于（>=）、小于等于（<=）、等于（==）、上穿（golden cross）、下穿（death cross）、从上跌破（break below）、从下突破（break above）、进入超买区、进入超卖区
- **D-08:** 无内置止损止盈规则，买卖完全由用户定义的条件驱动

### 预设策略模板
- **D-09:** 保留3个预设策略作为快速开始选项：MA交叉、放量突破、MACD背离。用户可以基于预设修改，也可从空白开始
- **D-10:** 预设模板本质上是预填的表达式+条件配置，不是硬编码逻辑。用户选择预设后可以看到并修改底层的表达式和条件

### 回测页面布局
- **D-11:** 上下布局：上方配置区（选股+时间范围+指标构建+条件设置+运行按钮），下方结果区
- **D-12:** 配置区分为三个步骤区块：1) 选股与时间范围 2) 自定义指标（可创建多个） 3) 买卖条件组
- **D-13:** 点击「运行回测」后下方展示结果，结果区可折叠收起以腾出配置空间

### 结果展示
- **D-14:** 完整四部分展示：1) 核心指标卡片（总收益率、年化收益率、最大回撤、交易次数、胜率、盈亏比、夏普比率、平均持仓天数）2) 资金曲线图（策略净值 vs 买入持有基准，双线对比）3) K线图（买卖点标记）4) 交易明细表格
- **D-15:** 复用 Phase 4 PracticeStats 的展示模式：指标卡片用相同样式，资金曲线用 ECharts 折线图，K线买卖标记复用 buySellMarkers prop
- **D-16:** 资金曲线图：策略净值线 + 买入持有基准线，双线对比。策略线用蓝色，基准线用灰色虚线

### Claude's Discretion
- 表达式解析器的具体实现方式（AST 解析、安全沙箱 eval 等）
- 嵌套条件组的 UI 组件设计（递归组件 vs 扁平化呈现）
- 预设模板的具体参数默认值
- 指标构建器的实时预览和错误提示细节
- 结果区各部分的精确排列和尺寸
- 回测执行的同步/异步策略
- 运算符的精确数学定义和边界情况处理

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目规划与技术栈
- `CLAUDE.md` — 完整技术栈版本、项目结构、关键决策
- `.planning/PROJECT.md` — 项目愿景、核心价值、约束条件
- `.planning/REQUIREMENTS.md` — 需求清单，Phase 5 涉及：BACK-01, BACK-02, BACK-03, BACK-04, BACK-05, DATA-05
- `.planning/ROADMAP.md` — Phase 5 目标、成功标准、需求映射

### 前置阶段上下文
- `.planning/phases/01-data-foundation-k-line-charting/01-CONTEXT.md` — 图表布局、配色、交互基础决策
- `.planning/phases/02-technical-indicators-volume-price-analysis/02-CONTEXT.md` — 指标子图系统、信号标记模式、store结构
- `.planning/phases/03-advanced-analysis-features/03-CONTEXT.md` — 高级分析功能、图表扩展模式
- `.planning/phases/04-trading-practice-module/04-CONTEXT.md` — 练习模块布局、交易费用、资金曲线、统计展示模式（回测模块重度复用）

### 用户笔记（量价分析理论参考）
- `笔记/第04章_量价分析的首要原则.md` — 量价确认/异常理论基础
- `笔记/第05章_量价分析的全局视角.md` — 市场循环、全局分析视角
- `笔记/第06章_K线图与量价分析.md` — K线形态识别理论

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/practice_service.py` — 交易逻辑可复用：费用计算（万2.5+千1）、FIFO交易配对（`_pair_trades_fifo`）、资金曲线构建（`_build_equity_curve`）、统计计算（`get_stats`）。回测引擎应复用这些核心逻辑
- `backend/app/services/indicator_service.py` — 指标计算模式（MACD/RSI/KDJ/BOLL），使用 `ta` 库和 pandas。自定义指标的表达式函数（MA/EMA/STD等）需要复用这些计算能力
- `backend/app/models.py` — SQLAlchemy 模型定义。回测需要新模型（BacktestSession/BacktestTrade），可参考 PracticeSession/Trade 的结构
- `frontend/src/components/KLineChart.vue` — 已支持 `buySellMarkers` 和 `fixedData` props，回测结果可直接复用
- `frontend/src/components/practice/PracticeStats.vue` — 指标卡片布局、资金曲线图（ECharts line chart）、交易明细表格（el-table）的模式可直接复用
- `frontend/src/stores/practice.js` — Pinia Option Store 模式，可参考创建 backtest store
- `frontend/src/api/index.js` — axios client 模式，可扩展添加回测 API 调用
- `frontend/src/components/StockSearch.vue` — 股票搜索组件，回测配置区可复用

### Established Patterns
- ECharts chart option 是 computed property，响应 store 数据变化
- Pinia store 使用 Option Store 模式（state/getters/actions）
- 后端 API 使用 FastAPI 路由 + SQLAlchemy async session
- 后端计算服务封装为 class，接收 db session
- 指标计算结果缓存到数据库（params_hash 去重）
- 图表配色：TradingView 深色主题（#131722），A股红涨绿跌
- 指标卡使用 $bg-secondary 背景 + $border-color 边框 + 居中文字

### Integration Points
- 前端路由：BacktestView.vue 已注册路由（当前为占位内容，需替换）
- 前端 store：新建 backtest store 管理配置和结果状态
- 前端组件：BacktestView.vue 改造为上下布局的完整回测页面
- 后端 API：新增 `/api/backtest/` 端点组（运行回测、获取结果、列出历史）
- 后端服务：新建 BacktestService，复用 PracticeService 的费用计算和统计逻辑
- 后端数据库：新增回测相关表（Alembic 迁移）
- 后端表达式解析：新建表达式解析器，计算自定义指标

</code_context>

<specifics>
## Specific Ideas

- 表达式输入框应支持实时校验和错误提示（语法错误、未识别函数、除零等）
- 嵌套条件组参考可视化查询构建器的交互模式（可添加/删除条件项，可创建子组）
- 预设模板选择后自动填入表达式和条件，用户可在此基础上修改
- 资金曲线双线对比：策略净值用蓝色实线，买入持有基准用灰色虚线
- 回测配置和结果在同一页面，不需要跳转

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-strategy-backtesting-module*
*Context gathered: 2026-05-07*
