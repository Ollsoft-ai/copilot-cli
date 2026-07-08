import json
import socket
from pathlib import Path

SERVER_URL: str = "https://compliance.ollsoft.org"
FRONTEND_URL: str = "https://compliance.ollsoft.org"
CALLBACK_PORT: int = 9876

_AUTH_FILE: Path = Path.home() / ".compliance" / "auth.json"


def get_auth_file() -> Path:
    _AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    return _AUTH_FILE


def load_tokens() -> dict | None:
    path = get_auth_file()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_tokens(access_token: str, refresh_token: str) -> None:
    path = get_auth_file()
    path.write_text(
        json.dumps({"access_token": access_token, "refresh_token": refresh_token}),
        encoding="utf-8",
    )


def save_pat(pat: str) -> None:
    """Persist a long-lived PAT, replacing any previous credentials."""
    tokens = load_tokens() or {}
    tokens["pat"] = tokens.get("pat") or pat
    path = get_auth_file()
    path.write_text(json.dumps({"pat": pat}), encoding="utf-8")


def save_company(company_id: str, company_name: str) -> None:
    tokens = load_tokens() or {}
    tokens["company_id"] = company_id
    tokens["company_name"] = company_name
    path = get_auth_file()
    path.write_text(json.dumps(tokens), encoding="utf-8")


def load_company() -> tuple[str, str] | None:
    """Return (company_id, company_name) or None if not set."""
    tokens = load_tokens()
    if tokens and tokens.get("company_id"):
        return tokens["company_id"], tokens.get("company_name", tokens["company_id"])
    return None


def load_pat() -> str | None:
    tokens = load_tokens()
    if tokens:
        return tokens.get("pat")
    return None


def clear_tokens() -> None:
    path = get_auth_file()
    if path.exists():
        path.unlink()


def default_token_name() -> str:
    return socket.gethostname()
