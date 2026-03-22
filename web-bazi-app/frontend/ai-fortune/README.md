# 前端 AI 算命入口

- `ai-fortune.js`：页面「AI算命」按钮与展示区的绑定；后续可在此发起请求或编排调用链。
- 排盘成功后，完整结果会缓存在 `window.__lastBaziResult`，供本模块读取。
