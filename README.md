# OpenAI Prices Monitor

OpenAIの新しいAIモデルのリリースと、主要モデルの価格改定を自動的に監視し、Discordへ通知するツールです。

## 特徴
- **APIキー不要**: OpenAI APIを使用せず、Simon Willison氏の [llm-prices](https://github.com/simonw/llm-prices) JSONデータを利用して監視を行います。
- **入出力価格の監視**: 1M（100万）トークンあたりの入力価格と出力価格の両方を個別に追跡します。
- **自動運用**: GitHub Actionsにより、毎週月曜日に自動実行されます。
- **日本語対応**: すべての通知は日本語で行われます。

## セットアップ

### ローカル実行
1. リポジトリをクローンします。
2. 依存ライブラリをインストールします。
   ```bash
   pip install -r requirements.txt
   ```
3. `.env` ファイルを作成し、DiscordのWebhook URLを設定します。
   ```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```
4. 実行します。
   ```bash
   python monitor.py
   ```

### GitHub Actions (自動運用)
GitHubリポジトリの **Settings > Secrets and variables > Actions** に以下の Secret を登録してください。
- `DISCORD_WEBHOOK_URL`: 通知を送信するDiscordのWebhook URL

※ `last_known_data.json` は実行後に自動的にコミット・プッシュされ、次回の比較に使用されます。

## 設定 (config.json)
`config.json` の `notify_models` リストに、価格を詳細に監視したいモデルのID（OpenAI APIで使用されるID）を記述します。

```json
{
  "notify_models": [
    "gpt-4o",
    "gpt-4o-mini",
    "o1-preview",
    "gpt-5-mini"
  ]
}
```

## 通知イメージ
```text
📅 **OpenAI Monitor Report (2026-02-23)**
✅ 新しいモデルは出ていませんでした。

💰 **注目モデルの価格監視 (per 1M tokens):**
🔔 **gpt-4o: 価格改定がありました！**
  - 入力: **価格改定あり** 2.5000$ (変化量: -2.5000$)
  - 出力: 価格改定なし (15.0$)
🔹 gpt-4o-mini: 価格改定はありませんでした。
  - 入力: 価格改定なし (0.15$)
  - 出力: 価格改定なし (0.6$)
```

## データソースについて
本プロジェクトは、[simonw/llm-prices](https://github.com/simonw/llm-prices) が提供するデータを元に価格監視を行っています。
