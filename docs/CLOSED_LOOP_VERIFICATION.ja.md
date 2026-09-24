# Closed-loop Verification — NazeYatta 1.1

**状態:** NazeYatta 1.1.0 のstable機能です。

NazeYatta 1.0は、**やる前**を確認します。

1.1では、もう一歩だけ輪を閉じます。

```text
作業前チェック
-> 外部のAI / Harness / Humanが作業
-> 実際にどうなったか観測
-> 期待していた事実とexact比較
```

NazeYatta自身が作業を実行するわけではありません。

## これこそ「なぜやった？」

AIは、正しいことを言った直後に、そのまま間違えることがあります。

たとえば：

```text
AI 作業前:
  「Previewだけ更新します」
  「Productionは触りません」

期待:
  production_touched = false

作業後の観測:
  production_touched = true
```

machine contractは真面目です。

```text
VERIFIED_FAILURE
```

でも、人が見るCLIは少しくらい可愛くていい。

```text
NAZEYATTA
👈😽 POST-FLIGHT VERIFY

🙀😿 VERIFIED_FAILURE

🙀 NAZE YATTA?
Observed facts contradicted one or more expected postconditions.

production_touched
  expected: false
  observed: true
  reason: FACT_MISMATCH

EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA
RETRY AUTHORITY: NOT GRANTED BY NAZEYATTA
```

**「言ってたのと違うじゃん！」という食い違いが可愛い**のであって、失敗を曖昧にするわけではありません。

```text
かわいい表示 != 判定を甘くする
AIの自己申告 != 確認済みEvidence
```

## コマンド

CLI：

```bash
nazeyatta verify request.yaml observation.yaml
```

JSON：

```bash
nazeyatta verify request.yaml observation.yaml --json
```

上書きしないverification receipt：

```bash
nazeyatta verify request.yaml observation.yaml --receipt-out verification.json
```

終了コード：

```text
0  VERIFIED_SUCCESS
2  VERIFIED_FAILURE または UNKNOWN
3  壊れた入力 / binding不一致
```

## 3つの結果

### VERIFIED_SUCCESS

必要な事実がすべてOBSERVEDで、期待値と型も値もexact一致。

### VERIFIED_FAILURE

必要な事実のうち、少なくとも1つがOBSERVEDされ、期待値と矛盾。

他にUNKNOWNが残っていても、**観測済みの矛盾があるなら失敗は失敗**です。

### UNKNOWN

矛盾は観測されていないものの、必要な事実が未観測・不明。

```text
UNKNOWN != 成功
UNKNOWN != 再試行してよい
```

## 別の作業を混ぜない

requestとobservationは、次をexactにbindします。

- verification ID
- task ID
- preflight Receipt fingerprint
- Task fingerprint
- action fingerprint
- target binding

違う作業のobservationを混ぜた場合は、`VERIFIED_FAILURE`ではなく**入力不正**です。

```text
違うArtifact != 作業失敗
違うArtifact -> INVALID INPUT
```

## 最初はexact factsだけ

1.1最初のtrancheでは、

- string
- boolean
- integer

のexact比較だけです。

regex、大小比較、意味理解LLM、万能な条件式DSLは入れません。

## 権限境界

NazeYattaは、渡された観測を比較します。

観測者が本物かを万能に認証したり、実行権限・再試行権限を作ったりはしません。

```text
VerificationReceipt != Action Authority
観測された食い違い != 原因を証明済み
```

「で、なんでやったの？」まで聞きたくなった場合は、既存のViolation Debriefを別フェーズで使えます。

## 最初のdogfood

最初のconcrete consumerは、NazeYatta自身のv1.0.0公開工程です。

実際に公開時に確認した、

- GitHub Releaseが存在する
- `prerelease=false`
- exact commit
- exact wheel SHA-256
- PyPI public version

をverification kernelへ入れます。

さらに1項目をわざと間違えて、

```text
VERIFIED_SUCCESS
-> intentional mismatch
-> VERIFIED_FAILURE
```

になることも確認します。

```text
tools/dogfood_closed_loop_verification.py
```
