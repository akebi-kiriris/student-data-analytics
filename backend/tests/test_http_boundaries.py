from app import app as flask_app


def _client():
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def test_files_endpoint_requires_jwt():
    response = _client().get("/api/files")
    assert response.status_code == 401


def test_analysis_endpoint_requires_jwt():
    response = _client().post("/api/column_stats", json={})
    assert response.status_code == 401


def test_register_missing_fields_returns_400():
    response = _client().post("/api/auth/register", json={})
    assert response.status_code == 400
