# NazeYatta

[English](README.md) | [日本語](README.ja.md)

**NazeYattaは、AIや自動化が何かを実行する前に使う、小さなコマンドラインの「事前チェック係」です。**

見るのは、まず一つだけです。

> **この作業を始める前に、必要な確認は本当に揃っているか？**

確認できていないものを、NazeYattaは「たぶん大丈夫」に変えません。

たとえば：

~~~text
やりたいこと:
  この写真を公開する

今わかっていること:
  公開先を確認した                 VERIFIED
  Workerの能力を確認した           VERIFIED
  公開してよい許可                 UNKNOWN

ルール:
  外部公開には、確認済みの公開許可が必要

NazeYatta:
  BLOCK
~~~

NazeYatta自身が写真を公開するわけではありません。  
NazeYatta自身が「公開してよい」という権限を与えるわけでもありません。

**実行前の確認をして、その結果を記録して返すだけ**です。

---

## 30秒で掴む全体像

~~~text
何かを実行したい
      |
      v
やりたい作業 + 今わかっている事実
      |
      v
   NazeYatta
   ルールと照合
      |
      v
PASS / REVIEW / BLOCK
+ 何を確認したかの記録
      |
      v
別のHuman / Worker / Harnessが
実際に進めるか判断・実行する
~~~

イメージとしては、

> **機械が読める「作業前チェックリスト」**

に近いです。

特に、

~~~text
「確認できなかった」
        ↓
「まあ大丈夫だろう」
~~~

へ勝手に変換してほしくない時に使います。

---

## これ、本当に必要？

場合によります。

小さなスクリプト1本と単純な if 文だけで十分なら、**その if 文を使った方がいい**です。

NazeYattaが役立つのは、複数のAI Workerや自動処理で、次のような境界を共通化したい時です。

- UNKNOWN / MISSING / STALE / VERIFIED を明示したい
- 同じ事前チェックのルールを再利用したい
- CLIの終了コードを一貫させたい
- 「何を確認したか」のreceiptを残したい
- **Evidenceと実行権限を混ぜたくない**

例：

- git push の前
- ファイルやresourceを削除・置換する前
- コンテンツを外部公開する前
- 外部へ書き込む前
- 資格確認が必要なCapabilityを使う前
- 操作対象が本当に正しいか確認したい時

---

## まず1回だけ動かす

Python 3.11+ が必要です。

~~~bash
git clone https://github.com/hopeless-t/NazeYatta.git
cd NazeYatta
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e .

nazeyatta check examples/publish-photo.yaml
~~~

このExampleでは、

~~~text
publication_permission_verified = UNKNOWN
~~~

です。

同梱されているbaseline ruleは、

> 外部公開には、確認済みの公開許可が必要

と要求します。

そのため結果は：

~~~text
NAZEYATTA
👈😽 PRE-FLIGHT KY

✋😾 BLOCK

NY-PUB-001  External publication requires verified provenance and permission
  hazard: PUBLICATION_WITH_UNKNOWN_RIGHTS
  evidence: publication_permission_verified = UNKNOWN
  effect: BLOCK

EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA
~~~

平たく言えば：

> **「公開していいことを確認できないので、この事前チェックでは進めてよい扱いにしません。」**

です。

安全なread-only例もあります。

~~~bash
nazeyatta check examples/safe-read.yaml
~~~

こちらは PASS になります。

ただし：

~~~text
PASS != Execution Authority
~~~

**PASSは「NazeYattaが実行権限を与えた」という意味ではありません。**

「今回渡された情報とルールでは、この事前チェックに強い停止理由がなかった」という結果です。

---

## NazeYattaには何を渡すの？

最初は、小さなYAMLファイル1つで試せます。

例：

~~~yaml
task_id: MY-FIRST-READ

action:
  operation: read
  side_effect: none
  externality: internal

worker:
  required_capability: read_repository

semantics:
  critical_meaning_complete: true

