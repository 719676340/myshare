# 量价交易学习平台

A 股量价分析学习工具，通过 tushare 获取日 K 数据，结合量价分析理论在 K 线图上直观展示分析结果。支持策略分析、交易练习、自动回测三大模块。

## 技术栈

- **前端**: Vue 3 + ECharts 6 + Element Plus
- **后端**: Python FastAPI + SQLAlchemy + tushare
- **数据库**: SQLite

## 启动方式

### 1. 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

后端运行在 http://localhost:8000

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

### 3. 数据源

项目使用 tushare 获取 A 股日 K 线数据，需要在 `backend/.env` 中配置自己的 tushare token：

```
TUSHARE_TOKEN=你的token
```

可在 [tushare.pro](https://tushare.pro) 注册获取。

## 功能模块

- **策略分析** — 选择个股查看 K 线图，叠加量价分析指标
- **交易练习** — 在历史数据上模拟买卖，练习量价分析技巧
- **自动回测** — 配置策略条件，自动回测历史收益
