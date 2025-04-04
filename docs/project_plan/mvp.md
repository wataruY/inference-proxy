# プロジェクト計画: AI推論プロキシサーバー

## フェーズ3: MVP開発

**目的:**
【解説】このフェーズでは、フェーズ2「設計」で定義した計画に基づき、MVP（Minimum Viable Product）スコープの機能を実際にコーディングし、テストを行います。開発環境を構築し、GitHub Issueに基づいたタスク管理、Pull Requestによるコードレビュー、マージという開発サイクルを回しながら、動作する最初のバージョンを作成することを目指します。

**想定期間:**
【解説】MVPスコープの機能実装、テストコード作成、基本的なドキュメント整備にかかる期間を見積もります。個人の開発速度や確保できる時間によりますが、3〜4週間程度が目安です。
【記入例】`{{3-4週}}`

---

### 1. 開発環境構築

**【解説】**
MVPの開発を開始するために必要なツールを準備し、プロジェクトのソースコードをローカルにセットアップします。開発をスムーズに進めるための環境を整えます。

* **必要なツール:**
  * 【解説】開発に必要なソフトウェアやライブラリをリストアップします。バージョンも指定しておくと環境差異による問題を減らせます。
  * 【記入例】
    * Python (`{{例: 3.10 以上}}`)
    * `uv` (`{{インストール手順: pip install uv または公式ドキュメント参照}}`)
    * Git
    * Docker Engine
    * NVIDIA Container Toolkit (`{{GPU利用の場合}}`)
    * テキストエディタ/IDE (`{{例: VS Code, Cursor}}`)
    * (任意) `pre-commit` (`{{pip install pre-commit}}`)

* **プロジェクトセットアップ:**
  * 【解説】GitHubリポジトリからコードを取得し、依存ライブラリをインストールする手順を記述します。
  * 【記入例】
        1. `git clone {{リポジトリのURL}}`
        2. `cd ai-inference-proxy`
        3. `uv venv` （仮想環境を作成）
        4. `. .venv/bin/activate` （または `source .venv/bin/activate` などで仮想環境を有効化）
        5. `uv pip install -r requirements.lock` （または `uv pip sync pyproject.toml` など、プロジェクトの管理方法に応じて）

