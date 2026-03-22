/**
 * 本地开发：留空则请求同源的 /api（Flask）。
 * 部署在 GitHub Pages 时：改为你的排盘 API 根地址（须 HTTPS），例如：
 * window.__BAZI_API_BASE__ = 'https://your-bazi-api.example.com';
 */
window.__BAZI_API_BASE__ = window.__BAZI_API_BASE__ || '';
