/*! coi-serviceworker — minimal GitHub-Pages-friendly COOP/COEP SW
 * Adds Cross-Origin-Opener-Policy + Cross-Origin-Embedder-Policy to responses,
 * enabling SharedArrayBuffer / cross-origin isolation for WebR on static hosts.
 *
 * Usage: <script src="coi-serviceworker.js"></script> at the top of <head>.
 * First load registers the SW and reloads; subsequent loads are already isolated.
 * Pattern origin: https://github.com/gzuidhof/coi-serviceworker (MIT).
 */
if (typeof window === 'undefined') {
  // --- Service Worker scope ---
  self.addEventListener('install', function () { self.skipWaiting(); });
  self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });
  self.addEventListener('fetch', function (event) {
    if (event.request.cache === 'only-if-cached' && event.request.mode !== 'same-origin') return;
    event.respondWith(
      fetch(event.request).then(function (response) {
        if (response.status === 0) return response;
        var nh = new Headers(response.headers);
        nh.set('Cross-Origin-Embedder-Policy', 'require-corp');
        nh.set('Cross-Origin-Opener-Policy',   'same-origin');
        // Allow cross-origin resources (webr.r-wasm.org) to load
        if (!nh.has('Cross-Origin-Resource-Policy')) {
          nh.set('Cross-Origin-Resource-Policy', 'cross-origin');
        }
        return new Response(response.body, {
          status: response.status, statusText: response.statusText, headers: nh
        });
      })
    );
  });
} else {
  // --- Page scope ---
  (function () {
    if (window.crossOriginIsolated !== false) return; // already isolated or env unsupported
    if (!window.isSecureContext) { console.warn('[coi-sw] insecure context'); return; }
    if (!('serviceWorker' in navigator)) { console.warn('[coi-sw] SW unsupported'); return; }

    var swUrl = document.currentScript ? document.currentScript.src : 'coi-serviceworker.js';
    navigator.serviceWorker.register(swUrl, { scope: './' }).then(function (reg) {
      reg.addEventListener('updatefound', function () {
        var sw = reg.installing;
        if (!sw) return;
        sw.addEventListener('statechange', function () {
          if (sw.state === 'activated' && !window.crossOriginIsolated) {
            window.location.reload();
          }
        });
      });
      if (reg.active && !navigator.serviceWorker.controller) {
        window.location.reload();
      }
    }).catch(function (e) { console.warn('[coi-sw] register failed:', e); });
  })();
}
