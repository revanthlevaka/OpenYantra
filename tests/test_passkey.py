import os
import json
import pytest
import shutil
import tempfile
import secrets
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from openyantra.core import OpenYantra
from cognitive_db import CognitiveMemoryStore
import openyantra.yantra_ui as yui
from openyantra.yantra_passkey import (
    make_registration_options,
    check_registration_response,
    make_authentication_options,
    check_authentication_response
)

@pytest.fixture
def temp_env():
    # Setup temporary directory, ODS path and settings.json
    temp_dir = tempfile.mkdtemp()
    ods_path = os.path.join(temp_dir, "chitrapat.ods")
    
    # Initialize and bootstrap OpenYantra
    oy = OpenYantra(ods_path)
    oy.bootstrap(user_name="Test User")
    
    # Initialize CognitiveMemoryStore
    cog_store = CognitiveMemoryStore(os.path.join(temp_dir, "cognitive_memories.json"))
    
    # Backup and replace globals in yantra_ui
    old_oy = yui._oy
    old_cog_store = yui._cog_store
    
    yui._oy = oy
    yui._cog_store = cog_store
    
    # Clear active sessions and challenges
    yui.authenticated_sessions.clear()
    yui.active_challenges.clear()
    
    # Remove mock cookie
    client = TestClient(yui.app)
    
    yield {
        "oy": oy,
        "cog_store": cog_store,
        "temp_dir": temp_dir,
        "settings_path": os.path.join(temp_dir, "settings.json"),
        "client": client
    }
    
    # Restore globals
    yui._oy = old_oy
    yui._cog_store = old_cog_store
    
    # Cleanup temp dir
    shutil.rmtree(temp_dir)

def test_passkey_status_initially_disabled(temp_env):
    client = temp_env["client"]
    response = client.get("/api/passkey/status")
    assert response.status_code == 200
    data = response.json()
    assert data["passkeyEnabled"] is False
    assert data["hasPasskeys"] is False
    assert data["authenticated"] is False

def test_register_options(temp_env):
    client = temp_env["client"]
    response = client.post("/api/passkey/register/options", json={"label": "My Test Key"})
    assert response.status_code == 200
    data = response.json()
    assert "options" in data
    assert "state_id" in data
    assert "challenge" in data["options"]
    
    # Verify challenge is stored in active challenges
    state_id = data["state_id"]
    assert state_id in yui.active_challenges
    assert yui.active_challenges[state_id] == data["options"]["challenge"]

