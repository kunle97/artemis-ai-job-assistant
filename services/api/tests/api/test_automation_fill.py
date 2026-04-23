def test_automation_fill_requires_auth(client):
    response = client.post(
        "/automation-fill",
        json={
            "application_url": "https://example.com",
            "inspected_fields": [],
        },
    )
    assert response.status_code == 401