import pytest

from app import build_user_profile_payload


def test_build_user_profile_payload_includes_expected_fields():
    payload = build_user_profile_payload(
        uid="abc123",
        name="Ada Lovelace",
        email="ada@example.com",
        device_id="ESP32_001",
    )

    assert payload["name"] == "Ada Lovelace"
    assert payload["email"] == "ada@example.com"
    assert payload["device_id"] == "ESP32_001"
    assert payload["scores"]["memory"] is None
    assert payload["scores"]["mlPrediction"] is None
