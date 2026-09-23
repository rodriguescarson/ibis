from __future__ import annotations

import getpass

import pytest

from ibis.backends.databricks import MemtableManager


class _FakeBackend:
    """Stand-in for a databricks `Backend` that avoids a live connection."""

    current_catalog = "main"
    current_database = "default"


def test_generate_volume_path_sanitizes_username_with_period(monkeypatch):
    # Usernames like "first.last" broke volume path generation because
    # Unity Catalog treats `.` as a namespace separator.
    monkeypatch.setattr(getpass, "getuser", lambda: "first.last")

    manager = MemtableManager(backend=_FakeBackend(), volume_path=None)
    volume_path = manager._generate_volume_path()

    assert volume_path.startswith("/Volumes/main/default/")
    username_segment = volume_path.rsplit("/", 1)[-1].split("-py=")[0]
    assert "." not in username_segment
    assert username_segment == "first_last"


@pytest.mark.parametrize(
    "username",
    ["first.last", "weird user!", "üser", "a/b\\c"],
)
def test_generate_volume_path_only_allows_safe_characters(monkeypatch, username):
    monkeypatch.setattr(getpass, "getuser", lambda: username)

    manager = MemtableManager(backend=_FakeBackend(), volume_path=None)
    volume_path = manager._generate_volume_path()

    username_segment = volume_path.rsplit("/", 1)[-1].split("-py=")[0]
    assert all(c.isalnum() or c in "_-" for c in username_segment)