def test_register_verify_and_login(temp_env):
    client = temp_env["client"]
    
    # 1. Get registration options
    reg_opt_resp = client.post("/api/passkey/register/options", json={"label": "Key 1"})
    reg_opt_data = reg_opt_resp.json()
    state_id = reg_opt_data["state_id"]
    challenge = reg_opt_data["options"]["challenge"]
    
    # 2. Mock webauthn check verification
    mock_reg_verification = {
        "credential_id": "test_cred_id_base64",
        "public_key": "test_pub_key_base64",
        "sign_count": 5
    }
    
    # We mock check_registration_response so we don't have to provide valid cryptographical signatures
    with patch("openyantra.yantra_ui.check_registration_response", return_value=mock_reg_verification):
        reg_verify_resp = client.post("/api/passkey/register/verify", json={
            "state_id": state_id,
            "credential": {"id": "test_cred_id_base64"},
            "label": "My Passkey Label"
        })
        
    assert reg_verify_resp.status_code == 200
    verify_data = reg_verify_resp.json()
    assert verify_data["status"] == "ok"
    assert "yantra_session" in reg_verify_resp.cookies
    
    # 3. Check status is now enabled, hasPasskeys is True, and authenticated is True
    # Pass the authenticated cookie
    response = client.get("/api/passkey/status")
    assert response.json()["authenticated"] is True
    assert response.json()["passkeyEnabled"] is True
    assert response.json()["hasPasskeys"] is True

    # 4. Try accessing api settings (protected when passkeys enabled)
    # Without cookie: should return 401
    unauth_client = TestClient(yui.app)
    unauth_resp = unauth_client.get("/api/settings")
    assert unauth_resp.status_code == 401
    
    # With cookie: should return 200
    auth_resp = client.get("/api/settings")
    assert auth_resp.status_code == 200

    # 5. Try login options
    login_opt_resp = client.post("/api/passkey/login/options")
    assert login_opt_resp.status_code == 200
    login_opt_data = login_opt_resp.json()
    assert "options" in login_opt_data
    assert "state_id" in login_opt_data
    login_state_id = login_opt_data["state_id"]
    
    # 6. Verify login with mock check_authentication_response
    mock_auth_verification = {
        "verified": True,
        "new_sign_count": 6
    }
    with patch("openyantra.yantra_ui.check_authentication_response", return_value=mock_auth_verification):
        login_verify_resp = client.post("/api/passkey/login/verify", json={
            "state_id": login_state_id,
            "credential": {"id": "test_cred_id_base64"}
        })
    assert login_verify_resp.status_code == 200
    assert login_verify_resp.json()["status"] == "ok"
    assert "yantra_session" in login_verify_resp.cookies

    # 7. Logout
    logout_resp = client.post("/api/passkey/logout")
    assert logout_resp.status_code == 200
    # Clean client status check should be unauthenticated now
    # Note: logout returns response that deletes cookie
    response_after_logout = client.get("/api/passkey/status")
    # client object retains cookies unless cleared or we use the deleted cookie response.
    # Wait, the response set delete_cookie, so the next request from client won't send it.
    assert response_after_logout.json()["authenticated"] is False

def test_delete_passkey(temp_env):
    client = temp_env["client"]
    
    # Add a mock passkey to settings
    settings_file = Path(temp_env["settings_path"])
    mock_settings = {
        "passkeyEnabled": True,
        "passkeys": [
            {
                "label": "Key to keep",
                "credential_id": "keep_id",
                "public_key": "keep_pub",
                "sign_count": 0,
                "added_at": "2026-05-20"
            },
            {
                "label": "Key to delete",
                "credential_id": "delete_id",
                "public_key": "delete_pub",
                "sign_count": 0,
                "added_at": "2026-05-20"
            }
        ]
    }
    with open(settings_file, "w") as f:
        json.dump(mock_settings, f)
        
    # Authenticate client
    session_token = secrets.token_hex(32)
    yui.authenticated_sessions.add(session_token)
    client.cookies.set("yantra_session", session_token)

    # Delete the passkey
    resp = client.post("/api/passkey/delete", json={"credential_id": "delete_id"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    
    # Verify only one remains
    pks = data["settings"]["passkeys"]
    assert len(pks) == 1
    assert pks[0]["credential_id"] == "keep_id"
    assert data["settings"]["passkeyEnabled"] is True
    
    # Delete the last one
    resp2 = client.post("/api/passkey/delete", json={"credential_id": "keep_id"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["settings"]["passkeys"]) == 0
    # passkeyEnabled should automatically become False when no passkeys remain
    assert data2["settings"]["passkeyEnabled"] is False

def test_passkey_helpers():
    from webauthn.helpers import bytes_to_base64url
    cred_id = bytes_to_base64url(b"cred1")
    
    # Test yantra_passkey helper functions with mock objects
    # 1. make_registration_options
    opts = make_registration_options(
        username="test_user",
        rp_id="localhost",
        existing_credentials=[{"credential_id": cred_id}]
    )
    assert opts is not None
    assert "challenge" in opts
    assert opts["user"]["name"] == "test_user"

    # 2. make_authentication_options
    auth_opts = make_authentication_options(
        rp_id="localhost",
        registered_credentials=[{"credential_id": cred_id}]
    )
    assert auth_opts is not None
    assert "challenge" in auth_opts
    assert len(auth_opts["allowCredentials"]) == 1
    assert auth_opts["allowCredentials"][0]["id"] == cred_id
