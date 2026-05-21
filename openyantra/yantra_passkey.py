"""
yantra_passkey.py -- WebAuthn / Passkey Helpers for OpenYantra
Provides helpers for Google and Apple Passkey registration and authentication.
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers import (
    bytes_to_base64url,
    base64url_to_bytes,
    generate_challenge,
    generate_user_handle,
    parse_registration_credential_json,
    parse_authentication_credential_json,
)
from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticationCredential,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
    AuthenticatorAttachment
)

def make_registration_options(
    username: str,
    rp_id: str,
    rp_name: str = "OpenYantra",
    existing_credentials: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate registration options to send to the browser.
    """
    existing_credentials = existing_credentials or []
    
    # Generate unique user handle
    user_handle = generate_user_handle()
    
    exclude_credentials = []
    for cred in existing_credentials:
        exclude_credentials.append(
            PublicKeyCredentialDescriptor(
                id=base64url_to_bytes(cred["credential_id"])
            )
        )
        
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=rp_name,
        user_id=user_handle,
        user_name=username,
        user_display_name=username,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    
    # Store user handle and challenge base64 representation to verify later
    return json.loads(options_to_json(options))

def check_registration_response(
    credential_data: Dict[str, Any],
    expected_challenge: str,
    expected_rp_id: str,
    expected_origin: str
) -> Dict[str, Any]:
    """
    Verify the registration credential payload from the browser.
    Returns the parsed credential details to save in settings.
    """
    credential = parse_registration_credential_json(credential_data)
    
    verification = verify_registration_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(expected_challenge),
        expected_rp_id=expected_rp_id,
        expected_origin=expected_origin,
        require_user_verification=False  # Allow flexible authenticators
    )
    
    return {
        "credential_id": bytes_to_base64url(verification.credential_id),
        "public_key": bytes_to_base64url(verification.credential_public_key),
        "sign_count": verification.sign_count,
    }

def make_authentication_options(
    rp_id: str,
    registered_credentials: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate login options to send to the browser.
    """
    allow_credentials = []
    for cred in registered_credentials:
        allow_credentials.append(
            PublicKeyCredentialDescriptor(
                id=base64url_to_bytes(cred["credential_id"])
            )
        )
        
    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    
    return json.loads(options_to_json(options))

def check_authentication_response(
    credential_data: Dict[str, Any],
    expected_challenge: str,
    expected_rp_id: str,
    expected_origin: str,
    public_key_b64: str,
    current_sign_count: int
) -> Dict[str, Any]:
    """
    Verify the authentication assertion payload from the browser.
    Returns verification status and the new sign count.
    """
    credential = parse_authentication_credential_json(credential_data)
    
    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(expected_challenge),
        expected_rp_id=expected_rp_id,
        expected_origin=expected_origin,
        credential_public_key=base64url_to_bytes(public_key_b64),
        credential_current_sign_count=current_sign_count,
        require_user_verification=False
    )
    
    return {
        "verified": True,
        "new_sign_count": verification.new_sign_count
    }
