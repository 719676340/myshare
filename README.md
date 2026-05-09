# 量价交易学习平台

A 股量价分析学习工具，通过 tushare 获取日 K 数据，结合量价分析理论在 K 线图上直观展示分析结果。支持策略分析、交易练习、自动回测三大模块。

## 技术栈

- **前端**: Vue 3 + ECharts 6 + Element Plus
- **后端**: Python FastAPI + SQLAlchemy + tushare
- **数据库**: SQLite

## 环境准备

### Miniconda 安装（推荐）

1. 下载安装 Miniconda：[https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)

   **macOS:**
   ```bash
   brew install --cask miniconda
   conda init zsh  # 或 bash，取决于你使用的 shell
   ```
   重启终端后生效。

   **Windows:**
   下载安装包运行即可，安装时勾选 "Add Miniconda to PATH"。

2. 创建并激活项目环境：
   ```bash
   conda create -n volume-price python=3.12
   conda activate volume-price
   ```

### Node.js

确保已安装 Node.js 18+，推荐使用 [nvm](https://github.com/nvm-sh/nvm) 管理版本：
```bash
nvm install 18
nvm use 18
```

## 启动方式

### 1. 后端

```bash
cd backend
conda activate volume-price
pip install -r requirements.txt
```

在 `backend/` 目录下创建 `.env` 文件，配置 tushare token：

```
TUSHARE_TOKEN=你的token
```

可在 [tushare.pro](https://tushare.pro) 注册获取。

启动服务：

```bash
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

## 功能模块

- **策略分析** — 选择个股查看 K 线图，叠加量价分析指标
- **交易练习** — 在历史数据上模拟买卖，练习量价分析技巧
- **自动回测** — 配置策略条件，自动回测历史收益
