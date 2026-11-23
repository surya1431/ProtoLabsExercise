from fastapi.testclient import TestClient
from app.api import get_packing_service
from app.main import create_app
from app.service import PackingService


def get_test_client() -> TestClient:
    app = create_app()
    fresh_service = PackingService()
    app.dependency_overrides[get_packing_service] = lambda: fresh_service
    return TestClient(app)


def test_health_endpoint():
    client = get_test_client()
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


def test_calculate_endpoint_with_details():
    client = get_test_client()
    payload = [
        {"id": 123, "width": 10, "height": 10, "length": 10, "weight": 5},
        {"id": 125, "width": 5, "height": 5, "length": 10, "weight": 10},
    ]
    res = client.post("/api/v1/packing/calculate?details=true", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["boxes_required"] == 1
    assert body["skipped_duplicate_ids"] == []
    assert body["unpackable_package_ids"] == []
    assert len(body["boxes"]) == 1
    assert body["boxes"][0]["box_type"] == "C"


def test_empty_list_returns_zero():
    client = get_test_client()
    res = client.post("/api/v1/packing/calculate", json=[])
    assert res.status_code == 200
    assert res.json() == {
        "boxes_required": 0,
        "skipped_duplicate_ids": [],
        "unpackable_package_ids": [],
    }


def test_invalid_inputs_return_422_envelope():
    client = get_test_client()
    # String ID, negative dimension, and extra unknown field
    bad_payloads = [
        [{"id": "abc", "width": 10, "height": 10, "length": 10, "weight": 5}],
        [{"id": 1, "width": -5, "height": 10, "length": 10, "weight": 5}],
        [{"id": 1, "width": 10, "height": 10, "length": 10, "weight": 5, "color": "red"}],
    ]
    for payload in bad_payloads:
        res = client.post("/api/v1/packing/calculate", json=payload)
        assert res.status_code == 422
        assert res.json()["error"]["code"] == "invalid_request"