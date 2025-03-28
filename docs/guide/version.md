## 4. バージョン管理 (Git)

### Gitコマンドのワークフロー

#### リポジトリの状態の確認

```bash
git status -s
```

#### 変更の確認

```bash
git --no-pager diff path/to/file
```

#### コミットメッセージの作成

1. edit_fileツールを使用してコミットメッセージを.git/COMMIT_EDITMSGに書き込みます。

2. コミットメッセージを参照してコミットします。

```bash
git commit -F .git/COMMIT_EDITMSG
```

### 4.0. GitHub CLIワークフロー

github mcpを使って管理します

#### 例外

PRのコメント取得はgithub mcpではうまく動作しないので `gh` クライアントを使って行う

##### PRのコメント取得

```bash
gh pr view 42 --json comments
```

### 4.1. コミットメッセージ規約

**Conventional Commits** (@仕様) スタイルに従います。これにより、変更履歴が理解しやすくなり、CHANGELOGの自動生成なども可能になります。

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

`~/.gitmessage` ファイルを作成し、Gitのグローバル設定で指定しコミットメッセージの形式を統一しやすくしています。

### 4.3. ブランチ戦略

@プロジェクト計画で定義した通り、以下の戦略を基本とします。

* `main`: 安定版（リリース可能な状態）。直接コミットは禁止。
* `develop` (任意): 開発中の最新版。`feature` ブランチのマージ先。`main` へのマージはリリース時。個人開発では省略し、`main` を直接開発ブランチとしても良い。
* `feature/xxx` (`feature/123-add-status-api` など): 個別の機能開発やバグ修正を行うブランチ。`develop` (または `main`) から分岐し、完了後にPRを作成してマージする。

## 5. Issue と Pull Request

### 5.1. Issueテンプレート

GitHubリポジトリの `.github/ISSUE_TEMPLATE/` ディレクトリに以下のテンプレートファイルを作成してあります。

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

GitHubリポジトリの `.github/PULL_REQUEST_TEMPLATE.md` に以下のテンプレートファイルを作成してあります。

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
