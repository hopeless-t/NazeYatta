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

PyPIから `0.2.0a3` technical prerelease を入れ、同梱Exampleを取り出します。

~~~bash
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install "nazeyatta==0.2.0a3"

nazeyatta --version
nazeyatta example publish-photo > task.yaml
nazeyatta check task.yaml
~~~

`example` コマンドが行うのは、固定された同梱YAML Exampleを標準出力へコピーすることだけです。**Taskの評価や実行権限の付与は行いません。**

ソースコードを変更・開発する場合はRepositoryをcloneしてください。開発参加手順は [CONTRIBUTING.md](CONTRIBUTING.md) にあります。

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
nazeyatta example safe-read > safe-read.yaml
nazeyatta check safe-read.yaml
~~~

こちらは PASS（チェック通過）になります。

Task YAMLは、1つのboundedなUTF-8標準入力から渡すこともできます。

~~~bash
nazeyatta example safe-read | nazeyatta check -
~~~

ここで `-` は「Task YAMLを標準入力から読む」という意味です。権限や評価意味論を拡張するものではありません。また、1本の標準入力をTaskとPolicyの両方に曖昧に使わないため、`--policy -` は拒否されます。

既存core schemaの、packageに同梱されたexact copyも取り出せます。

~~~bash
nazeyatta schema task > task.schema.json
nazeyatta schema evidence > evidence.schema.json
nazeyatta schema receipt > receipt.schema.json
~~~

Schemaの取り出しはtransport / convenience用のsurfaceです。**実行権限を与えるものでも、新しいschema semanticsを追加するものでもありません。**

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
nazeyatta check safe-read.yaml --json
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

## NazeYattaの役割と限界

ここまでを短くまとめると、NazeYattaの役割は、

> **AIや自動化プログラムが作業を始める前に、渡された作業内容・確認情報・ルールを照らし合わせ、作業前チェックの結果を返すこと**

です。

一方で、NazeYatta自身は次のことを行いません。

- 実際の作業そのものを実行する
- 「この作業をしてよい」という実行権限を新しく作る
- ルールを決めた人・組織が、本当にその権限を持っているかまで自動で証明する
- BLOCKになった作業を、現在のalpha版だけで物理的に停止させる

つまり、

~~~text
NazeYattaの判定
      !=
実際の作業を強制的に止める仕組み
~~~

です。

重要な操作で本当にBLOCK時の実行を防ぎたい場合は、NazeYattaの判定を受け取る側の仕組みでも、

> **BLOCKなら次の処理を実行しない**

ように作る必要があります。

---

## なぜ「NazeYatta（なぜやった？）」なの？

開発のきっかけは、AIに作業を頼んだ時に何度も起きた、こんな失敗でした。

~~~text
人:
  「今日はこの範囲だけ作業してください」
  「ここから先は許可していません」

AI:
  「了解しました。許可された範囲だけ作業します」

その後……

AI:
  許可していない作業まで実行
~~~

終わった後に、

> **「なぜやった？」**

と聞くことになります。

そこで最初は、工事現場の朝礼やKY（危険予知）のように、**作業を始める前にAI自身にも、これから行う作業を言葉にさせる**ことから始まりました。

たとえば：

~~~text
本日の作業:
  確認用環境（Preview）へ反映します

自分が許可されていると理解している範囲:
  確認用環境（Preview）だけを変更します
  本番環境（Production）は変更しません

考えられる危険:
  反映先を取り違える
  秘密情報を外へ出してしまう

作業前の確認:
  反映先を確認してから実行します
  対象が曖昧なら作業を止めます
~~~

大事なのは、**AIがこう発言したから安全だ、と信用することではありません。**

AI自身の発言は、

> **「このAIは、今の作業・危険・許可範囲をどう理解していると主張しているか」**

を外から確認するための材料です。

その理解を、別に与えられたルールや許可範囲、確認情報と照らし合わせます。

~~~text
AI自身の作業前KY
  「Productionは触りません」
        +
実際に与えられた許可範囲
  「Previewのみ」
        +
プロジェクトのルール
        +
確認情報
        |
        v
     検査役（Validator）
        |
        v
   作業前の判定
~~~

逆に、

~~~text
AI:
  「Productionへの反映も許可されています」

実際の許可:
  「Previewのみ」
~~~

なら、**その食い違いを作業前に見つけ、BLOCK（停止）などの判定につなげる**、というのが原点の発想です。

現在のalpha版では、**AI自身に作業前KYを自動生成させるところから実行までを、一連の自律フローとして動かす機能**はまだ実装されていません。

一方で、その原点に必要な機械的な部品は一段進みました。現在のRepositoryには、Workerから受け取ったKY申告を型付きデータとして扱い、独立した基準と決定論的に比較するKY Gate、PASS後のFresh Handoff、境界状態の変化を見てRe-KYを判断するcontractがあります。さらに、固定されたローカルfixtureをFresh Processで読み取るread-only dogfoodまで実装されています。

つまり、

~~~text
AI自身がKYを自動生成して
そのまま本番作業まで自律実行
!=
現在のalpha

型付きKY申告
-> 決定論的な照合
-> bounded handoff
-> 境界観測 / Re-KY判定
-> 固定fixtureでのdogfood
=
現在実装されている実験的な経路
~~~

です。

ここで重要なのは：

~~~text
AI自身の発言
      !=
確認済みの証跡（Evidence）
~~~

