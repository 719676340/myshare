# Phase 4: Trading Practice Module - Context

**Gathered:** 2026-05-06
**Status:** Ready for planning

<domain>
## Phase Boundary

用户在历史A股数据上进行逐日向前模拟交易练习。选定股票和时间范围后，从起始日前逐日推进K线（不可回退），在推进过程中执行买入/卖出操作。系统强制执行A股交易规则（T+1、涨跌停价格限制、交易费用），管理持仓和资金，练习结束后展示完整绩效统计（收益、资金曲线、交易记录、K线图买卖标记）。

</domain>

<decisions>
## Implementation Decisions

### 练习界面整体布局
- **D-01:** 左右分栏布局：左侧K线图占主区域（约70%），右侧固定宽度操作面板（约30%）
- **D-02:** 练习前显示配置页：选股 + 起止日期选择器 + 初始资金输入（默认100万）。确认后进入练习模式，配置页隐藏
- **D-03:** 练习模式下策略分析的全部功能可用：指标开关（MACD/RSI/KDJ/BOLL）、信号标记、支撑阻力等。用户可用完整分析工具辅助决策
- **D-04:** 右侧操作面板分为上中下三区：账户信息（资金/持仓/盈亏）在上，交易操作（买入/卖出）在中，交易记录列表在下

### 逐日推进机制
- **D-05:** 每次推进只揭示1根K线，用户完全控制节奏
- **D-06:** 推进触发方式：页面上的「下一日」按钮 + 键盘空格键快捷键
- **D-07:** 进度条显示当前进度（第X天/共Y天）+ 已用天数占总天数的百分比
- **D-08:** 推进到最后一天后自动提示结束，也支持提前点击「结束练习」查看统计

### 交易操作面板
- **D-09:** 买入/卖出两个Tab切换，每个Tab下有仓位选择和确认按钮。下单前显示预估费用和金额
- **D-10:** 仓位选择：预设按钮（1/4仓、1/3仓、半仓、全仓）+ 自定义输入框（手动输入股数）
- **D-11:** 持仓列表显示：股票代码 + 持有股数 + 成本价 + 当前市值 + 浮动盈亏，可从持仓列表操作卖出
- **D-12:** A股交易规则强制执行：T+1（当天买入不可当天卖出）、涨跌停价格限制（普通股±10%、ST±5%、创业板/科创板±20%）、停牌日跳过
- **D-13:** 交易费用模拟：佣金万2.5（买卖双向）+ 印花税千1（仅卖出）

### 结果统计展示
- **D-14:** 统计页面三部分：顶部核心指标卡片（总收益率、最终资金、交易次数、胜率）、中部资金曲线图（净值随时间变化）、底部交易记录表格
- **D-15:** 交易记录表格：每行一笔完整交易（买入日期/价格 → 卖出日期/价格，持仓天数、盈亏金额、盈亏百分比），买卖配对归为一行
- **D-16:** 统计页面的K线图标记所有买卖点：向上箭头=买入，向下箭头=卖出

### Claude's Discretion
- 右侧面板的精确宽度像素值
- 配置页的具体视觉设计和动画效果
- 仓位预设按钮的精确选项（1/4、1/3、半仓、全仓 vs 其他组合）
- 进度条的具体样式和颜色
- 资金曲线图的图表细节（线条颜色、坐标轴、网格）
- 买卖标记箭头的具体样式和大小
- 统计指标卡片的具体排列和样式
- 停牌日的处理细节（是否显示灰色K线、自动跳过等）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目规划与技术栈
- `CLAUDE.md` — 完整技术栈版本、项目结构、关键决策
- `.planning/PROJECT.md` — 项目愿景、核心价值、约束条件
- `.planning/REQUIREMENTS.md` — 需求清单，Phase 4 涉及：PRACT-01, PRACT-02, PRACT-03, PRACT-04, PRACT-05, PRACT-06, PRACT-07, PRACT-08
- `.planning/ROADMAP.md` — Phase 4 目标、成功标准、需求映射

### 前置阶段上下文
- `.planning/phases/01-data-foundation-k-line-charting/01-CONTEXT.md` — 图表布局、配色、交互基础决策（K线图结构、深色主题）
- `.planning/phases/02-technical-indicators-volume-price-analysis/02-CONTEXT.md` — 指标子图系统、信号标记模式、store结构
- `.planning/phases/03-advanced-analysis-features/03-CONTEXT.md` — 高级分析功能、图表扩展模式

### 用户笔记（量价分析理论参考）
- `笔记/第04章_量价分析的首要原则.md` — 量价确认/异常的理论基础
- `笔记/第05章_量价分析的全局视角.md` — 市场循环、全局分析视角
- `笔记/第06章_K线图与量价分析.md` — K线形态识别理论基础

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `KLineChart.vue` — K线图组件，ECharts grid 系统，可直接复用于练习模式的K线展示，可扩展添加买卖点标记（scatter series）
- `StockSearch.vue` — 股票搜索组件，可直接复用于练习配置页的选股
- `stores/stock.js` — stock store 管理股票数据和API调用模式，可参考创建 practice store
- `stores/chart.js` — chart store 的指标开关/参数模式，练习模式可直接使用
- `backend/app/models.py` — SQLAlchemy 模型定义（Stock、DailyBar），可参考创建 PracticeSession/Trade 模型
- `backend/app/api/daily.py` — 日K数据API模式，可复用于按日期范围获取K线数据
- `backend/app/services/` — 后端服务模式，可参考创建 practice service

### Established Patterns
- ECharts chart option 是 computed property，响应 store 数据变化
- Pinia store 使用 Option Store 模式（state/getters/actions）
- 后端 API 使用 FastAPI 路由 + SQLAlchemy async session
- 前端 API 调用统一通过 api/index.js 的 axios client
- 图表配色：TradingView 深色主题，A股红涨绿跌
- 组件结构：view 组件包含工具栏 + 图表区域 + 侧面板

### Integration Points
- 前端路由：PracticeView.vue 已注册路由（需替换占位内容）
- 前端图表：KLineChart.vue 可复用，需支持按日期截断数据 + 买卖标记 overlay
- 前端 store：新建 practice store 管理练习状态（当前日、资金、持仓、交易记录）
- 前端 API：新增练习相关 API 调用（创建练习、推进日期、下单、获取统计）
- 后端 API：新增 `/api/practice/` 端点组（创建session、推进、下单、统计）
- 后端数据库：新增 practice_sessions 和 trades 表，Alembic 迁移
- 后端计算：practice service 处理交易规则验证、费用计算、持仓管理

</code_context>

<specifics>
## Specific Ideas

- 右侧面板参考同花顺模拟交易的布局风格
- 仓位预设按钮：1/4仓、1/3仓、半仓、全仓 + 自定义输入
- 统计页资金曲线图用 ECharts 折线图，与K线图风格统一（深色主题）
- 买卖标记：向上箭头（绿色/红色，按A股惯例）= 买入，向下箭头 = 卖出
- 练习配置页简洁明了：选股 → 选时间范围 → 设置资金 → 开始

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-trading-practice-module*
*Context gathered: 2026-05-06*
