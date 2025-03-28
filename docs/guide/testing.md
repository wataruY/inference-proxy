# テスト

## 3.1. 基本原則

* **テストは必須:** 新しい機能を追加したり、既存のコードを修正したりする際には、必ず対応するテストコードを作成または更新します。
* **AAAパターン:** テストケースは Arrange（準備）、Act（実行）、Assert（検証）の構造を意識して記述します。
* **独立性:** 各テストケースは他のテストケースに依存せず、独立して実行可能であるべきです。`pytest` の Fixture を活用して、テスト間の状態を分離します。
* **処理速度:** テストは処理速度が速いほど良いです。時間がかかるテストはマーカーをつけて、特定のテストのみを実行可能にします。

### 3.2. pytest

* **Fixture:** テストデータの準備や、テストに必要なリソース（例: `TestClient`, モック化したオブジェクト、一時ファイル/ディレクトリ）のセットアップとクリーンアップには、`@pytest.fixture` を積極的に使用します。スコープ (`function`, `class`, `module`, `session`) を適切に設定します。
* **マーカー:** `@pytest.mark` を使用して、テストにメタデータ（例: `slow`, `integration`, `unit`）を付与し、特定のテストのみを実行可能にします (`pytest -m integration`)。
* **パラメータ化:** `@pytest.mark.parametrize` を使用して、同じテストロジックを異なる入力データで繰り返し実行します。

```python
# tests/unit/test_utils.py
import pytest
from src.ai_proxy.utils import add # 仮のモジュール

@pytest.mark.parametrize(
    "a, b, expected",
    [
        (1, 2, 3),
        (-1, 1, 0),
        (0, 0, 0),
        (100, 200, 300),
    ]
)
def test_add(a, b, expected):
    """add関数のパラメータ化テスト"""
    # Arrange (パラメータで完了)
    # Act
    result = add(a, b)
    # Assert
    assert result == expected
```

### 3.3. pytest-asyncio

* 非同期関数 (`async def`) をテストする場合、テスト関数も `async def` で定義し、`@pytest.mark.asyncio` デコレータを付与します。

```python
# tests/unit/test_docker_manager.py
import pytest
from unittest.mock import AsyncMock # 非同期関数をモックする場合
# from src.ai_proxy.docker_manager import DockerManager # 仮

@pytest.mark.asyncio
async def test_start_container_success(mocker):
    """コンテナ起動成功時のテスト"""
    # Arrange
    mock_docker_client = AsyncMock()
    mock_container = AsyncMock()
    mock_container.short_id = "abc123def"
    mock_docker_client.containers.run.return_value = mock_container
    mocker.patch("docker.from_env", return_value=mock_docker_client) # Dockerクライアント初期化をモック

    # manager = DockerManager() # 実際にはFixtureで準備
    mock_config = ... # ServiceConfigのモックまたはインスタンス

    # Act
    # container = await manager.start_container("test_service", mock_config) # 実際の呼び出し

    # Assert
    # assert container.short_id == "abc123def"
    mock_docker_client.containers.run.assert_awaited_once()
    # TODO: runメソッドの引数が正しいか検証
    pass # 仮
```

### 3.4. pytest-mock

* 外部依存（Docker SDK, 外部API, ファイルシステムなど）を分離するために、`pytest-mock` の `mocker` fixture を使用します。
* `mocker.patch("path.to.your.module.TargetClassOrFunction")` で対象をモックします。`patch` のスコープ（テスト関数内、`with` 文）に注意します。
* モックオブジェクトのメソッド呼び出しを検証するには `mock_object.method.assert_called_once_with(...)` などを利用します。非同期メソッドの場合は `assert_awaited_once_with(...)` を使用します。

### 3.5. FastAPIテスト

* FastAPIアプリケーションのテストには `fastapi.testclient.TestClient` を使用します。これは `httpx` をベースにしており、実際のHTTPリクエストと同様の方法でAPIエンドポイントをテストできます。
* `TestClient` は同期的ですが、内部で非同期イベントループを処理するため、`async def` で定義されたエンドポイントもテスト可能です。
* Dependency Injectionのオーバーライド機能 (`app.dependency_overrides`) を使用して、テスト時に特定の依存性（例: `DockerManager`）をモックオブジェクトやテスト用の実装に差し替えることができます。

```python
# tests/integration/test_api.py
from fastapi.testclient import TestClient
from src.ai_proxy.main import app # FastAPIアプリケーションインスタンス
from src.ai_proxy.dependencies import get_docker_manager # DI関数
from unittest.mock import AsyncMock

# TestClientをFixtureで準備
@pytest.fixture(scope="module")
def client():
    # DockerManagerのモックを作成
    mock_docker_manager = AsyncMock()
    # モックの振る舞いを設定 (例: start_container)
    async def mock_start(*args, **kwargs):
        mock_container = AsyncMock()
        mock_container.short_id = "mock123"
        return mock_container
    mock_docker_manager.start_container = mock_start

    # DIをオーバーライド
    app.dependency_overrides[get_docker_manager] = lambda: mock_docker_manager
    yield TestClient(app)
    # クリーンアップ (オーバーライドを元に戻す)
    app.dependency_overrides = {}


def test_start_service_api_success(client):
    """POST /api/v1/service/{service_id}/start 成功時のテスト"""
    # Arrange
    service_id = "test_service"
    # TODO: テスト用の設定が読み込まれるようにする

    # Act
    response = client.post(f"/api/v1/service/{service_id}/start")

    # Assert
    assert response.status_code == 200
    assert "mock123" in response.json()["message"]
    # TODO: モックされたdocker_managerのメソッドが期待通り呼ばれたか検証
```

### 3.6. ドキュメントテスト

* ドキュメントテストは `pytest --xdoctest` で実行します。
* 特定のモジュールのみをテストする場合は `pytest --xdoctest-glob src/ai_proxy/utils.py` のように指定します。

### 3.7. テストの実行

テストの実行は `pytest` コマンドで実行します。

```bash
pytest
```

個別のテストファイルを実行する場合は `pytest tests/unit/test_utils.py` のように指定します。

ドキュメントテストも含まれているので、`pytest --xdoctest` で実行します。
特定のテストのみを実行する場合は `pytest -m integration` のようにマーカーを指定します。
テストの実行結果は `pytest --cov=src/ai_proxy` で確認できます。
