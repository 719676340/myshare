# Phase 3: Advanced Analysis Features - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-06
**Phase:** 03-advanced-analysis-features
**Areas discussed:** 支撑/阻力+趋势线, 市场循环标注, VAP价量分布, 多时间跨度联动

---

## 支撑/阻力位展示

| Option | Description | Selected |
|--------|-------------|----------|
| 虚线水平线 | 半透明虚线横跨图表区域，价格标签在右侧Y轴，视觉干扰小 | ✓ |
| 实线水平线 | 实线横跨图表，更显眼但可能遮挡K线 | |
| 水平线 + 强度色带 | 线附近叠加半透明色带，带宽代表强度，实现复杂 | |

**User's choice:** 虚线水平线
**Notes:** 推荐选项，经典做法，视觉干扰小

---

## 趋势线展示

| Option | Description | Selected |
|--------|-------------|----------|
| 连接支点的斜线 | 自动连接相邻高点/低点支点画斜线，虚线延伸 | ✓ |
| 斜线 + 通道线 | 连接高点/低点画趋势线，同时画平行线形成通道 | |
| 仅当有效时显示 | 只显示经过多次触碰确认的趋势线（至少2-3次），减少噪音 | |

**User's choice:** 连接支点的斜线
**Notes:** 经典技术分析做法

---

## 支撑/阻力+趋势线开关交互

| Option | Description | Selected |
|--------|-------------|----------|
| 统一开关按钮 | 工具栏上一个"支撑/阻力"按钮同时控制水平线和趋势线 | ✓ |
| 分开两个开关 | "水平位"和"趋势线"分别开关 | |
| 加入现有指标开关系统 | 和MACD/RSI一样，点击弹出Popover显示参数 | |

**User's choice:** 统一开关按钮
**Notes:** 简洁，一个按钮控制两种图形元素

---

## 市场循环标注呈现

| Option | Description | Selected |
|--------|-------------|----------|
| 底部色带标注 | 图表底部时间轴下方用色带标注不同阶段，不干扰K线 | ✓ |
| 背景色块叠加 | K线图背景直接叠加半透明色块 | |
| 转换点标记 | 仅在阶段转换点放置标记点+文字标签 | |

**User's choice:** 底部色带标注
**Notes:** 视觉清晰，不干扰K线主体

---

## 市场循环检测方式

| Option | Description | Selected |
|--------|-------------|----------|
| 自动检测 | 后端规则算法检测（基于成交量模式、价格趋势、支点位置等） | ✓ |
| 自动检测 + 手动调整 | 算法结果作为参考，用户可手动调整阶段边界 | |
| 纯手动标注 | 不做算法检测，用户自行标注 | |

**User's choice:** 自动检测
**Notes:** 符合需求ADVAN-03"自动标注"

---

## 循环标注信息密度

| Option | Description | Selected |
|--------|-------------|----------|
| 仅标注阶段名 | 每个阶段只标注名称和起止时间 | |
| 标注 + 特征摘要 | 标注名称 + 成交量特征、价格变化幅度等摘要 | |
| 标注 + 悬浮详情 | 标注阶段名，悬浮时显示详细分析 | ✓ |

**User's choice:** 标注 + 悬浮详情
**Notes:** 日常显示简洁，悬浮展开详细信息

---

## VAP 布局

| Option | Description | Selected |
|--------|-------------|----------|
| 叠加在K线右侧 | 横向直方图在K线主图右侧，价格对齐，长度代表成交量 | ✓ |
| 独立子图 | VAP作为独立子图显示在K线下方 | |
| 直接叠加在K线上 | 半透明横向柱状叠加在K线主体区域 | |

**User's choice:** 叠加在K线右侧
**Notes:** 经典VAP展示方式，价格关联直观

---

## VAP 计算范围

| Option | Description | Selected |
|--------|-------------|----------|
| 当前可见区域 | 对当前可见区域的日K数据计算VAP，随缩放动态重算 | ✓ |
| 全部历史数据 | 对全部历史数据计算VAP | |
| 用户可选范围 | 用户可选择计算范围 | |

**User's choice:** 当前可见区域
**Notes:** 数据量可控，缩放时动态更新

---

## VAP 开关交互

| Option | Description | Selected |
|--------|-------------|----------|
| 工具栏开关按钮 | 和MACD/RSI一样，工具栏上VAP按钮切换 | ✓ |
| 指标开关 + 参数调节 | 加入指标开关系统，点击弹出Popover可调参数 | |

**User's choice:** 工具栏开关按钮
**Notes:** 简洁统一

---

## 时间跨度切换 UI

| Option | Description | Selected |
|--------|-------------|----------|
| 工具栏按钮组 | 工具栏上一排按钮（日K、周K、月K），点击切换 | ✓ |
| 下拉框选择 | 下拉框选择时间跨度 | |
| 多图表并排 | 三个图表并排或上下展示 | |

**User's choice:** 工具栏按钮组
**Notes:** 参考同花顺/通达信风格

---

## 联动含义

| Option | Description | Selected |
|--------|-------------|----------|
| 时间位置保持 | 切换跨度时保持时间位置大致对应 | ✓ |
| 不联动 | 重新加载完整数据 | |
| 时间 + 指标状态保持 | 保持时间位置和指标开关状态 | |

**User's choice:** 时间位置保持
**Notes:** 操作流畅，用户不需要重新定位

---

## 周/月K数据来源

| Option | Description | Selected |
|--------|-------------|----------|
| 日K聚合 | 从已有日K数据在后端聚合为周K/月K，无需额外tushare调用 | ✓ |
| tushare单独拉取 | 调用tushare的周K/月K接口 | |

**User's choice:** 日K聚合
**Notes:** 节约API调用额度，日K数据已在本地

---

## Claude's Discretion

- 支撑/阻力线的精确颜色和透明度
- 趋势线线宽和延伸方式
- 孤立支点检测算法阈值
- 市场循环检测规则细节
- 色带高度和位置
- VAP 分箱策略
- 日K聚合规则
- 时间位置匹配算法

## Deferred Ideas

None — discussion stayed within phase scope
