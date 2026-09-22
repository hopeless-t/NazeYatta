# NazeYatta（なぜやった？）

[English](README.md) | [日本語](README.ja.md)

**NazeYattaは、AIや自動化プログラムが何らかの作業を始める前に使う、機械が読める「作業前チェックリスト」です。コマンドラインから使います。**

基本の問いは一つです。

> **この作業を始めるために必要な確認は、本当にそろっているか？**

確認できていないことを、NazeYattaは「たぶん大丈夫」に変えません。

たとえば：

~~~text
やりたい作業:
  この写真を外部に公開する

渡された確認情報:
  公開先が正しいこと                         VERIFIED（確認済み）
  作業を行うAIやツールに必要な能力があること   VERIFIED（確認済み）
  写真の公開を許可できる人・組織からの許可     UNKNOWN（不明・未確認）

ルール:
  外部に公開するには、
  その公開を許可できる人・組織からの許可が
  確認済みであることが必要

NazeYatta:
  BLOCK（停止）
~~~

NazeYattaは、**渡された作業内容と確認情報を、決められたルールに照らし合わせます。**

写真そのものを公開するわけではありません。  
「公開してよい」という権限をNazeYatta自身が与えるわけでもありません。

**作業前のチェックを行い、その結果を記録して返す道具**です。

---

## 30秒で掴む全体像

~~~text
これから行う作業
      +
その作業について確認できていること
      |
      v
   NazeYatta
   作業前チェックリストと照合
      |
      v
PASS（チェック通過） / REVIEW（要確認） / BLOCK（停止）
+ 何を確認したかの記録
      |
      v
あなた（利用者）や、あらかじめ決められた承認の仕組みが
次に進めてよいかを判断する

実際の作業は、人・AI・自動化プログラムなどが行う
~~~

つまりNazeYattaは、

> **「確認できていないのに、たぶん大丈夫として進んでしまう」ことを防ぐための、機械が読める作業前チェックリスト**

です。

NazeYatta自身は、実際の作業を行ったり、実行権限を発行したりしません。

---

## このルールは誰が決めるの？

最初のExampleでは、**NazeYattaに同梱されている汎用のルール**を使います。

実際のProjectで使う場合は、NazeYattaが勝手にルールを決める想定ではありません。

そのProjectで「何をしてよいか・何を確認すべきか」を決める権限を持つ人や組織が、Project固有のルールを用意する想定です。

たとえば：

- Repositoryの運用ルールなら、その運用ルールを決める権限を持つ管理者・チーム
- 社内の公開ルールなら、その公開判断をする権限を持つ担当者や組織
- 顧客データの扱いなら、そのデータの利用条件を決める権限を持つ人や組織

NazeYattaの役割は、**渡されたルールと、今回の作業について確認できている情報を照らし合わせること**です。

現在のalpha版は、

> **「この人・組織が本当にそのルールを決める権限を持っているか」まで自動で証明するものではありません。**

つまり：

~~~text
ルールを決める権限
      != 
NazeYatta

NazeYatta
      =
渡されたルールを使って作業前チェックを行う
~~~

この「誰が正当なルール作成者なのか」を、より機械的に確認する仕組みは今後の設計課題です。

---
## これ、本当に必要？

場合によります。

小さなスクリプト1本と単純な if 文だけで十分なら、**その if 文を使った方がいい**です。

NazeYattaが役立つのは、複数のAIや自動化処理で、次のような確認方法を共通化したい時です。

- UNKNOWN（不明・未確認） / MISSING（必要な情報がない） / STALE（情報が古い） / VERIFIED（確認済み）を区別したい
- 同じ作業前チェックのルールを再利用したい
- コマンドの終了コードを一貫させたい
- 「何を確認したか」のチェック記録（receipt）を残したい
- **確認情報・証跡（Evidence）と、実際に作業してよい権限を混ぜたくない**

たとえば：

- GitHubなどへ変更を送る git push の前
- ファイルやサービスなどを削除・置換する前
- コンテンツを外部公開する前
- 外部のシステムへ書き込む前
- 作業に必要な能力（Capability）が、そのAIやツールにあるか確認したい時
- 操作する対象が本当に正しいか確認したい時

---
## まず1回だけ動かす

Python 3.11以上が必要です。

~~~bash
git clone https://github.com/hopeless-t/NazeYatta.git
cd NazeYatta
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e .

nazeyatta check examples/publish-photo.yaml
~~~

この例では、

> **「この写真を公開してよい許可」が、まだ確認できていない**

という状態を試します。

実際の入力ファイルでは、次のように書かれています。

~~~yaml
publication_permission_verified: UNKNOWN
~~~

