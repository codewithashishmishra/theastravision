/**
 * Public visit counter (free CountAPI) + dynamic JSON for display & schema.
 * Counts once per browser session per day to limit refresh inflation.
 */
(function () {
  const NAMESPACE = 'theastravision-aastraa';
  const SESSION_KEY = 'aastraa_visit_counted';
  const API_BASE = 'https://api.countapi.xyz';

  function todayKey() {
    return 'daily-' + new Date().toISOString().slice(0, 10);
  }

  function apiGet(key) {
    return fetch(API_BASE + '/get/' + NAMESPACE + '/' + key)
      .then((r) => r.json())
      .then((d) => (typeof d.value === 'number' ? d.value : 0))
      .catch(() => null);
  }

  function apiHit(key) {
    return fetch(API_BASE + '/hit/' + NAMESPACE + '/' + key)
      .then((r) => r.json())
      .then((d) => (typeof d.value === 'number' ? d.value : null))
      .catch(() => null);
  }

  function formatNum(n) {
    if (n == null) return '—';
    return Number(n).toLocaleString('en-IN');
  }

  function renderStats(stats) {
    const dailyEl = document.getElementById('visit-daily-count');
    const totalEl = document.getElementById('visit-total-count');
    const dateEl = document.getElementById('visit-stats-date');
    const jsonEl = document.getElementById('visit-stats-data');

    if (dailyEl) dailyEl.textContent = formatNum(stats.daily);
    if (totalEl) totalEl.textContent = formatNum(stats.total);
    if (dateEl) dateEl.textContent = stats.date;

    if (jsonEl) {
      jsonEl.textContent = JSON.stringify(stats, null, 2);
    }

    updateInteractionSchema(stats.total);
  }

  function updateInteractionSchema(total) {
    if (!total || total < 1) return;
    const el = document.getElementById('visit-interaction-schema');
    if (!el) return;
    el.textContent = JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'InteractionCounter',
      interactionType: 'https://schema.org/ViewAction',
      name: 'AASTRAA HRMS website views',
      userInteractionCount: total,
    });
  }

  async function loadStats(recordVisit) {
    const date = new Date().toISOString().slice(0, 10);
    const dailyKey = todayKey();

    let daily = await apiGet(dailyKey);
    let total = await apiGet('total');

    if (recordVisit && !sessionStorage.getItem(SESSION_KEY)) {
      sessionStorage.setItem(SESSION_KEY, '1');
      const hitDaily = await apiHit(dailyKey);
      const hitTotal = await apiHit('total');
      if (hitDaily != null) daily = hitDaily;
      if (hitTotal != null) total = hitTotal;
    }

    if (daily == null && total == null) {
      try {
        const res = await fetch('data/visit-stats.json', { cache: 'no-store' });
        if (res.ok) {
          const fallback = await res.json();
          if (daily == null) daily = fallback.daily ?? 0;
          if (total == null) total = fallback.total ?? 0;
        }
      } catch (_) { /* ignore */ }
    }

    const stats = {
      site: 'https://theastravision.com/',
      product: 'AASTRAA HRMS',
      date,
      daily: daily ?? 0,
      total: total ?? 0,
      updatedAt: new Date().toISOString(),
      source: 'countapi',
    };

    renderStats(stats);
    if (typeof window !== 'undefined') {
      window.AASTRAA_VISIT_STATS = stats;
    }
    return stats;
  }

  document.addEventListener('DOMContentLoaded', () => loadStats(true));
})();
