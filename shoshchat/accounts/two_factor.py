"""Two-Factor Authentication utilities."""
from __future__ import annotations

import hashlib
import io
import secrets
from typing import TYPE_CHECKING

import pyotp
import qrcode
from django.conf import settings

if TYPE_CHECKING:
    from django.contrib.auth.models import User


def generate_totp_secret() -> str:
    """Generate a random base32 secret for TOTP."""
    return pyotp.random_base32()


def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate backup codes for 2FA recovery."""
    codes = []
    for _ in range(count):
        code = secrets.token_hex(4).upper()  # 8-character hex code
        codes.append(code)
    return codes


def hash_backup_code(code: str) -> str:
    """Hash a backup code for secure storage."""
    return hashlib.sha256(code.encode()).hexdigest()


def verify_backup_code(code: str, hashed_codes: list[str]) -> bool:
    """Verify a backup code against stored hashed codes."""
    hashed = hash_backup_code(code)
    return hashed in hashed_codes


def get_totp_uri(user, secret: str) -> str:
    """
    Generate a TOTP URI for QR code generation.

    Args:
        user: Django user object
        secret: Base32 secret

    Returns:
        TOTP URI string
    """
    issuer = getattr(settings, "SITE_NAME", "ShoshChat")
    account_name = user.email or user.username

    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=account_name, issuer_name=issuer)


def generate_qr_code(uri: str) -> bytes:
    """
    Generate QR code image from TOTP URI.

    Args:
        uri: TOTP URI string

    Returns:
        PNG image bytes
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def verify_totp(secret: str, token: str) -> bool:
    """
    Verify a TOTP token against a secret.

    Args:
        secret: Base32 secret
        token: 6-digit TOTP code

    Returns:
        True if valid, False otherwise
    """
    if not secret or not token:
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)  # Allow 30-second window


def setup_two_factor(user) -> dict:
    """
    Set up 2FA for a user.

    Args:
        user: Django user object

    Returns:
        Dictionary with secret, QR code URI, and backup codes
    """
    secret = generate_totp_secret()
    uri = get_totp_uri(user, secret)
    backup_codes = generate_backup_codes()

    # Hash backup codes for storage
    hashed_codes = [hash_backup_code(code) for code in backup_codes]

    # Update user profile
    profile = user.profile
    profile.two_factor_secret = secret
    profile.backup_codes = hashed_codes
    profile.save(update_fields=["two_factor_secret", "backup_codes"])

    return {
        "secret": secret,
        "qr_uri": uri,
        "backup_codes": backup_codes,  # Return plain codes for user to save
    }


def enable_two_factor(user, verification_token: str) -> bool:
    """
    Enable 2FA after verifying setup token.

    Args:
        user: Django user object
        verification_token: 6-digit TOTP token

    Returns:
        True if enabled successfully, False otherwise
    """
    profile = user.profile

    if not profile.two_factor_secret:
        return False

    # Verify the token
    if not verify_totp(profile.two_factor_secret, verification_token):
        return False

    # Enable 2FA
    profile.two_factor_enabled = True
    profile.save(update_fields=["two_factor_enabled"])

    return True


def disable_two_factor(user):
    """Disable 2FA for a user."""
    profile = user.profile
    profile.two_factor_enabled = False
    profile.two_factor_secret = ""
    profile.backup_codes = []
    profile.save(update_fields=["two_factor_enabled", "two_factor_secret", "backup_codes"])


def verify_two_factor(user, token: str) -> bool:
    """
    Verify 2FA token (TOTP or backup code).

    Args:
        user: Django user object
        token: TOTP token or backup code

    Returns:
        True if valid, False otherwise
    """
    profile = user.profile

    if not profile.two_factor_enabled:
        return True  # 2FA not enabled, skip verification

    # Try TOTP first
    if verify_totp(profile.two_factor_secret, token):
        return True

    # Try backup code
    if verify_backup_code(token, profile.backup_codes):
        # Remove used backup code
        hashed = hash_backup_code(token)
        profile.backup_codes = [code for code in profile.backup_codes if code != hashed]
        profile.save(update_fields=["backup_codes"])
        return True

    return False