日本語にすると、

~~~text
写真の公開許可:
  UNKNOWN（不明・未確認）
~~~

という意味です。

NazeYattaに同梱されている**基本ルール**では、

> **外部に公開する前に、その公開を許可できる人・組織からの許可が確認済みであること**

を求めています。

そのため、実行すると主要部分は次のように表示されます。
（実際の出力から説明に必要な部分を抜粋しています）

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

### この表示を日本語で読むと

- **PRE-FLIGHT KY**  
  「作業前の危険予知チェック」という意味です。  
  工事前のKY活動のように、作業を始める前に「確認漏れはないか」を見るイメージです。

- **BLOCK（停止）**  
  必要な確認が足りないため、**NazeYattaのチェックでは作業開始条件を満たしていない**という判定です。  
  NazeYatta自身が作業を物理的に止める、という意味ではありません。

- **hazard**  
  このルールが想定している危険や問題です。

- **evidence**  
  今回の判定に使った確認情報・証跡です。

- **effect**  
  そのルールによって返される判定結果です。

- **EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA**  
  「NazeYattaは実行権限を与えていません」という意味です。

平たく言えば、

> **この作業は、渡されたルールで必要とされた「公開許可の確認」が足りません。  
> そのためNazeYattaは「作業開始条件を満たしていない」と判定し、BLOCK（停止）を返します。**

ということです。

ファイルなどを書き換えず、**読み取りだけを行う例**もあります。

~~~bash
nazeyatta check examples/safe-read.yaml
~~~

こちらは PASS（チェック通過）になります。

ただし、

~~~text
PASS（チェック通過） ≠ 実行権限の付与
~~~

です。

ここでの「≠」は、**「同じ意味ではない」**という意味です。

PASSは、

> **「今回渡された情報とルールでは、この作業前チェックに停止・要確認となる理由がなかった」**

という結果です。

NazeYattaが「この作業を実行してよい」という権限そのものを与えたわけではありません。

---

## NazeYattaには何を渡すの？

最初は、小さなYAMLファイル1つで試せます。

YAMLは、設定内容を人にもプログラムにも読みやすく書くためのテキスト形式です。

例：

~~~yaml
task_id: MY-FIRST-READ                  # この作業につける名前

action:
  operation: read                       # 読み取りを行う
  side_effect: none                     # ファイルなどを書き換えない
  externality: internal                 # 外部公開・外部送信をしない

worker:
  required_capability: read_repository  # Repositoryを読む能力が必要

semantics:
  critical_meaning_complete: true       # 作業内容に重大な曖昧さがない

evidence:
  worker_capability_qualified: VERIFIED # 必要な能力があることを確認済み
~~~

英語のfield名はNazeYattaが機械的に読むための名前です。  
右側の日本語コメントは、それぞれ何を表しているかの説明です。

この例では説明のために VERIFIED（確認済み）を直接書いていますが、実際の運用では、

> **作業を行うAI自身が、都合よく自分を VERIFIED にする**

ことは想定していません。

人や、信頼できる確認元・自動チェックなどから得た情報を使う想定です。

この内容を my-first-task.yaml として保存したら：

~~~bash
nazeyatta check my-first-task.yaml
~~~

NazeYattaには**基本ルールが最初から同梱**されているので、最初の1回を動かすためにルール用の設定ファイル（policy file）まで自作する必要はありません。

大まかに言えば、

~~~text
何をしたいか
+
今わかっていること
+
適用されるルール
~~~

を照合して、判定結果と**チェック記録（receipt）**を返します。

---

## 何が返ってくるの？

現在の主な判定結果は：

- **PASS（チェック通過）**
- **CAUTION（注意）**
- **REVIEW（要確認）**
- **EVIDENCE_REQUIRED（確認情報・証跡が必要）**
- **BLOCK（停止）**

です。

コマンドライン（CLI）では、PASSの時だけ終了コード 0 を返します。

プログラムから扱いやすいJSON形式でも結果を受け取れます。

~~~bash
nazeyatta check examples/safe-read.yaml --json
~~~

チェック記録（receipt）には、判定結果だけでなく、

- 判定に引っかかったルールと、その理由
- 評価器のversion
- どの方式の確認情報を使ったか
- 作業内容を照合するためのfingerprint
- 使用したルール一式を照合するためのfingerprint

などが含まれます。

作業内容とルール一式に付く **fingerprint（識別用のハッシュ値）** は、

> **「前に評価した内容と、今回の内容が同じものか」を後から照合しやすくするための識別値**

です。

fingerprintだけで「誰がその内容を作ったか」や「その内容が正しいか」まで証明するものではありません。

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
