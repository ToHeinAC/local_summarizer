"""Local user store with bcrypt password hashes. Plain Python, no LangChain.

Schema (`data/users.json`):
    {"users": {"<username>": {"pw_hash": "..."}}}

On first run the file is seeded from the environment: each account in
`SEED_USERS` takes its password from the named variable in `.env`. Passwords are
never hardcoded, and `data/` is gitignored. Delete `data/users.json` to re-seed.
Ported from
[KB_BS_local-wiki-he](https://github.com/ToHeinAC/KB_BS_local-wiki-he)
(Apache-2.0) without its per-database access and maintainer layers.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import bcrypt
from dotenv import load_dotenv

load_dotenv()

DATA_ROOT = Path(__file__).resolve().parent.parent / "data"

#: username -> environment variable holding that account's seed password.
SEED_USERS = {
    "T. Hein": "SEED_PW_HEIN",
    "Gast": "SEED_PW_GAST",
}


def _path() -> Path:
    return DATA_ROOT / "users.json"


def _load() -> dict:
    p = _path()
    if not p.exists():
        return {"users": {}}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"users": {}}


def _save(data: dict) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_passwords() -> dict[str, str]:
    """Seed accounts whose password variable is set in the environment."""
    return {u: os.environ[var] for u, var in SEED_USERS.items() if os.getenv(var)}


def ensure_seeded() -> None:
    """Create users.json from the environment's seed passwords, once."""
    if _path().exists():
        return
    users = seed_passwords()
    if not users:
        raise RuntimeError(
            "No seed passwords found. Set "
            + " / ".join(SEED_USERS.values())
            + " in .env (see .env.example)."
        )
    _save({"users": {u: {"pw_hash": _hash(pw)} for u, pw in users.items()}})


def verify(username: str, password: str) -> bool:
    user = _load().get("users", {}).get(username)
    if not user:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), user["pw_hash"].encode("utf-8"))
    except Exception:
        return False
