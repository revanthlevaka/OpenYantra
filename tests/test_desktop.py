"""
Unit tests for OpenYantra Desktop App and HUD (v1.0.0).
"""

import pytest
from starlette.testclient import TestClient
from openyantra.core import OpenYantra
from openyantra.yantra_ui import app, set_oy
from openyantra.desktop import is_port_open


@pytest.fixture
def mock_oy(tmp_path, monkeypatch):
    oy_file = tmp_path / "chitrapat.ods"
    oy = OpenYantra(oy_file)
    oy.bootstrap(user_name="Desktop Tester", occupation="Engineer")
    set_oy(oy)
    monkeypatch.setenv("OPENYANTRA_FILE", str(oy_file))
    return oy


def test_hud_endpoint(mock_oy):
    client = TestClient(app)
    res = client.get("/hud")
    assert res.status_code == 200
    assert "OpenYantra HUD" in res.text
    assert "capture-input" in res.text
    assert "recall-input" in res.text


def test_is_port_open():
    # An unused high port should return False
    assert is_port_open(59123) is False


def test_desktop_daemon_spawn(tmp_path, monkeypatch):
    from openyantra.desktop import launch_desktop

    oy_file = tmp_path / "chitrapat.ods"
    oy = OpenYantra(oy_file)
    oy.bootstrap(user_name="Daemon Desktop Tester", occupation="Engineer")

    # Mock ensure_server_running and webbrowser so no actual process or browser opens
    monkeypatch.setattr("openyantra.desktop.ensure_server_running", lambda *args, **kwargs: None)
    monkeypatch.setattr("webbrowser.open", lambda *args, **kwargs: True)

    # Launch desktop with daemon=True
    launch_desktop(oy_file=str(oy_file), mode="hud", daemon=True)
