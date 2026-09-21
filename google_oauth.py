from __future__ import annotations

import base64
import json
import mimetypes
import os
import webbrowser
from email.message import EmailMessage
from pathlib import Path

ROOT = Path.home() / "TraderPlannerPro"
TOKEN_PATH = ROOT / "google_token.json"
DEFAULT_CLIENT_NAMES = ("google_client_secret.json", "credentials.json")

GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.send",
]


def candidate_client_paths(custom_path: str | None = None):
    paths = []
    if custom_path:
        paths.append(Path(custom_path).expanduser())
    paths.extend(
        [
            ROOT / "google_client_secret.json",
            ROOT / "credentials.json",
            Path.cwd() / "google_client_secret.json",
            Path.cwd() / "credentials.json",
        ]
    )
    appdata = os.environ.get("APPDATA")
    if appdata:
        paths.append(Path(appdata) / "TraderPlannerPro" / "google_client_secret.json")
    seen = set()
    result = []
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path)
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def find_client_file(custom_path: str | None = None):
    for path in candidate_client_paths(custom_path):
        if path.exists() and path.is_file():
            return path
    return None


def google_status():
    try:
        from google.oauth2.credentials import Credentials
        if not TOKEN_PATH.exists():
            return {"connected": False, "email": "", "name": ""}
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GOOGLE_SCOPES)
        if not creds.valid and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        if not creds.valid:
            return {"connected": False, "email": "", "name": ""}
        from google.auth.transport.requests import AuthorizedSession
        session = AuthorizedSession(creds)
        response = session.get("https://www.googleapis.com/oauth2/v3/userinfo", timeout=10)
        response.raise_for_status()
        info = response.json()
        return {
            "connected": True,
            "email": info.get("email", ""),
            "name": info.get("name", ""),
        }
    except Exception:
        return {"connected": False, "email": "", "name": ""}


def login_google(custom_path: str | None = None):
    client_file = find_client_file(custom_path)
    if not client_file:
        raise FileNotFoundError(
            "Google OAuth desktop credentials were not found. "
            "Select the OAuth client JSON created in Google Cloud."
        )

    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), GOOGLE_SCOPES)
    creds = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        access_type="offline",
        prompt="consent",
        authorization_prompt_message="Opening Google sign-in in your browser…",
        success_message="Google sign-in completed. You can return to Trader Planner Pro.",
    )
    ROOT.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    try:
        from google.auth.transport.requests import AuthorizedSession
        session = AuthorizedSession(creds)
        info = session.get("https://www.googleapis.com/oauth2/v3/userinfo", timeout=10).json()
    except Exception:
        info = {}
    return {
        "connected": True,
        "email": info.get("email", ""),
        "name": info.get("name", ""),
    }


def logout_google():
    try:
        TOKEN_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def send_gmail(to_address: str, subject: str, body: str, attachments=None):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not TOKEN_PATH.exists():
        raise RuntimeError("Google account is not connected.")
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GOOGLE_SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    if not creds.valid:
        raise RuntimeError("Google authorization is no longer valid. Sign in again.")

    attachments = attachments or []
    message = EmailMessage()
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    for file_path in attachments:
        path = Path(file_path)
        data = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        main_type, sub_type = mime.split("/", 1)
        message.add_attachment(
            data,
            maintype=main_type,
            subtype=sub_type,
            filename=path.name,
        )

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()
