---
id: adk-session-memory-restaurant-agent
title: ADK セッションとメモリーバンクを使ったレストランエージェントの構築
summary: Google ADK と Vertex AI メモリーバンクを使用して、ユーザーの好み、アレルギー、人間関係をセッション間で記憶する、パーソナライズされたレストラン推薦エージェントの構築方法を学びます。
authors: Restaurant Agent Team
keywords: docType:Codelab, skill:Beginner, language:Python, category:Cloud, category:AiAndMachineLearning, product:VertexAI, product:GoogleCloud, product:ADK
award_behavior: AWARD_BEHAVIOR_ENABLE
layout: paginated
duration: 117

---

# ADK セッションとメモリーバンクを使ったレストランエージェントの構築

## はじめに
Duration: 0:05:00

### 問題: 忘れてしまうエージェント

毎回レストランのおすすめを聞くたびに「私はベジタリアンです」と伝えなければならないことを想像してみてください。メモリーがなければ、すべての会話は最初から始まります - エージェントはあなたが誰なのか、以前何を伝えたのか、何が重要なのかについてのコンテキストを持っていません。

![メモリーありとなしのエージェント比較](img/01-problem-comparison.png)
<!--
IMAGE PLACEHOLDER: 問題の比較
説明: 2つのシナリオを並べて比較。左側は混乱したロボットに「私はベジタリアンです」と繰り返し言うイライラしたユーザー。右側は「ベジタリアンだと覚えています！」と言うスマートなロボットと幸せなユーザー。
タイプ: イラスト
含めるべき主要要素:
- 2つのパネルを並べて配置
- 左: 「メモリーなし」ラベル、「また言うけど、私はベジタリアンです」と吹き出しのあるユーザー、「？」マークのロボット
- 右: 「メモリーあり」ラベル、笑顔のユーザー、「ベジタリアンだと知っています！」と言う電球マークのロボット
- 不満と満足の視覚的コントラスト
推奨スタイル: フレンドリー、カートゥーン風、カラフル
-->

| シナリオ | メモリーなし | メモリーあり |
|----------|-------------|-------------|
| 「夕食を見つけて」 | 一般的なレストランリスト | 「ベジタリアンになられたので、あなたに最適なオプションをご紹介します」 |
| 「金曜日のレストラン」 | 「何かの記念日ですか？」 | 「サムさんとの記念日ですか？ロマンチックなスポットを見つけました！」 |
| 「近くのタイ料理」 | 標準的な結果 | 「重度のピーナッツアレルギーをお持ちなので、ピーナッツを使用する店舗を除外しました」 |

### 構築するもの

このコードラボでは、以下の機能を持つ**レストランエージェント**を構築します：

1. **レストランを検索** - Google Maps API を使用してインテリジェントなフィルタリングを行う
2. **ユーザーの好みを記憶** - Vertex AI メモリーバンクを使用してセッション間で保持
3. **アレルギーからユーザーを保護** - 危険な食品について積極的に警告

![構築するもの](img/02-what-you-build.png)
<!--
IMAGE PLACEHOLDER: 構築するもの
説明: 完成したアプリケーションのモックアップ - ユーザーがレストランのおすすめを尋ね、エージェントが食事制限を考慮したパーソナライズされた提案で応答するチャットインターフェース。
タイプ: スクリーンショットモックアップ
含めるべき主要要素:
- 「ダウンタウンで夕食を見つけて」というユーザーメッセージのあるチャットインターフェース
- 「ベジタリアンでピーナッツアレルギーをお持ちなので...」と言及するエージェントの応答
- 評価付きのレストランカード
- 「新しいセッション」ボタンが表示
推奨スタイル: クリーンなUIモックアップ、モダンなデザイン
-->

### アーキテクチャ概要

![アーキテクチャ図](img/03-architecture.png)
<!--
IMAGE PLACEHOLDER: アーキテクチャ概要
説明: Web フロントエンドから RestaurantRunner を経由してエージェントへのフローを示すアーキテクチャ図。
タイプ: 技術図
含めるべき主要要素:
- 最上層: Web フロントエンド（FastAPI + JavaScript）とブラウザアイコン
- 中間層: VertexAiSessionService（短期）と VertexAiMemoryBankService（長期）を含む RestaurantRunner
- ADK Runner 層と「イベントループ & ステート」ラベル
- 最下層: root_agent とツール（GoogleSearchTool、Maps MCP Toolset、PreloadMemoryTool）
- 層間のデータフローを示す矢印
推奨スタイル: ボックスと矢印を使用したクリーンな技術図、Google Cloud カラーを使用
-->

システムには4つの主要な層があります：

1. **Web フロントエンド**: ユーザーがエージェントとチャットする FastAPI アプリ
2. **RestaurantRunner**: エージェントを Vertex AI サービスに接続
3. **ADK Runner**: イベントループと状態遷移を管理
4. **エージェント**: ルートエージェントが複数のツールを使用してタスクを実行

### 主要コンセプト

構築を始める前に、主要なコンポーネントを理解しましょう：

| コンポーネント | 役割 |
| :---- | :---- |
| **Agent Development Kit (ADK)** | ツールとコールバックを持つエージェントを構築するためのフレームワーク |
| **セッションサービス** | **短期メモリー** を保存 - 現在の会話コンテキスト |
| **メモリーバンク** | **長期メモリー** を保存 - 永続的に保存されるユーザーの事実 |
| **Agent Engine** | エージェントを大規模にホストする Google Cloud インフラストラクチャ |
| **PreloadMemoryTool** | 会話開始時に関連するメモリーを取得 |
| **MCP Toolset** | Google Maps API などの外部サービスへの接続 |

> aside positive
> **重要な洞察**: セッション = 短期（現在のチャット）。メモリーバンク = 長期（すべてのチャットにまたがる）。


## 環境のセットアップ
Duration: 0:10:00

### 前提条件

開始する前に、以下を確認してください：

- 課金が有効な Google Cloud プロジェクト
- Python 3.10 以上
- Google Cloud SDK がインストールおよび設定済み


