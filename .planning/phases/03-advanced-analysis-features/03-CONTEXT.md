# Phase 3: Advanced Analysis Features - Context

**Gathered:** 2026-05-06
**Status:** Ready for planning

<domain>
## Phase Boundary

在现有K线图基础上添加五大高级分析功能：支撑/阻力位自动检测（孤立支点算法）、动态趋势线绘制、市场循环阶段标注（吸筹→上涨→派发→下跌）、VAP价量分布图、日/周/月K线多时间跨度联动。所有计算在后端完成，结果缓存到数据库。

</domain>

<decisions>
## Implementation Decisions

### 支撑/阻力位展示
- **D-01:** 支撑/阻力位用半透明虚线水平线展示，横跨图表区域，价格标签在右侧Y轴上
- **D-02:** 支撑/阻力检测基于用户笔记中的孤立支点算法（第07章），后端Python计算
- **D-03:** 支撑/阻力和趋势线共用一个工具栏开关按钮（"支撑/阻力"），统一控制显示/隐藏

### 趋势线展示
- **D-04:** 趋势线自动连接相邻高点/低点支点画斜线，虚线样式延伸
- **D-05:** 趋势线算法基于用户笔记中的动态趋势线构造方法（第08章），使用支点检测后连线

### 市场循环标注
- **D-06:** 市场循环阶段用底部色带标注：吸筹=蓝、上涨=绿、派发=橙、下跌=红
- **D-07:** 阶段检测用后端规则算法自动完成（基于成交量模式、价格趋势、支点位置等）
- **D-08:** 色带上标注阶段名称，鼠标悬浮时显示该阶段的详细分析（成交量特征、价格变化幅度、关键支点等）

### VAP 价量分布图
- **D-09:** VAP 以横向直方图形式叠加在K线主图右侧，价格轴对齐，柱长代表成交量
- **D-10:** VAP 计算范围限定为当前可见区域的日K数据，随缩放/平移动态重算
- **D-11:** VAP 有独立的工具栏开关按钮，与现有指标按钮风格统一

### 多时间跨度联动
- **D-12:** 工具栏上放置按钮组（日K、周K、月K），点击切换，风格参考同花顺/通达信
- **D-13:** 切换时间跨度时保持时间位置大致对应（如日K看2025-03，切周K也显示附近时间）
- **D-14:** 周K/月K数据从已有日K数据在后端聚合生成（OHLCV），不额外调用 tushare 接口

### Claude's Discretion
- 支撑/阻力线的精确颜色色值和透明度
- 趋势线的线宽和延伸方式
- 孤立支点检测算法的具体阈值参数
- 市场循环检测算法的规则细节和判定阈值
- 底部色带的高度和位置
- VAP 直方图的价格分箱策略和精度
- 日K聚合为周K/月K的周/月起止规则（自然周/交易周）
- 时间位置保持的近似匹配算法

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目规划与技术栈
- `CLAUDE.md` — 完整技术栈版本、项目结构、关键决策
- `.planning/PROJECT.md` — 项目愿景、核心价值、约束条件
- `.planning/REQUIREMENTS.md` — 需求清单，Phase 3 涉及：VPA-04, ADVAN-01, ADVAN-02, ADVAN-03, ADVAN-04, ADVAN-05
- `.planning/ROADMAP.md` — Phase 3 目标、成功标准、需求映射

### 用户笔记（核心算法理论参考）
- `笔记/第07章_支撑位和阻力位.md` — 孤立支点检测算法、支撑/阻力位判定规则、突破确认
- `笔记/第08章_动态趋势及趋势线.md` — 动态趋势线构造方法、支点连线算法
- `笔记/第09章_价量分布分析VAP.md` — VAP 分布计算方法、可视化方式
- `笔记/第05章_量价分析的全局视角.md` — 市场循环四阶段（吸筹→上涨→派发→下跌）、嵌套循环

### 前置阶段上下文
- `.planning/phases/01-data-foundation-k-line-charting/01-CONTEXT.md` — 图表布局、配色、交互基础决策
- `.planning/phases/02-technical-indicators-volume-price-analysis/02-CONTEXT.md` — 指标子图系统、信号标记模式、参数调节交互

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `KLineChart.vue` — 动态多 grid 系统可直接扩展新子图（市场循环色带可加在底部独立 grid），series 数组可添加 markLine/markArea
- `stores/chart.js` — 已有指标开关模式（showMACD/showRSI 等），可直接添加新开关
- `stores/stock.js` — 数据获取和缓存模式，可扩展支撑/阻力/VAP/循环数据的 API 调用
- `backend/app/services/vpa_service.py` — VPA 信号检测服务，可扩展市场循环检测逻辑
- `backend/app/services/indicator_service.py` — 指标计算缓存模式（params_hash），可复用于新分析结果缓存
- `backend/app/models.py` — IndicatorValue 表结构可复用或参考创建新表

### Established Patterns
- ECharts chart option 是 computed property，响应 store 数据变化
- 指标子图通过 activeIndicators 数组动态构建 grid/series/xAxis/yAxis
- 信号标记用 scatter series（自定义 symbol + color）
- 后端计算 + 数据库缓存 + API → 前端 store → computed chart option
- 工具栏按钮：Element Plus el-button + Popover 参数面板

### Integration Points
- 前端图表：扩展 KLineChart.vue 的 grid/series 配置，添加支撑阻力 markLine、趋势线 line series、VAP bar series、循环色带 grid
- 前端 store：chart store 添加新开关状态，stock store 添加新数据获取
- 前端工具栏：StrategyView.vue 工具栏添加支撑/阻力按钮、VAP按钮、时间跨度按钮组
- 后端 API：新增支撑/阻力、趋势线、市场循环、VAP、多时间跨度数据端点
- 后端数据库：新增分析结果表或复用 IndicatorValue 模式
- 后端计算：新增分析服务（支点检测、趋势线、循环判定、VAP 分布、K线聚合）

</code_context>

<specifics>
## Specific Ideas

- 底部色带颜色方案参考：吸筹=蓝色系、上涨=绿色系、派发=橙色系、下跌=红色系
- 工具栏时间跨度按钮组参考同花顺/通达信风格（紧凑排列的日/周/月按钮）
- VAP 横向直方图叠加在K线右侧，参考 TradingView 的 Volume Profile 功能
- 支撑/阻力虚线水平线参考传统技术分析图表的标准画法

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-advanced-analysis-features*
*Context gathered: 2026-05-06*
