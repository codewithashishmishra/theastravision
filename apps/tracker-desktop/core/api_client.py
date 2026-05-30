import httpx

from core.auth import save_session
from core.config import API_BASE_URL
from core.e2ee_client import E2EEClient
from core.gcm_crypto import ALGORITHM, data_key_from_b64


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class PlatformCooldownError(ApiError):
    def __init__(self, message: str, retry_after_seconds: int = 300):
        super().__init__(message, 503)
        self.retry_after_seconds = retry_after_seconds
        self.code = "PLATFORM_COOLDOWN"


class ApiClient:
    def __init__(self):
        self.base = API_BASE_URL
        self.access_token = None
        self.refresh_token = None
        self.email = None
        self.encryption_key_b64 = None
        self.encryption_algorithm = ALGORITHM
        self.e2ee = E2EEClient(self.base)

    @property
    def data_key(self) -> bytes | None:
        if not self.encryption_key_b64:
            return None
        try:
            return data_key_from_b64(self.encryption_key_b64)
        except ValueError:
            return None

    def _apply_auth_payload(self, data: dict):
        self.access_token = data["access_token"]
        if data.get("refresh_token"):
            self.refresh_token = data["refresh_token"]
        if data.get("encryption_key"):
            self.encryption_key_b64 = data["encryption_key"]
        if data.get("encryption_algorithm"):
            self.encryption_algorithm = data["encryption_algorithm"]

    def _persist_session(self):
        if self.email and self.refresh_token:
            save_session(
                self.email,
                self.access_token,
                self.refresh_token,
                self.encryption_key_b64,
            )

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        if self.encryption_algorithm:
            h["X-Tracker-Encryption"] = self.encryption_algorithm
        h.update(self.e2ee.auth_headers())
        return h

    def _parse_error(self, response: httpx.Response) -> str:
        try:
            body = response.json()
            try:
                body = self.e2ee.decrypt_if_needed(body)
            except Exception:
                pass
            if isinstance(body, dict):
                return (
                    body.get("error")
                    or body.get("detail")
                    or body.get("message")
                    or str(body)
                )
        except Exception:
            pass
        return response.text or f"HTTP {response.status_code}"

    def _decode_payload(self, response: httpx.Response):
        if not response.content:
            return {}
        body = response.json()
        return self.e2ee.decrypt_if_needed(body)

    def _request_e2ee(self, method: str, url: str, *, timeout: float = 30.0, retry_on_handshake: bool = True, **kwargs):
        self.e2ee.ensure_session()
        response = httpx.request(method, url, headers=self._headers(), timeout=timeout, **kwargs)
        if response.status_code == 428 and retry_on_handshake:
            try:
                body = response.json()
            except Exception:
                body = {}
            if isinstance(body, dict) and body.get("code") in {"E2EE_HANDSHAKE_REQUIRED", "E2EE_SESSION_EXPIRED"}:
                self.e2ee.reset()
                self.e2ee.ensure_session()
                response = httpx.request(method, url, headers=self._headers(), timeout=timeout, **kwargs)
        return response

    @staticmethod
    def _check_cooldown(response: httpx.Response):
        if response.status_code != 503:
            return
        try:
            body = response.json()
            if isinstance(body, dict) and body.get("code") == "PLATFORM_COOLDOWN":
                retry = int(body.get("retry_after_seconds") or 300)
                raise PlatformCooldownError(
                    body.get("message")
                    or "Server is cooling down (~5 min). Data will be queued locally.",
                    retry,
                )
        except PlatformCooldownError:
            raise
        except Exception:
            pass

    def exchange_browser_token(self, access_token: str) -> dict:
        """Get tracker-only session (independent from web logout)."""
        r = self._request_e2ee(
            "POST",
            f"{self.base}/tracker/auth/session/exchange/",
            json={"access_token": access_token},
        )
        if r.status_code >= 400:
            raise ApiError(self._parse_error(r), r.status_code)
        data = self._decode_payload(r)
        self._apply_auth_payload(data)
        self.email = data.get("email")
        self._persist_session()
        return data

    def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return False
        r = self._request_e2ee(
            "POST",
            f"{self.base}/tracker/auth/refresh/",
            json={"refresh_token": self.refresh_token},
        )
        if r.status_code >= 400:
            return False
        data = self._decode_payload(r)
        self._apply_auth_payload(data)
        self._persist_session()
        return True

    def logout(self):
        if self.refresh_token:
            try:
                httpx.post(
                    f"{self.base}/tracker/logout/",
                    json={"refresh_token": self.refresh_token},
                    headers=self._headers(),
                    timeout=15.0,
                )
            except Exception:
                pass
        self.access_token = None
        self.refresh_token = None
        self.email = None
        self.encryption_key_b64 = None
        self.e2ee.reset()

    def _request_with_refresh(self, method: str, url: str, **kwargs):
        r = self._request_e2ee(method, url, timeout=kwargs.pop("timeout", 30.0), **kwargs)
        if r.status_code == 401 and self.refresh_token and self.refresh_access_token():
            r = self._request_e2ee(method, url, timeout=kwargs.get("timeout", 30.0), **kwargs)
        return r

    def get(self, path: str) -> dict:
        r = self._request_with_refresh("GET", f"{self.base}/tracker{path}")
        if r.status_code >= 400:
            self._check_cooldown(r)
            raise ApiError(self._parse_error(r), r.status_code)
        return self._decode_payload(r)

    def post(self, path: str, json=None, data=None, files=None) -> dict:
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.encryption_algorithm:
            headers["X-Tracker-Encryption"] = self.encryption_algorithm
        timeout = 60.0 if files else 30.0
        self.e2ee.ensure_session()
        headers.update(self.e2ee.auth_headers())
        r = httpx.post(f"{self.base}/tracker{path}", headers=headers, json=json if not files else None, data=data, files=files, timeout=timeout)
        if r.status_code == 401 and self.refresh_token and self.refresh_access_token():
            headers["Authorization"] = f"Bearer {self.access_token}"
            headers.update(self.e2ee.auth_headers())
            r = httpx.post(
                f"{self.base}/tracker{path}",
                headers=headers,
                json=json if not files else None,
                data=data,
                files=files,
                timeout=timeout,
            )
        if r.status_code == 428:
            try:
                body = r.json()
            except Exception:
                body = {}
            if isinstance(body, dict) and body.get("code") in {"E2EE_HANDSHAKE_REQUIRED", "E2EE_SESSION_EXPIRED"}:
                self.e2ee.reset()
                self.e2ee.ensure_session()
                headers.update(self.e2ee.auth_headers())
                r = httpx.post(
                    f"{self.base}/tracker{path}",
                    headers=headers,
                    json=json if not files else None,
                    data=data,
                    files=files,
                    timeout=timeout,
                )
        if r.status_code >= 400:
            self._check_cooldown(r)
            raise ApiError(self._parse_error(r), r.status_code)
        if r.content:
            return self._decode_payload(r)
        return {}
