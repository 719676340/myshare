# 量价交易学习平台

## What This Is

一个本地运行的 A 股量价分析学习工具，通过 tushare 获取日 K 数据，结合量价分析理论，在 K 线图上直观展示分析结果。支持策略分析、交易练习、自动回测三大模块，帮助用户通过看、练、测的方式学习量价交易。

## Core Value

在真实 A 股数据上可视化量价分析理论 — 让用户通过看图、模拟练习、策略回测来学习交易。

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 策略分析模块 — K 线图 + 成交量展示
- [ ] 策略分析模块 — 量价确认/异常标记（放量上涨、缩量下跌、量价背离等）
- [ ] 策略分析模块 — K 线形态识别（锤头线、射击十字星、十字星、吊人线等）
- [ ] 策略分析模块 — 技术指标计算与展示（MACD、RSI、KDJ、BOLL），结果存入数据库
- [ ] 策略分析模块 — 支撑/阻力位自动识别（孤立支点检测）
- [ ] 策略分析模块 — 动态趋势线绘制
- [ ] 策略分析模块 — 市场循环阶段标注（吸筹→上涨→派发→下跌）
- [ ] 策略分析模块 — VAP 价量分布图
- [ ] 策略分析模块 — 多时间跨度联动分析
- [ ] 交易练习模块 — 选股后逐日推进，不可回退
- [ ] 交易练习模块 — 买入/卖出 + 仓位比例选择
- [ ] 交易练习模块 — 模拟交易费用（佣金万 2.5 + 印花税千 1）
- [ ] 交易练习模块 — 最终收益统计
- [ ] 自动回测模块 — 预设策略模板 + 参数调节
- [ ] 自动回测模块 — 回测指标输出（总收益率、年化收益率、最大回撤、胜率等）
- [ ] 自动回测模块 — 资金曲线图 + 买卖点标记
- [ ] 数据管理 — tushare 拉取 A 股日 K 数据存入 SQLite
- [ ] 数据管理 — 技术指标计算后存入数据库
- [ ] 数据管理 — 支持预定义指标 + 参数调节 + 四则运算组合新指标
- [ ] UI — TradingView 风格深色主题
- [ ] UI — 股票搜索选择（代码/名称模糊匹配）
- [ ] UI — K 线图交互（十字光标、缩放、拖拽平移、OHLCV 显示）

### Out of Scope

- 用户系统 — 单人本地使用，无需多用户
- 非 A 股市场 — 只支持沪深 A 股
- 分钟级/Tick 数据 — 只用日 K 线
- 做空机制 — 只做多
- 服务器部署 — 本地运行
- 手动标注功能（画趋势线、标记支撑/阻力位）— 后续迭代

## Context

- 用户正在学习量价分析理论，笔记存放在项目目录的 `笔记/` 下
- 量价分析核心逻辑基于用户笔记：确认（长阳线+高量）、异常（长阳线+低量=陷阱）、K 线七元素、市场循环（吸筹→上涨→派发→下跌）
- A 股颜色惯例：红涨绿跌（与美股相反）
- tushare token 已配置，可直接使用

## Constraints

- **Tech Stack**: Vue + JS + ECharts（前端）、Python FastAPI（后端）、SQLite（数据库）、tushare（数据源）
- **Data Source**: 仅日 K 线数据（OHLCV），仅 A 股
- **Deployment**: 本地开发运行，前后端 localhost 访问
- **Cost**: tushare 有接口调用限制，需注意数据缓存

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 策略分析模块先行 | 核心价值所在，K 线图是其他两个模块的基础 | — Pending |
| 按需拉取数据 | 首次选股时从 tushare 拉取，减少初始加载时间和 API 调用 | — Pending |
| 股票列表存入数据库 | 沪深 A 股列表预加载，支持代码/名称模糊搜索 | — Pending |
| TradingView 深色主题 | 符合交易软件行业标准，用户习惯 | — Pending |
| 技术指标计算后存入数据库 | 避免重复计算，提升响应速度 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-30 after initialization*
