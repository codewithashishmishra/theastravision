"""Self-contained HTML login for desktop tracker (no Next.js required)."""

import json
import re

BROWSER_LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Aastraa WFH Tracker — Sign in</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; min-height: 100vh; font-family: "Segoe UI", system-ui, sans-serif;
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
      display: flex; align-items: center; justify-content: center; padding: 24px;
      color: #f8fafc;
    }}
    .card {{
      width: 100%; max-width: 400px; background: #1e293b; border: 1px solid #475569;
      border-radius: 20px; padding: 32px; box-shadow: 0 25px 50px rgba(0,0,0,.4);
    }}
    .logo {{ text-align: center; margin-bottom: 8px; font-size: 48px; }}
    h1 {{ text-align: center; font-size: 1.35rem; margin: 0 0 8px; }}
    .sub {{ text-align: center; color: #94a3b8; font-size: 0.9rem; margin-bottom: 24px; }}
    label {{ display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px; }}
    input {{
      width: 100%; padding: 12px 14px; margin-bottom: 16px; border-radius: 10px;
      border: 1px solid #475569; background: #334155; color: #f8fafc; font-size: 1rem;
    }}
    input:focus {{ outline: none; border-color: #f97316; }}
    button {{
      width: 100%; padding: 14px; border: none; border-radius: 10px;
      background: #f97316; color: white; font-weight: 600; font-size: 1rem; cursor: pointer;
    }}
    button:hover {{ background: #ea580c; }}
    button:disabled {{ opacity: 0.6; cursor: wait; }}
    .err {{ color: #f87171; font-size: 0.85rem; margin-top: 12px; text-align: center; display: none; }}
    .err.show {{ display: block; }}
    #totp-box {{ display: none; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">🟠</div>
    <h1>WFH Tracker Sign in</h1>
    <p class="sub">Use your HRMS email and password.<br/>You will return to the desktop app automatically.</p>
    <form id="login-form">
      <div id="cred-box">
        <label>Email</label>
        <input type="email" id="email" name="email" required placeholder="you@company.com" autocomplete="username" />
        <label>Password</label>
        <input type="password" id="password" name="password" required placeholder="••••••••" autocomplete="current-password" />
      </div>
      <div id="totp-box">
        <label>Authenticator code (6 digits)</label>
        <input type="text" id="totp" maxlength="6" pattern="[0-9]{{6}}" placeholder="000000" />
      </div>
      <button type="submit" id="submit-btn">Sign in</button>
      <p class="err" id="error"></p>
    </form>
  </div>
  <script>
    const API = "{api_base}";
    const trackerRedirect = {tracker_redirect_js};
    const state = {state_js};
    let preAuthToken = "";

    const errEl = document.getElementById("error");
    const totpBox = document.getElementById("totp-box");
    const credBox = document.getElementById("cred-box");
    const btn = document.getElementById("submit-btn");

    function showErr(msg) {{
      errEl.textContent = msg;
      errEl.classList.add("show");
    }}

    function redirectWithTokens(access, email) {{
      const u = new URL(trackerRedirect);
      u.searchParams.set("access_token", access);
      if (state) u.searchParams.set("state", state);
      if (email) u.searchParams.set("email", email);
      window.location.href = u.toString();
    }}

    async function finishLogin(access, refresh, email) {{
      const boot = await fetch(API + "/tracker/auth/bootstrap/", {{
        headers: {{ Authorization: "Bearer " + access }}
      }});
      if (boot.status === 403) {{
        showErr("No employee profile linked to this account. Ask HR or run: python manage.py seed_wfh");
        btn.disabled = false;
        btn.textContent = "Sign in";
        return;
      }}
      if (!boot.ok) {{
        showErr("Could not verify tracker access.");
        btn.disabled = false;
        btn.textContent = "Sign in";
        return;
      }}
      redirectWithTokens(access, email);
    }}

    document.getElementById("login-form").addEventListener("submit", async (e) => {{
      e.preventDefault();
      errEl.classList.remove("show");
      btn.disabled = true;
      btn.textContent = "Signing in…";
      const email = document.getElementById("email").value.trim();
      try {{
        if (totpBox.style.display === "block") {{
          const code = document.getElementById("totp").value.trim();
          const r = await fetch(API + "/auth/totp/verify-login/", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ pre_auth_token: preAuthToken, code }})
          }});
          const d = await r.json();
          if (!r.ok) throw new Error(d.error || "Invalid code");
          await finishLogin(d.access_token, d.refresh_token, email);
          return;
        }}
        const r = await fetch(API + "/auth/login/password/", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          credentials: "include",
          body: JSON.stringify({{ email, password: document.getElementById("password").value }})
        }});
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || "Login failed");
        if (d.requires_totp) {{
          preAuthToken = d.pre_auth_token;
          credBox.style.display = "none";
          totpBox.style.display = "block";
          btn.textContent = "Verify";
          btn.disabled = false;
          return;
        }}
        await finishLogin(d.access_token, d.refresh_token, email);
      }} catch (ex) {{
        showErr(ex.message || "Login failed");
        btn.disabled = false;
        btn.textContent = totpBox.style.display === "block" ? "Verify" : "Sign in";
      }}
    }});
  </script>
</body>
</html>
"""


def _allowed_redirect(url: str) -> bool:
    return bool(re.match(r"^http://(127\.0\.0\.1|localhost):\d+/callback", url))


def render_browser_login_page(request, api_base: str) -> str:
    tracker_redirect = request.GET.get("tracker_redirect", "")
    state = request.GET.get("state", "")
    if not _allowed_redirect(tracker_redirect):
        tracker_redirect = ""
    return BROWSER_LOGIN_HTML.format(
        api_base=api_base.rstrip("/"),
        tracker_redirect_js=json.dumps(tracker_redirect),
        state_js=json.dumps(state),
    )
