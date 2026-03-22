/**
 * AI 算命 / 程序化解读入口（占位）
 * 传参仅含：四柱、出生地、性别（见 buildAiPayload）。
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
      var payload = buildAiPayload(ctx);
      if (!payload) {
        out.textContent = '无法组装传参，请确认已排出四柱。';
        return;
      }
      // 占位：后续在此 POST payload 或接 MCP / 自建 API
      out.innerHTML =
        '<p style="margin:0 0 8px;color:var(--muted);font-size:13px">（占位）以下为接入 AI/规则引擎时建议传入的 JSON（仅四柱、出生地、性别）：</p>' +
        '<pre style="margin:0;font-size:12px;overflow:auto;max-height:200px;background:var(--panel-alt);padding:8px;border-radius:6px;border:1px solid var(--border)">' +
        escapeHtml(JSON.stringify(payload, null, 2)) +
        '</pre>';
    });
  }

  /**
   * 仅返回：四柱（年柱/月柱/日柱/时柱）、出生地、性别（男/女）
   * @param {object} data — 通常为 __lastBaziResult，可带 _ai_birth_place、_ai_gender 作兜底
   */
  function buildAiPayload(data) {
    if (!data || typeof data !== 'object') return null;
    var y = data.year_pillar || '';
    var m = data.month_pillar || '';
    var d = data.day_pillar || '';
    var t = data.time_pillar || '';
    if (!y && data.bazi) {
      var parts = String(data.bazi)
        .trim()
        .split(/\s+/)
        .filter(Boolean);
      if (parts.length >= 4) {
        y = parts[0];
        m = parts[1];
        d = parts[2];
        t = parts[3];
      }
    }
    if (!y && !m && !d && !t) return null;

    var genderRaw =
      data.yun && typeof data.yun.gender !== 'undefined' && data.yun.gender !== null
        ? data.yun.gender
        : data._ai_gender !== undefined && data._ai_gender !== ''
          ? parseInt(String(data._ai_gender), 10)
          : null;
    var genderLabel =
      genderRaw === 1 ? '男' : genderRaw === 0 ? '女' : genderRaw != null && !isNaN(genderRaw) ? String(genderRaw) : '';

    var birth =
      (data.location_label && String(data.location_label).trim()) ||
      (data._ai_birth_place && String(data._ai_birth_place).trim()) ||
      '';

    return {
      四柱: {
        年柱: y,
        月柱: m,
        日柱: d,
        时柱: t,
      },
      出生地: birth,
      性别: genderLabel,
    };
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  window.AiFortune = { bind: bind, buildAiPayload: buildAiPayload };
})();
