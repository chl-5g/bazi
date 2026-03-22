/**
 * AI 算命 / 程序化解读入口（占位）
 * 后续逻辑可在此文件扩展，或调用 web-bazi-app/ai-divination 下的后端模块。
 */
(function () {
  'use strict';

  function bind(btnId, outputId, getContext) {
    var btn = document.getElementById(btnId);
    var out = document.getElementById(outputId);
    if (!btn || !out) return;

    btn.addEventListener('click', function () {
      var ctx = typeof getContext === 'function' ? getContext() : null;
      out.style.display = 'block';
      if (!ctx) {
        out.textContent = '请先完成排盘后再使用 AI算命。';
        return;
      }
      // 占位：后续在此调用接口或本地推演
      out.innerHTML =
        '<p style="margin:0 0 8px;color:var(--muted);font-size:13px">（占位）已缓存本次排盘结果，可在此接入程序化解读。</p>' +
        '<pre style="margin:0;font-size:12px;overflow:auto;max-height:200px;background:var(--panel-alt);padding:8px;border-radius:6px;border:1px solid var(--border)">' +
        escapeHtml(JSON.stringify(summarizeContext(ctx), null, 2)) +
        '</pre>';
    });
  }

  function summarizeContext(data) {
    if (!data || typeof data !== 'object') return {};
    return {
      solar_datetime: data.solar_datetime,
      lunar_date: data.lunar_date,
      bazi: [data.year_pillar, data.month_pillar, data.day_pillar, data.time_pillar].filter(Boolean).join(' '),
      gender: data.yun && data.yun.gender,
      time_mode: data.time_mode,
      location_label: data.location_label,
    };
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  window.AiFortune = { bind: bind };
})();
