"""Tests for auth.py — the local bcrypt-backed user store."""

import json

import pytest

from src import auth

PASSWORDS = {"T. Hein": "hein-pw", "Gast": "gast-pw"}


@pytest.fixture
def users_root(tmp_path, monkeypatch):
    """Isolated data root and seed passwords; nothing touches the real .env."""
    monkeypatch.setattr(auth, "DATA_ROOT", tmp_path)
    for username, var in auth.SEED_USERS.items():
        monkeypatch.setenv(var, PASSWORDS[username])
    return tmp_path


def test_seeds_the_two_default_users(users_root):
    auth.ensure_seeded()
    data = json.loads((users_root / "users.json").read_text())
    assert set(data["users"]) == {"T. Hein", "Gast"}


def test_seeded_users_verify_with_their_passwords(users_root):
    auth.ensure_seeded()
    for username, password in PASSWORDS.items():
        assert auth.verify(username, password) is True


def test_wrong_password_is_rejected(users_root):
    auth.ensure_seeded()
    assert auth.verify("Gast", "nope") is False


def test_unknown_user_is_rejected(users_root):
    auth.ensure_seeded()
    assert auth.verify("ghost", PASSWORDS["Gast"]) is False


def test_verify_without_a_store_is_false(users_root):
    assert auth.verify("T. Hein", PASSWORDS["T. Hein"]) is False


def test_passwords_are_not_stored_in_plaintext(users_root):
    auth.ensure_seeded()
    raw = (users_root / "users.json").read_text()
    for password in PASSWORDS.values():
        assert password not in raw


def test_missing_seed_passwords_raise(users_root, monkeypatch):
    for var in auth.SEED_USERS.values():
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError, match="SEED_PW_HEIN"):
        auth.ensure_seeded()


def test_seeds_only_the_users_with_a_password_set(users_root, monkeypatch):
    monkeypatch.delenv("SEED_PW_GAST")
    auth.ensure_seeded()
    data = json.loads((users_root / "users.json").read_text())
    assert list(data["users"]) == ["T. Hein"]


def test_ensure_seeded_does_not_overwrite_existing_store(users_root):
    (users_root / "users.json").write_text(json.dumps({"users": {"only": {"pw_hash": "x"}}}))
    auth.ensure_seeded()
    data = json.loads((users_root / "users.json").read_text())
    assert list(data["users"]) == ["only"]


def test_corrupt_store_denies_access(users_root):
    (users_root / "users.json").write_text("{ not json")
    assert auth.verify("T. Hein", PASSWORDS["T. Hein"]) is False
