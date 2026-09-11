"""Gmail OAuth 2.0 authentication (Desktop App flow).

Handles the OAuth flow, token loading/saving/refresh, and credential validation.
No tokens or secrets are ever logged or printed.
"""

from __future__ import annotations

from pathlib import Path

from app.config import BASE_DIR, get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

NOT_CONFIGURED_MSG = (
    "Gmail OAuth is not configured.\n\n"
    "Please set:\n"
    "GMAIL_CLIENT_ID\n"
    "GMAIL_CLIENT_SECRET"
)
NOT_AUTHENTICATED_MSG = "Gmail account is not authenticated.\n\nRun:\njobapply auth gmail"
REVOKED_MSG = (
    "Gmail authentication has expired or been revoked.\n\nRun:\njobapply auth gmail"
)


class GmailAuthError(RuntimeError):
    pass


def is_configured() -> bool:
    settings = get_settings()
    return bool(settings.gmail_client_id and settings.gmail_client_secret)


def _require_configured() -> None:
    if not is_configured():
        raise GmailAuthError(NOT_CONFIGURED_MSG)


def token_path() -> Path:
    settings = get_settings()
    path = Path(settings.gmail_token_file)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


def _import_google():
    try:
        from google.auth.exceptions import RefreshError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:  # pragma: no cover
        raise GmailAuthError(
            "Google auth libraries missing. Run: pip install -r requirements.txt"
        ) from exc
    return RefreshError, Request, Credentials, InstalledAppFlow


def load_credentials():
    """Load credentials from the local token file (without refreshing)."""
    _, _, Credentials, _ = _import_google()
    path = token_path()
    if not path.exists():
        return None
    return Credentials.from_authorized_user_file(str(path), SCOPES)


def _save_credentials(creds) -> None:
    path = token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")


def get_credentials():
    """Return valid credentials, auto-refreshing an expired access token.

    Raises GmailAuthError when OAuth is not configured, the account is not
    authenticated, or the refresh token is invalid/revoked.
    """
    _require_configured()
    RefreshError, Request, _, _ = _import_google()

    creds = load_credentials()
    if creds is None:
        raise GmailAuthError(NOT_AUTHENTICATED_MSG)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except (RefreshError, Exception) as exc:  # noqa: BLE001
                logger.warning("Gmail token refresh failed: %s", type(exc).__name__)
                raise GmailAuthError(REVOKED_MSG) from exc
        else:
            raise GmailAuthError(NOT_AUTHENTICATED_MSG)

    _save_credentials(creds)
    return creds


def authenticate() -> str:
    """Run the OAuth 2.0 desktop flow and persist the token.

    Returns the authenticated Gmail account email address.
    """
    _require_configured()
    _, _, _, InstalledAppFlow = _import_google()
    settings = get_settings()

    client_config = {
        "installed": {
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            # NOTE: GMAIL_REDIRECT_URI is legacy/compat only. InstalledAppFlow
            # runs its own local loopback server and does not rely on it.
            "redirect_uris": [settings.gmail_redirect_uri],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    _save_credentials(creds)
    try:
        return get_authenticated_email(creds)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not resolve authenticated email: %s", type(exc).__name__)
        return ""


def get_authenticated_email(creds=None) -> str:
    """Return the email of the authenticated account via Google userinfo.

    Uses only the ``userinfo.email`` scope (no inbox access required).
    """
    if creds is None:
        creds = get_credentials()

    try:
        from google.auth.transport.requests import AuthorizedSession
    except ImportError as exc:  # pragma: no cover
        raise GmailAuthError(
            "google-auth missing. Run: pip install -r requirements.txt"
        ) from exc

    session = AuthorizedSession(creds)
    response = session.get("https://www.googleapis.com/oauth2/v1/userinfo?alt=json")
    if response.status_code != 200:
        logger.warning(
            "userinfo request failed with status %s", response.status_code
        )
        return ""
    return response.json().get("email", "")


def status() -> dict:
    """Return authentication status without exposing tokens."""
    if not is_configured():
        return {"configured": False, "authenticated": False, "email": None}
    creds = load_credentials()
    if creds is None:
        return {"configured": True, "authenticated": False, "email": None}
    try:
        email = get_authenticated_email(creds)
        return {"configured": True, "authenticated": True, "email": email}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not resolve authenticated email: %s", type(exc).__name__)
        return {"configured": True, "authenticated": True, "email": None}


def logout() -> None:
    """Remove the locally stored token file (no revoke, no account deletion)."""
    path = token_path()
    if path.exists():
        path.unlink()
