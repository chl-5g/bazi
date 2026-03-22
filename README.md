# Bazi 八字排盘系统

一套八字（四柱）排盘工具：**Web 应用**（Flask + 单页前端）、**GitHub Pages 在线界面**，以及 **MCP Server** 扩展。

在线站点（GitHub Pages，静态界面）：**<https://chl-5g.github.io/bazi/>**  
（仓库归属：`chl-5g/bazi`；若你记成 chi-5g，请以此 GitHub 用户名为准。）

> Pages 上仅为**静态页面**，排盘接口需自行部署后端，并在 `config.js` 里配置 `__BAZI_API_BASE__`（见下文「GitHub Pages」）。

---

## 项目结构

```
bazi/
├── web-bazi-app/
│   ├── backend/           # Flask API（lunar_python）
│   ├── frontend/          # index.html、config.js、ai-fortune/
│   └── ai-divination/     # 程序化解读 / AI 逻辑占位（Python 包）
├── .github/workflows/     # GitHub Actions：部署 Pages
├── render.yaml            # Render 一键部署 API（可选）
├── bazi-mcp/              # 八字 MCP Server（cantian-ai）
├── bazi-mcp-custom/       # 自定义 MCP
├── docs/
│   └── cursor-git-commit.md   # Cursor Agent 触发 git commit 与旧版 Git 的说明
└── README.md
```

**Cursor 用户**：若 Agent 执行 `git commit` 出现 `unknown option trailer`，见 [`docs/cursor-git-commit.md`](docs/cursor-git-commit.md)。

---

## Web 应用功能摘要

- **三种排盘**：公历时间 / 农历（含闰月）/ 四柱反查公历（1900–2100）
- **年份校验**：公历、农历提交与后端均限制 **1900–2100**
- **用户与乾造/坤造**、**真太阳时**、**国内省市区 / 海外国家城市**、**五行配色**
- **大运 / 流年表**（可横向滚动）、点击流年联动四柱展示 **周岁 / 虚岁**（标题「四柱」后小字）
- **明暗主题**、**加载动画**、**四柱下拉**（五虎遁 / 五鼠遁）
- **AI算命**：结果区下方占位区块与按钮；逻辑目录 `ai-divination/` + `frontend/ai-fortune/`

### 技术栈

| 层     | 技术 |
|--------|------|
| 后端   | Python / Flask、`flask-cors`（允许跨域调 API） |
| 历法   | [lunar_python](https://github.com/6tail/lunar-python) |
| 前端   | 单页 HTML/CSS/JS，`config.js` 配置 API 根地址 |

### 本地启动

```bash
cd web-bazi-app/backend
pip3 install -r requirements.txt
python3 app.py
# 浏览器打开 http://localhost:8000
```

本地默认 `config.js` 中 `__BAZI_API_BASE__` 为空，请求走**同源** `/api/*`。

---

## GitHub Pages（chl-5g.github.io）

推送 `master`/`main` 后，Workflow **Deploy GitHub Pages** 会把 `web-bazi-app/frontend/` 中的静态文件发布为：

**<https://chl-5g.github.io/bazi/>**（用户名是 **`chl-5g`**，不是 chi-5g）

### 若打开是 404

1. 确认地址拼写：**`chl-5g.github.io`**，路径 **`/bazi/`**（建议带末尾 `/`）。  
2. 打开仓库 **Actions**，确认 **Deploy GitHub Pages** 最近一次为绿色；若曾失败，多半是当时仓库仍为 Private、尚未开启 Pages，已成功重跑后即恢复。  
3. 强制刷新或无痕窗口（CDN 可能短暂缓存旧 404）。

### 你需要操作一次

1. GitHub 仓库 **Settings → Pages**  
2. **Build and deployment → Source** 选 **GitHub Actions**（不要选 Branch 的 docs，除非你自己改流程）

### 在线排盘：部署 API + 自动注入地址（推荐）

Pages 上没有 Python，需要公网 API。已帮你配好两条线：

**A. Render 一键部署（仓库根目录 `render.yaml`）**

1. 打开 [Render](https://render.com) → **New** → **Blueprint** → 连接 GitHub 选 `chl-5g/bazi`。  
2. 按向导创建 **bazi-api**（免费 Web Service，`rootDir` 指向 `web-bazi-app/backend`）。  
3. 部署成功后复制公网地址，例如 `https://bazi-api-xxxx.onrender.com`（**不要**末尾 `/`）。

**B. 让 GitHub Pages 自动指向该 API**

1. 打开仓库 **Settings → Secrets and variables → Actions**。  
2. 新建 **`BAZI_API_BASE`**（值：上一步的 API 根 URL，无尾斜杠），**必须放在下面两处之一**（不要只写在 Organization 变量里却未勾选本仓库）：  
   - **Repository variables**（页面上方「Actions secrets and variables」里的 **Variables** 标签 → **Repository variables** → **New repository variable**），**或**  
   - **Environment `github-pages`**：同一页点 **Environments** → **github-pages** → **Environment variables** → 添加 `BAZI_API_BASE`。  
   - 若误建在 **Secrets** 里同名 `BAZI_API_BASE`，工作流也会尝试读取（API 根地址本身会进公开 `config.js`，用 Variables 即可）。  
3. **Actions** 里 **Re-run** **Deploy GitHub Pages**，或 push 触发构建。

构建时会自动生成带 `window.__BAZI_API_BASE__` 的 `config.js`，无需手改前端文件。

**备选**：不配变量时，Pages 仍使用仓库里的默认 `config.js`（空基址，仅适合本地同源调试）；也可本地改 `frontend/config.js` 后 push（不推荐，易与变量注入混淆）。

后端已开 **`/api/*` CORS**（`flask-cors`），允许从 `github.io` 调用。

---

## API 摘要

- `POST /api/bazi` — `mode`: `datetime` | `lunar` | `pillars`（详见此前文档示例）
- `GET /api/locations` — 省市 / 国家城市

静态资源：`/config.js`、`/locations.json`、`/ai-fortune/ai-fortune.js`  
（`locations.json` 由 `python3 web-bazi-app/scripts/export_locations_json.py` 生成，与 `/api/locations` 一致；修改 `app.py` 里省市后请重新运行脚本。）

**GitHub Pages**：无后端时页面会 **自动回退** 加载同目录下的 `locations.json`，省市下拉可正常使用；排盘仍依赖 `BAZI_API_BASE` 指向的 API。

---

## MCP Server

- **bazi-mcp**：`getBaziDetail`、`getSolarTimes`、`getChineseCalendar`
- **bazi-mcp-custom**：可 fork 扩展

```bash
cd bazi-mcp && npm install && npm start
```

---

## macOS 持久运行（launchd，可选）

```bash
launchctl start com.caihaolun.bazi-web
launchctl stop com.caihaolun.bazi-web
```

配置示例：`~/Library/LaunchAgents/com.caihaolun.bazi-web.plist`。

---

## License

Private repository unless otherwise noted.
