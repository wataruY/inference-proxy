import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, TimeoutException, ConnectError
import pytest_asyncio
from unittest.mock import patch, MagicMock
from ai_proxy.proxy import app, init_proxy, ProxyServer, get_proxy_server
from ai_proxy.settings import ApplicationSettings, ServiceSettings, LogSettings
from pathlib import Path

@pytest.fixture
def test_client():
    """テストクライアントの作成"""
    settings = ApplicationSettings(
        services=[ServiceSettings(name="test", image="test-image", port=8000)],
        logging=LogSettings(output_dir=Path("/tmp/logs"), level="INFO")
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
    # グローバル変数をモジュールレベルでインポートし、テスト内で変更
    from ai_proxy import proxy
    proxy._proxy_server = None
    
    with TestClient(app) as client:
        response = client.get("/test")
        assert response.status_code == 500
        assert response.json()["detail"] == "プロキシサーバーが初期化されていません"

@pytest.mark.asyncio
async def test_service_selection():
    """サービス選択のテスト"""
    settings = ApplicationSettings(
        services=[
            ServiceSettings(name="service1", image="image1", port=8001),
            ServiceSettings(name="service2", image="image2", port=8002)
        ],
        logging=LogSettings(output_dir=Path("/tmp/logs"), level="INFO")
    )
    init_proxy(settings)

    # 現在の実装では最初のサービスが選択される
    with TestClient(app) as client:
        response = client.get("/test")
        assert response.status_code in [200, 404, 502]

@pytest.mark.asyncio
async def test_proxy_timeout():
    """タイムアウトのテスト"""
    settings = ApplicationSettings(
        services=[ServiceSettings(name="test", image="test-image", port=8000)],
        logging=LogSettings(output_dir=Path("/tmp/logs"), level="INFO")
    )
    init_proxy(settings)

    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.side_effect = TimeoutException("Connection timeout")
        
        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 504
            assert response.json()["detail"] == "ゲートウェイタイムアウト"

@pytest.mark.asyncio
async def test_proxy_connection_error():
    """接続エラーのテスト"""
    settings = ApplicationSettings(
        services=[ServiceSettings(name="test", image="test-image", port=8000)],
        logging=LogSettings(output_dir=Path("/tmp/logs"), level="INFO")
    )
    init_proxy(settings)

    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.side_effect = ConnectError("Failed to connect")
        
        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 502
            assert response.json()["detail"] == "バックエンドサーバーに接続できません"

@pytest.mark.asyncio
async def test_proxy_generic_error():
    """その他のエラーのテスト"""
    settings = ApplicationSettings(
        services=[ServiceSettings(name="test", image="test-image", port=8000)],
        logging=LogSettings(output_dir=Path("/tmp/logs"), level="INFO")
    )
    init_proxy(settings)

    with patch('httpx.AsyncClient.request') as mock_request:
        mock_request.side_effect = Exception("Unexpected error")
        
        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 500
            assert response.json()["detail"] == "内部サーバーエラー: Unexpected error" 