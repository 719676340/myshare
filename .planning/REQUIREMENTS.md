# Requirements: 量价交易学习平台

**Defined:** 2026-04-30
**Core Value:** 在真实 A 股数据上可视化量价分析理论 — 让用户通过看图、模拟练习、策略回测来学习交易

## v1 Requirements

### Data Management

- [x] **DATA-01**: 用户可通过股票搜索选择股票，支持代码和名称模糊匹配
- [x] **DATA-02**: 选择股票后自动从 tushare 拉取日 K 数据（OHLCV）存入 SQLite
- [x] **DATA-03**: 技术指标计算结果存入数据库，避免重复计算
- [x] **DATA-04**: 支持指标参数调节（如 MA 周期、RSI 周期等）
- [ ] **DATA-05**: 支持基于基础字段的四则运算组合新指标

### K-Line Charting

- [x] **CHART-01**: 用户可查看 K 线图 + 成交量柱状图，数据同步显示
- [x] **CHART-02**: K 线图支持十字光标，鼠标悬浮显示 OHLCV 数据
- [x] **CHART-03**: K 线图支持缩放、拖拽平移、时间轴导航
- [x] **CHART-04**: A 股颜色惯例：红涨绿跌
- [x] **CHART-05**: TradingView 风格深色主题

### Volume-Price Analysis

- [x] **VPA-01**: 自动标记量价确认信号（放量上涨、缩量下跌）
- [x] **VPA-02**: 自动标记量价异常信号（长阳+低量陷阱、短阳+高量走弱、上涨量递减）
- [x] **VPA-03**: K 线形态自动识别（锤头线、射击十字星、十字星、吊人线等）
- [x] **VPA-04**: 量价背离检测（价格创新高但成交量下降等）

### Technical Indicators

- [x] **INDIC-01**: 用户可查看 MACD 指标（MACD 线 + 信号线 + 柱状图），显示在子图中
- [x] **INDIC-02**: 用户可查看 RSI 指标，显示在子图中，支持参数调节
- [x] **INDIC-03**: 用户可查看 KDJ 指标，显示在子图中
- [x] **INDIC-04**: 用户可查看 BOLL 指标（上轨+中轨+下轨），叠加在 K 线图上
- [x] **INDIC-05**: 用户可查看移动平均线（MA5/MA10/MA20/MA60），叠加在 K 线图上
- [x] **INDIC-06**: 用户可调节指标参数并重新计算

### Advanced Analysis

- [x] **ADVAN-01**: 自动识别支撑/阻力位（孤立支点检测）
- [x] **ADVAN-02**: 自动绘制动态趋势线
- [x] **ADVAN-03**: 市场循环阶段自动标注（吸筹→上涨→派发→下跌）
- [x] **ADVAN-04**: VAP 价量分布图（横向直方图叠加在价格图上）
- [x] **ADVAN-05**: 多时间跨度联动分析（日/周/月 K 联动）

### Trading Practice

- [x] **PRACT-01**: 用户可选择股票和练习时间范围，系统展示起始日之前的 K 线数据
- [x] **PRACT-02**: 用户逐日推进，不可回退，每次揭示下一天 K 线
- [x] **PRACT-03**: 用户可执行买入/卖出操作，支持仓位比例选择（半仓、全仓等）
- [x] **PRACT-04**: 初始资金可自定，默认 100 万
- [x] **PRACT-05**: 模拟 A 股交易费用：佣金万 2.5 + 印花税千 1（卖出时收取）
- [x] **PRACT-06**: 强制 T+1 规则：当天买入不可当天卖出
- [x] **PRACT-07**: 涨跌停价格限制执行（普通股 ±10%、ST ±5%、创业板/科创板 ±20%）
- [x] **PRACT-08**: 练习结束后展示最终收益、交易记录、每笔盈亏

### Strategy Backtesting

- [ ] **BACK-01**: 提供预设策略模板（MA 交叉、放量突破、MACD 背离等）
- [ ] **BACK-02**: 用户可调节策略参数（阈值、回看天数、MA 周期等）
- [ ] **BACK-03**: 回测输出：总收益率、年化收益率、最大回撤、交易次数、胜率、盈亏比、夏普比率、平均持仓天数
- [ ] **BACK-04**: 资金曲线图：策略净值 vs 基准净值（买入持有）
- [ ] **BACK-05**: 每笔交易买卖点标记在 K 线图上

## v2 Requirements

### Enhanced Features

- **ENHANC-01**: 手动画趋势线、标记支撑/阻力位（手动标注功能）
- **ENHANC-02**: 量烛图/等量图
- **ENHANC-03**: 交易练习中添加交易理由记录
- **ENHANC-04**: 自定义指标构建器（四则运算表达式解析器）

## Out of Scope

| Feature | Reason |
|---------|--------|
| 用户系统/多用户 | 单人本地使用，无需认证 |
| 实时/分钟级数据 | 只用日 K 线，实时数据需要 WebSocket 基础设施 |
| 做空/融资融券 | 只做多，专注学习 |
| 服务器部署 | 本地运行，localhost 访问 |
| 移动端适配 | 桌面优先，固定宽度设计可接受 |
| AI/ML 预测 | 教育工具，不提供黑盒预测 |
| 新闻/舆情 | 专注技术分析和量价理论 |
| 社交功能 | 个人学习工具，不需要社区 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 2 | Complete |
| DATA-04 | Phase 2 | Complete |
| DATA-05 | — | Deferred to v2 (ENHANC-04) |
| CHART-01 | Phase 1 | Complete |
| CHART-02 | Phase 1 | Complete |
| CHART-03 | Phase 1 | Complete |
| CHART-04 | Phase 1 | Complete |
| CHART-05 | Phase 1 | Complete |
| VPA-01 | Phase 2 | Complete |
| VPA-02 | Phase 2 | Complete |
| VPA-03 | Phase 2 | Complete |
| VPA-04 | Phase 3 | Complete |
| INDIC-01 | Phase 2 | Complete |
| INDIC-02 | Phase 2 | Complete |
| INDIC-03 | Phase 2 | Complete |
| INDIC-04 | Phase 2 | Complete |
| INDIC-05 | Phase 1 | Complete |
| INDIC-06 | Phase 2 | Complete |
| ADVAN-01 | Phase 3 | Complete |
| ADVAN-02 | Phase 3 | Complete |
| ADVAN-03 | Phase 3 | Complete |
| ADVAN-04 | Phase 3 | Complete |
| ADVAN-05 | Phase 3 | Complete |
| PRACT-01 | Phase 4 | Complete |
| PRACT-02 | Phase 4 | Complete |
| PRACT-03 | Phase 4 | Complete |
| PRACT-04 | Phase 4 | Complete |
| PRACT-05 | Phase 4 | Complete |
| PRACT-06 | Phase 4 | Complete |
| PRACT-07 | Phase 4 | Complete |
| PRACT-08 | Phase 4 | Complete |
| BACK-01 | Phase 5 | Pending |
| BACK-02 | Phase 5 | Pending |
| BACK-03 | Phase 5 | Pending |
| BACK-04 | Phase 5 | Pending |
| BACK-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 35 total
- Mapped to phases: 34
- Deferred to v2: 1 (DATA-05 custom indicator builder -> ENHANC-04)

---
*Requirements defined: 2026-04-30*
*Last updated: 2026-04-30 after roadmap creation*
