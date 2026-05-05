"""
Shared helpers for API validation scripts.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import requests


DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEFAULT_PASSWORD = os.getenv("SCRIPT_TEST_PASSWORD", "Passw0rd!123")


@dataclass
class AuthSession:
    base_url: str
    token: str
    user_id: str
    email: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def check_health(base_url: str) -> None:
    resp = requests.get(f"{base_url}/health", timeout=20)
    resp.raise_for_status()


def register_and_login(
    base_url: str,
    prefix: str,
    password: str = DEFAULT_PASSWORD,
) -> AuthSession:
    ts = int(time.time() * 1000)
    email = f"{prefix}_{ts}@example.com"

    reg = requests.post(
        f"{base_url}/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Script",
            "last_name": "Runner",
        },
        timeout=30,
    )
    reg.raise_for_status()

    login = requests.post(
        f"{base_url}/auth/login",
        data={"username": email, "password": password},
        timeout=30,
    )
    login.raise_for_status()
    token = login.json().get("access_token")
    if not token:
        raise RuntimeError("Login response did not include access_token")

    session = requests.get(
        f"{base_url}/auth/session",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    session.raise_for_status()
    user_id = session.json().get("id")
    if not user_id:
        raise RuntimeError("Auth session response did not include user id")

    return AuthSession(base_url=base_url, token=token, user_id=user_id, email=email)


def create_job_and_application(auth: AuthSession, apply_url: str) -> tuple[str, str]:
    job_resp = requests.post(
        f"{auth.base_url}/jobs",
        headers=auth.headers,
        json={"apply_url": apply_url},
        timeout=30,
    )
    job_resp.raise_for_status()
    job_id = job_resp.json().get("id")
    if not job_id:
        raise RuntimeError("Job create response missing id")

    app_resp = requests.post(
        f"{auth.base_url}/applications",
        headers=auth.headers,
        json={"job_id": job_id},
        timeout=30,
    )
    app_resp.raise_for_status()
    app_id = app_resp.json().get("id")
    if not app_id:
        raise RuntimeError("Application create response missing id")

    return job_id, app_id
