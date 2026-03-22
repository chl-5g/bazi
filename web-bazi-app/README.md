# Web Bazi App

一个前后端分离风格的八字生成 Web 项目：
- 前端：网页输入出生日期时间
- 后端：Python API 计算四柱八字

## 目录结构

- `backend/app.py`: Flask 后端接口
- `backend/requirements.txt`: Python 依赖
- `frontend/index.html`: 页面

## 启动方式

1. 安装依赖

```bash
cd /Users/caihaolun/testJava/web-bazi-app/backend
pip3 install -r requirements.txt
```

2. 启动后端

```bash
python3 app.py
```

3. 打开浏览器

访问 [http://localhost:8000](http://localhost:8000)

## API

- `POST /api/bazi`
- Body:

```json
{
  "datetime": "1998-07-31T14:10"
}
```
