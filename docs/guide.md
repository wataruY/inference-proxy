# AI推論プロキシサーバー 実装ガイド (v0.1)

## 1. はじめに

このガイドは、「AI推論プロキシサーバー」プロジェクトにおける開発プロセスを円滑に進め、コードの品質と一貫性を保つことを目的としています。主に以下の技術スタックとプラクティスに基づいています。

* **コアライブラリ:** FastAPI, Pydantic, Loguru, Docker SDK for Python
* **テスト:** pytest, pytest-asyncio, pytest-mock, doctest
* **バージョン管理:** Git, Conventional Commits
* **プロジェクト管理:** GitHub Issues, Pull Requests

対象読者は、このプロジェクトの開発に参加する（または将来コードを読む可能性のある）開発者（主にあなた自身）です。

## 2. コーディングスタイルとドキュメンテーション

### 2.1. 基本原則

* **Python 3.12+:** プロジェクトはPython 3.12+を使用します。
* **PEP 8準拠:** Pythonコードは [PEP 8](https://peps.python.org/pep-0008/) に準拠します。`ruff` や `black` などのフォーマッタ/リンタを利用して自動的に準拠させます。
* **型ヒント必須:** すべての関数・メソッドの引数と戻り値には型ヒント (`typing`) を付与します。変数への型ヒントも可能な限り付与します。
* **Docstring必須:** すべての公開モジュール、クラス、関数、メソッドにはDocstringを記述します。

### 2.2. Pydantic

* **モデル定義:** データ構造（設定ファイル、APIリクエスト/レスポンス）はPydanticモデル (`BaseModel`) を使用して定義します。
* **フィールド説明:** `Field` を使用して、各フィールドに `description`（説明）や `example`（例）を追加します。これはOpenAPIドキュメントの品質向上に繋がります。
* **バリデーション:** Pydanticの組み込みバリデータやカスタムバリデータ (`@validator`, `@root_validator`) を活用して、データの整合性を保証します。

```python
from pydantic import BaseModel, Field, PositiveInt, validator
from typing import List, Optional

class ResourceRequirements(BaseModel):
    """リソース要求に関する設定"""
    min_memory_mb: Optional[PositiveInt] = Field(
        None,
        description="最低限必要なメモリ量 (MB)",
        example=2048
    )
    vram_required_mb: Optional[PositiveInt] = Field(
        None,
        description="必要なVRAM量 (MB)。GPU利用時に参照される。",
        example=16000
    )

class ServiceConfig(BaseModel):
    """単一の推論サービスに関する設定"""
    type: str = Field(..., description="サービスタイプ (例: 'llama-cpp-server')", example="llama-cpp-server")
    port: PositiveInt = Field(..., description="コンテナが公開するポート番号", example=8080)
    # ... 他のフィールド ...

    @validator('volumes', each_item=True)
    def validate_volume_format(cls, v):
        """ボリューム指定が 'host:container' または 'host:container:mode' 形式か検証"""
        parts = v.split(':')
        if not (2 <= len(parts) <= 3):
            raise ValueError("Volume format must be 'host:container' or 'host:container:mode'")
        if len(parts) == 3 and parts[2] not in ('ro', 'rw'):
            raise ValueError("Volume mode must be 'ro' or 'rw'")
        # TODO: hostパスが存在するかなどの検証はここでは難しい
        return v
```

### 2.3. FastAPI

* **Dependency Injection:** 設定オブジェクト (`Config`) や `DockerManager` インスタンスなど、複数のエンドポイントで共有されるリソースは、FastAPIのDependency Injectionシステム ([`Depends`](https://fastapi.tiangolo.com/tutorial/dependencies/)) を使用して注入します。これにより、テスト時のモック差し替えが容易になります。
* **非同期処理:** I/Oバウンドな処理（Docker操作、外部API呼び出し、ファイル読み書きなど）は `async def` を使用して非同期に実装します。CPUバウンドな重い処理や同期ライブラリの使用が必要な場合は `asyncio.to_thread` や `starlette.concurrency.run_in_threadpool` を検討します。
* **API Router:** 機能ごと（例: プロキシ、管理API）に `APIRouter` を使用してエンドポイントを分割し、メインアプリケーション (`main.py`) をシンプルに保ちます。
* **エラーハンドリング:** 予期されるエラー（例: リソースが見つからない、不正なリクエスト）は `raise HTTPException(...)` でクライアントに適切なステータスコードとエラー詳細を返します。予期しないサーバー内部エラーは、カスタム例外ハンドラやミドルウェアで捕捉し、ログ記録と汎用的な `500 Internal Server Error` レスポンスを返すようにします（FastAPIのデフォルトでもある程度カバーされます）。
* **レスポンスモデル:** `response_model` 引数を指定して、レスポンスのスキーマを定義・強制します。これにより、意図しないデータがレスポンスに含まれることを防ぎ、APIドキュメントの精度を高めます。

```python
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from typing import Dict
from .settings import Config, ServiceConfig # 仮のimport
from .docker_manager import DockerManager, ServiceState # 仮のimport
from .dependencies import get_settings, get_docker_manager # 仮のDI関数

router = APIRouter(prefix="/api/v1", tags=["Management"])

@router.post(
    "/service/{service_id}/start",
    summary="Start a service container",
    description="Starts the Docker container for the specified service ID based on the configuration.",
    status_code=status.HTTP_200_OK,
    # response_model=StartResponse # Pydanticモデルを定義した場合
)
async def start_service(
    service_id: str,
    settings: Config = Depends(get_settings),
    docker_manager: DockerManager = Depends(get_docker_manager),
    # service_states: Dict[str, ServiceState] = Depends(get_service_states) # 状態管理のDI
):
    """指定されたサービスIDのコンテナを起動するAPI。"""
    if service_id not in settings.services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found in configuration."
        )
    # TODO: 既に起動中の場合の処理 (冪等性)
    try:
        # state = service_states[service_id] # 状態を取得
        # state.status = ServiceStatus.STARTING # 状態を更新
        container = await docker_manager.start_container(service_id, settings.services[service_id])
        # state.container_id = container.id
        # state.status = ServiceStatus.RUNNING
        return {"message": f"Container for service '{service_id}' started with ID {container.short_id}."}
    except docker.errors.APIError as e:
        # state.status = ServiceStatus.ERROR
        # state.last_error = str(e)
        logger.exception(f"Failed to start container for service '{service_id}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start container: {e}"
        )
    # ... 他のエラーハンドリング ...
```

### 2.4. Loguru

* **設定:** プロジェクト初期（例: `src/ai_proxy/logging.py` と `main.py`）で `loguru.logger` を設定します。推奨フォーマットには、タイムスタンプ、レベル、モジュール/関数名、行番号を含めます。
* **ログレベル:** 以下のガイドラインに従って使い分けます。
  * `DEBUG`: 詳細なデバッグ情報（リクエスト内容、変数の値、処理ステップ）。通常運用では抑制。
  * `INFO`: 通常の操作記録（サーバー起動、API呼び出し受付、コンテナ起動/停止成功など）。
  * `WARNING`: 軽微な問題、予期しないが処理は続行可能な状況。
  * `ERROR`: 処理が失敗したエラー（APIエラー、コンテナ操作失敗など）。原因調査が必要。
  * `CRITICAL`: システムが続行不可能な致命的エラー。即時対応が必要。
* **例外ロギング:** `try...except` ブロックで例外を捕捉した際は、`logger.exception("エラーメッセージ")` を使用して、メッセージと共にスタックトレースを記録します。
* **コンテキスト:** `logger.bind()` を使って、リクエストIDやサービスIDなどのコンテキスト情報をログに追加すると、追跡が容易になります。
* **デコレータ:** `@logger.catch` デコレータを使用すると、関数内で発生した捕捉されなかった例外を自動的にログに記録できます（乱用注意）。

```python
# src/ai_proxy/logging.py
import sys
from loguru import logger

def setup_logging(log_level="INFO"):
    logger.remove()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        # "<cyan>req_id:{extra[request_id]}</cyan> | " # コンテキスト例
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, level=log_level, format=log_format, colorize=True)
    logger.info(f"Logging setup complete. Level: {log_level}")

# main.py や DI 関数内で使用例
# from .logging import logger
# logger.bind(request_id="xyz123").info("Processing request...")
```

### 2.5. Docstrings と Doctest

* **スタイル:** Googleスタイル ([例](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)) を推奨します。関数の目的、引数 (`Args:`）、戻り値 (`Returns:`）、発生しうる例外 (`Raises:`) を記述します。
* **Doctest:** 簡単な関数や純粋なロジックに対しては、Docstring内に `Example:` セクションを設け、`doctest` 形式で実行可能なサンプルコードと期待される出力を記述します。これにより、ドキュメントが常に正しく、コードが期待通りに動作することを保証しやすくなります。

```python
def add(a: int, b: int) -> int:
    """二つの整数を加算します。

    Args:
        a (int): 最初の整数。
        b (int): 二番目の整数。

    Returns:
        int: 二つの整数の和。

    Example:
        >>> add(1, 2)
        3
        >>> add(-1, 1)
        0
    """
    return a + b

# ターミナルで実行:
# pytest --doctest-modules src/your_module.py
# または python -m doctest src/your_module.py
```

## 3. テスト

### 3.1. 基本原則

* **テストは必須:** 新しい機能を追加したり、既存のコードを修正したりする際には、必ず対応するテストコードを作成または更新します。
* **AAAパターン:** テストケースは Arrange（準備）、Act（実行）、Assert（検証）の構造を意識して記述します。
* **独立性:** 各テストケースは他のテストケースに依存せず、独立して実行可能であるべきです。`pytest` の Fixture を活用して、テスト間の状態を分離します。

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

## 4. バージョン管理 (Git)

### 4.1. コミットメッセージ規約

**Conventional Commits** ([仕様](https://www.conventionalcommits.org/)) スタイルに従います。これにより、変更履歴が理解しやすくなり、CHANGELOGの自動生成なども可能になります。

**フォーマット:**

```text
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

* **`<type>`:** コミットの種類を示す必須フィールド。以下のいずれかを使用します。
  * `feat`: 新機能の追加 (minorバージョンアップに対応)
  * `fix`: バグ修正 (patchバージョンアップに対応)
  * `chore`: ビルドプロセスや補助ツール、設定ファイルの変更など（コードの動作に影響しないもの）
  * `docs`: ドキュメントのみの変更
  * `style`: コードの動作に影響しない、スタイルに関する変更（フォーマット、セミコロンなど）
  * `refactor`: コードの動作に影響しないリファクタリング
  * `test`: テストコードの追加・修正
  * `ci`: CI設定ファイルやスクリプトの変更
  * `build`: ビルドシステムや外部依存関係に関する変更 (例: `pyproject.toml` の更新)
  * `perf`: パフォーマンスを向上させるコード変更
* **`<scope>` (任意):** コミットが影響する範囲を示す。例: `api`, `docker`, `config`, `proxy`, `tests` など。
* **`<subject>`:** コミット内容の簡潔な説明。必須。
  * 現在形の命令形（例: `add`, `fix`, `change`）で始める。
  * 最初の文字は小文字。
  * 末尾にピリオドは付けない。
  * 50文字以内を目安にする。
* **`<body>` (任意):** より詳細な説明。変更の背景や理由などを記述。
* **`<footer>` (任意):** 関連するIssue番号 (`Closes #123`, `Refs #456`) や、破壊的変更 (`BREAKING CHANGE: ...`) を記述。

**例:**

```text
feat(api): add endpoint to get container status

Implement GET /api/v1/container/{service_id} to retrieve the status
of a specific service container using Docker SDK.

Closes #25
```

```text
fix(proxy): handle connection errors to backend container

Return 502 Bad Gateway instead of 500 Internal Server Error when
the proxy fails to connect to the target container. Improve error logging.
```

```text
chore: update ruff configuration

Enable new linting rules and adjust settings in pyproject.toml.
```

### 4.2. コミットメッセージテンプレート

任意ですが、`~/.gitmessage` ファイルを作成し、Gitのグローバル設定で指定すると、コミットメッセージの形式を統一しやすくなります。

```bash
# ~/.gitmessage の例
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>

# --- Conventional Commits Guide ---
# type: feat, fix, chore, docs, style, refactor, test, ci, build, perf
# scope: (optional) ex: api, docker, config, proxy, tests
# subject: imperative, present tense, max 50 chars, no period at the end
# body: (optional) motivation, details
# footer: (optional) Closes #issue, Refs #issue, BREAKING CHANGE: description
```

```bash
# Git設定
git config --global commit.template ~/.gitmessage
```

### 4.3. ブランチ戦略

フェーズ0で定義した通り、以下の戦略を基本とします。

* `main`: 安定版（リリース可能な状態）。直接コミットは禁止。
* `develop` (任意): 開発中の最新版。`feature` ブランチのマージ先。`main` へのマージはリリース時。個人開発では省略し、`main` を直接開発ブランチとしても良い。
* `feature/xxx` (`feature/123-add-status-api` など): 個別の機能開発やバグ修正を行うブランチ。`develop` (または `main`) から分岐し、完了後にPRを作成してマージする。

## 5. Issue と Pull Request

### 5.1. Issueテンプレート

GitHubリポジトリの `.github/ISSUE_TEMPLATE/` ディレクトリに以下のテンプレートファイルを作成します。

**`.github/ISSUE_TEMPLATE/feature_request.md`**

```markdown
---
name: ✨ 機能要望 (Feature Request)
about: 新しい機能や改善の提案
title: "feat: [簡潔な機能名]"
labels: Type: Feature
assignees: ''
---

## 🚀 機能説明 (Description)

<!-- この機能が何を解決するのか、どのようなものかを説明してください -->

## 👤 ユーザーストーリー / 価値 (User Story / Value)

<!--
As a [ユーザーの種類],
I want to [実現したいこと],
so that [得られる価値].
-->

## ✅ 機能要件 / 受け入れ基準 (Requirements / Acceptance Criteria)

<!--
この機能が完了したと判断できる具体的な条件をリストアップしてください。
- [ ] 条件1
- [ ] 条件2
- [ ] 条件3
-->

## 📚 関連情報 (Additional Context)

<!-- スクリーンショット、関連Issue、参考資料などがあれば記述 -->
```

**`.github/ISSUE_TEMPLATE/bug_report.md`**

```markdown
---
name: 🐛 バグ報告 (Bug Report)
about: 動作しない、または期待通りに動作しない問題の報告
title: "fix: [バグの概要]"
labels: Type: Bug
assignees: ''
---

## 🐞 バグの説明 (Description)

<!-- バグの内容を明確かつ簡潔に説明してください -->

## 🔁 再現手順 (Steps to Reproduce)

<!-- バグを再現させるための具体的な手順を記述してください -->
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## 🤔 期待される動作 (Expected Behavior)

<!-- 本来、どのように動作すべきだったかを説明してください -->

## 💥 実際の動作 (Actual Behavior)

<!-- 実際に何が起こったかを説明してください -->

## 🖥️ 環境 (Environment)

<!-- (任意) バグが発生した環境情報を記述してください (OS, Pythonバージョン, Dockerバージョンなど) -->
- OS: [e.g. Ubuntu 22.04]
- Python Version: [e.g. 3.11]
- Docker Version: [e.g. 24.0]
- Project Version: [e.g. v0.1.0 or commit hash]

## 📚 関連情報 (Additional Context)

<!-- エラーメッセージ全文、ログ、スクリーンショットなど、問題解決に役立つ情報があれば記述 -->
```

**`.github/ISSUE_TEMPLATE/documentation.md`**

```markdown
---
name: 📖 ドキュメント (Documentation)
about: ドキュメントの追加・修正に関するタスク
title: "docs: [ドキュメント変更の概要]"
labels: Type: Documentation
assignees: ''
---

## 📝 目的 (Purpose)

<!-- このドキュメント変更の目的を説明してください (例: READMEのセットアップ手順を更新する) -->

## 📄 対象ファイル/箇所 (Target Files/Sections)

<!-- 変更対象となるファイルやセクションを具体的に記述してください -->
- `README.md`
- `docs/config.example.yaml`
- `src/ai_proxy/module.py` のDocstring

## ✅ タスク (Tasks)

<!-- 具体的な作業内容をリストアップしてください -->
- [ ] READMEの実行方法を修正
- [ ] config.example.yamlに新しい設定項目を追加
- [ ] module.pyの関数のDocstringを修正
```

### 5.2. Pull Requestテンプレート

GitHubリポジトリの `.github/PULL_REQUEST_TEMPLATE.md` に以下のテンプレートファイルを作成します。

**`.github/PULL_REQUEST_TEMPLATE.md`**

```markdown
## 概要 (Overview)

<!-- このPRの目的や変更内容の概要を記述してください -->

## 関連Issue (Related Issues)

<!-- このPRが関連するIssue番号を記述してください -->
<!-- 例: Closes #123, Refs #456 -->
- Closes #

## 変更点 (Changes)

<!-- 具体的な変更内容を箇条書きで記述してください -->
- 機能Aを追加しました
- バグBを修正しました
- 設定ファイルの読み込みロジックをリファクタリングしました

## ✅ テスト (Tests)

<!-- 実施したテスト内容や、テストが不要な場合はその理由を記述してください -->
- [ ] ユニットテストを追加・パスしました (`pytest tests/unit`)
- [ ] 結合テストを追加・パスしました (`pytest tests/integration`)
- [ ] 手動で以下のケースを確認しました:
  1. ケース1
  2. ケース2
- [ ] テストは不要です (理由: ドキュメントのみの変更のため)

## 影響範囲 (Impact Scope)

<!-- この変更が影響を与える可能性のある範囲を記述してください (任意) -->
- API `/api/v1/...`
- 設定ファイルの `services` セクション
- Dockerコンテナの起動引数

## レビュー担当者へのメッセージ (Message to Reviewers)

<!-- 特にレビューしてほしい点や、懸念事項などがあれば記述してください (任意) -->

## ☑️ セルフチェックリスト (Self Checklist)

<!-- PR作成者が確認する項目 -->
- [ ] `ruff check .` および `ruff format .` を実行した
- [ ] `pytest` を実行し、すべてのテストがパスした (`--doctest-modules` も含む)
- [ ] コミットメッセージは Conventional Commits 規約に従っている
- [ ] 関連するドキュメント (README, Docstrings 등) を更新した
- [ ] (必要な場合) 設定ファイルサンプル (`config.example.yaml`) を更新した
```
