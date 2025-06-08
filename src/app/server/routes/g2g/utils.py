import hashlib
import hmac


def generate_signature(
    webhook_url: str,
    user_id: str,
    timestamp: str,
    secret_token: str,
) -> str:
    """
    Generate HMAC-SHA256 signature for webhook authentication.

    Args:
        webhook_url (str): The URL of the webhook.
        user_id (str): The user ID.
        timestamp (str): Timestamp string, usually in milliseconds.
        secret_token (str): The webhook secret token.

    Returns:
        str: Hexadecimal HMAC signature.
    """
    canonical_string = f"{webhook_url}{user_id}{timestamp}"
    signature = hmac.new(
        key=secret_token.encode("utf-8"),
        msg=canonical_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return signature
