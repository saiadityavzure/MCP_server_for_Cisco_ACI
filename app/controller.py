import logging
import requests
import urllib3
from typing import Any, Dict, Optional

from fastmcp.exceptions import ToolError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("ACIMCPServer")

_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


class ACIController:
    """Single responsibility: authenticate with APIC and execute HTTP requests."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password

    # ── Public HTTP methods ────────────────────────────────────────────────────

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> dict:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, payload: Dict[str, Any]) -> dict:
        return self._acknowledge_write(self._request("POST", endpoint, json=payload))

    def put(self, endpoint: str, payload: Dict[str, Any]) -> dict:
        return self._acknowledge_write(self._request("PUT", endpoint, json=payload))

    def delete(self, endpoint: str) -> dict:
        return self._acknowledge_write(self._request("DELETE", endpoint))

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _acknowledge_write(result: dict) -> dict:
        """APIC returns {"totalCount":"0","imdata":[]} on successful writes.
        Convert that to an explicit success acknowledgement so the caller
        never misinterprets an empty imdata array as a failure."""
        if (
            isinstance(result, dict)
            and result.get("imdata") == []
            and str(result.get("totalCount", "")) == "0"
        ):
            return {"status": "success", "message": "Operation completed successfully on APIC."}
        return result

    # ── Auth ───────────────────────────────────────────────────────────────────

    def _get_token(self):
        login_url = f"{self.base_url}/api/aaaLogin.json"
        payload = {"aaaUser": {"attributes": {"name": self.username, "pwd": self.password}}}
        try:
            response = requests.post(login_url, json=payload, verify=False, timeout=15)
            response.raise_for_status()
            logger.info("Authenticated with APIC.")
            return response.cookies
        except requests.exceptions.RequestException as e:
            logger.error(f"APIC auth failed: {e}")
            raise

    # ── Core request ──────────────────────────────────────────────────────────

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = None
        try:
            cookies = self._get_token()
            logger.debug(f"{method} {url} | payload: {kwargs.get('json')}")
            response = requests.request(
                method, url, headers=_HEADERS, cookies=cookies,
                verify=False, timeout=15, **kwargs
            )
            logger.debug(
                f"{method} {url} | status: {response.status_code} "
                f"| body: {response.text[:500]}"
            )
            response.raise_for_status()
            data = response.json()
            self._raise_on_apic_error(method, url, data)
            return data
        except requests.exceptions.HTTPError as e:
            body = response.text[:1000] if response is not None else "no response"
            logger.error(f"HTTP {e.response.status_code} on {method} {url} | body: {body}")
            raise ToolError(f"{method} {url} failed HTTP {e.response.status_code}: {body}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error on {method} {url}: {e}")
            raise ToolError(f"{method} request failed: {e}")

    @staticmethod
    def _raise_on_apic_error(method: str, url: str, data: dict) -> None:
        """APIC sometimes embeds errors inside a 200 response."""
        if not isinstance(data, dict):
            return
        for item in data.get("imdata", []):
            if "error" in item:
                err = item["error"]["attributes"]
                logger.error(
                    f"APIC error on {method} {url} "
                    f"| code: {err.get('code')} | text: {err.get('text')}"
                )
                raise ToolError(f"APIC error {err.get('code')}: {err.get('text')}")
