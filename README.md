# Bazi 八字排盘系统

一套完整的八字（四柱）排盘工具集，包含 Web 应用和 MCP Server。

## 项目结构

```
bazi/
├── web-bazi-app/          # 八字排盘 Web 应用
│   ├── backend/
│   │   ├── app.py         # Flask 后端 API
│   │   └── requirements.txt
│   └── frontend/
│       └── index.html     # 单页前端（HTML/CSS/JS）
├── bazi-mcp/              # 八字 MCP Server（来自 cantian-ai）
│   └── src/
├── bazi-mcp-custom/       # 自定义八字 MCP Server
│   └── src/
└── README.md
```

## Web 应用

### 功能

- **三种排盘方式**：统一入口，下拉切换
  - 按公历时间排盘：输入公历日期时间
  - 按农历时间排盘：选择农历年月日 + 时辰，支持闰月
  - 按四柱排盘：选择年柱/月柱/日柱/时柱干支，反查 1900–2100 年内匹配的公历时间，点击即可查看完整排盘
- **用户信息**：支持输入姓名，结果页显示姓名与乾造/坤造
- **真太阳时校正**：滑块开关，根据出生地经度和时区自动换算；四柱排盘模式下自动隐藏
- **出生地选择**：国内按省份-城市、海外按国家-城市级联选择
- **五行配色**：甲乙寅卯（木/绿）、丙丁巳午（火/红）、戊己辰戌丑未（土/棕）、庚辛申酉（金/金色）、壬癸亥子（水/蓝）
- **大运流年表**：默认显示 8 列大运，横向滚动查看更多，上限 120 岁
- **四柱下拉联动**：年柱/日柱提供 60 甲子选项，月柱按五虎遁、时柱按五鼠遁动态生成
- **明暗主题切换**：日间/夜间模式，偏好自动保存
- **响应式布局**：适配桌面、平板、手机
- **加载指示器**：排盘计算中显示转圈动画

### 技术栈

| 层       | 技术                                  |
|---------|-------------------------------------|
| 后端      | Python / Flask                      |
| 历法计算    | [lunar_python](https://github.com/6tail/lunar-python) |
| 前端      | 原生 HTML / CSS / JavaScript（单文件）     |
| 持久化运行   | macOS launchd                       |

### 快速启动

```bash
# 1. 安装依赖
cd web-bazi-app/backend
pip3 install -r requirements.txt

# 2. 启动
python3 app.py

# 3. 访问
open http://localhost:8000
```

### API

#### POST /api/bazi

按公历时间排盘：

```json
{
  "mode": "datetime",
  "datetime": "1998-07-31T14:10",
  "gender": 1,
  "timeMode": "true_solar",
  "locationType": "domestic",
  "province": "fujian",
  "city": "fuzhou"
}
```

按农历时间排盘：

```json
{
  "mode": "lunar",
  "lunarYear": 1998,
  "lunarMonth": 6,
  "lunarDay": 9,
  "hour": 14,
  "minute": 10,
  "isLeapMonth": false,
  "gender": 1,
  "timeMode": "true_solar",
  "locationType": "domestic",
  "province": "fujian",
  "city": "fuzhou"
}
```

按四柱反查：

```json
{
  "mode": "pillars",
  "yearPillar": "戊寅",
  "monthPillar": "己未",
  "dayPillar": "己卯",
  "timePillar": "辛未"
}
```

#### GET /api/locations

返回国内省市和海外国家城市列表（含经度和时区信息）。

## MCP Server

### bazi-mcp

来自 cantian-ai 的八字 MCP Server，提供以下工具：

- `getBaziDetail` — 根据公历/农历时间计算完整八字信息
- `getSolarTimes` — 根据八字反查公历时间
- `getChineseCalendar` — 获取黄历信息

### bazi-mcp-custom

基于 bazi-mcp 的自定义版本，可按需扩展功能。

```bash
cd bazi-mcp
npm install
npm start
```

## macOS 持久化运行（launchd）

Web 应用已配置为 macOS 后台服务，开机自动启动：

```bash
# 启动
launchctl start com.caihaolun.bazi-web

# 停止
launchctl stop com.caihaolun.bazi-web

# 查看状态
launchctl list | grep bazi
```

配置文件位于 `~/Library/LaunchAgents/com.caihaolun.bazi-web.plist`。

## License

Private repository.
