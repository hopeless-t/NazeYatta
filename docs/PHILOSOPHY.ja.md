# NazeYatta Design Philosophy — 日本語

NazeYattaは大きな理論から始まったわけではありません。

**Workerから始まりました。**

私たちはかなり丁寧に指示を書きました。Scopeを狭め、作業ディレクトリを指定し、要求品質を決め、Evidenceを求め、Authorityの終点を書き、不明なら止まるように伝えました。

Workerは言います。

> 「理解しました。」

ときには、こちらのRuleを完璧に説明して返してくれることさえあります。

そして、そのあと違うことをします。

NazeYattaの中心問題は、このGapです。

```text
Rules Available != Rules Attended
Rule Acknowledgement != Rule Compliance
```

## Safetyは儀式ではない

意味のあるControlは、慣れによってRitualへ劣化します。

```text
危険を見る
  ↓
状態を確認する
  ↓
判断する
  ↓
行動を確認する
```

が、やがて：

```text
いつもの動作
  ↓
いつもの言葉
  ↓
そのまま作業
```

になる。

AI Agentでも同じです。

```text
Policyを読む
  ↓
"reviewed" と言う
  ↓
普通に違反する
```

**The ritual is not the control.**

## 慣れは現在のEvidenceではない

熟練は重要なCapabilityです。しかし慣れた作業ほどShortcutを生みます。

```text
Familiar Task != Same State
Past Success != Current Safety
```

Branchが違うかもしれない。Productionかもしれない。EvidenceがSTALEかもしれない。Observerが失敗しているかもしれない。Authorityが失効しているかもしれない。

熟練とは確認をしなくてよくなることではありません。**何を省略してはいけないかを知ることでもあります。**

## UNKNOWNはUNKNOWNのまま扱う

観測に失敗したからといって、次のActionに都合のよいFactへ変換してはいけません。

```text
Failed observation != proof of absence
Unknown liveness != authority to kill
Missing meaning != permission to guess
```

UNKNOWNだから常にDENYする、という意味ではありません。EffectはPolicyが決めます。重要なのは、不足した観測を勝手に潰さないことです。

## Authorityは別物

NazeYattaはActionを制約したり、Evidenceを要求したり、BLOCK / ESCALATEしたりできます。

しかしAuthorityを製造してはいけません。

```text
KY PASS != Authority Granted
Capability Gain != Authority Grant
Hazard Detected != Automatic Remediation Authority
```

問題を発見したことと、その周囲を勝手に修正してよいことは別です。

## なぜDebriefするのか

Workerは正しいRuleを認識したうえで違反することがあります。そのとき「なぜやった？」と聞くことでSelf-Reportを取れますが、それはRoot Causeそのものではありません。

```text
Worker Explanation != Root Cause
```

Observed Trace、Policy、Environment State、Enforcer Evidence、Reviewer Findingなどと照合します。

目的は罰ではありません。

**次のKYを良くすることです。**

```text
KY
 ↓
Execution
 ↓
Observation
 ↓
Violation
 ↓
Debrief
 ↓
Evidence
 ↓
Review
 ↓
Better next KY
```

## KYは少数にする

Design Targetは通常3件、高リスクでも最大5件程度です。

**If everything is critical, nothing is attended.**

Mandatory HazardはAuthoritative Policyから来て、Generative Laneが消してはいけません。HumanやLLMはSituational Candidate Hazardを追加できますが、注意領域を広げることはできても、Authoritative Requirementを狭めることはできません。

## 結局なぜ作ったのか

NazeYattaは本質的には、小さな願いです。

> お願いです。こちらも頑張って指示を書きました。あなたも理解したと言いました。どうか、その指示通りに働いてください。🙏

それでも失敗したら：

```text
🙅‍♂️😿
🫵😿❓
NAZE YATTA?
```
