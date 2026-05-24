(function e2eeDemo() {
  'use strict';

  var HKDF_INFO = new TextEncoder().encode('aastraa-e2ee-v1');

  function $(id) {
    return document.getElementById(id);
  }

  async function hkdf(ikm, salt, info, len) {
    var key = await crypto.subtle.importKey('raw', ikm, 'HKDF', false, ['deriveBits']);
    var bits = await crypto.subtle.deriveBits(
      { name: 'HKDF', hash: 'SHA-256', salt: salt, info: info },
      key,
      len * 8
    );
    return new Uint8Array(bits);
  }

  async function runBenchmark() {
    var timingEl = $('e2ee-timing');
    var statusEl = $('e2ee-status');
    if (!timingEl || !statusEl || !window.crypto || !crypto.subtle) {
      if (statusEl) statusEl.textContent = 'Web Crypto unavailable in this browser.';
      return;
    }

    statusEl.textContent = 'Running AES-256-GCM round-trip…';
    var sample = {
      employees: Array.from({ length: 20 }, function (_, i) {
        return { id: i + 1, name: 'Employee ' + (i + 1), salary_band: 'L' + ((i % 5) + 1) };
      }),
      note: 'Simulated HR API payload (~1 KB JSON)',
    };
    var plaintext = new TextEncoder().encode(JSON.stringify(sample));
    while (plaintext.byteLength < 900) {
      sample.pad = 'x'.repeat(100);
      plaintext = new TextEncoder().encode(JSON.stringify(sample));
    }

    var sessionId = 'demo-session-' + crypto.randomUUID();
    var aesRaw = crypto.getRandomValues(new Uint8Array(32));
    var aesKey = await crypto.subtle.importKey('raw', aesRaw, { name: 'AES-GCM', length: 256 }, false, [
      'encrypt',
      'decrypt',
    ]);

    var seq = 1;
    var nonceUuid = crypto.randomUUID();
    var ts = Date.now();
    var iv = crypto.getRandomValues(new Uint8Array(12));
    var aad = new TextEncoder().encode(sessionId + ':' + seq + ':' + nonceUuid + ':' + ts);

    var t0 = performance.now();
    var ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv: iv, additionalData: aad }, aesKey, plaintext);
    var decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: iv, additionalData: aad },
      aesKey,
      ct
    );
    var t1 = performance.now();
    var ms = (t1 - t0).toFixed(2);

    JSON.parse(new TextDecoder().decode(decrypted));
    timingEl.textContent = ms + ' ms';
    statusEl.textContent = 'Encrypted ' + plaintext.byteLength + ' bytes — keys stay in memory only.';
    timingEl.classList.remove('text-slate-400');
    timingEl.classList.add('text-emerald-600');
  }

  function init() {
    var btn = $('e2ee-run-demo');
    if (btn) btn.addEventListener('click', runBenchmark);
    if (document.getElementById('e2ee-showcase')) {
      runBenchmark();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
