# Phase 2: Technical Indicators + Volume-Price Analysis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-06
**Phase:** 02-technical-indicators-volume-price-analysis
**Areas discussed:** 指标展示布局, 量价信号标记样式, 指标参数调节交互, 指标计算架构

---

## 指标展示布局

### MACD/RSI/KDJ 子图显示方式

| Option | Description | Selected |
|--------|-------------|----------|
| 全部展开 | K线主图 + 成交量 + MACD + RSI + KDJ 全部同时显示，每个指标一个子图。信息密度高但屏幕空间紧张。 | |
| Tab 切换 | K线主图 + 成交量固定显示，下方指标区域用 Tab 切换（MACD / RSI / KDJ），每次只看一个指标。 | |
| 指标开关组合 | 每个指标有独立开关，用户勾选哪个就显示哪个，可以同时展开多个。灵活但操作复杂。 | ✓ |

**User's choice:** 指标开关组合
**Notes:** 用户偏好灵活性，希望可以自由组合显示哪些指标

### BOLL 指标处理

| Option | Description | Selected |
|--------|-------------|----------|
| 叠加显示 | BOLL 上轨/中轨/下轨直接画在 K 线图上，和 MA 线一样。信息集中但线条多。 | |
| 默认关闭，手动开 | BOLL 有自己的独立开关，默认关闭，用户手动开启才显示。避免线条过多。 | ✓ |

**User's choice:** 默认关闭，手动开
**Notes:** K线图上已有4条MA线，BOLL默认关闭避免线条过多

### 多指标展开时图表高度

| Option | Description | Selected |
|--------|-------------|----------|
| 图表区滚动 | 图表区域自动扩展，于窗口内滚动查看所有展开的指标。页面其他部分不变。 | ✓ |
| 压缩 K 线高度 | 展开的指标压缩 K 线图高度，所有内容始终可见于一个屏幕内。 | |
| 固定子图高度 + 滚动 | 每个子图固定高度（如 150px），K 线主图固定 400px，超出屏幕时图表区域可滚动。 | |

**User's choice:** 图表区滚动
**Notes:** 保持K线主图不被压缩，展开的指标通过滚动查看

---

## 量价信号标记样式

### 量价确认/异常信号展示

| Option | Description | Selected |
|--------|-------------|----------|
| 图标标记 | 在信号出现的 K 线上方/下方显示小图标（如放量涨=绿色三角▲、缩量跌=红色三角▼）。简洁直观。 | ✓ |
| 背景色高亮 | 在 K 线上叠加半透明背景色，整根 K 线高亮。信息密集时难以分辨。 | |
| 文字标签 | 在 K 线旁边显示简短文字标签（如"放量涨"、"陷阱"）。占空间但信息明确。 | |

**User's choice:** 图标标记
**Notes:** 确认信号和异常信号用不同图标和颜色区分

### K 线形态标注

| Option | Description | Selected |
|--------|-------------|----------|
| 名称标签 | 在形态 K 线上方显示名称标签（如"锤头线"、"十字星"），字体小。 | |
| 彩色图标 + 图例 | 不同形态用不同颜色小图标标记。不占空间但需要记忆。 | |
| 圆点标记 + 悬浮 | 只在 K 线上方显示一个小圆点标记，鼠标悬浮弹出形态名称和说明。最简洁。 | ✓ |

**User's choice:** 圆点标记 + 悬浮
**Notes:** 最简洁的标注方式，悬浮提供详细信息

### 信号默认显示

| Option | Description | Selected |
|--------|-------------|----------|
| 默认显示 + 可隐藏 | 信号默认全部显示，用户可以通过开关隐藏特定类型。 | ✓ |
| 默认隐藏 | 信号默认隐藏，用户主动开启才显示。 | |

**User's choice:** 默认显示 + 可隐藏
**Notes:** 让用户打开就能看到分析结果，符合"学习工具"定位

---

## 指标参数调节交互

### 参数 UI 位置

| Option | Description | Selected |
|--------|-------------|----------|
| 弹出面板 | 点击工具栏上的指标按钮弹出 Popover，显示参数输入框。不占固定空间。 | ✓ |
| 工具栏下方展开行 | 工具栏下方展开一行参数调节栏。始终可见但占空间。 | |
| 右侧侧边栏 | 图表右侧固定侧边栏。信息集中但挤压图表宽度。 | |

**User's choice:** 弹出面板（Popover）
**Notes:** 不占用工具栏永久空间，按需弹出

### 刷新方式

| Option | Description | Selected |
|--------|-------------|----------|
| 实时刷新 | 输入参数后立即重新计算。体验流畅但频繁计算可能卡顿。 | |
| 确认后刷新 | 调整参数后需点击"应用"按钮才重新计算。避免频繁计算。 | ✓ |
| 防抖自动刷新 | 输入停顿 500ms 后自动刷新。平衡流畅和性能。 | |

**User's choice:** 确认后刷新
**Notes:** 明确的用户操作触发计算，避免不必要的计算开销

---

## 指标计算架构

### 计算位置

| Option | Description | Selected |
|--------|-------------|----------|
| 后端计算 + 存库 | 后端用 Python ta 库 + pandas 计算，结果存入数据库。计算准确、可复用（回测模块也能用）。 | ✓ |
| 前端实时计算 | 前端 JavaScript 实时计算（像现在的 MA）。不需要后端改动但逻辑重复。 | |
| 混合：默认后端 + 调节前端 | 默认参数后端计算存库，参数调节时前端临时计算。混合方案。 | |

**User's choice:** 后端计算 + 存库
**Notes:** 回测模块（Phase 5）需要复用指标计算逻辑；DATA-03 明确要求存库

### KDJ 处理

| Option | Description | Selected |
|--------|-------------|----------|
| 手写 KDJ | 用 pandas 手写 KDJ 公式（基于 Stochastic Oscillator 修改）。代码量小。 | ✓ |
| 用 Stoch 近似 | 用 ta 库的 Stochastic Oscillator 作为 KDJ 的近似替代。 | |

**User's choice:** 手写 KDJ
**Notes:** 保持和其他指标统一管理，KDJ 公式简单可直接手写

### 数据库存储方案

| Option | Description | Selected |
|--------|-------------|----------|
| 扩展 daily_bars 表 | 在 daily_bars 表上加列。查询简单但列多且参数变化需清空重算。 | |
| 独立指标表 | 新建 indicator_values 表（ts_code, trade_date, indicator_name, params_hash, value_json）。支持多参数共存。 | ✓ |
| 每指标一张表 | 每个指标一张独立表。结构清晰但表多。 | |

**User's choice:** 独立指标表
**Notes:** params_hash 区分不同参数的计算结果，灵活支持参数调节

---

## Claude's Discretion

- 图标标记的具体样式（三角大小、颜色色值）
- 信号检测算法的阈值参数
- K线形态识别的具体算法细节
- Popover 面板的具体布局和样式
- 指标子图的高度比例
- params_hash 的生成算法
- value_json 的内部结构

## Deferred Ideas

None — discussion stayed within phase scope
