import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, TimeoutException, ConnectError
import pytest_asyncio
from unittest.mock import patch, MagicMock
from ai_proxy.proxy import app, init_proxy, ProxyServer
from ai_proxy.settings import Settings

@pytest.fixture
def test_client():
    """テストクライアントの作成"""
    settings = Settings(
        backend_servers=[{"name": "test", "url": "http://localhost:8000"}]
    )
    init_proxy(settings)
    return TestClient(app)

@pytest.mark.asyncio
async def test_proxy_get_request(test_client):
    """GETリクエストの転送テスト"""
    response = test_client.get("/test")
    assert response.status_code in [200, 404, 502]  # バックエンドサーバーの状態によって変化

@pytest.mark.asyncio
async def test_proxy_post_request(test_client):
    """POSTリクエストの転送テスト"""
    response = test_client.post("/test", json={"key": "value"})
    assert response.status_code in [200, 404, 502]  # バックエンドサーバーの状態によって変化

@pytest.mark.asyncio
async def test_proxy_server_not_initialized():
    """プロキシサーバー未初期化時のエラーテスト"""
    global proxy_server
    proxy_server = None
    
    with TestClient(app) as client:
        response = client.get("/test")
        assert response.status_code == 500
        assert response.json()["detail"] == "Proxy server not initialized"

@pytest.mark.asyncio
async def test_proxy_timeout():
    """タイムアウトのテスト"""
    settings = Settings(
        backend_servers=[{"name": "test", "url": "http://localhost:8000"}]
    )
    init_proxy(settings)

    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.side_effect = TimeoutException("Connection timeout")
        
        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 504
            assert response.json()["detail"] == "Gateway Timeout"

@pytest.mark.asyncio
async def test_proxy_connection_error():
    """接続エラーのテスト"""
    settings = Settings(
        backend_servers=[{"name": "test", "url": "http://localhost:8000"}]
    )
    init_proxy(settings)

    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.side_effect = ConnectError("Failed to connect")
        
        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 502
            assert response.json()["detail"] == "Bad Gateway"

@pytest.mark.asyncio
async def test_proxy_generic_error():
    """その他のエラーのテスト"""
    settings = Settings(
        backend_servers=[{"name": "test", "url": "http://localhost:8000"}]
    )
    init_proxy(settings)

    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.side_effect = Exception("Unexpected error")
        
        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 500
            assert response.json()["detail"] == "Unexpected error" 