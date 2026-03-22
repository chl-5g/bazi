# 前端 AI 算命入口

- `ai-fortune.js`：页面「AI算命」按钮与展示区的绑定；后续可在此 `POST` 或接 MCP。
- 排盘成功后，完整结果缓存在 `window.__lastBaziResult`；点击按钮时用 `buildAiFortuneContext()` 合并表单上的**出生地、性别**（接口里已有则优先用接口值）。

## 建议传参（仅三项）

`AiFortune.buildAiPayload(ctx)` 或占位展示中的 JSON 结构：

```json
{
  "四柱": { "年柱": "", "月柱": "", "日柱": "", "时柱": "" },
  "出生地": "",
  "性别": "男"
}
```

- **四柱**：来自接口的 `year_pillar` 等；若无则解析顶层 `bazi` 空格分隔四字。
- **出生地**：`location_label`，否则用表单省市区文案。
- **性别**：`yun.gender`（`1` 男 / `0` 女），否则用表单性别。