* **ローカル実行環境:**
  * 【解説】開発したサーバーを実行するために必要な外部環境（Dockerデーモンなど）の状態を確認する手順です。
  * 【記入例】
    * Dockerデーモンが起動していることを確認する (`{{docker info}}` など）。
    * GPUを利用する場合、NVIDIAドライバとNVIDIA Container Toolkitが正しく設定されていることを確認する (`{{docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi}}` などで確認）。

* **(任意) pre-commitフック設定:**
  * 【解説】コードフォーマットの自動化やリントチェックをコミット前に実行するための設定です。コードスタイルの一貫性を保つのに役立ちます。
  * 【記入例】
    * リポジトリルートに `.pre-commit-config.yaml` を作成または編集し、使用するフック（例: `ruff`, `black`）を設定する。
    * `pre-commit install` を実行して、Gitフックを有効化する。

---

### 2. 実装 (Issue駆動開発)

**【解説】**
フェーズ2の設計に基づき、実際にコードを書いていきます。GitHub Issueをタスクの単位とし、ブランチを作成して開発、Pull Requestでレビューとマージを行うプロセスで進めます。

* **開発プロセス:**
  * 【解説】具体的な開発の進め方をステップで記述します。Issue、ブランチ、PRの流れを明確にします。
  * 【記入例】
        1. 実装する機能に対応するGitHub Issueを選択または新規作成する（`Scope: MVP` ラベルが付いているもの）。
        2. 選択したIssueに基づき、`feature/{{Issue番号}}-{{短い説明}}` のような命名規則で `develop` (または `main`) ブランチから新しいブランチを作成する。
        3. フェーズ2の設計書を参照しながら、機能の実装と関連するテストコードを作成する。
        4. ローカル環境で `pytest` を実行し、全てのテストがパスすることを確認する。
        5. 変更内容をコミットし、GitHubにプッシュする。
        6. `develop` (または `main`) ブランチに対するPull Requestを作成する。PRの概要欄に、対応するIssueへのリンクや実装内容の説明を記述する。
        7. (セルフ)レビューを実施し、必要に応じて修正をコミット＆プッシュする。
        8. レビューが完了したら、PRをマージする。

* **MVP主要機能の実装順序案 (依存関係考慮):**
  * 【解説】どの機能から実装に着手するとスムーズに進むか、依存関係を考慮した推奨順序を示します。これはあくまで目安であり、状況に応じて変更可能です。
  * 【記入例】
        1. **FR-01: 設定ファイル読み込み:** Pydanticモデル定義 (`{{src/ai_proxy/settings.py}}` など)、YAML読み込み処理、バリデーションロジック。(設計: データモデル設計参照)
        2. **FR-06: 基本的なログ出力:** `loguru` の初期設定 (`{{src/ai_proxy/logging.py}}` など) と、FastAPIアプリへの組み込み。(設計: ロギング設計参照)
        3. **DockerManager 基本実装:** クラス定義 (`{{src/ai_proxy/docker_manager.py}}` など)、Dockerクライアント初期化、ボリューム解析メソッド (`_parse_volumes`)。(設計: コンテナ管理ロジック設計参照)
        4. **FR-03, FR-04: 手動コンテナ管理API (起動/停止):** `DockerManager` に `start_container`, `stop_container` メソッドを実装。対応するFastAPIエンドポイント (`{{src/ai_proxy/routers/management.py}}` など) を実装。(設計: API設計, コンテナ管理ロジック設計参照)
        5. **FR-05: コンテナ状態取得API:** `DockerManager` に `get_container_status` メソッドを実装。対応するFastAPIエンドポイントを実装。(設計: API設計, コンテナ管理ロジック設計参照)
        6. **FR-02: 基本的なプロキシ機能:** プロキシ処理を行うハンドラ関数またはクラス (`{{src/ai_proxy/routers/proxy.py}}` など) を実装。バックエンドコンテナの状態を確認し、`httpx` などでリクエストを転送。(設計: API設計, アーキテクチャ設計参照)
        7. 各ステップの実装と並行して、関連する処理箇所にログ出力 (`logger.info`, `logger.error` など) を追加する。

* **実装上の注意点:**
  * 【解説】コーディングを進める上でのTipsや注意点を記述します。品質の高いコードを書くための指針となります。
  * 【記入例】
    * **型ヒント:** Pythonの型ヒント (`typing`) を可能な限り使用し、`ruff` などの静的解析ツールでチェックする。
    * **非同期処理:** FastAPIの `async def` を適切に使用する。`Docker SDK for Python` の非同期クライアント (`aiohttp` ベース) の利用を検討する。ブロッキングI/Oを行う場合は `asyncio.to_thread` などで別スレッド実行を検討する。
    * **エラーハンドリング:** フェーズ2で設計したエラーハンドリング方針に基づき、`try...except` 構文で想定される例外を捕捉し、適切なログ出力とエラーレスポンス (FastAPIの `HTTPException`) を返すように実装する。
    * **設定と状態管理:** アプリケーション全体で共有する設定情報 (`Config` オブジェクト) や実行時状態 (`ServiceState` の辞書など) の管理方法を統一する（例: FastAPIの `request.app.state` や Dependency Injection パターンを利用）。

---

### 3. テスト実装

**【解説】**
実装したコードが期待通りに動作することを保証するために、テストコードを作成します。実装と並行してテストを書くことで、バグの早期発見やリファクタリングの安全性を高めます。

* **方針:**
  * 【解説】テストコードの作成方針や、使用するツールについて記述します。
  * 【記入例】
    * 機能の実装と同時に、対応するテストコードを `tests/` ディレクトリ以下に作成する。
    * テストフレームワークとして `pytest` を使用する。
    * 非同期コードのテストには `pytest-asyncio` を利用する。

* **ユニットテスト:**
  * 【解説】個々の関数やクラス（モジュール）が単体で正しく動作するかを確認するテストです。外部依存はモック化します。
  * 【記入例】
    * テストコードは `tests/unit/` ディレクトリに配置する。
    * テスト対象例: 設定読み込みのバリデーションロジック、`DockerManager` のメソッド（Docker SDKの呼び出しはモック）、APIエンドポイントの入力検証や基本的なロジック（FastAPIの `TestClient` を使用し、`DockerManager` などの依存性はモック）。
    * 外部依存のモック化には `pytest-mock` ライブラリを使用する。

* **結合テスト:**
  * 【解説】複数のコンポーネントが連携して正しく動作するかを確認するテストです。実際にDockerデーモンなどと通信します。
  * 【記入例】
    * テストコードは `tests/integration/` ディレクトリに配置する。
    * テスト対象例:
      * `/api/v1/service/{id}/start` API を呼び出し、実際にコンテナが起動することを確認する。
      * `/api/v1/service/{id}/stop` API を呼び出し、実際にコンテナが停止することを確認する。
      * コンテナを起動した後、`/service/{id}/{path}` エンドポイント経由でリクエストが正しくプロキシされることを確認する（テスト用に `nginx` や `httpbin` などのコンテナを利用）。
    * ローカルまたはCI環境のDockerデーモンを実際に使用する。
    * `pytest` の fixture (`@pytest.fixture`) を活用し、テストの前後で必要なコンテナの起動・停止・クリーンアップを行う。

---

### 4. ロギング実装

**【解説】**
システムの動作状況を把握し、問題発生時の原因調査を容易にするために、設計に基づいたログ出力をコードに組み込みます。

* **組み込み:**
  * 【解説】`loguru` の設定を適用し、コード内の適切な箇所にログ出力処理を追加する手順です。
  * 【記入例】
    * FastAPIアプリケーションの起動処理（例: `main.py`）の中で、フェーズ2で設計した `setup_logging()` 関数を呼び出す。
    * 設定ファイルの読み込み、APIリクエストの受付、コンテナ操作の開始/終了、エラー発生時など、設計書で定義した箇所に `logger.info()`, `logger.debug()`, `logger.warning()`, `logger.error()`, `logger.exception()` などのログ出力コードを追加する。
    * エラーハンドリング (`try...except`) 内では、捕捉した例外情報もログに出力することを推奨 (`logger.exception()` を使うとトレースバックも記録される)。

---

### 5. ドキュメント作成

**【解説】**
他の人（将来の自分を含む）がプロジェクトを理解し、利用できるように、必要なドキュメントを整備します。コードとドキュメントの同期を保つことが重要です。

* **README.md:**
  * 【解説】プロジェクトの入り口となる最も重要なドキュメントです。必要な情報を簡潔にまとめます。
  * 【記入例】
    * プロジェクトの概要と目的を最新の状態に更新する。
    * **セットアップ手順:** 開発環境構築（`### 1. 開発環境構築`）の手順を記述する。
    * **設定ファイル:** `config.yaml` のサンプルを示し、MVPスコープで利用可能な設定項目について説明を追加する。
    * **実行方法:** 開発サーバーの起動コマンド例 (`uvicorn src.ai_proxy.main:app --host 0.0.0.0 --port 11000 --reload` など) を記述する。
    * **APIエンドポイント:** MVPで実装された主要なAPI (`/service/...`, `/api/v1/...`) の概要、使い方（`curl` コマンド例など）を記述する。

* **設定ファイルサンプル:**
  * 【解説】ユーザーが設定ファイルを作成する際の参考となる、具体的なサンプルファイルを提供します。
  * 【記入例】
    * `docs/config.example.yaml` またはリポジトリルートに `config.example.yaml` として、MVP機能を利用するための最小限の設定例を記述する。必要に応じてコメントで各項目の意味を補足する。

* **APIドキュメント:**
  * 【解説】APIの仕様を明確に示すドキュメントです。FastAPIの自動生成機能を活用します。
  * 【記入例】
    * FastAPIが自動生成する `/docs` (Swagger UI) および `/redoc` (ReDoc) のURLをREADMEに記載する。
    * コード内のPydanticモデルやAPIエンドポイント関数（`@app.post(...)` など）に `title`, `description`, `summary`, `tags` などの引数を追加し、自動生成されるドキュメントの内容を充実させる。

---

### 6. コードレビュー

**【解説】**
作成したコードの品質を確保し、バグを早期に発見するためのプロセスです。個人開発であっても、セルフレビューを行うことで客観的な視点を取り入れることができます。

* **観点:**
  * 【解説】Pull Requestをレビューする際に、どのような点に注目すべきかをリストアップします。
  * 【記入例】
    * **設計準拠:** フェーズ2の設計（アーキテクチャ、API仕様、ロジック）に沿って実装されているか。
    * **要求充足:** フェーズ1の機能要求を満たしているか。
    * **コード品質:** 可読性（命名、コメント、複雑度）、保守性（モジュール分割）、Pythonicな書き方になっているか。
    * **エラーハンドリング:** 想定されるエラーケースが考慮され、適切に処理（ログ出力、エラーレスポンス）されているか。
    * **テスト:** 実装された機能に対するテストコードが追加されており、カバレッジは十分か。テスト自体は妥当か。
    * **ドキュメント:** コードコメント、README、APIドキュメントなどが適切に更新されているか。
    * **(任意) パフォーマンス:** 非効率な処理やボトルネックになりそうな箇所はないか。

* **プロセス:**
  * 【解説】レビューをどのように進めるかの手順です。
  * 【記入例】
        1. 開発者はPull Requestを作成した後、まず自身で上記の観点に基づきセルフレビューを行う。
        2. (チーム開発の場合、他のメンバーにレビューを依頼する)
        3. GitHubのレビュー機能（コメント、修正提案）を活用してフィードバックを行う。
        4. 開発者はレビューコメントに対応し、必要に応じてコードを修正し、再度プッシュする。
        5. 全ての指摘事項が解決され、レビュワー（または開発者自身）が承認 (Approve) したら、Pull Requestをマージする。

---

### 7. 成果物

**【解説】**
このフェーズ3「MVP開発」が完了した時点で、どのようなものが完成しているかのリストです。

* 【記入例】
  * MVPスコープの機能（基本的なプロキシ機能、手動でのコンテナ起動/停止API、設定ファイル読み込み、基本的なログ出力）を実装したPythonコード（`src/ai_proxy` ディレクトリ以下など）。
  * 上記コードの動作を検証するためのユニットテストおよび結合テストコード（`tests/` ディレクトリ以下）。
  * プロジェクトの概要、セットアップ方法、使い方、API概要などを記載した最新の `README.md`。
  * ユーザーが設定ファイルを作成する際の参考となる `config.example.yaml`。
  * FastAPIによって自動生成され、ブラウザからアクセス可能なOpenAPI準拠のAPIドキュメント (`/docs`, `/redoc`)。
