# AI推論プロキシサーバー 実装ガイド (v0.1)

## 1. はじめに

このガイドは、「AI推論プロキシサーバー」プロジェクトにおける開発プロセスを円滑に進め、コードの品質と一貫性を保つことを目的としています。主に以下の技術スタックとプラクティスに基づいています。

* **コアライブラリ:** FastAPI, Pydantic, Loguru, Docker SDK for Python
* **パッケージ管理:** uv
* **テスト:** pytest, pytest-asyncio, pytest-mock, doctest
* **バージョン管理:** Git, Conventional Commits
* **プロジェクト管理:** GitHub Issues, Pull Requests

対象読者は、このプロジェクトの開発に参加する（または将来コードを読む可能性のある）開発者（主にあなた自身）です。

### パッケージ管理

pipではなくuvを使用します。

uvの使用方法は[uvの公式ドキュメント](https://docs.astral.sh/uv/getting-started/installation/)を参照してください。

#### パッケージの追加

```bash
uv add <package>
```

#### 開発時のみ使うパッケージ

pytestのプラグインなどは開発時のみ使うパッケージです。

```bash
uv add -d <package>
```

#### パッケージの更新

```bash
uv sync
```

### テスト

## 2. コーディングスタイルとドキュメンテーション

### 2.1. 基本原則

* **Python 3.12+:** プロジェクトはPython 3.12+を使用します。
* **PEP 8準拠:** Pythonコードは [PEP 8](https://peps.python.org/pep-0008/) に準拠します。`ruff` や `black` などのフォーマッタ/リンタを利用して自動的に準拠させます。
* **型ヒント必須:** すべての関数・メソッドの引数と戻り値には型ヒント (`typing`) を付与します。変数への型ヒントも可能な限り付与します。
* **Docstring必須:** すべての公開モジュール、クラス、関数、メソッドにはDocstringを記述します。

### モジュールの作成

* src以下にモジュールを作成します。
* モジュールのパスには`__init__.py` を作成します。

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
```

このようなDocstringを持つ関数は、以下のようにテストできます。

```bash
pytest --doctest-modules src/ai_proxy/utils.py
```
