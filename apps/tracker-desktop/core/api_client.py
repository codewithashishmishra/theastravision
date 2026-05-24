import httpx

from core.auth import save_session
from core.config import API_BASE_URL
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
        return h

    @staticmethod
    def _parse_error(response: httpx.Response) -> str:
        try:
            body = response.json()
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
        r = httpx.post(
            f"{self.base}/tracker/auth/session/exchange/",
            json={"access_token": access_token},
            timeout=30.0,
        )
        if r.status_code >= 400:
            raise ApiError(self._parse_error(r), r.status_code)
        data = r.json()
        self._apply_auth_payload(data)
        self.email = data.get("email")
        self._persist_session()
        return data

    def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return False
        r = httpx.post(
            f"{self.base}/tracker/auth/refresh/",
            json={"refresh_token": self.refresh_token},
            timeout=30.0,
        )
        if r.status_code >= 400:
            return False
        data = r.json()
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

    def _request_with_refresh(self, method: str, url: str, **kwargs):
        r = httpx.request(method, url, headers=self._headers(), timeout=kwargs.pop("timeout", 30.0), **kwargs)
        if r.status_code == 401 and self.refresh_token and self.refresh_access_token():
            r = httpx.request(method, url, headers=self._headers(), timeout=kwargs.get("timeout", 30.0), **kwargs)
        return r

    def get(self, path: str) -> dict:
        r = self._request_with_refresh("GET", f"{self.base}/tracker{path}")
        if r.status_code >= 400:
            self._check_cooldown(r)
            raise ApiError(self._parse_error(r), r.status_code)
        return r.json()

    def post(self, path: str, json=None, data=None, files=None) -> dict:
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.encryption_algorithm:
            headers["X-Tracker-Encryption"] = self.encryption_algorithm
        timeout = 60.0 if files else 30.0
        r = httpx.post(
            f"{self.base}/tracker{path}",
            headers=headers,
            json=json if not files else None,
            data=data,
            files=files,
            timeout=timeout,
        )
        if r.status_code == 401 and self.refresh_token and self.refresh_access_token():
            headers["Authorization"] = f"Bearer {self.access_token}"
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
            return r.json()
        return {}
