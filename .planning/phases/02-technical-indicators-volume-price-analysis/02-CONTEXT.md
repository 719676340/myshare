# Phase 2: Technical Indicators + Volume-Price Analysis - Context

**Gathered:** 2026-05-06
**Status:** Ready for planning

<domain>
## Phase Boundary

在现有K线图基础上添加：四个技术指标（MACD、RSI、KDJ、BOLL）的独立开关式展示、量价确认/异常信号的图标标记、K线形态自动识别的圆点标注。指标在后端Python计算并存入独立指标表，支持参数调节。

</domain>

<decisions>
## Implementation Decisions

### 指标展示布局
- **D-01:** 每个指标（MACD、RSI、KDJ）有独立开关按钮，用户可自由组合显示，支持同时展开多个
- **D-02:** BOLL 指标叠加在K线主图上，默认关闭，用户手动开启
- **D-03:** 成交量子图始终显示（不可关闭），三个指标子图按开关状态动态添加/移除
- **D-04:** 展开多个指标时图表区域整体变高，图表区域可滚动查看所有内容（非压缩K线高度）
- **D-05:** 指标子图的排列顺序：K线主图（含BOLL叠加）→ 成交量 → MACD → RSI → KDJ

### 量价信号标记样式
- **D-06:** 量价确认信号（放量涨、缩量跌）用小图标标记：K线上方/下方的三角图标，颜色区分信号类型
- **D-07:** 量价异常信号（长阳+低量陷阱、短阳+高量走弱）同样用图标标记，视觉上与确认信号区分
- **D-08:** K线形态识别（锤头线、射击十字星、十字星、吊人线等）用圆点标记在K线上方，鼠标悬浮显示形态名称和说明
- **D-09:** 量价信号和K线形态标注默认显示，用户可通过开关隐藏特定类型

### 指标参数调节交互
- **D-10:** 点击工具栏上的指标按钮弹出 Popover 面板，显示该指标的参数输入框
- **D-11:** 参数调节后需点击"应用"按钮才重新计算并刷新图表（非实时刷新）
- **D-12:** 参数面板显示当前参数值和允许范围，如 MACD 快线默认12、慢线默认26、信号线默认9

### 指标计算架构
- **D-13:** 所有指标在后端用 Python 计算（ta 库 + pandas），计算结果存入数据库
- **D-14:** KDJ 指标手写实现（基于 Stochastic Oscillator 公式修改），不依赖 ta 库
- **D-15:** MA 均线保持前端计算（Phase 1 已实现，与回测模块不直接关联）
- **D-16:** 默认参数的计算结果在后端计算后存库，用户调节自定义参数时也存库（不同参数用 params_hash 区分）
- **D-17:** 数据库使用独立 indicator_values 表，结构：(ts_code, trade_date, indicator_name, params_hash, value_json)，支持不同参数的计算结果共存

### Claude's Discretion
- 图标标记的具体样式（三角大小、颜色色值）
- 信号检测算法的阈值参数
- K线形态识别的具体算法细节
- Popover 面板的具体布局和样式
- 指标子图的高度比例
- params_hash 的生成算法
- value_json 的内部结构

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目规划与技术栈
- `CLAUDE.md` — 完整技术栈版本、项目结构、关键决策（ta库选型、ECharts 6、SQLAlchemy 2.0）
- `.planning/PROJECT.md` — 项目愿景、核心价值、约束条件
- `.planning/REQUIREMENTS.md` — 需求清单，Phase 2 涉及：DATA-03, DATA-04, VPA-01, VPA-02, VPA-03, INDIC-01, INDIC-02, INDIC-03, INDIC-04, INDIC-06
- `.planning/ROADMAP.md` — Phase 2 目标、成功标准、需求映射

### 用户笔记（量价分析理论参考）
- `笔记/第04章_量价分析的首要原则.md` — 量价确认/异常的理论基础
- `笔记/第05章_量价分析的全局视角.md` — 量价分析整体框架
- `笔记/第06章_K线图与量价分析.md` — K线形态识别的理论基础（七元素、锤头线、十字星等）

### Phase 1 上下文
- `.planning/phases/01-data-foundation-k-line-charting/01-CONTEXT.md` — Phase 1 的布局、配色、交互决策

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `KLineChart.vue` — K线图组件，ECharts grid 系统可扩展新子图，series 数组可添加新指标线
- `stores/chart.js` — chart store 已有 showMA 开关模式，可直接扩展为指标开关
- `stores/stock.js` — stock store 管理股票数据和API调用，可扩展指标数据获取
- `calculateMA()` 函数 — MA 计算模式可参考（但新指标改后端计算）
- `backend/app/models.py` — SQLAlchemy 模型定义，可参考创建新模型
- `backend/app/api/daily.py` — 日K数据API模式，可参考创建指标API

### Established Patterns
- ECharts chart option 是 computed property，响应 store 数据变化
- Pinia store 使用 Option Store 模式（state/getters/actions）
- 后端 API 使用 FastAPI 路由 + SQLAlchemy async session
- 数据管道：tushare → DataFetcher → SQLite → API → 前端
- 图表配色：TradingView 深色主题，A股红涨绿跌

### Integration Points
- 前端图表：扩展 grid/series/dataZoom 配置添加新子图
- 前端 store：chart store 添加指标开关状态，stock store 添加指标数据获取
- 前端工具栏：添加指标按钮和 Popover 参数面板
- 后端 API：新增 `/api/indicators/{ts_code}` 端点
- 后端数据库：新增 indicator_values 表，Alembic 迁移
- 后端计算：新增 indicator service，使用 ta 库 + pandas

</code_context>

<specifics>
## Specific Ideas

- 量价信号图标参考：放量涨=向上三角（绿色系）、缩量跌=向下三角（红色系）、陷阱信号=警告图标
- K线形态标注：小圆点 + 悬浮弹出形态名称和说明文字
- 指标开关按钮排列在工具栏中，与现有MA开关风格统一
- 默认参数：MACD(12,26,9)、RSI(14)、KDJ(9,3,3)、BOLL(20,2)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-technical-indicators-volume-price-analysis*
*Context gathered: 2026-05-06*
