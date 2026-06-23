/* ============================================================================
 * RapidMeta Living-Meta — Supabase auth + cross-device save-progress
 * ----------------------------------------------------------------------------
 * Drop-in, additive, backward-compatible. A single <script src="rapidmeta-auth.js">
 * tag on any living-meta app gives it:
 *   - email+password / Google sign-in, sign-up, sign-out (Supabase Auth)
 *   - a floating login widget (logged-out vs logged-in + email + logout)
 *   - per-user cross-device save/restore of the app's state
 *
 * Anonymous users are unaffected: the apps keep using localStorage locally.
 * Login is purely additive — it mirrors localStorage to Supabase so the same
 * user can resume on another device.
 *
 * SECURITY: only the project URL + publishable (anon) key live here. They are
 * designed to be public. All DB access is gated by Row Level Security so each
 * user can only touch their own rows (auth.uid() = user_id). Never put a
 * service_role / secret key in this file.
 * ========================================================================== */
(function () {
  'use strict';

  // ---- Config (public anon key — safe to embed in a static site) ----------
  var SUPABASE_URL = 'https://cfgywerxufcoutnplwhs.supabase.co';
  var SUPABASE_ANON_KEY = 'sb_publishable_DOHFZx59IvZPq3FonqbpXA_w7FCeftk';
  // Prefer the same-origin vendored copy (offline-resilient); fall back to CDN.
  var SUPABASE_LOCAL = 'vendor/supabase-js.min.js';
  var SUPABASE_CDN = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js';
  var TABLE = 'living_meta_progress';
  var SCROLL_FLAG = 'rapidmeta_restore_scroll';

  if (window.__rapidMetaAuthLoaded) return;     // idempotent guard
  window.__rapidMetaAuthLoaded = true;

  // ---- Identify which living-meta app this page is -------------------------
  function appId() {
    try {
      var p = decodeURIComponent(location.pathname || '');
      var name = p.split('/').filter(Boolean).pop() || 'index.html';
      return name;
    } catch (e) { return 'index.html'; }
  }
  var APP_ID = appId();

  // ---- Capture / restore app state (localStorage is the source of truth) ---
  // The living-meta apps autosave their full working state (inputs, selected
  // studies, notes) into versioned localStorage keys and rehydrate from them on
  // load. So a faithful "resume where you left off" = snapshot those keys +
  // scroll, write them back, reload.
  function captureState() {
    var ls = {};
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (!k) continue;
        if (k.indexOf('sb-') === 0) continue;            // supabase session
        if (k.indexOf('rapidmeta_auth') === 0) continue; // our own keys
        ls[k] = localStorage.getItem(k);
      }
    } catch (e) {}
    return {
      v: 1,
      ls: ls,
      scrollY: window.scrollY || 0,
      url: location.href,
      title: document.title || APP_ID,
      ts: new Date().toISOString()
    };
  }

  function applyState(state) {
    if (!state || !state.ls) return;
    try {
      Object.keys(state.ls).forEach(function (k) {
        try { localStorage.setItem(k, state.ls[k]); } catch (e) {}
      });
      try { sessionStorage.setItem(SCROLL_FLAG, String(state.scrollY || 0)); } catch (e) {}
    } catch (e) {}
    // The apps read localStorage at init — reload so they rehydrate the state.
    location.reload();
  }

  // Restore scroll after a reload triggered by applyState()
  function restoreScrollIfFlagged() {
    try {
      var y = sessionStorage.getItem(SCROLL_FLAG);
      if (y !== null) {
        sessionStorage.removeItem(SCROLL_FLAG);
        window.setTimeout(function () { window.scrollTo(0, parseInt(y, 10) || 0); }, 400);
      }
    } catch (e) {}
  }

  // ---- Load supabase-js (UMD) from CDN, then boot --------------------------
  function loadScript(src, onload, onerror) {
    var s = document.createElement('script');
    s.src = src;
    s.async = true;
    s.onload = onload;
    s.onerror = onerror;
    document.head.appendChild(s);
  }
  function loadSupabase(cb) {
    if (window.supabase && window.supabase.createClient) return cb();
    // Try the vendored (same-origin) build first, then CDN as a fallback.
    loadScript(SUPABASE_LOCAL, cb, function () {
      loadScript(SUPABASE_CDN, cb, function () {
        console.warn('[rapidmeta-auth] supabase-js failed to load (offline?). Anonymous mode only.');
      });
    });
  }

  // ======================================================================
  // Boot
  // ======================================================================
  function boot() {
    restoreScrollIfFlagged();
    var sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    var ui = buildWidget();
    var currentUser = null;
    var lastSavedAt = null;

    // ---- Auth state -------------------------------------------------------
    sb.auth.getSession().then(function (res) {
      handleSession(res && res.data ? res.data.session : null);
    });
    sb.auth.onAuthStateChange(function (_evt, session) {
      handleSession(session);
    });

    function handleSession(session) {
      currentUser = session && session.user ? session.user : null;
      renderState();
      if (currentUser) loadProgress();
    }

    // ---- DB: load / save --------------------------------------------------
    function loadProgress() {
      sb.from(TABLE).select('state, updated_at')
        .eq('meta_app_id', APP_ID).maybeSingle()
        .then(function (res) {
          if (res.error) { console.warn('[rapidmeta-auth] load error', res.error.message); return; }
          if (res.data && res.data.state) {
            lastSavedAt = res.data.updated_at;
            ui.setSaved(lastSavedAt);
            offerRestore(res.data.state, res.data.updated_at);
          }
        });
    }

    function saveProgress(opts) {
      if (!currentUser) return Promise.resolve();
      var row = {
        user_id: currentUser.id,
        meta_app_id: APP_ID,
        state: captureState(),
        updated_at: new Date().toISOString()
      };
      ui.setStatus('Saving…');
      return sb.from(TABLE).upsert(row, { onConflict: 'user_id,meta_app_id' })
        .then(function (res) {
          if (res.error) { ui.setStatus('Save failed'); console.warn('[rapidmeta-auth] save error', res.error.message); return; }
          lastSavedAt = row.updated_at;
          ui.setSaved(lastSavedAt);
          ui.setStatus(opts && opts.silent ? '' : 'Saved ✓');
        });
    }

    // ---- Debounced autosave on any input/change ---------------------------
    var saveTimer = null;
    function scheduleAutosave() {
      if (!currentUser) return;
      if (saveTimer) clearTimeout(saveTimer);
      saveTimer = setTimeout(function () { saveProgress({ silent: true }); }, 2000);
    }
    document.addEventListener('input', scheduleAutosave, true);
    document.addEventListener('change', scheduleAutosave, true);

    // ---- Restore prompt (never clobbers silently) -------------------------
    function offerRestore(state, when) {
      ui.showToast(
        'Saved progress found' + (when ? ' (' + relTime(when) + ')' : '') + '. Restore it?',
        [
          { label: 'Restore', primary: true, onClick: function () { applyState(state); } },
          { label: 'Dismiss', onClick: function () {} }
        ]
      );
    }

    // ---- Wire widget buttons ---------------------------------------------
    ui.onSignIn = function (email, pw) {
      return sb.auth.signInWithPassword({ email: email, password: pw });
    };
    ui.onSignUp = function (email, pw) {
      return sb.auth.signUp({ email: email, password: pw, options: { emailRedirectTo: location.href } });
    };
    ui.onGoogle = function () {
      return sb.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: location.href } });
    };
    ui.onSignOut = function () { return sb.auth.signOut(); };
    ui.onSave = function () { return saveProgress(); };

    function renderState() {
      ui.setUser(currentUser ? (currentUser.email || 'Signed in') : null);
    }
    renderState();
  }

  function relTime(iso) {
    try {
      var then = new Date(iso).getTime();
      var diff = (new Date().getTime() - then) / 1000;
      if (diff < 60) return 'just now';
      if (diff < 3600) return Math.floor(diff / 60) + ' min ago';
      if (diff < 86400) return Math.floor(diff / 3600) + ' h ago';
      return Math.floor(diff / 86400) + ' d ago';
    } catch (e) { return ''; }
  }

  // ======================================================================
  // Widget (isolated in a Shadow DOM so app CSS can't touch it)
  // ======================================================================
  function buildWidget() {
    var host = document.createElement('div');
    host.id = 'rapidmeta-auth-host';
    host.style.cssText = 'position:fixed;z-index:2147483000;bottom:16px;right:16px;';
    (document.body || document.documentElement).appendChild(host);
    var root = host.attachShadow ? host.attachShadow({ mode: 'open' }) : host;

    root.innerHTML = [
      '<style>',
      ':host,*{box-sizing:border-box;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;}',
      '.pill{display:flex;align-items:center;gap:8px;background:#0f172a;color:#e2e8f0;border:1px solid #334155;',
      '  border-radius:999px;padding:8px 14px;font-size:13px;box-shadow:0 6px 24px rgba(0,0,0,.35);cursor:pointer;}',
      '.pill:hover{border-color:#14b8a6;}',
      '.dot{width:8px;height:8px;border-radius:50%;background:#64748b;}',
      '.dot.on{background:#10b981;}',
      '.email{max-width:170px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}',
      '.btn{border:none;border-radius:8px;padding:7px 12px;font-size:13px;font-weight:600;cursor:pointer;}',
      '.btn.teal{background:#14b8a6;color:#042f2e;}',
      '.btn.ghost{background:transparent;color:#94a3b8;border:1px solid #334155;}',
      '.btn.teal:hover{background:#2dd4bf;} .btn.ghost:hover{color:#e2e8f0;border-color:#475569;}',
      '.panel{position:absolute;bottom:48px;right:0;width:280px;background:#0f172a;color:#e2e8f0;border:1px solid #334155;',
      '  border-radius:16px;padding:16px;box-shadow:0 12px 40px rgba(0,0,0,.5);display:none;}',
      '.panel.open{display:block;}',
      '.panel h4{margin:0 0 10px;font-size:14px;font-weight:700;}',
      '.panel input{width:100%;margin:6px 0;padding:9px 10px;border-radius:8px;border:1px solid #334155;',
      '  background:#1e293b;color:#e2e8f0;font-size:13px;}',
      '.row{display:flex;gap:8px;margin-top:8px;}',
      '.row .btn{flex:1;}',
      '.muted{color:#94a3b8;font-size:11px;margin-top:8px;}',
      '.err{color:#f87171;font-size:12px;margin-top:6px;min-height:14px;}',
      '.status{color:#5eead4;font-size:11px;margin-left:4px;}',
      '.gbtn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;margin-top:8px;',
      '  background:#fff;color:#1f2937;border:none;border-radius:8px;padding:9px;font-size:13px;font-weight:600;cursor:pointer;}',
      '.gbtn:hover{background:#f1f5f9;}',
      '.toast{position:absolute;bottom:48px;right:0;width:280px;background:#0f172a;color:#e2e8f0;border:1px solid #14b8a6;',
      '  border-radius:14px;padding:14px;box-shadow:0 12px 40px rgba(0,0,0,.5);display:none;}',
      '.toast.open{display:block;} .toast p{margin:0 0 10px;font-size:13px;}',
      '.divider{height:1px;background:#334155;margin:12px 0;}',
      '.link{background:none;border:none;color:#5eead4;font-size:12px;cursor:pointer;padding:0;text-decoration:underline;}',
      '</style>',
      '<div class="toast" id="toast"><p id="toast-msg"></p><div class="row" id="toast-actions"></div></div>',
      '<div class="panel" id="panel">',
      '  <div id="logged-out">',
      '    <h4>Save your progress</h4>',
      '    <button class="gbtn" id="google">',
      '      <svg width="16" height="16" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.6 2.4 30.1 0 24 0 14.6 0 6.4 5.4 2.5 13.3l7.9 6.1C12.3 13.3 17.6 9.5 24 9.5z"/><path fill="#4285F4" d="M46.1 24.6c0-1.6-.1-3.1-.4-4.6H24v9.1h12.4c-.5 2.9-2.1 5.3-4.6 7l7.1 5.5c4.1-3.8 6.5-9.4 6.5-17z"/><path fill="#FBBC05" d="M10.4 28.6c-.5-1.4-.8-2.9-.8-4.6s.3-3.2.8-4.6l-7.9-6.1C.9 16.5 0 20.1 0 24s.9 7.5 2.5 10.7l7.9-6.1z"/><path fill="#34A853" d="M24 48c6.1 0 11.3-2 15-5.5l-7.1-5.5c-2 1.3-4.6 2.1-7.9 2.1-6.4 0-11.7-3.8-13.6-9.4l-7.9 6.1C6.4 42.6 14.6 48 24 48z"/></svg>',
      '      Continue with Google</button>',
      '    <div class="divider"></div>',
      '    <input id="email" type="email" placeholder="you@example.com" autocomplete="email">',
      '    <input id="password" type="password" placeholder="Password" autocomplete="current-password">',
      '    <div class="row"><button class="btn teal" id="signin">Log in</button>',
      '      <button class="btn ghost" id="signup">Sign up</button></div>',
      '    <div class="err" id="err"></div>',
      '    <div class="muted">Optional. Anonymous use still works — progress just stays on this device.</div>',
      '  </div>',
      '  <div id="logged-in" style="display:none">',
      '    <h4>Signed in</h4>',
      '    <div class="muted" id="who" style="margin-top:0"></div>',
      '    <div class="row"><button class="btn teal" id="save">Save progress</button>',
      '      <button class="btn ghost" id="signout">Log out</button></div>',
      '    <div class="muted" id="saved-at"></div>',
      '  </div>',
      '</div>',
      '<div class="pill" id="pill"><span class="dot" id="dot"></span>',
      '  <span class="email" id="pill-label">Sign in to save</span>',
      '  <span class="status" id="status"></span></div>'
    ].join('');

    var $ = function (id) { return root.getElementById(id); };
    var api = { onSignIn: null, onSignUp: null, onGoogle: null, onSignOut: null, onSave: null };

    function togglePanel() { $('panel').classList.toggle('open'); $('toast').classList.remove('open'); }
    $('pill').addEventListener('click', togglePanel);

    $('signin').addEventListener('click', function () { doAuth(api.onSignIn); });
    $('signup').addEventListener('click', function () { doAuth(api.onSignUp, true); });
    $('google').addEventListener('click', function () { if (api.onGoogle) api.onGoogle(); });
    $('signout').addEventListener('click', function () { if (api.onSignOut) api.onSignOut(); $('panel').classList.remove('open'); });
    $('save').addEventListener('click', function () { if (api.onSave) api.onSave(); });

    function doAuth(fn, isSignup) {
      if (!fn) return;
      $('err').textContent = '';
      var email = $('email').value.trim();
      var pw = $('password').value;
      if (!email || !pw) { $('err').textContent = 'Email and password required.'; return; }
      fn(email, pw).then(function (res) {
        if (res && res.error) { $('err').textContent = res.error.message; return; }
        if (isSignup && res && res.data && res.data.user && !res.data.session) {
          $('err').style.color = '#5eead4';
          $('err').textContent = 'Check your email to confirm your account.';
        } else {
          $('panel').classList.remove('open');
        }
      }).catch(function (e) { $('err').textContent = String(e && e.message || e); });
    }

    api.setUser = function (email) {
      if (email) {
        $('dot').classList.add('on');
        $('pill-label').textContent = email;
        $('logged-out').style.display = 'none';
        $('logged-in').style.display = 'block';
        $('who').textContent = email;
      } else {
        $('dot').classList.remove('on');
        $('pill-label').textContent = 'Sign in to save';
        $('logged-out').style.display = 'block';
        $('logged-in').style.display = 'none';
        $('saved-at').textContent = '';
      }
    };
    api.setStatus = function (txt) {
      $('status').textContent = txt || '';
      if (txt && /✓|Saved/.test(txt)) setTimeout(function () { $('status').textContent = ''; }, 2500);
    };
    api.setSaved = function (iso) {
      $('saved-at').textContent = iso ? ('Last saved ' + relTime(iso)) : '';
    };
    api.showToast = function (msg, actions) {
      $('toast-msg').textContent = msg;
      var box = $('toast-actions');
      box.innerHTML = '';
      (actions || []).forEach(function (a) {
        var b = document.createElement('button');
        b.className = 'btn ' + (a.primary ? 'teal' : 'ghost');
        b.style.flex = '1';
        b.textContent = a.label;
        b.addEventListener('click', function () { $('toast').classList.remove('open'); if (a.onClick) a.onClick(); });
        box.appendChild(b);
      });
      $('toast').classList.add('open');
    };
    return api;
  }

  // ---- Go -----------------------------------------------------------------
  function start() { loadSupabase(function () { if (window.supabase && window.supabase.createClient) boot(); }); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
