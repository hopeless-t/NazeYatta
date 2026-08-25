# NazeYatta — OSSを初めて触る人へ

このページは、GitHubやCLIをほとんど使ったことがない人向けです。

NazeYattaを壊しても、あなたのPCやGitHub上の本体が勝手に壊れることはありません。まずはExampleをローカルで動かしてみます。

## 1. GitHubとRepository

GitHubは、Source CodeやIssue、変更履歴などを共有する場所です。

Repository（リポジトリ）は、ひとつのProjectのFileと履歴をまとめた単位です。

NazeYattaのRepositoryは：

`https://github.com/hopeless-t/NazeYatta`

です。

## 2. Terminalを開く

WindowsならPowerShell、macOS/LinuxならTerminalを使えます。

Python 3.11以上とGitが必要です。

確認：

```bash
python --version
git --version
```

## 3. cloneする

`clone`は、GitHub上のRepositoryを自分のPCへコピーする操作です。

```bash
git clone https://github.com/hopeless-t/NazeYatta.git
cd NazeYatta
```

## 4. Pythonの仮想環境を作る

```bash
python -m venv .venv
```

macOS / Linux:

```bash
. .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## 5. NazeYattaをinstallする

```bash
python -m pip install -e .
```

## 6. 安全なExampleを実行する

```bash
nazeyatta check examples/safe-read.yaml
```

`PASS`が表示されれば、最初の実行成功です。

次に、わざとBLOCKされるExampleを試します。

```bash
nazeyatta check examples/publish-photo.yaml
```

このExampleでは公開許可のEvidenceが`UNKNOWN`なので、`✋😾 BLOCK`になります。

## 7. ファイルを眺める

最初は全部理解しなくて大丈夫です。

- `examples/` — 入力例
- `policies/generic/rules.yaml` — Generic Rule
- `src/nazeyatta/` — Python実装
- `tests/` — 動作確認
- `docs/` — 設計思想とSemantics

## 8. Issueを読む

GitHubのIssueは、Bug、改善案、作業計画などを話す場所です。

Codeを書かなくても、READMEで分からなかったところをIssueで報告することはOSSへの有用なContributionです。

「この用語が分からない」というFeedbackもDocumentation改善のEvidenceになります。

## 9. 次に読むもの

- [`../README.ja.md`](../README.ja.md)
- [`PHILOSOPHY.ja.md`](PHILOSOPHY.ja.md)
- [`SEMANTICS.md`](SEMANTICS.md)

最初の目標は、すべて理解することではありません。

**自分のPCで一度 `👈😽` や `✋😾` を出してみること。**

そこからで十分です。