evidence:
  worker_capability_qualified: VERIFIED
~~~

my-first-task.yaml として保存したら：

~~~bash
nazeyatta check my-first-task.yaml
~~~

NazeYattaには小さなgeneric baseline policyが同梱されているので、**最初の1回を動かすためにpolicy fileまで自作する必要はありません。**

大づかみに言えば、

~~~text
何をしたいか
+
今わかっていること
+
適用されるルール
~~~

を照合して、結果とreceiptを返します。

---

## 何が返ってくるの？

現在の主な結果は：

- PASS
- CAUTION
- REVIEW
- EVIDENCE_REQUIRED
- BLOCK

です。

CLIでは PASS の時だけ終了コード 0 を返します。

JSONでも受け取れます。

~~~bash
nazeyatta check examples/safe-read.yaml --json
~~~

receiptには、何を評価したか後から確認できるよう、fingerprintや評価結果が含まれます。

---

## NazeYattaではないもの

NazeYattaは次のものではありません。

- 作業そのものを実行するAI Worker
- 実行engine
- 権限を発行するauthority
- certification system
- 完成した万能policy platform
- 自動remediation system
- Evidence Sourceが本当に正しい人・機械だったと証明する仕組み
- end-to-endの自動enforcement

現在のalphaは、**渡されたTask / Evidence構造とPolicy条件をdeterministicに評価する道具**です。

大きな影響を持つ操作では、Workerが回避できない別のenforcement pointを使ってください。

---

## なぜ「NazeYatta」なの？

**なぜやった？**

名前の由来は、AI Workerで時々起きるこの現象です。

~~~text
Human:
  「Xはやらないで」

AI:
  「了解しました。Xはしません」

AI:
  Xを実行
~~~

そこで、

> **実行する前に、何が確認済みでなければならなかったのか？**

を機械的に確認しよう、というのがNazeYattaの出発点です。

猫だらけの表示は意図的にふざけています。  
その下のresult semanticsはふざけていません。

---

## 詳しい設計はどこ？

**最初のExampleを動かすだけなら、ここから先の概念を理解する必要はありません。**

必要になった時だけ読めます。

- [Semantics](docs/SEMANTICS.md) — Policy != Evidence、Evidence != Authority、stateと境界
- [Evidence Model](docs/EVIDENCE_MODEL.md) — Evidence Record、provenance、freshness
- [Policy Model](docs/POLICY_MODEL.md) — applicabilityとpolicy effect
- [Threat Model](docs/THREAT_MODEL.md) — 何が壊れ得ると仮定しているか
- [Roadmap](docs/ROADMAP.md) — 実装済み・研究中・意図的に後回しにしたもの
- [Violation Debrief](docs/VIOLATION_DEBRIEF.md) — 違反後の振り返り構造
- [日本語 First Steps](docs/FIRST_STEPS.ja.md) — さらに手順寄りの導入

---

## 現在の状態

NazeYattaは **alpha research tool** です。

現在実装されているもの：

- deterministic YAML preflight evaluation
- generic baseline rules
- explicit evidence states
- conservative CLI exit code
- JSON / human-readable receipt
- task / policy fingerprint
- provenance-linked v0.2 input lane
- violation-debrief template
- tests / examples

まだend-to-endで自動化していないもの：

- Taskそのものの自動生成
- runtime observation adapter
- live execution enforcement
- provenance sourceの自動認証
- automatic remediation
- authority generation

最後に、この4本だけ覚えれば十分です。

~~~text
Unknown != Safe
Worker Self-Declaration != Evidence
Evidence != Authority
PASS != Execution Authority
~~~

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

もし「何が分からないのかすら分からない」状態になったら、それ自体が重要なdocumentation bugの証拠です。

そのままIssueへ：

> **「何を見ているのか分からない」**

と書いてもらって構いません。

## License

Apache-2.0. [LICENSE](LICENSE) を参照してください。
