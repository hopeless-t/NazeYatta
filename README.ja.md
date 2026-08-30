# NazeYatta

[English](README.md) | [日本語](README.ja.md)

> **AI Workerは「ルールを理解しました」と言った。**  
> **そのあと、なぜかそのルールで禁止したことをそのままやった。**
>
> 🙏 お願いです。指示通り働いてください。

**NazeYatta** は、AI WorkerやSoftware Agent向けの、実験的な**作業前危険予知（Preflight Hazard Analysis）＋違反振り返り（Violation Debrief）ツール**です。

作業前に今回重要なルールと危険を少数だけ前景化し、機械的に確認できる要求はEvidenceと照合し、違反が観測されたら「なぜやった？」から始まるStructured Debriefへつなげます。

## v0.1-alpha：最初に分かること

**現在実装済み：** deterministic YAML preflight evaluation、明示的なEvidence State model、保守的なCLI exit status、receipt fingerprint、structured violation-debrief template。

**意図的に未実装：** task YAMLの生成、provenance adapter、runtime observation、live traceとのviolation detection、automatic enforcement。特に、NazeYattaは与えられたYAMLを評価しますが、誰が`VERIFIED`をassertしてよいかをauthorizeするものではありません。このinput / evidence provenanceの境界は、現行evaluatorのruntime failureではなく、[research / design Issue #2](https://github.com/hopeless-t/NazeYatta/issues/2)として追跡しています。

これはalpha段階のresearch toolです。Certification・導入実績・authority granting systemを主張するものではありません。

```text
👈😽  「この危険を認識しました」
        !=
✅😺  「Evidence上、実際に遵守されました」
```

この二つが食い違ったら：

```text
🙅‍♂️😿 VIOLATION

🫵😿❓
NAZE YATTA?
（なぜやった？ / 何が起きた？）
```

## 30秒で見るNazeYatta

```text
$ nazeyatta check examples/publish-photo.yaml

NAZEYATTA
👈😽 PRE-FLIGHT KY

✋😾 BLOCK

NY-PUB-001  External publication requires verified provenance and permission
  hazard: PUBLICATION_WITH_UNKNOWN_RIGHTS
  evidence: publication_permission_verified = UNKNOWN
  effect: BLOCK

EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA
```

表示はふざけています。**Evidenceはふざけていません。**

## Quick Start

Python 3.11+ が必要です。

```bash
git clone https://github.com/hopeless-t/NazeYatta.git
cd NazeYatta
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e .

nazeyatta check examples/safe-read.yaml
nazeyatta check examples/publish-photo.yaml
nazeyatta check examples/destructive-delete.yaml
nazeyatta debrief-template NY-LIVE-001
```

CLIのexit statusは保守的です。`PASS`だけが`0`で、`CAUTION / REVIEW / EVIDENCE_REQUIRED / BLOCK`はnon-zeroです。

## どう動くの？

```mermaid
flowchart TB
    A[BEFORE]
    B["👈😽 KY<br/>(危険予知 / Kiken Yochi / Hazard Anticipation)"]
    C[EXECUTION]
    D["👀 OBSERVATION<br/>(runtime evidence)"]

    A --> B --> C --> D
    D --> E["✅😺 COMPLIED"]
    D --> F["🙅‍♂️😿 VIOLATED"]
    F --> G["🫵😿❓ NAZE YATTA?<br/>(なぜやった？ / 何が起きた？)"]
```

現在の`v0.1-alpha`が実装しているのは、主に**Mandatory Ruleの決定論的Preflight lane**と**Structured Debrief Template**です。Runtime Observation AdapterやWorker自身によるSituational KY生成は、現時点では自動のend-to-end enforcementとしては未実装です。

## KY / 危険予知とは

ここでいう**KYは「危険予知（Kiken Yochi）」**です。

日本の建設・製造・運輸などの現場で使われてきた、作業前に「今回の作業にはどんな危険があるか」を考える安全活動から着想を得ています。

重要なのは、どこかのManualにSafety Ruleが存在することだけではありません。

**実際に行動する直前に、今回重要な危険がWorkerの注意領域にあること。**

関連する「指差し呼称」も、対象を見る・指す・状態を確かめる・声に出す、という確認機構に意味があります。

対象を見ずに指だけ差して「ヨシ！」と言えば、Controlは単なる儀式になってしまいます。

> **The ritual is not the control.**  
> **儀式はControlではない。**

NazeYattaはKYから**着想を得ています**が、労働安全システム、Safety Certification、専門的な安全工学の代替ではありません。

## なぜ「NazeYatta」なの？

**Naze yatta?（なぜやった？）** は、そのまま英語にすれば：

> **Why did you do that?**

です。

この名前は、AI Workerを使っていて何度も遭遇した流れから来ています。

1. こちらがルールを説明する。
2. Workerが正しく復唱する。
3. Workerが「そのルールを守ります」と言う。
4. そして、そのルールをそのまま破る。

そこで自然に出てくるのが：

> **「お前さっき、それやらないって言ったよね？ 何が起きた？」**

です。

ただし、AIへ「なぜやった？」と聞いて返ってきた説明をRoot Causeとは扱いません。

```text
Worker Explanation != Root Cause
```

「なぜやった？」は**調査の開始**です。Workerの説明は`WORKER_SELF_REPORT`として保存し、Observed Behavior、Trace、Policy、Environment State、Reviewer Evidenceなどと比較します。

## なぜ猫なの？ 🐈

日本のTraditionalな伝統において、古来より猫は労働者を象徴する存在として広く認識されてきた――

**というEvidenceは一切ありません。捏造です。引用しないでください。**

本当の理由はもっと単純です。

猫の絵文字は状態を一目で区別しやすく、覚えやすく、そして「さっき注意すると言ったルールをWorkerが破った」という悲しい出来事を、ほんの少しだけ楽しくしてくれます。

```text
👈😽 PRE-FLIGHT KY
🔎😼 VERIFY
⚠️😼 CAUTION
📋😾 EVIDENCE REQUIRED
❓🐈 UNKNOWN
🔁👀 RECHECK
✋😾 BLOCK
🚫😾 DENY
🙅‍♂️😿 VIOLATION
🫵😿❓ DEBRIEF
✅😺 PASS
```

**猫はふざけています。Semanticsはふざけていません。**

絵文字はPresentation Conventionであって、EvidenceでもAuthorityでもありません。

## Core Invariants

```text
Rules Available != Rules Attended
Rule Acknowledgement != Rule Compliance
Worker Explanation != Root Cause
KY Completed != Authority to Execute
KY PASS != Authority Granted
Unknown != Safe
Worker Self-Declaration != Evidence
Artifact != Evidence
Familiar Task != Same State
Past Success != Current Safety
Missing Rule != Permission
Hazard Detected != Automatic Remediation Authority
Preflight Pass != Eternal Pass
```

`UNKNOWN`はすべてのWorkflowで自動的に`DENY`を意味するわけではありません。

重要なのは、**不足している観測を、Workerに都合のよい事実へ勝手に変換しないこと**です。UNKNOWNにどんなoperational effectを与えるかはPolicy側が決めます。

Generative Discoveryは注意領域を広げてもよい。Authoritative Requirementを狭めてはいけません。

## 現在の実装状況

### v0.1-alphaで実装済み

- 機械的に評価できる範囲でのdeterministic YAML rule evaluation
- Generic 10-rule baseline policy bundle
- Evidence Stateの明示的取扱い
- Task / Policy fingerprint付きPreflight Receipt
- `PASS`だけをexit `0`とする保守的CLI
- Naze-Yatta Debrief Template
- Examples / Tests

### Experimental Design：まだ自動end-to-end enforcementではないもの

- 通常3件・高リスク最大5件というKY attention model
- Worker自身によるSituational Hazard Discovery
- Runtime Observation Adapter
- Live Tool TraceとのViolation照合
- TOCTOU / Receipt Freshnessの自動Re-check
- Observed Violationに基づくQualification Update

詳しくは[`docs/ROADMAP.md`](docs/ROADMAP.md)を参照してください。

## Evidence・Authority・Completion

NazeYattaでは、Evidenceを少なくとも**「何を主張するのか」「何を観測したのか」「その観測はどこから来たのか」**に結び付け、必要に応じて時点・状態も扱います。詳しくは[`docs/EVIDENCE_MODEL.md`](docs/EVIDENCE_MODEL.md)。

`PASS`はAuthorityを製造しません。

```text
KY PASS != Authority Granted
```

そしてTask Contract上、CompletionでControlをHuman / Planner / Reviewerなどへ返すなら：

```text
🏁 Completion reported
        ↓
      ✋😾 STOP
```

**Helpful != Authorized.**

## Limitations

NazeYattaは、AI Workerが必ず指示通り動くことを保証しません。PreflightだけではComplianceを強制できません。

高ImpactなActionでは、Worker自身がbypassできないExternal Runtime Gateと組み合わせてください。

NazeYattaは以下ではありません。

- Safety Certification System
- 法令・規格適合保証
- 労働安全の代替
- Authority Granting System
- Autonomous Policy Generator
- Automatic Remediation Engine
- OPA/Cedar等のFull Policy Engineの代替

## Deep Docs

- [`docs/PHILOSOPHY.ja.md`](docs/PHILOSOPHY.ja.md) — なぜこれを作ったのか
- [`docs/SEMANTICS.md`](docs/SEMANTICS.md) — Stateと区別
- [`docs/POLICY_MODEL.md`](docs/POLICY_MODEL.md) — Policy / Applicability / Effect
- [`docs/EVIDENCE_MODEL.md`](docs/EVIDENCE_MODEL.md) — EvidenceとFreshness
- [`docs/VIOLATION_DEBRIEF.md`](docs/VIOLATION_DEBRIEF.md) — DebriefとFailure Taxonomy
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) — Threat Model
- [`docs/FIRST_STEPS.ja.md`](docs/FIRST_STEPS.ja.md) — OSSを初めて触る人向け

## OSSを初めて触る方へ

NazeYattaは、OSSやCLIに詳しい人だけのためのプロジェクトではありません。

AIを使い始めて「どうして指示した通りに動かないんだろう？」と思ったことがあるなら、この問題はすでにあなたにも関係しています。

READMEを読む、Issueを眺める、安全なExampleを実際に動かしてみる——どれもOSSへ触れる立派な第一歩です。

分からない言葉があったら、それもDocumentationの改善候補かもしれません。

初めての方は[`docs/FIRST_STEPS.ja.md`](docs/FIRST_STEPS.ja.md)へどうぞ。

## Contributing

[`CONTRIBUTING.md`](CONTRIBUTING.md)を参照してください。

## License

Apache-2.0. [`LICENSE`](LICENSE)を参照してください。
