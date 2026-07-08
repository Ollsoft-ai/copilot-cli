from pathlib import Path

import httpx

from .config import SERVER_URL, load_tokens


def _auth_headers(access_token: str | None = None) -> dict[str, str]:
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    tokens = load_tokens()
    if not tokens:
        return {}
    token = tokens.get("pat") or tokens.get("access_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def login(email: str, password: str) -> dict:
    with httpx.Client(base_url=SERVER_URL) as client:
        resp = client.post("/api/auth/login", json={"email": email, "password": password})
        resp.raise_for_status()
        return resp.json()


def logout() -> None:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.post("/api/auth/logout")
        resp.raise_for_status()


def create_pat(access_token: str, name: str) -> str:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers(access_token)) as client:
        resp = client.post("/api/auth/token", json={"name": name})
        resp.raise_for_status()
        return resp.json()["token"]


def skills_init() -> dict:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.get("/api/skills/init")
        resp.raise_for_status()
        return resp.json()


def documents_list() -> list:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.get("/api/documents/")
        resp.raise_for_status()
        return resp.json()


def documents_get(doc_id: int) -> dict:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.get(f"/api/documents/{doc_id}")
        resp.raise_for_status()
        return resp.json()


def documents_upload(file_paths: list[str]) -> list:
    handles = [open(p, "rb") for p in file_paths]
    try:
        files = [("files", (Path(p).name, fh)) for p, fh in zip(file_paths, handles)]
        with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
            resp = client.post("/api/documents/upload", files=files)
            resp.raise_for_status()
            return resp.json()
    finally:
        for fh in handles:
            fh.close()


def documents_delete(doc_id: int) -> None:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.delete(f"/api/documents/{doc_id}")
        resp.raise_for_status()


def companies_list() -> list[dict]:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.get("/api/companies/")
        resp.raise_for_status()
        return resp.json()


def rules_list(company_id: str) -> list[dict]:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.get("/api/rules/agent", params={"company_id": company_id})
        resp.raise_for_status()
        return resp.json()


def tags_list(company_id: str) -> list[str]:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.get("/api/agent/tags", params={"company_id": company_id})
        resp.raise_for_status()
        return resp.json()


def keywords_list(company_id: str) -> list[str]:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.get("/api/agent/keywords", params={"company_id": company_id})
        resp.raise_for_status()
        return resp.json()


def rules_search(
    company_id: str,
    query: str | None = None,
    tags: list[str] | None = None,
    severity: list[str] | None = None,
    limit: int = 10,
    offset: int = 0,
) -> list[dict]:
    params: dict = {"company_id": company_id, "limit": limit, "offset": offset}
    if query:
        params["q"] = query
    if tags:
        params["tags"] = tags
    if severity:
        params["severity"] = severity
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.get("/api/agent/search", params=params)
        resp.raise_for_status()
        return resp.json()


def report_event(payload: dict) -> None:
    with httpx.Client(base_url=SERVER_URL, headers=_auth_headers()) as client:
        resp = client.post("/api/telemetry/report_event", json=payload)
        resp.raise_for_status()



def health() -> dict:
    with httpx.Client(base_url=SERVER_URL) as client:
        resp = client.get("/api/health")
        resp.raise_for_status()
        return resp.json()