> aside positive
> **Google Cloud 無料枠**: Google Cloud の無料枠クレジットを使用してこのコードラボを完了できます。詳細は [cloud.google.com/free](https://cloud.google.com/free) をご覧ください。

### Step 1: 環境を開く

Cloud Shell Editor またはローカル開発環境のいずれかを使用できます。

#### Cloud Shell Editor を使用する場合：

1. 👉以下の [リンク](https://ssh.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/GoogleCloudPlatform/gcp-getting-started-lab-jp&cloudshell_git_branch=restaurant-agent) をコピーしてブラウザーに貼り付けてリンクを開いてください。
こちらのリンクを開くだけで、本ラボの Github 上のコードが Clone されて Cloud Shell エディターも開いた状態になります。
```
https://ssh.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/GoogleCloudPlatform/gcp-getting-started-lab-jp&cloudshell_git_branch=restaurant-agent
```
> aside negative
> **Qwiklabs ユーザー**: Qwiklabs を利用する場合はブラウザのシークレットウィンドで開いてください。


2. 👉プロンプトが表示されたら Confirm をクリック
![リポジトリのクローンを確認](img/confirm_clone_repo.png)

3. 👉本日中に認証を求められた場合は、認証をクリックして続行
![cloudshell を認証](img/authorize-cloud-shell_1920.png)

4. 👉以下のようなエディター画面が開けたら正解です。
5. 
![editor](img/editor.png)

#### ローカル開発環境を使用する場合：

1. 👉ターミナルを開き、スターターリポジトリをクローン：

```bash
git clone https://github.com/GoogleCloudPlatform/gcp-getting-started-lab-jp
```

これにより、このコードラボに必要なすべてのスターターファイルがダウンロードされます。

2. 👉クローンしたディレクトリに移動：

```bash
cd gcp-getting-started-lab-jp
```

3. 👉restaurant-agent ブランチにチェックアウト：

```bash
$ git checkout restaurant-agent
```

4. 👉uv のインストール
    このプロジェクトでは Python パッケージマネージャーとして `uv` を使用します。
    以下のコマンドでインストール：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
> aside negative
> **Windows ユーザー**: PowerShell で `irm https://astral.sh/uv/install.ps1 | iex` を使用して uv をインストールしてください。

> aside positive
> **uv とは**: uv は高速な Python パッケージマネージャーです。pip の代替として使用できます。


### Step 2: 依存関係のインストール

👉 プロジェクトのルートディレクトリに移動して依存関係をインストールします。以下のコマンドをターミナルで実行してください。

Cloud Shell Editor の場合は以下のような黒い画面です。

![terminal](img/terminal.png)

> aside negative 
> **注意** ~/gcp-getting-started-lab-jp のディレクトリで以下を実行します。
> ディレクトリがあっているのか注意してください。
> 違うディレクトリーの場合は cd ~/gcp-getting-started-lab-jp を先に実行してください。

```bash
uv sync
source .venv/bin/activate
```

これにより以下がインストールされます：
- **google-adk**: Agent Development Kit
- **google-cloud-aiplatform**: Vertex AI SDK
- **fastapi**: Web フレームワーク
- **googlemaps**: Google Maps API クライアント

もしターミナルを閉じてしまった場合、Cloud Shell Editor の右上にあるターミナルのボタンを押すとターミナルを開けます。

![open_terminal](img/open_terminal.png)

### Step 3: 環境のセットアップ（API 有効化 & 環境変数）

このプロジェクトには、必要な API の有効化と環境変数の設定を自動で行うスクリプトが含まれています。

👉 まず以下のコマンドを実行してプロジェクト ID を設定します。YOUR_PROJECT_ID の代わりに Google Cloud Project ID を入れて実行してください。

```bash
gcloud config set project YOUR_PROJECT_ID
```

Qwiklab を利用する方は Qwiklab の手順画面の以下のパネルから Project ID をご利用いただけます。
![Qwiklab](img/qwiklab_project_id.png)

👉 ターミナルのディレクトリが gcp-getting-started-jp にあることを確認してセットアップスクリプトを実行してください。

> aside negative 
> **注意** ~/gcp-getting-started-lab-jp のディレクトリで以下を実行します。
> ディレクトリがあっているのか注意してください。
> 違うディレクトリーの場合は cd ~/gcp-getting-started-lab-jp を先に実行してください。

```bash
chmod +x setup_env.sh
./setup_env.sh
```

このスクリプトが自動的に以下を行います：

| 処理 | 説明 |
|------|------|
| **API 有効化** | Vertex AI、Cloud Run、Cloud Build、Maps API などを有効化 |
| **MCP サービス有効化** | Google Maps MCP ツールセット用のサービスを有効化 |
| **API キー作成** | Google Maps Platform 用の API キーを自動生成 |
| **`.env` ファイル作成** | 必要な環境変数を自動設定 |

スクリプト実行後、以下のような出力が表示されます：

```
Found Project ID: your-project-id
Enabling APIs..
Creating Google Maps Platform API Key...
Successfully created API Key.
Successfully updated /path/to/.env
```

> aside positive
> **チェックポイント**: 環境の準備が完了しました！API が有効化され、環境変数が自動設定されています。

> aside negative
> **手動設定が必要な場合**: スクリプトが失敗した場合は、`.env.example` を `.env` にコピーし、手動で値を入力してください。

### Step 4: スターターディレクトリに移動


ディレクトリ構造は以下のとおりです。
![directory](img/directory.png)

👉 スターターディレクトリに移動：

```bash
cd 01-starter
```

## シンプルなエージェントを作成
Duration: 0:10:00

早速レストラン検索エージェントを作成してみましょう！

> aside positive
> 困った場合は、`02-solution/` フォルダですべてのファイルの完全な実装を確認してください。


### Step 1: エージェントファイルを開く

👉 エディタで `01-starter/agent/agent.py` を開きます。

コードを追加する場所を示す TODO コメント付きのファイルが表示されます。

![LlmAgent 構造](img/15-llmagent-structure.png)
<!--
IMAGE PLACEHOLDER: LlmAgent 構造
説明: LlmAgent のコンポーネントを示す図: name、model、description、instruction、tools。
タイプ: 構造図
含めるべき主要要素:
- 「LlmAgent」とラベル付けされた中央のボックス
- 接続されたコンポーネント: name、model、description、instruction、tools、output_key、after_agent_callback
- 各コンポーネントの役割を示す簡潔なラベル
推奨スタイル: コンポーネント図
-->


### Step 2: MCP ツールセットを初期化

MCP（Model Context Protocol）は、エージェントが外部サービスに接続するための標準化された方法です。Google Maps MCP Toolset を使用すると、エージェントはレストラン検索や場所の詳細取得などの機能にアクセスできます。

👉 Google Maps MCP Toolset は `01-starter/agent/tool.py` で以下のように定義されています。

```python
"""
Google Maps MCP Toolset for the Restaurant Agent.
"""
MAPS_MCP_URL = "https://mapstools.googleapis.com/mcp"

def get_maps_mcp_toolset():
    dotenv.load_dotenv()
    maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY', 'no_api_found')

    tools = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=MAPS_MCP_URL,
            headers={
                "X-Goog-Api-Key": maps_api_key
            }
        )
    )
```

👉 `agent.py` で MCP ツールセットの初期化 TODO を見つけます：

```python
# TODO: Initialize the Maps MCP toolset
maps_toolset = None  # REPLACE THIS
```

👉 以下に置き換えます：

```python
maps_toolset = get_maps_mcp_toolset()
```

**これが行うこと:**
- `tool.py` で定義した関数を呼び出して MCP ツールセットを初期化
- エージェントが使用できるようにツールセットを準備

### Step 3: エージェントを定義する

👉 `agent.py` でこの行を見つけます：

```python
# TODO: Create root_agent with all tools
root_agent = None  # REPLACE THIS WITH YOUR AGENT DEFINITION
```

👉 `None` を以下のエージェント定義に置き換えます：

```python
root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-pro",
    description="Personal concierge that likes to help user",
    instruction="""
        You are a thoughtful restaurant assistant with perfect memory - like a personal concierge.
        PERSONALITY & APPROACH:
        - Be warm, personal, and emotionally intelligent
        - Make connections between past conversations and current requests
        - Proactively mention what you remember about the user.

        Do not start search restaurant unless the user asks for it.
        """,
    tools=[GoogleSearchTool(bypass_multi_tools_limit=True), maps_toolset],
    output_key="searched_restaurant_info"
)
```

エージェントは3つのツールを使用します：

1. **`GoogleSearchTool(bypass_multi_tools_limit=True)`**: 一般的な Web 検索
2. **`maps_toolset`**: Google Maps API を使用したレストラン検索


> aside positive
> **チェックポイント**: エージェントを作成しました！

### Step 4: エージェントの動作を確認する

ターミナルで以下を実行してください。

> aside negative 
> **注意** ~/gcp-getting-started-lab-jp/01-starter のディレクトリで以下を実行します。
> ディレクトリがあっているのか注意してください。
> 違うディレクトリーの場合は cd ~/gcp-getting-started-lab-jp/01-starter を先に実行してください。


```web
adk web
```

Editor の右上の Web Preview ボタンを押してください。

![web_preview](img/web_preview.png)

Change Port を押してください。

![web_preview](img/change_port.png)

8000を入力して Change and Preview を押してください。
![web_preview](img/change_preview.png)

以下のような　ADK Web (開発用のテストアプリ)が開けたら成功です。

![web_preview](img/adk_web.png)

左上の Select an agent をクリックして agent を選択すると作成したエージェントと対話できる画面が表示されます。

![web_preview](img/agent_select.png)

チャットで以下のようなプロンプトを入力してください。

Prompt 1
```bash
ラーメンが好きです。
```

Prompt 2
```bash
渋谷近くのおすすめのレストランを教えてください。
```


## エージェントメモリーの理解
Duration: 0:07:00

コーディングを始める前に、エージェントシステムにおける2種類のメモリーについて理解しましょう。

### Session: 短期記憶

**セッション**はワーキングメモリーのようなもので、現在の会話の間だけ持続します。

AI エージェントのコンテキストでは、短期メモリーとは1つのセッション内でエージェントが覚えていられるものです。

では、セッションとは何でしょうか？セッションはカスタマーサポート担当者との電話のようなものですが、電話するたびに別の担当者になると考えてください。その担当者はその会話中にあなたが伝えたことしか覚えていられません。電話を切ると、すべてのコンテキストが失われます。

短期メモリーは悪いことのように聞こえるかもしれませんが、AI エージェントにおいて重要な役割を果たします。例えば、Python チューターエージェントは、これまでに完了した問題数など、ユーザーのクイズの進捗を追跡する必要があるかもしれません。エージェントはおそらくその進捗を長期的に保存する必要はなく、最終スコアだけを保存すればよいかもしれません。

ADK エージェントとのすべてのユーザーインタラクションにはセッションが与えられ、そのセッションは ADK SessionService によって管理されます。各セッションには、セッション ID、ユーザー ID、イベント履歴（会話スレッド）、ステートなどの重要なフィールドが含まれています。

![cloudshell を認証](img/session-anatomy.png)

セッションステートとは何でしょうか？ユーザーとの「電話」中のエージェントのメモ帳のようなものと考えてください。各セッションのステートには、セッション全体を通じてエージェントによって更新される値を持つキーと値のペアのリストが含まれています。

デフォルトでは、ステートフィールドは現在のセッション内でのみ持続します。同じユーザーであっても、新しいセッションを開始すると値は失われます。しかし、ADK には `user:` や `app:` などのマジックステートキープレフィックスがあり、すべてのユーザーセッションにまたがって、またはすべてのユーザーとのすべてのセッションにまたがってステートキー値を永続化できます。これらのマジックプレフィックスは、`dark-mode=true` のような、セッション間で永続化したいシンプルなテキスト設定がある場合に便利です。

以上が ADK の短期メモリーの基本です。では、ADK はセッションとステートデータをどのように保存するのでしょうか？

デフォルトでは、ADK Web UI の SessionService はセッションデータをメモリに書き込みます。これは、ADK のランナーがクラッシュしたり、シャットダウンされたりすると、すべてのセッションデータが失われることを意味します。また、ADK エージェントの複数のインスタンスを持つスケールされた本番グレードのエージェントを実行している場合、ユーザーリクエストが常に同じインスタンスにヒットすることを保証できません。つまり、リクエスト1がインスタンス A に行き、リクエスト2がインスタンス B に行くと、インスタンス B はインスタンス A 内に保存されているインメモリセッションステートを持っていないことになります。

![cloudshell を認証](img/session-memory-architecture.png)

したがって、本番グレードのエージェントでは、エージェントのランタイム外にセッションデータを保存する必要があります。ADK はこれを行う2つの方法を提供しています。1つ目は DatabaseSessionService です：SQLLite、MySQL、PostgreSQL などの SQL データベースにセッションデータを保存します。これはセットアップが簡単で、データベースがあればよいだけです。その後、データベースの URI を ADK ランナーに渡すことができます：
```python
uv run adk web --session_service_uri="postgresql://$USERNAME:$PASSWORD@127.0.0.1:5432/pythontutor"
```
そこから、SQL データベースにアクセスしてセッションとステートテーブルを確認できます。
もう1つのオプションは VertexAISessionService で、Agent Engine にセッションデータを保存します。すでに ADK ランタイムとして Agent Engine を使用している場合、これは良いオプションです。

### Memory: 長期記憶

セッション内でのデータ保存方法について説明しました。しかし、同じユーザーとのセッション間で永続化したいデータがある場合はどうでしょうか？ここで ADK の長期メモリーが登場します。
長期メモリーを持つ ADK エージェントは、毎回同じカスタマーサービス担当者と話すようなものです。そして、その担当者は過去のすべての会話からのすべての重要な情報にアクセスできます。



![メモリーバンク図](img/07-memory-bank.png)
<!--
IMAGE PLACEHOLDER: メモリーバンク図
説明: セッション図と似ているが、メモリーバンクがセッション間で情報を保存および取得する様子を示す。
タイプ: 図
含めるべき主要要素:
- セッション1ボックス: ユーザーが「私はベジタリアンです」と言い、エージェントがメモリーバンク（クラウドアイコン）に保存
- 中央に「ユーザーはベジタリアン」が保存されたメモリーバンククラウド
- 「数日後...」と書かれた矢印
- セッション2ボックス: エージェントがメモリーバンクから取得し、チェックマーク付きのベジタリアンオプションを表示
- 幸せなユーザーとエージェント
推奨スタイル: クラウドストレージ要素を含むフローチャート
-->

```
セッション1:
  ユーザー: 「私はベジタリアンです」
  エージェント: 「了解しました！」
  [エージェントがメモリーバンクに保存 💾]

[数日後...]

セッション2:
  [エージェントがメモリーバンクから取得 📖]
  ユーザー: 「レストランを見つけて」
  エージェント: ✅ ベジタリアンオプションを表示
         「ベジタリアンなので...」
```


なぜプロンプトに入れないのか？
「ユーザーの履歴をプロンプトに貼り付ければいいのでは？」と思うかもしれません。

サイズ制限: コンテキストウィンドウは大きいですが、無限ではありません。5年分の履歴を入れることはできません。
コスト: 「こんにちは」のたびに100万トークンを処理するのは法外に高価です。
フォーカス: メモリーバンクはエージェントの検索エンジンとして機能します。関連する事実のみを取得します。


#### まとめ

| 機能 | セッションステート | メモリーバンク |
|---------|---------------|-------------|
| **永続性** | 単一セッションのみ | すべてのセッションにわたって永続 |
| **ストレージ** | インメモリ、一時的 | Vertex AI クラウドストレージ |
| **内容** | 生の会話 | 抽出された事実と洞察 |


> aside positive
> **メモリーバンクはエージェントをツールからコンパニオンに変える** - あなたを本当に知っていて、時間とともに改善するアシスタント。

## メモリーバンクの詳細
Duration: 0:10:00

では、メモリーバンクが内部でどのように動作するかを探ってみましょう。

### メモリーライフサイクル

メモリーバンクは**生成**と**取得**の継続的なサイクルを通じて動作します：

![メモリーライフサイクル](img/10-memory-lifecycle.png)
<!--
IMAGE PLACEHOLDER: メモリーライフサイクル図
説明: 生成 → 保存 → 取得 → 使用のサイクルを示す循環図。
タイプ: 循環フロー図
含めるべき主要要素:
- 4つのステージを持つ円
- ステージ1: 「会話」（チャットバブル）
- ステージ2: 「生成」（LLM が事実を抽出）
- ステージ3: 「保存」（メモリーバンクに保存）
- ステージ4: 「取得」（新しい会話のためにフェッチ）
- 各ステージを接続する矢印
- 中央ラベル: 「メモリーライフサイクル」
推奨スタイル: 循環プロセス図、クリーンでモダン
-->

1. **ユーザーが会話** → セッションが生のチャットをキャプチャ
2. **セッション終了** → LLM が重要な事実を抽出
3. **事実を保存** → メモリーバンクに保存
4. **新しいセッション開始** → 関連するメモリーを取得
5. **エージェントが応答** → パーソナライゼーションにメモリーを使用

### メモリー生成: 2Step プロセス

セッションが終了すると、メモリーバンクは2つの操作を実行します：

![抽出と統合](img/11-extraction-consolidation.png)
<!--
IMAGE PLACEHOLDER: 抽出 + 統合プロセス
説明: 会話からメモリーが抽出され、既存のメモリーと統合される2Step プロセスを示す図。
タイプ: プロセス図
含めるべき主要要素:
- Step 1ボックス: 「抽出」
  - 入力: 会話のトランスクリプト
  - 分析中の LLM アイコン
  - 出力: 抽出された事実
- Step 2への矢印
- Step 2ボックス: 「統合」
  - 表示される既存のメモリー
  - 比較される新しい事実
  - 3つの可能なアクション: 作成、更新、削除
- 最終出力: 更新されたメモリーストア
推奨スタイル: 水平プロセスフロー
-->

**Step 1: 抽出**

LLM が会話を読み、意味のある事実を抽出します：

```
会話: 「以前はステーキが大好きでしたが、今はベジタリアンです。」

抽出された事実: 「ユーザーは現在ベジタリアン（以前はステーキを食べていた）」
```

**Step 2: 統合**

システムは既存のメモリーをチェックし、何をするか決定します：

| アクション | 発生するとき | 例 |
|--------|-----------------|---------|
| **作成** | 新しい情報 | ユーザーが初めて名前を言及 |
| **更新** | 情報が変更 | ユーザーの食べ物の好みが変更 |
| **削除** | 矛盾する情報 | 古い好みがもはや有効でない |

> aside positive
> **スマート統合**: 「赤が好き」と言って後で「青が好き」と言うと、メモリーバンクは重複を作成せずにメモリーを自動的に更新します。

### デフォルトのメモリートピック

メモリーバンクはデフォルトで4種類の情報を抽出します：

<!--
IMAGE PLACEHOLDER: デフォルトのメモリートピック
説明: アイコンと例を含む4つのデフォルトメモリートピックを示す4つのカードまたはボックス。
タイプ: カードレイアウト
含めるべき主要要素:
- カード1: USER_PERSONAL_INFO - 人物アイコン - 「名前: アレックス、パートナー: サム」
- カード2: USER_PREFERENCES - ハートアイコン - 「ベジタリアン料理が好き」
- カード3: KEY_CONVERSATION_DETAILS - マイルストーンアイコン - 「シェマリーで予約」
- カード4: EXPLICIT_INSTRUCTIONS - スピーチアイコン - 「常にピーナッツアレルギーについてリマインド」
推奨スタイル: アイコン付きカードベースレイアウト
-->

| トピック | キャプチャするもの | 例 |
|-------|------------------|---------|
| **USER_PERSONAL_INFO** | 名前、関係、日付 | 「ユーザーの名前はアレックス、パートナーはサム」 |
| **USER_PREFERENCES** | 好き嫌い、スタイル | 「ユーザーはベジタリアン料理を好む」 |
| **KEY_CONVERSATION_DETAILS** | 重要なマイルストーン | 「ユーザーが予約をした」 |
| **EXPLICIT_INSTRUCTIONS** | 覚える/忘れるリクエスト | 「常にピーナッツアレルギーについてリマインド」 |

> aside negative
> **重要**: 一般的な雑談は保存されません。これらのトピックに一致する意味のある事実のみが永続化されます。

### メモリー取得: 類似性検索

新しい会話が始まると、エージェントは関連するメモリーを必要とします。仕組みは以下の通りです：

![類似性検索](img/13-similarity-search.png)
<!--
IMAGE PLACEHOLDER: 類似性検索の視覚化
説明: ユーザークエリが埋め込みに変換され、保存されたメモリーと照合される仕組みを示す図。
タイプ: 技術図
含めるべき主要要素:
- ユーザークエリ: 「タイ料理店を見つけて」
- 「埋め込みに変換」への矢印（ベクトルアイコン）
- 複数のメモリーベクトルを持つメモリーバンク
- 距離スコア付きでクエリとメモリーを接続する線
- ハイライトされたトップ3の結果
- 関連性でソートされた結果リスト
推奨スタイル: 技術的だがアクセスしやすい図
-->

1. **クエリを変換** → ユーザーのメッセージがベクトル埋め込みになる
2. **メモリーを検索** → クエリに類似したメモリーを検索
3. **アイデンティティフィルタリング** → このユーザーのメモリーのみを検索
4. **距離でランク付け** → ユークリッド距離でソート（近い = より関連性が高い）
5. **上位k件を返す** → デフォルト: 最も関連性の高い3つのメモリー

**例:**

```
ユーザークエリ: 「タイ料理店を見つけて」

取得されたメモリー（関連性順）:
1. 「ユーザーには重度のピーナッツアレルギーがある」（非常に関連 - タイ料理はピーナッツを使う！）
2. 「ユーザーはベジタリアンを好む」（関連 - 食事制限）
3. 「ユーザーのパートナーはサム」（あまり関連性がない）
```

### ADK の2つのメモリーツール

ADK はメモリーを読み込む2つの方法を提供しています：

| ツール | 読み込みタイミング | 最適な用途 |
|------|---------------|----------|
| **PreloadMemoryTool** | すべてのターンの開始時 | 常にコンテキストを持つ（これを使用） |
| **LoadMemoryTool** | エージェントが決定したとき | オンデマンド読み込み |

> aside positive
> **PreloadMemoryTool を使用します** - エージェントが応答する前にアレルギーや好みについて常に知っておいてほしいからです。

### データ分離

メモリーバンクは各ユーザーのデータを完全に分離して保持します：

- **ユーザーA** は **ユーザーB** のメモリーを見ることは**絶対にできません**
- ユーザーアイデンティティによる自動フィルタリング
- マルチテナントアプリケーションに安全

## エージェントに覚えてもらおう！
Duration: 0:18:00

`agent.py` では、2つの主要なメモリーコンポーネントを追加します:

1. **PreloadMemoryTool**: エージェントがメモリーバンクを検索できるツールです。ユーザーが「いつものレストランを予約して」のような曖昧なことを尋ねると、エージェントはこのツールを使用して「お気に入りのレストラン」をメモリーから取得できます。

2. **save_session_to_memory**: 会話終了時に実行されるコールバック関数です。なぜ非同期？ メモリーの保存には時間がかかります（チャットの要約、事実の抽出）。ユーザーを待たせないために `after_agent_callback` を使用してバックグラウンドで実行します。

#### 連携の仕組み

私たちのレストランエージェントでは：

1. **セッションサービス**が現在の会話を追跡
2. **メモリーバンク**が重要な事実（名前、アレルギー、好み）を保存
3. **PreloadMemoryTool**が会話開始時に関連するメモリーを読み込み
4. **コールバック**が会話終了時に新しい事実をメモリーバンクに保存

![連携の仕組み](img/09-working-together.png)
<!--
IMAGE PLACEHOLDER: セッション + メモリーの連携
説明: セッションとメモリーバンクが連携して動作する会話のフローを示す図。
タイプ: フロー図
含めるべき主要要素:
- 新しい会話の開始
- PreloadMemoryTool がメモリーバンクからフェッチ
- 会話が発生（セッションステートが保存）
- 会話の終了
- コールバックが事実を抽出してメモリーバンクに保存
- サイクルの繰り返し
推奨スタイル: 循環フロー図
-->



### Step 1: Agent Engine の作成
Duration: 0:08:00

Vertex AI Memory サービスを使用する前に、Google Cloud で Agent Engine インスタンスを作成する必要があります。

👉 デプロイメントスクリプトを実行：

> aside negative 
> **注意** ~/gcp-getting-started-lab-jp/01-starter のディレクトリで以下を実行します。
> ディレクトリがあっているのか注意してください。
> 違うディレクトリーの場合は cd ~/gcp-getting-started-lab-jp/01-starter を先に実行してください。



```bash
python create_agent_engine.py
```

![デプロイメント出力](img/agent_engine.png)

👉 出力から `AGENT_ENGINE_ID` をコピーして `.env` ファイルに追加：

> aside negative .env が表示されない場合は view-> Toggle hidden files　を押してください。

```bash
AGENT_ENGINE_ID="your-agent-engine-id-here"
```

### Step 2: コールバック関数を完成する

各会話の後に実行される**コールバック関数**を作成しましょう。

![コールバックフロー](img/17-callback-flow.png)
<!--
IMAGE PLACEHOLDER: コールバックフロー図
説明: 会話ライフサイクルで after_agent_callback がいつ実行されるかを示す図。
タイプ: フロー図
含めるべき主要要素:
- ユーザーがメッセージを送信
- エージェントが処理して応答
- 会話の終了
- after_agent_callback がトリガー
- メモリーバンクへの矢印「事実を保存」
- 注: 「自動的に実行！」
推奨スタイル: タイムラインまたはフロー図
-->

ADK では、コールバックは特定のポイントで実行される関数です：
- **`before_agent_callback`**: エージェントが処理する**前**に実行
- **`after_agent_callback`**: エージェントが終了した**後**に実行

重要な事実をメモリーバンクに保存するために `after_agent_callback` を使用します。


### Step 3: Agent を完成する

👉 `agent.py` で `save_session_to_memory` 関数を見つけます：

```python
async def save_session_to_memory(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Save completed sessions to memory bank.

    This callback is triggered after the agent finishes processing a request.
    It extracts important facts from the conversation and stores them in
    the Memory Bank for future sessions.
    """
    # TODO: Implement the memory saving logic
    # Access the invocation context and call add_session_to_memory
    #
    # Example:
    # await callback_context._invocation_context.memory_service.add_session_to_memory(
    #     callback_context._invocation_context.session)
    # REPLACE_MEMORY_CALLBACK
    pass
```

👉 `pass` 文を以下に置き換えます：

```python
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session)
```

**これが行うこと:**
- **`_invocation_context`**: セッションとメモリーサービスを含むコンテキスト
- **`memory_service`**: VertexAiMemoryBankService インスタンス
- **`add_session_to_memory(session)`**: セッションから事実を抽出して保存

完成した関数は以下のようになるはずです：

```python
async def save_session_to_memory(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Save completed sessions to memory bank.

    This callback is triggered after the agent finishes processing a request.
    It extracts important facts from the conversation and stores them in
    the Memory Bank for future sessions.
    """
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session)
```

> aside positive
> **なぜ非同期？** `add_session_to_memory` 呼び出しは LLM をトリガーして事実を抽出します。これには時間がかかるため、ユーザーをブロックしないように非同期で実行します。

> aside negative
> **重要**: ADK では、メモリー生成は自動ではありません。`add_session_to_memory` を明示的に呼び出す必要があります。そのためこのコールバックを使用します。


次に、メインエージェントのtoolsに以下のように`PreloadMemoryTool()`を追加します。
そして`after_agent_callback=save_session_to_memory`も追加します。


```python
root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-pro",
    description="Personal concierge that likes to help user",
    instruction="""
        You are a thoughtful restaurant assistant with perfect memory - like a personal concierge.
        PERSONALITY & APPROACH:
        - Be warm, personal, and emotionally intelligent
        - Make connections between past conversations and current requests
        - Proactively mention what you remember about the user.

        Do not start search restaurant unless the user asks for it.
        """,
    tools=[PreloadMemoryTool(), GoogleSearchTool(bypass_multi_tools_limit=True), maps_toolset],
    output_key="searched_restaurant_info",
    after_agent_callback=save_session_to_memory,
)
```
Adk web を Ctrl + C 押して停止して、以下のコマンドで再起動します。
agent_engine_id は先ほど取得した Agent Engine の ID です。

> aside negative 
> **注意** ~/gcp-getting-started-lab-jp/01-starter のディレクトリで以下を実行します。
> ディレクトリがあっているのか注意してください。
> 違うディレクトリーの場合は cd ~/gcp-getting-started-lab-jp/01-starter を先に実行してください。



```python
adk web --memory_service_uri="agentengine://agent_engine_id"
```

チャットで以下のようなプロンプトを入力してください。

Prompt 1
```bash
ラーメンが好きです。
```

Prompt 2
```bash
渋谷近くのおすすめのレストランを教えてください。
```

セッションを切り替えて以下のプロンプトを入力してください。


Prompt 1
```bash
私の好きな食べ物を教えてください。
```


## Vertex AI サービスを使用したランナーの構築
Duration: 0:12:00

ランナーはエージェントを Vertex AI のマネージドサービスに接続するものです。すべてを動かす「エンジン」です。

![ランナーアーキテクチャ](img/22-runner-architecture.png)
<!--
IMAGE PLACEHOLDER: ランナーアーキテクチャ
説明: ランナーがエージェント、セッションサービス、メモリーサービスを接続する方法を示す図。
タイプ: アーキテクチャ図
含めるべき主要要素:
- 中央の RestaurantRunner クラス
- 3つの接続:
  - エージェントへ（あなたの root_agent）
  - VertexAiSessionService へ（短期メモリー）
  - VertexAiMemoryBankService へ（長期メモリー）
- それらを結びつける Runner（ADK）ボックス
- データフローを示す矢印
推奨スタイル: コンポーネントアーキテクチャ図
-->

ランナーは以下を結びつけます：
- **あなたのエージェント**: 作成した root_agent
- **セッションサービス**: 短期会話メモリーを管理
- **メモリーサービス**: 長期事実ストレージを管理
- **ADK ランナー**: イベントループを実行

### Step 1: ランナーファイルを開く

👉 エディタで `01-starter/agent/runner.py` を開きます。

TODO プレースホルダー付きのクラスが表示されます：

```python
class RestaurantRunner:
    """Runner for the Restaurant Agent."""

    def __init__(self, agent, user_id, session_id=None):
        self.agent = agent
        self.user_id = user_id
        self._session_id = session_id

        # TODO: Initialize VertexAiSessionService
        self.session_service = None  # REPLACE THIS

        # TODO: Initialize VertexAiMemoryBankService
        self.memory_service = None  # REPLACE THIS

        # TODO: Create the ADK Runner
        self.runner = None  # REPLACE THIS
```

### Step 2: VertexAiSessionService を初期化

👉 最初の TODO を見つけて `self.session_service = None  # REPLACE THIS` を以下に置き換え：

```python
        self.session_service = VertexAiSessionService(
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION,
            agent_engine_id=AGENT_ENGINE_ID,
        )
```

**各パラメータの役割:**

| パラメータ | 目的 |
|-----------|---------|
| `project` | Google Cloud プロジェクト ID |
| `location` | Agent Engine がデプロイされているリージョン |
| `agent_engine_id` | Agent Engine インスタンスの ID |


### Step 3: VertexAiMemoryBankServiceを初期化

👉 2番目の TODO を見つけて `self.memory_service = None  # REPLACE THIS` を以下に置き換え：

```python
        self.memory_service = VertexAiMemoryBankService(
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION,
            agent_engine_id=AGENT_ENGINE_ID,
        )
```

**これが行うこと:**
- セッションサービスと同じ Agent Engine に接続
- 長期メモリーストレージへのアクセスを提供
- `add_session_to_memory` とメモリー取得を有効化

### Step 4: ランナーを作成

👉 3番目の TODO を見つけて `self.runner = None  # REPLACE THIS` を以下に置き換え：

```python
        self.runner = Runner(
            app_name=self.agent.name,
            agent=self.agent,
            session_service=self.session_service,
            memory_service=self.memory_service,
        )
```

**各パラメータの役割:**

| パラメータ | 目的 |
|-----------|---------|
| `app_name` | このアプリケーションの識別子 |
| `agent` | 実行するルートエージェント |
| `session_service` | セッション管理 |
| `memory_service` | メモリー管理 |


> aside positive
> **ランナー**はエージェントの心臓部です。以下を行います：
> - エージェントをユーザーとセッションにバインド
> - イベントループを実行
> - 状態遷移を管理
> - メモリー操作を調整

### チェックポイント: 完成した __init__ メソッド

完成した `__init__` メソッドは以下のようになるはずです：

```python
def __init__(self, agent, user_id, session_id=None):
    self.agent = agent
    self.user_id = user_id
    self._session_id = session_id

    self.session_service = VertexAiSessionService(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        agent_engine_id=AGENT_ENGINE_ID,
    )

    self.memory_service = VertexAiMemoryBankService(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        agent_engine_id=AGENT_ENGINE_ID,
    )

    self.runner = Runner(
        app_name=self.agent.name,
        agent=self.agent,
        session_service=self.session_service,
        memory_service=self.memory_service,
    )
```

> aside positive
> **チェックポイント**: ランナーが設定されました！エージェントが Vertex AI のセッションおよびメモリーサービスに接続されています。



## Web アプリとの統合
Duration: 0:08:00

では、FastAPI Web アプリケーションをエージェントに接続しましょう。

### Step 1: Web アプリファイルを開く

👉 エディタで `01-starter/web/app.py` を開きます。

### Step 2: ask() 関数を見つける

👉 ユーザーメッセージを処理する `ask()` 関数を見つけます：

```python
@app.post("/ask")
async def ask(request: Request, body: MessageRequest):
    """Handle user messages and get agent responses."""
    # ... バリデーションコード ...

    try:
        # TODO: Create RestaurantRunner instance
        runner = None  # REPLACE THIS

        # TODO: Call the agent and get response
        agent_response_html = "TODO: Implement agent call"  # REPLACE THIS
```

### Step 3: ランナーインスタンスを作成

👉 `runner = None  # REPLACE THIS` を以下に置き換え：

```python
        runner = RestaurantRunner(
            agent=root_agent,
            user_id=username,
            session_id=agent_session_id
        )
```

**各パラメータの役割:**

| パラメータ | 目的 |
|-----------|---------|
| `agent=root_agent` | メモリー付きオーケストレーターエージェント |
| `user_id=username` | メモリースコーピング用の一意識別子 |
| `session_id` | 既存のセッション ID（新規セッションの場合は None）|

### Step 4: エージェントを呼び出す

👉 `agent_response_html = "TODO: Implement agent call"  # REPLACE THIS` を以下に置き換え：

```python
        agent_response_md = await runner.call_agent(user_message)
        agent_response_html = markdown.markdown(agent_response_md or "No response from agent.")
```

**これが行うこと:**
- **`await`**: FastAPI の非同期ハンドラ内で非同期エージェントを実行
- **`runner.call_agent()`**: メッセージをエージェントに送信し、応答を取得
- **`markdown.markdown()`**: 表示用にマークダウン応答を HTML に変換

`ask()` 関数の主要部分は以下のようになるはずです：

```python
@app.post("/ask")
async def ask(request: Request, body: MessageRequest):
    """Handle user messages and get agent responses."""
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_message = body.message
    if not user_message:
        raise HTTPException(status_code=400, detail="No message provided")

    current_session_id = request.session.get("current_chat_session")
    chat_session = user_sessions.get(username, {}).get(current_session_id)

    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    agent_session_id = chat_session.get("agent_session_id")

    try:
        runner = RestaurantRunner(
            agent=root_agent,
            user_id=username,
            session_id=agent_session_id
        )

        agent_response_md = await runner.call_agent(user_message)
        agent_response_html = markdown.markdown(agent_response_md or "No response from agent.")

        # ... 関数の残り（メッセージの保存、セッション ID の更新）...
```

![Web 統合完了](img/28-web-integration.png)
<!--
IMAGE PLACEHOLDER: Web 統合完了
説明: FastAPI アプリが RestaurantRunner に接続する方法を示す図。
タイプ: フロー図
含めるべき主要要素:
- ユーザー付きブラウザ
- POST /ask を受け取る FastAPI アプリ
- 作成される RestaurantRunner
- 呼び出されるエージェント
- ブラウザに戻る応答フロー
- フローを示す矢印
推奨スタイル: リクエスト-レスポンスフロー図
-->

> aside positive
> **チェックポイント**: Web UI がエージェントに接続されました！ユーザーがメッセージを送信すると、メモリー対応エージェントを通過します。


## アプリケーションの実行とテスト
Duration: 0:08:00

すべてをテストしましょう！

### Step 1: サーバーを起動

👉 Web サーバーを実行：

> aside negative 
> **注意** ~/gcp-getting-started-lab-jp/01-starter のディレクトリで以下を実行します。
> ディレクトリがあっているのか注意してください。
> 違うディレクトリーの場合は cd ~/gcp-getting-started-lab-jp/01-starter を先に実行してください。



```bash
python main.py
```

以下のような出力が表示されるはずです：

```
INFO:     Will watch for changes in these directories: ['/path/to/01-starter']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Step 2: アプリケーションの動作を確認する


ターミナルで以下を実行してください
```web
adk web
```

Editor の右上の Web Preview ボタンを押してください。

![web_preview](img/web_preview.png)

Change Port を押してください。

![web_preview](img/change_port.png)

8080を入力して Change and Preview を押してください。
以下のようにチャットアプリのログイン画面が表示されます。

![ログインページ](img/user_name.png)
<!--
IMAGE PLACEHOLDER: ログインページ
説明: アプリケーションのログインページのスクリーンショット。
タイプ: スクリーンショット
含めるべき主要要素:
- シンプルなログインフォーム
- ユーザー名入力フィールド
- 「チャットを開始」ボタン
- クリーンでモダンなデザイン
推奨スタイル: 実際のスクリーンショット
-->

### Step 3: ユーザー名を入力

👉 ユーザー名（例: 「田中」）を入力し、「チャットを開始」をクリック。

### Step 4: メモリー永続性をテスト

メモリーがセッション間で機能するかテストするために3つのデモシナリオを実行します。

---

#### デモ1: 好みの進化


**セッション1:**
```
ステーキが大好きです！渋谷の近くに住んでいます。
```
*(応答を待ってから「新しいセッション」をクリック)*

![デモ1](img/demo_1.png)
<!--
IMAGE PLACEHOLDER: デモ1 - 好みの進化
説明: 好みの進化テストを示す3パネルスクリーンショット。
タイプ: スクリーンショットシリーズ
含めるべき主要要素:
- パネル1: セッション1 - ユーザーが「ステーキハウスが大好き」と言う
- パネル2: セッション2 - ユーザーが「今はベジタリアンです」と言う
- パネル3: セッション3 - エージェントがベジタリアンオプションを推奨
推奨スタイル: アノテーション付きスクリーンショットシリーズ
-->

**セッション2:**
```
健康のためにベジタリアンになることにしました。
```
*(応答を待ってから「新しいセッション」をクリック)*

**セッション3:**
```
私の住んでいるエリア近くで夕食のおすすめを教えて
```

**期待される結果:** エージェントは以下を行うべきです：
- ベジタリアンに切り替えたことを覚えている
- keyword="vegetarian" で検索
- 「ベジタリアンに切り替えられたので、素晴らしいオプションをご紹介...」のようなことを言う

---

#### デモ2: アレルギーガーディアン

<!--
IMAGE PLACEHOLDER: デモ2 - アレルギーガーディアン
説明: アレルギー警告テストを示す2パネルスクリーンショット。
タイプ: スクリーンショットシリーズ
含めるべき主要要素:
- パネル1: ユーザーがピーナッツアレルギーを言及
- パネル2: ユーザーがタイ料理を尋ね、エージェントがピーナッツについて警告
推奨スタイル: 警告がハイライトされたスクリーンショットシリーズ
-->

**セッション1:**
```
重度のピーナッツアレルギーがあります。
```
*(応答を待ってから「新しいセッション」をクリック)*

**セッション2:**
```
近くのタイ料理店を見つけて。
```

**期待される結果:** エージェントは結果を表示する前にタイ料理のピーナッツリスクについて積極的に警告すべきです。

---

#### デモ3: 記念日プランナー

<!--
IMAGE PLACEHOLDER: デモ3 - 記念日プランナー
説明: 記念日メモリーテストを示す2パネルスクリーンショット。
タイプ: スクリーンショットシリーズ
含めるべき主要要素:
- パネル1: ユーザーが記念日と最初のデートの場所を言及
- パネル2: エージェントが記念日にルーフトップレストランを提案
推奨スタイル: パーソナルタッチがハイライトされたスクリーンショットシリーズ
-->

**セッション1:**
```
来週の金曜日にパートナーのサムと5周年記念日を祝います。最初のデートはルーフトップレストランでした。
```
*(応答を待ってから「新しいセッション」をクリック)*

**セッション2:**
```
金曜日のレストランのおすすめが必要です。
```

**期待される結果:** エージェントはルーフトップレストランを提案し、記念日について言及すべきです。

---

> aside positive
> **ヒント**: メモリー生成には少し時間がかかります。各セッション終了後、メモリーが保存されていることを確認するため、次のセッションを開始する前に数秒待ってください。

> aside negative
> **トラブルシューティング**: メモリーが機能していないようであれば、サーバーログで `memories:generate` メッセージを確認してください。表示されない場合は、Agent Engine ID が正しいことを確認してください。


## ログでメモリーを確認
Duration: 0:05:00

メモリー操作が正しく行われていることを確認しましょう。

👉 [Google Cloud Console](https://console.cloud.google.com/vertex-ai/agents/agent-engines) に移動

👉 プロジェクトを選択し、Agent Engine をクリック
![Cloud Console メモリー](img/agent_engine_list.png)

👉 **Memories** タブをクリック

![Cloud Console メモリー](img/34-cloud-console-memories.png)
<!--
IMAGE PLACEHOLDER: Cloud Console メモリータブ
説明: Agent Engine の Memories タブを示す Google Cloud Console のスクリーンショット。
タイプ: スクリーンショット
含めるべき主要要素:
- Google Cloud Console インターフェース
- 選択された Agent Engine
- ハイライトされた Memories タブ
- 表示される保存されたメモリーのリスト
- メモリーコンテンツの例（例: 「ユーザーはベジタリアン」）
推奨スタイル: アノテーション付き実際のスクリーンショット
-->

会話から抽出されたメモリーが表示されるはずです：
- 「ユーザーの名前はアレックス」
- 「ユーザーはベジタリアン（以前はステーキが好きだった）」
- 「ユーザーには重度のピーナッツアレルギーがある」
- 「ユーザーのパートナーはサム」
- 「ユーザーの記念日が近い」

> aside positive
> **成功！** Cloud Console でメモリーが表示されれば、メモリーバンクが正しく機能しています。

### 表示される内容の理解

各メモリーエントリには以下が含まれます：
- **Fact**: 抽出された情報
- **Topic**: 一致するデフォルトトピック（例: USER_PREFERENCES）
- **Create Time**: 抽出された日時
- **Scope**: 属するユーザー ID


## Cloud Run へのデプロイ
Duration: 0:05:00

ローカルで動作確認ができたので、本番環境にデプロイしましょう。Google Cloud Run を使えば、**たった1つのコマンド**でソースコードから本番グレードのアプリケーションをデプロイできます。

> aside positive
> **API は既に有効化済み**: `setup_env.sh` スクリプトで Cloud Run と Cloud Build API は既に有効化されています。

### Step 1: ソースからデプロイ

👉 `01-starter` ディレクトリから以下のコマンドを実行：

```bash
# .env ファイルから環境変数を読み込む
source .env

# Cloud Run にデプロイ（環境変数を含む）
gcloud run deploy restaurant-agent \
  --source . \
  --allow-unauthenticated \
  --region=${GOOGLE_CLOUD_LOCATION:-us-central1} \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=1,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,AGENT_ENGINE_ID=$AGENT_ENGINE_ID,GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY"
```

このコマンドが以下を自動的に行います：

1. **ソースコードの検出** - Python アプリケーションを自動認識
2. **コンテナのビルド** - Cloud Build が最適化されたコンテナイメージを作成
3. **デプロイ** - Cloud Run にサービスをデプロイ
4. **HTTPS エンドポイントの発行** - セキュアな URL を自動生成

### Step 2: デプロイ完了を確認

デプロイが完了すると、以下のような出力が表示されます：

```
Building using Buildpacks and deploying container to Cloud Run...
✓ Building and deploying... Done.
  ✓ Uploading sources...
  ✓ Building Container...
  ✓ Creating Revision...
  ✓ Routing traffic...
Done.
Service [restaurant-agent] revision [restaurant-agent-00001-xxx] has been deployed
Service URL: https://restaurant-agent-xxxxx-an.a.run.app
```

👉 表示された **Service URL** をブラウザで開いてアクセスしてください！

[//]: # (![デプロイ成功]&#40;img/38-deploy-success.png&#41;)

[//]: # (<!--)

[//]: # (IMAGE PLACEHOLDER: デプロイ成功)

[//]: # (説明: Cloud Run にデプロイされたアプリのスクリーンショット。)

[//]: # (タイプ: スクリーンショット)

[//]: # (含めるべき主要要素:)

[//]: # (- ブラウザで開かれたレストランエージェント)

[//]: # (- HTTPS URL バー)

[//]: # (- 動作するチャットインターフェース)

[//]: # (推奨スタイル: 実際のスクリーンショット)

[//]: # (-->)

> aside positive
> **これだけ！** Dockerfile を書く必要も、Kubernetes を設定する必要もありません。Google Cloud が自動的に最適な設定でアプリケーションをコンテナ化し、スケーラブルな環境にデプロイします。

### Cloud Run の利点

| 特徴 | 説明 |
|------|------|
| **ゼロから自動スケール** | リクエストがないときはゼロにスケールダウン（コスト最適化） |
| **自動 HTTPS** | SSL 証明書を自動管理 |
| **リクエストベース課金** | 使用した分だけ支払い |
| **高可用性** | 複数のゾーンに自動分散 |
| **継続的デプロイ** | 同じコマンドで更新も簡単 |



## まとめ
Duration: 0:03:00

### おめでとうございます！

![成功](img/35-success.png)
<!--
IMAGE PLACEHOLDER: 成功のお祝い
説明: 完了したコードラボを示すお祝いグラフィック。
タイプ: イラスト
含めるべき主要要素:
- チェックマークまたはトロフィーアイコン
- 「コードラボ完了！」テキスト
- レストランエージェントアイコン
- メモリーバンクアイコン
- お祝い要素（紙吹雪、星）
推奨スタイル: お祝い、ポジティブなイラスト
-->

以下の機能を持つ完全なレストラン推薦エージェントの構築に成功しました：

- **セッション管理**: 会話コンテキスト用に `VertexAiSessionService` を使用
- **長期メモリー**: 永続的なユーザー知識用に `VertexAiMemoryBankService` を使用
- **単一エージェント**: 複数のツールを使用する ADK の `LlmAgent`
- **MCP Toolset**: Google Maps API への接続
- **本番デプロイ**: Cloud Run への1コマンドデプロイ

### 構築したもの

![最終アーキテクチャ](img/36-final-architecture.png)
<!--
IMAGE PLACEHOLDER: 最終アーキテクチャの要約
説明: このコードラボで構築したすべてを示す完全なアーキテクチャ図。
タイプ: アーキテクチャ図
含めるべき主要要素:
- ラベル付きのすべてのコンポーネント
- データフロー矢印
- メモリーライフサイクルの表示
- Web UI から Agent Engine、メモリーバンクへのフロー
- エージェントと3つのツール（PreloadMemoryTool、GoogleSearchTool、Maps MCP）
推奨スタイル: 洗練されたアーキテクチャ図
-->

| コンポーネント | 目的 |
|-----------|---------|
| `VertexAiSessionService` | 短期会話メモリー |
| `VertexAiMemoryBankService` | 長期ユーザー事実と好み |
| `PreloadMemoryTool` | 類似性検索を介してセッション開始時にメモリーを読み込み |
| `GoogleSearchTool` | 一般的な Web 検索機能 |
| `Maps MCP Toolset` | Google Maps API を使用したレストラン検索 |
| `after_agent_callback` | セッション終了時に非同期メモリー生成をトリガー |
| Agent Engine | セッションとメモリー用のマネージドインフラストラクチャ |
| Cloud Run | ソースコードから自動デプロイ、スケーラブルな本番環境 |

### メモリーのフロー

1. **セッション終了** → `after_agent_callback` が**非同期メモリー生成**をトリガー
2. **抽出** → LLM が会話を分析し、重要な事実を抽出
3. **統合** → システムがメモリーを作成、更新、削除するかを決定
4. **保存** → アイデンティティスコーピング付きでメモリーを保存（各ユーザー分離）
5. **新しいセッション開始** → `PreloadMemoryTool` が**類似性検索**を実行
6. **エージェントが応答** → パーソナライズされたコンテキスト対応の推奨にメモリーを使用

### 次のStep 

- **カスタムメモリートピックの追加**: 抽出する特定の情報タイプを定義
- **メモリー TTL の実装**: 機密性の高いまたは時間制限のあるメモリーに有効期限を設定
- **さらなるツールの追加**: 予約、レビュー、食事分析用のツールを追加
- **メモリー管理 UI の追加**: ユーザーが保存されたメモリーを表示および削除できるようにする

> aside negative 
> **トラブルシューティング方法一覧**

デプロイ中に問題が発生した場合の解決方法：

#### 問題: "Setting IAM policy failed, try "gcloud beta run services add-iam-policy-binding --region=us-central1 --member=allUsers --role=roles/run.invoker restaurant-agent" と表示される

デプロイは成功していますが、IAM ポリシーの設定に失敗しています。

**原因**: `--allow-unauthenticated` フラグを設定する権限が不足しています。

**解決方法:**

```bash
# 1. パブリックアクセスを手動で許可
gcloud run services add-iam-policy-binding restaurant-agent \
  --region=us-central1 \
  --member=allUsers \
  --role=roles/run.invoker

# 2. トラフィックを最新リビジョンにルーティング
gcloud run services update-traffic restaurant-agent \
  --region=us-central1 \
  --to-latest
```

#### 問題: "serving 0 percent of traffic" と表示される

新しいリビジョンにトラフィックがルーティングされていません。

**解決方法:**

```bash
gcloud run services update-traffic restaurant-agent \
  --region=us-central1 \
  --to-latest
```

#### 環境変数の更新が必要な場合

デプロイ後に環境変数を変更したい場合：

```bash
gcloud run services update restaurant-agent \
  --region=us-central1 \
  --set-env-vars="AGENT_ENGINE_ID=新しい値"
```

または [Cloud Run コンソール](https://console.cloud.google.com/run) から **変数とシークレット** タブで編集できます。

> aside negative
> **重要**: API キーなどの機密情報は、本番環境では [Secret Manager](https://cloud.google.com/secret-manager) を使用することをお勧めします。

> aside positive
> **リソース**
> - [ADK ドキュメント](https://cloud.google.com/vertex-ai/docs/agents/adk)
> - [メモリーバンク概要](https://cloud.google.com/agent-builder/agent-engine/memory-bank/overview)
> - [メモリーの生成](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories)
> - [メモリーの取得](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/fetch-memories)
> - [Cloud Run ソースからデプロイ](https://cloud.google.com/run/docs/deploying-source-code)
> - [Google Maps API](https://developers.google.com/maps)