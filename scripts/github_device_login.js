/* RapidMeta GitHub sign-in — DEVICE FLOW drop-in (Phase 2).
 *
 * NO CLIENT SECRET (correct for a static site). Needs only a public CLIENT_ID.
 * Login is required for exactly TWO things: (a) syncing across devices, (b)
 * collaborating (fork + PR dual screening). It is NEVER required to read, use an
 * app, dispute a number, save your own work locally, export, or download an
 * offline copy. No sign-up wall, nothing between a user and the work.
 *
 * ⚠️ HONEST CONSTRAINT (Codex-A confirmed): GitHub's device-flow token-poll POST
 * to github.com is CORS-blocked from a pure browser page. device-flow-no-secret
 * removes the SECRET but not the CORS wall. So one of these is required and MUST be
 * chosen by Mahmood:
 *   (i)  a minimal CORS token-broker (a tiny serverless relay that forwards the
 *        poll; holds NO secret — device flow needs none), OR
 *   (ii) a GitHub App backend, OR
 *   (iii) a user-supplied Personal Access Token (paste-once) — zero infra, most
 *        private, slightly more friction.
 * Set BROKER below to (i)'s URL, or set MODE='pat' for (iii).
 *
 * Wire-up: set CLIENT_ID (public, from Mahmood's registered OAuth App with Device
 * Flow enabled) and BROKER (or MODE='pat'). Nothing else. The secret never appears.
 */
(function (global) {
  var CFG = {
    CLIENT_ID: '__GITHUB_CLIENT_ID__',      // <- Mahmood sends this (public, safe to embed)
    BROKER: '',                              // <- (i) CORS token-broker URL, or '' to use PAT mode
    MODE: 'device',                          // 'device' | 'pat'
    SCOPES: 'public_repo',                   // least privilege: create issues/forks/PRs on public repos
  };

  async function startDeviceFlow() {
    if (CFG.MODE === 'pat') return patFlow();
    if (!CFG.BROKER) throw new Error('Device flow needs a CORS token-broker URL (or use MODE="pat").');
    // 1) request a device + user code (via broker to avoid CORS)
    var r = await fetch(CFG.BROKER + '/device/code', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: CFG.CLIENT_ID, scope: CFG.SCOPES })
    });
    var d = await r.json();  // { device_code, user_code, verification_uri, interval, expires_in }
    // 2) open GitHub with the code PRE-FILLED — user just clicks Authorise
    global.open(d.verification_uri + '?user_code=' + encodeURIComponent(d.user_code), '_blank');
    showCode(d.user_code);
    // 3) poll for the token (through the broker; no secret involved)
    var deadline = Date.now() + (d.expires_in || 900) * 1000;
    while (Date.now() < deadline) {
      await sleep((d.interval || 5) * 1000);
      var p = await fetch(CFG.BROKER + '/device/token', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: CFG.CLIENT_ID, device_code: d.device_code })
      });
      var t = await p.json();
      if (t.access_token) return onToken(t.access_token);
      if (t.error && t.error !== 'authorization_pending' && t.error !== 'slow_down') throw new Error(t.error);
    }
    throw new Error('Sign-in timed out.');
  }

  async function patFlow() {
    var tok = global.prompt('Paste a GitHub Personal Access Token (scope: public_repo). '
      + 'Create one at github.com/settings/tokens — it never leaves your browser.');
    if (tok) return onToken(tok.trim());
  }

  function onToken(token) {
    // token stays in this browser only (sessionStorage), never sent to us.
    try { global.sessionStorage.setItem('rm_gh_token', token); } catch (e) {}
    if (global.RapidMetaAuth && global.RapidMetaAuth.onLogin) global.RapidMetaAuth.onLogin(token);
    return token;
  }

  function showCode(code) {
    if (global.RapidMetaAuth && global.RapidMetaAuth.showCode) global.RapidMetaAuth.showCode(code);
  }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  global.RapidMetaAuth = Object.assign(global.RapidMetaAuth || {}, {
    config: CFG, signIn: startDeviceFlow,
    token: function () { try { return global.sessionStorage.getItem('rm_gh_token'); } catch (e) { return null; } },
    signOut: function () { try { global.sessionStorage.removeItem('rm_gh_token'); } catch (e) {} },
  });
})(typeof window !== 'undefined' ? window : globalThis);
