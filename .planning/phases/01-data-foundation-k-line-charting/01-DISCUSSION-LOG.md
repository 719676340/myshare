# Phase 1: Data Foundation + K-Line Charting - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-05
**Phase:** 01-data-foundation-k-line-charting
**Areas discussed:** 页面布局与导航, 股票搜索交互, 图表布局与默认值, 数据拉取与缓存

---

## 页面布局与导航

| Option | Description | Selected |
|--------|-------------|----------|
| 单页布局 | 顶部导航栏切换模块，K线图占满主区域，搜索栏在图表上方 | ✓ |
| 多页布局 | 每个模块独立页面，路由切换 | |

**User's choice:** 单页布局

| Option | Description | Selected |
|--------|-------------|----------|
| 左侧侧边栏 | 图标导航，收缩时只显示图标 | |
| 顶部水平导航 | 水平 Tab 或菜单切换，简洁直接 | ✓ |
| 隐藏式导航 | 通过下拉菜单或按钮切换模块 | |

**User's choice:** 顶部水平导航

| Option | Description | Selected |
|--------|-------------|----------|
| 搜索框在图表上方工具栏 | 搜索框 + 图表参数控制在同一工具栏 | ✓ |
| 搜索框在导航栏中 | 搜索框在顶部导航栏，图表工具栏单独一行 | |

**User's choice:** 搜索框在图表上方工具栏

| Option | Description | Selected |
|--------|-------------|----------|
| 引导页 | 显示欢迎引导文字，提示用户搜索股票 | ✓ |
| 默认加载股票 | 默认加载一只热门股票的K线图 | |

**User's choice:** 引导页

---

## 股票搜索交互

| Option | Description | Selected |
|--------|-------------|----------|
| 实时自动补全下拉 | 输入时实时显示匹配结果，点击即选中 | ✓ |
| 搜索按钮 + 结果列表 | 输入后点搜索按钮，结果展示在独立列表 | |

**User's choice:** 实时自动补全下拉

| Option | Description | Selected |
|--------|-------------|----------|
| 代码 + 名称 | 每行显示股票代码和名称，简洁明了 | ✓ |
| 代码 + 名称 + 市场 + 行业 | 信息更丰富但可能影响加载速度 | |

**User's choice:** 代码 + 名称

| Option | Description | Selected |
|--------|-------------|----------|
| 300ms 防抖 | 输入停顿 300ms 后触发搜索 | ✓ |
| 即时查询 | 每次输入都查询，无防抖 | |

**User's choice:** 300ms 防抖

| Option | Description | Selected |
|--------|-------------|----------|
| 直接替换 | 选中新股票后直接替换当前图表 | ✓ |
| 多标签页切换 | 支持同时打开多只股票，Tab 切换 | |

**User's choice:** 直接替换

---

## 图表布局与默认值

| Option | Description | Selected |
|--------|-------------|----------|
| K线 75% + 成交量 25% | K线图为主角，成交量辅助 | ✓ |
| K线 80% + 成交量 20% | 成交量更紧凑 | |
| K线 70% + 成交量 30% | 成交量更突出 | |

**User's choice:** K线 75% + 成交量 25%

| Option | Description | Selected |
|--------|-------------|----------|
| 120 日 | 约半年，能看清中期趋势 | ✓ |
| 60 日 | 约一个季度，数据更紧凑 | |
| 250 日 | 约一年，能看清长期趋势 | |

**User's choice:** 120 日

| Option | Description | Selected |
|--------|-------------|----------|
| 传统配色 | MA5=白、MA10=黄、MA20=紫、MA60=绿 | ✓ |
| 你来决定 | 高对比度深色主题配色 | |

**User's choice:** 传统配色（MA5=白、MA10=黄、MA20=紫、MA60=绿）

| Option | Description | Selected |
|--------|-------------|----------|
| 左上角 | 不遮挡数据，包含线名和当前值 | ✓ |
| 顶部居中 | 居中对齐但可能遮挡 | |

**User's choice:** 左上角

---

## 数据拉取与缓存

| Option | Description | Selected |
|--------|-------------|----------|
| 全部历史数据 | 上市以来所有日K数据，数据完整 | ✓ |
| 最近 2 年 | 加载快，长期分析可能不够 | |
| 最近 1 年 | 最快，限制分析范围 | |

**User's choice:** 全部历史数据

| Option | Description | Selected |
|--------|-------------|----------|
| 缓存 + 手动刷新 | 首次拉取后缓存，显示更新时间，用户可手动刷新 | ✓ |
| 自动增量更新 | 每次打开自动检查新数据 | |

**User's choice:** 缓存 + 手动刷新

| Option | Description | Selected |
|--------|-------------|----------|
| 加载动画 + 文字提示 | 简单明了 | |
| 进度条 | 提示加载进度，更精确 | ✓ |

**User's choice:** 进度条

| Option | Description | Selected |
|--------|-------------|----------|
| 错误提示 + 重试按钮 | 用户可重试或换股票 | ✓ |
| 自动重试 + 错误提示 | 自动重试3次 | |

**User's choice:** 错误提示 + 重试按钮

---

## Claude's Discretion

- 图表工具栏具体按钮设计
- 引导页文案和视觉设计
- 进度条样式和精度
- 错误提示措辞
- 深色主题精确色值

## Deferred Ideas

None — discussion stayed within phase scope
