"""Tests for FastAPI endpoints.

Uses TestClient with the test DB session override from conftest.
These tests verify endpoint routing, response shapes, and status codes
without requiring real pipeline data.
"""

from unittest.mock import patch, MagicMock

from src.constants import API_VERSION, ALLOWED_TICKERS


class TestRootEndpoint:

    def test_root_returns_welcome(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Sen2Nal" in data["message"]
        assert "docs" in data


class TestHealthEndpoint:

    @patch("src.api.main.check_db_connection", return_value=True)
    def test_health_connected(self, mock_db, client):
        response = client.get(f"/api/{API_VERSION}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    @patch("src.api.main.check_db_connection", return_value=False)
    def test_health_degraded(self, mock_db, client):
        response = client.get(f"/api/{API_VERSION}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


class TestStocksEndpoints:

    def test_stocks_empty_db(self, client):
        response = client.get(f"/api/{API_VERSION}/stocks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_stocks_with_seed(self, client, seed_stock):
        response = client.get(f"/api/{API_VERSION}/stocks")
        assert response.status_code == 200

    def test_fear_greed_empty(self, client):
        response = client.get(f"/api/{API_VERSION}/stocks/fear-greed")
        assert response.status_code == 200


class TestExperimentsEndpoints:

    def test_experiments_empty(self, client):
        response = client.get(f"/api/{API_VERSION}/experiments")
        assert response.status_code == 200

    def test_experiments_summary_empty(self, client):
        response = client.get(f"/api/{API_VERSION}/experiments/summary")
        assert response.status_code == 200


class TestPipelineEndpoints:

    def test_pipeline_status(self, client):
        response = client.get(f"/api/{API_VERSION}/pipeline/status")
        assert response.status_code == 200

    def test_pipeline_logs(self, client):
        response = client.get(f"/api/{API_VERSION}/pipeline/logs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAlertsEndpoint:

    def test_alerts_empty_db(self, client):
        response = client.get(f"/api/{API_VERSION}/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTickerWhitelist:

    def test_history_rejects_non_whitelisted_ticker(self, client):
        response = client.get(f"/api/{API_VERSION}/stocks/history?ticker=FAKE")
        assert response.status_code == 200
        data = response.json()
        assert data["history"] == []
        assert "not in allowed list" in data["error"]

    def test_history_accepts_whitelisted_ticker(self, client):
        response = client.get(f"/api/{API_VERSION}/stocks/history?ticker=AAPL")
        assert response.status_code == 200
        data = response.json()
        # May have empty history (no data seeded), but should NOT have whitelist error
        assert "not in allowed list" not in data.get("error", "")


class TestPipelineAuth:

    @patch("src.api.routers.pipeline.settings")
    def test_pipeline_run_requires_auth_when_key_set(self, mock_settings, client):
        mock_settings.pipeline_api_key = "secret-key-123"
        response = client.post(f"/api/{API_VERSION}/pipeline/run")
        assert response.status_code == 403

    @patch("src.api.routers.pipeline.settings")
    def test_pipeline_run_accepts_valid_key(self, mock_settings, client):
        mock_settings.pipeline_api_key = "secret-key-123"
        response = client.post(
            f"/api/{API_VERSION}/pipeline/run",
            headers={"X-Api-Key": "secret-key-123"},
        )
        # Should pass auth (may fail for other reasons like no pipeline, but not 403)
        assert response.status_code != 403

    @patch("src.api.routers.pipeline.settings")
    def test_pipeline_run_rejects_wrong_key(self, mock_settings, client):
        mock_settings.pipeline_api_key = "secret-key-123"
        response = client.post(
            f"/api/{API_VERSION}/pipeline/run",
            headers={"X-Api-Key": "wrong-key"},
        )
        assert response.status_code == 403


class TestPipelineLogs:

    def test_logs_returns_empty_list_when_no_runs(self, client):
        response = client.get(f"/api/{API_VERSION}/pipeline/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["logs"] == []

    def test_logs_no_synthetic_data(self, client):
        """Verify no fake 'System' log entries are returned."""
        response = client.get(f"/api/{API_VERSION}/pipeline/logs")
        data = response.json()
        for log in data["logs"]:
            assert log.get("stage") != "System"


class TestNotFound:

    def test_404_returns_error_json(self, client):
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
