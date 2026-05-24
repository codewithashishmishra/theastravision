"""Open system browser for HRMS login; receive JWT on localhost callback."""

import secrets
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, quote, urlparse


SUCCESS_HTML = b"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Aastraa Tracker</title>
<style>
  body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc;
         display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
  .card { text-align: center; padding: 2rem; border-radius: 16px; background: #1e293b;
          border: 1px solid #475569; max-width: 400px; }
  h1 { color: #22c55e; font-size: 1.5rem; }
  p { color: #94a3b8; }
</style></head>
<body><div class="card"><h1>Signed in successfully</h1>
<p>You can close this tab and return to the Aastraa WFH Tracker app.</p></div></body></html>
"""

ERROR_HTML = b"""<!DOCTYPE html><html><body style="font-family:sans-serif;padding:2rem">
<h2>Login failed</h2><p>Return to the tracker app and try again.</p></body></html>"""


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _CallbackHandler(BaseHTTPRequestHandler):
    result: dict | None = None
    expected_state: str = ""

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        qs = parse_qs(parsed.query)
        flat = {k: v[0] if v else "" for k, v in qs.items()}
        if flat.get("error"):
            _CallbackHandler.result = {"error": flat.get("error", "login_failed")}
            body = ERROR_HTML
        elif flat.get("state") != _CallbackHandler.expected_state:
            _CallbackHandler.result = {"error": "invalid_state"}
            body = ERROR_HTML
        elif not flat.get("access_token"):
            _CallbackHandler.result = {"error": "missing_token"}
            body = ERROR_HTML
        else:
            _CallbackHandler.result = flat
            body = SUCCESS_HTML
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def login_via_browser(web_login_url: str, timeout: float = 180.0) -> dict:
    """
    Open HRMS login in browser; wait for redirect to http://127.0.0.1:<port>/callback.
    Returns dict with access_token, refresh_token, email, etc.
    """
    port = _free_port()
    state = secrets.token_urlsafe(24)
    redirect_uri = f"http://127.0.0.1:{port}/callback"
    sep = "&" if "?" in web_login_url else "?"
    login_url = (
        f"{web_login_url}{sep}tracker_redirect={quote(redirect_uri, safe='')}"
        f"&state={quote(state, safe='')}"
    )

    _CallbackHandler.result = None
    _CallbackHandler.expected_state = state
    server = HTTPServer(("127.0.0.1", port), _CallbackHandler)
    server.timeout = 1

    def serve():
        while _CallbackHandler.result is None:
            server.handle_request()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    # Brief delay so callback server is listening before browser opens
    import time
    time.sleep(0.3)
    webbrowser.open(login_url)
    thread.join(timeout=timeout)
    server.server_close()

    if _CallbackHandler.result is None:
        raise TimeoutError("Login timed out. Complete sign-in in the browser or try again.")
    if _CallbackHandler.result.get("error"):
        raise RuntimeError(_CallbackHandler.result.get("error", "Login failed"))
    return _CallbackHandler.result
