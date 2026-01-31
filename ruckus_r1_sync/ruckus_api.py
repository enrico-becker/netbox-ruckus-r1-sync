from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests


class RuckusR1Client:
    """
    RUCKUS One API Client

    Important:
    - Resource APIs live on: https://api.{region}.ruckus.cloud
    - OAuth2 token endpoint lives on: https://{region}.ruckus.cloud/oauth2/token/{tenantId}
      and requires form body: grant_type, client_id, client_secret
      (NOT HTTP Basic Auth). See official docs.
    """

    def __init__(
        self,
        base_url: str,
        ruckus_tenant_id: str,
        client_id: str,
        client_secret: str,
        verify_tls: bool = True,
        timeout: int = 30,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.ruckus_tenant_id = (ruckus_tenant_id or "").strip()
        self.client_id = (client_id or "").strip()
        self.client_secret = (client_secret or "").strip()
        self.verify_tls = verify_tls
        self.timeout = timeout

        self._token: Optional[str] = None
        self._token_exp: float = 0.0

        if not self.base_url:
            raise ValueError("base_url is empty")
        if not self.ruckus_tenant_id:
            raise ValueError("ruckus_tenant_id is empty")
        if not self.client_id or not self.client_secret:
            raise ValueError("client_id/client_secret is empty")

    def _auth_base_url(self) -> str:
        """
        Convert API host -> Auth host.
        Examples:
          https://api.eu.ruckus.cloud -> https://eu.ruckus.cloud
          https://api.ruckus.cloud    -> https://ruckus.cloud
        """
        url = self.base_url

        # strip any path (shouldn't be there, but keep robust)
        # simplest: only keep scheme://host
        try:
            from urllib.parse import urlparse

            p = urlparse(url)
            scheme = p.scheme or "https"
            host = p.netloc or p.path  # in case someone passed without scheme
            host = host.split("/")[0]
            if host.startswith("api."):
                host = host[len("api.") :]
            return f"{scheme}://{host}"
        except Exception:
            # fallback: best effort replace
            if "://api." in url:
                return url.replace("://api.", "://", 1)
            return url

    def _token_url(self) -> str:
        # Official pattern: https://{region}.ruckus.cloud/oauth2/token/{tenantId}
        return f"{self._auth_base_url()}/oauth2/token/{self.ruckus_tenant_id}"

    def _get_token(self) -> str:
        now = time.time()
        if self._token and now < (self._token_exp - 30):
            return self._token

        # IMPORTANT: do NOT follow redirects; if we get redirected to /oauth2/authorization/idm
        # then credentials/endpoint/flow is wrong for client_credentials.
        r = requests.post(
            self._token_url(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=self.timeout,
            verify=self.verify_tls,
            allow_redirects=False,
        )

        if 300 <= r.status_code < 400:
            raise RuntimeError(
                f"OAuth token endpoint redirected (status {r.status_code}) to {r.headers.get('Location')} "
                f"— expected a direct token response. Check region host and application token."
            )

        r.raise_for_status()
        payload = r.json()

        self._token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        self._token_exp = now + expires_in

        if not self._token:
            raise RuntimeError(f"No access_token in OAuth response: {payload}")

        return self._token

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        r = requests.get(
            url,
            params=params or {},
            headers=self._headers(),
            timeout=self.timeout,
            verify=self.verify_tls,
        )
        if r.status_code >= 400:
            try:
                msg = r.json()
            except Exception:
                msg = r.text
            raise RuntimeError(f"GET {path} failed ({r.status_code}): {msg}")
        try:
            return r.json()
        except Exception:
            return r.text

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        r = requests.post(
            url,
            json=body or {},
            headers=self._headers(),
            timeout=self.timeout,
            verify=self.verify_tls,
        )
        if r.status_code >= 400:
            try:
                msg = r.json()
            except Exception:
                msg = r.text
            raise RuntimeError(f"POST {path} failed ({r.status_code}): {msg}")
        return r.json()

    def get_vlan_unions(self, *, venue_id: str, switch_id: str) -> Dict[str, Any]:
        """GET /venues/{venueId}/switches/{switchId}/vlanUnions"""
        venue_id = (venue_id or "").strip()
        switch_id = (switch_id or "").strip()
        if not venue_id or not switch_id:
            raise ValueError("venue_id/switch_id required")
        return self._get(f"/venues/{venue_id}/switches/{switch_id}/vlanUnions")  # type: ignore[return-value]


    def query_all(
        self,
        *,
        path: str,
        page_size: int = 100,
        extra_body: Optional[Dict[str, Any]] = None,
        data_key: str = "data",
    ) -> List[Dict[str, Any]]:
        body = dict(extra_body or {})
        body.setdefault("limit", page_size)

        out: List[Dict[str, Any]] = []
        resp = self._post(path, body)
        data = resp.get(data_key) if isinstance(resp, dict) else None
        if isinstance(data, list):
            out.extend([x for x in data if isinstance(x, dict)])
        return out
 