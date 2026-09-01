from __future__ import annotations

import getpass

from ibis.backends.databricks import MemtableManager


class _FakeBackend:
    current_catalog = "demo"
    current_database = "reference"


def test_generate_volume_path_sanitizes_dotted_username(monkeypatch):
    # GH #11950: a local username containing a "." (e.g. "first.last") was
    # passed straight into the volume path, and "." is a namespace separator
    # for Unity Catalog identifiers, so the volume ended up split into extra
    # catalog/schema segments and CREATE VOLUME could never find it.
    monkeypatch.setattr(getpass, "getuser", lambda: "first.last")
    manager = MemtableManager(_FakeBackend(), volume_path=None)

    path = manager._generate_volume_path()
    volume_name = path.rsplit("/", 1)[-1]

    assert "." not in volume_name
    assert path == f"/Volumes/demo/reference/{volume_name}"
    assert volume_name.startswith("first_last-py=")
