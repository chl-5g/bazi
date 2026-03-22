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
├── bazi-mcp/              # 八字 MCP Server（cantian-ai）
├── bazi-mcp-custom/       # 自定义 MCP
└── README.md
```

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

**<https://chl-5g.github.io/bazi/>**

### 你需要操作一次

1. GitHub 仓库 **Settings → Pages**  
2. **Build and deployment → Source** 选 **GitHub Actions**（不要选 Branch 的 docs，除非你自己改流程）

### 在线排盘要配 API

Pages 上没有 Python 后端。请：

1. 把 Flask 部署到任意 **HTTPS** 主机（Render、Fly、自建等）  
2. 修改仓库里 **`web-bazi-app/frontend/config.js`**（或仅在 gh-pages 构建产物里改），设置：

   ```js
   window.__BAZI_API_BASE__ = 'https://你的-api-域名';
   ```

3. 再推送，让 Actions 重新部署。

后端已启用 **`/api/*` CORS**（`flask-cors`），允许浏览器从 `github.io` 调用。

---

## API 摘要

- `POST /api/bazi` — `mode`: `datetime` | `lunar` | `pillars`（详见此前文档示例）
- `GET /api/locations` — 省市 / 国家城市

静态资源：`/config.js`、`/ai-fortune/ai-fortune.js`

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
