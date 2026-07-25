import hashlib
import hmac
import json
import time


def sign_payload(secret: str, body: bytes, timestamp: int) -> str:
    """Stripe-style signing: sign f'{timestamp}.{body}' with HMAC-SHA256,
    hex-encoded. The timestamp is included in the signed content (and sent
    as its own header) so a receiver can reject stale/replayed deliveries."""
    signed_content = f"{timestamp}.{body.decode('utf-8')}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), signed_content, hashlib.sha256).hexdigest()


def build_signature_headers(secret: str, body: bytes) -> dict[str, str]:
    timestamp = int(time.time())
    signature = sign_payload(secret, body, timestamp)
    return {
        "X-Nexora-Signature": signature,
        "X-Nexora-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")