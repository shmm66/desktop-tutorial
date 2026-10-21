"""Bitunix API boundary.

Do not sign private requests until the exchange's current signature specification has
been independently verified. This module deliberately fails closed instead of faking
connectivity or placing orders.
"""

class BitunixNotConfigured(RuntimeError):
    pass


def test_connection(api_key: str, api_secret: str) -> tuple[bool, str]:
    if not api_key.strip() or not api_secret.strip():
        return False, "API key and secret are required."
    return False, (
        "Private API connectivity is not enabled in this build. Verify the current "
        "Bitunix signing, timestamp, nonce, and permission requirements before enabling it. "
        "No request or order was sent."
    )
