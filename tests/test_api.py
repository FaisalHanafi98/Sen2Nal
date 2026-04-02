"""Tests for FastAPI endpoints.

Uses TestClient with the test DB session override from conftest.
These tests verify endpoint routing, response shapes, and status codes
without requiring real pipeline data.
"""

from unittest.mock import patch

from src.constants import API_VERSION


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


class TestNotFound:

    def test_404_returns_error_json(self, client):
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
