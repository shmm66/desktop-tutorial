"""Read-only Bitunix API authentication test.

Signature algorithm follows the official REST signing guide. This module only calls a
read-only pending-positions endpoint; it never places, edits, or cancels orders.
"""
from __future__ import annotations

import hashlib
import secrets
import time
from typing import Mapping

import requests

BASE_URL = "https://fapi.bitunix.com"
READ_ONLY_TEST_PATH = "/api/v1/futures/position/get_pending_positions"

# Messages are based on Bitunix's official Futures API error-code table.
# These give the user actionable diagnostics instead of requiring them to decode a code.
ERROR_GUIDANCE = {
    "10003": "Bitunix did not receive an API key. Check that the API Key field is filled correctly.",
    "10004": (
        "The public IP address used by this computer is not on this API key's IP whitelist. "
        "In Bitunix, open API Management, edit this key's IP whitelist, and add this computer "
        "network's current public outbound IP. If you use a VPN or proxy, whitelist the IP used "
        "by that route. If your ISP changes your IP, update the whitelist when it changes. "
        "This request is read-only; no order was sent."
    ),
    "10007": (
        "Bitunix rejected the request signature. Recheck the API Secret and make sure the key "
        "belongs to the Futures API environment."
    ),
    "10010": "Bitunix rejected the request IP. Check the key's IP restrictions and current public IP.",
    "10011": (
        "The request timestamp is outside Bitunix's 60-second window. Synchronize Windows date/time "
        "automatically and retry."
    ),
    "10005": "Bitunix rate limit was reached. Wait briefly before trying again.",
    "403": (
        "Bitunix says this API key does not support the requested operation. For automatic orders, "
        "create/use an API key with Futures trading permission; a Read-only or third-party-app key "
        "cannot submit orders. Keep withdrawals disabled and verify the key IP whitelist."
    ),
    "20011": (
        "Bitunix reports that this account is not allowed to trade. Check Futures account restrictions "
        "and API trading permissions in Bitunix; contact Bitunix support if the account itself is restricted."
    ),
    "20012": (
        "Bitunix says this futures contract does not allow trading. The app will skip this symbol; "
        "check the contract status and supported API trading pairs."
    ),
    "30040": (
        "Bitunix reports that futures trading is prohibited for this account. No new order can be placed; "
        "check account restrictions or contact Bitunix support."
    ),
}


class BitunixNotConfigured(RuntimeError):
    pass


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_signature(
    nonce: str,
    timestamp: str,
    api_key: str,
    secret_key: str,
    query_params: str = "",
    body: str = "",
) -> str:
    """Build Bitunix's documented double-SHA256 REST signature."""
    digest = sha256_hex(nonce + timestamp + api_key + query_params + body)
    return sha256_hex(digest + secret_key)


def _headers(api_key: str, api_secret: str, query_params: str = "", body: str = "") -> Mapping[str, str]:
    nonce = secrets.token_hex(8)
    timestamp = str(int(time.time() * 1000))
    return {
        "api-key": api_key,
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": make_signature(nonce, timestamp, api_key, api_secret, query_params, body),
        "language": "en-US",
        "Content-Type": "application/json",
        "User-Agent": "WhaleRadarPro/2.1",
    }


def explain_api_error(code: object, api_message: object = None) -> str:
    """Return a helpful Bitunix diagnostic without exposing credentials."""
    key = str(code)
    guidance = ERROR_GUIDANCE.get(key)
    if guidance:
        return f"Bitunix error {key}: {guidance}"
    message = str(api_message or "Unknown API error")
    return f"Bitunix rejected the request (code {key}): {message}"


def test_connection(api_key: str, api_secret: str, timeout: float = 10.0) -> tuple[bool, str]:
    """Verify credentials with a safe, read-only request and return an actionable status message."""
    if not api_key.strip() or not api_secret.strip():
        return False, "API key and secret are required."

    try:
        response = requests.get(
            BASE_URL + READ_ONLY_TEST_PATH,
            headers=_headers(api_key.strip(), api_secret.strip()),
            timeout=timeout,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError:
            return False, "Bitunix returned a non-JSON response; authentication could not be verified."

        if not isinstance(payload, dict):
            return False, "Bitunix returned an unexpected response format."
        code = payload.get("code")
        if str(code) == "0":
            return True, ("Read-only API authentication succeeded (key, signature and IP accepted). "
                          "This does NOT verify Futures trading permission and no order was sent. "
                          "Automatic copy trading requires an API key with Futures trading permission; "
                          "keep withdrawals disabled.")
        return False, explain_api_error(code, payload.get("msg") or payload.get("message"))
    except requests.Timeout:
        return False, "Bitunix connection timed out. Check network access and try again."
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status:
            if str(status) in ERROR_GUIDANCE:
                return False, explain_api_error(status)
            return False, f"Bitunix HTTP error {status}. Check API permissions, IP restrictions, and key validity."
        return False, "Could not reach Bitunix. Check internet access and try again."