ということです。

自己申告だけで「安全」「確認済み」にはしません。

### 現在のalpha版では

原点にある、

> **AI自身に作業前KYを自動生成させること**

は、まだ自動化されていません。

一方、外から渡されたKY申告を機械的に扱う経路は、次のところまで実装されています。

~~~text
型付きのWorker KY申告
        |
        v
独立したValidationBaselineとの
決定論的な照合
        |
        v
Fresh Handoff
        |
        v
Boundary Observation / Re-KY
        |
        v
固定fixtureを使った
Fresh Process read-only dogfood
~~~

さらに、ValidationBaselineがどのsource snapshotと結び付いていたかを記録するDerivation Record、dogfood用の小さなDerivationSpec、そのSpecをどのscope/lifecycleで採用したと記録するSpecAdoptionRecordもあります。

ただし、これらは**実験的なcontractとdogfood**です。

~~~text
Fixtureで動いた
!=
Productionで自動運用できる

RECORD_BOUND
!=
そのAuthorityが本物だと認証済み

PROVENANCE_BOUND
!=
意味的・規範的に正しいと証明済み
~~~

NazeYatta自身が本番のIAM・PKI・万能な権限管理システムになったわけではありません。

猫だらけの表示は意図的にふざけています。  
でも、確認できていないことを「たぶん大丈夫」にしない、という考え方は真面目です。

---

## もっと詳しく知りたい場合

最初の例を動かすだけなら、以下を全部理解する必要はありません。

必要になった時だけ読めるよう、詳しい設計を別の文書に分けています。

- [Semantics](docs/SEMANTICS.md)  
  **判定ルール・確認情報・実行権限は別物**、という基本的な考え方

- [Evidence Model](docs/EVIDENCE_MODEL.md)  
  **何を確認したのか、その情報はどこから来たのか、いつ確認したのか**を扱う考え方

- [Policy Model](docs/POLICY_MODEL.md)  
  **どの作業に、どのルールを適用し、どんな判定を返すか**の考え方

- [Threat Model](docs/THREAT_MODEL.md)  
  **どんな失敗や危険が起きる可能性を想定しているか**

- [Roadmap](docs/ROADMAP.md)  
  **今できること、これから研究・実装したいこと、あえて後回しにしていること**

- [Violation Debrief](docs/VIOLATION_DEBRIEF.md)  
  **実際にルール違反が起きた後、「なぜやった？」を記録して振り返るための形式**

- [日本語 First Steps](docs/FIRST_STEPS.ja.md)  
  **日本語でさらに手順を追って試したい場合の導入**

---

## 現在の状態

NazeYattaは、まだ**開発途中の実験版（alpha版）**です。

### 現在できること

- YAMLで書かれた作業内容を読み込む
- 同梱または指定されたルールと照らし合わせる
- VERIFIED（確認済み）や UNKNOWN（不明・未確認）などの状態を区別する
- PASS（チェック通過） / REVIEW（要確認） / BLOCK（停止）などの判定を返す
- 人が読む表示と、プログラムが扱いやすいJSON形式の両方でチェック記録を返す
- 作業内容やルール一式に識別用のfingerprint（ハッシュ値）を付ける
- 確認情報の出所を記録できる、実験的なv0.2形式を扱う
- ルール違反が起きた後の振り返り用テンプレートを出す
- 型付きのWorker KY申告を、独立したValidationBaselineと決定論的に照合する
- PASSした申告から、1回の作業境界用のFresh Handoffを作る
- 境界状態を比較して、CONTINUE / Re-KYを判定する
- 固定ローカルfixtureをFresh Processで読み取るread-only dogfoodを実行する
- BaselineDerivationRecord / bounded DerivationSpec / SpecAdoptionRecordを使った実験的なprovenance bindingを行う
- 自動テストで基本動作を検証する

### まだ自動化できていないこと

- AI自身に「今日の作業・危険・許可範囲」を作業前KYとして自動生成させる
- Production環境のsource/runtime adapterで、実際に作業中のAIやツールを継続観測する
- BLOCK判定になった操作を、NazeYatta単体で強制停止する
- 確認情報を出した人・システムが、本当にその情報を保証する権限を持つか自動認証する
- ルールやDerivationSpecを採用した人・組織が、本当にそのscopeの決定権限を持つか自動認証する
- DerivationSpecの内容が、その組織・domainにとって規範的に正しいと自動証明する
- 問題を見つけた後、自動で修復作業まで行う

最後に、現在の重要な境界です。

~~~text
Fixtureでのdogfood
  !=
Production Runtime

RECORD_BOUND
  !=
Authority認証済み

PROVENANCE_BOUND
  !=
意味的な正しさを検証済み

Unknown（不明・未確認）
  !=
Safe（安全）

AI自身の自己申告
  !=
確認済みの証跡（Evidence）

確認情報・証跡（Evidence）
  !=
実行権限

PASS（チェック通過）
  !=
実行権限の付与
~~~

---

## 開発に参加する

修正案や改善提案については [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

もしREADMEを読んで、

> **「何が分からないのかすら分からない」**

となった場合も、それ自体が重要なフィードバックです。

そのままIssueへ、

> **「何を見ているのか分からない」**

と書いてもらって構いません。

READMEの説明不足として扱います。

## ライセンス

Apache-2.0で公開しています。詳しくは [LICENSE](LICENSE) を参照してください。
