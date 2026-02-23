import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む (主にDISCORD_WEBHOOK_URL用)
load_dotenv()

# 設定
DATA_FILE = "last_known_data.json"
LLM_PRICES_URL = "https://www.llm-prices.com/current-v1.json"

def get_env_var(name):
    return os.getenv(name)

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def send_notification(message):
    webhook_url = get_env_var("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[WARNING] DISCORD_WEBHOOK_URL not set. Message:")
        print(message)
        return

    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to send notification: {e}")

def fetch_llm_prices():
    """llm-pricesのエンドポイントからOpenAIのデータを抽出して辞書で返す"""
    try:
        response = requests.get(LLM_PRICES_URL, timeout=15)
        response.raise_for_status()
        full_data = response.json()

        # OpenAIのモデルのみを抽出してIDをキーとした辞書にする
        openai_prices = {}
        for item in full_data.get("prices", []):
            if item.get("vendor") == "openai":
                model_id = item.get("id")
                openai_prices[model_id] = {
                    "input": item.get("input"),
                    "output": item.get("output")
                }
        return openai_prices
    except Exception as e:
        print(f"[ERROR] Failed to fetch llm-prices: {e}")
        return None

def main():
    config = load_json("config.json")
    notify_models = config.get("notify_models", [])
    last_data = load_json(DATA_FILE)

    # 1. データの取得
    print("Fetching pricing data from llm-prices.com...")
    openai_data = fetch_llm_prices()
    if not openai_data:
        print("[ERROR] No OpenAI data found.")
        return

    notifications = []

    # 2. 新モデル検知
    current_models = sorted(openai_data.keys())
    last_models = last_data.get("models", [])
    new_models = set(current_models) - set(last_models)

    if new_models:
        notifications.append("モデルリストチェック\n🆕 新しいモデルが出ました。\n- " + "\n- ".join(new_models))
    else:
        notifications.append("モデルリストチェック\n✅ 新しいモデルはありませんでした。")

    # 3. 注目モデルの価格監視
    notifications.append("\nモデル価格監視 (per 1M tokens)")
    last_pricing = last_data.get("pricing", {})
    current_pricing = {}

    for model in notify_models:
        curr_p = openai_data.get(model)
        if not curr_p:
            notifications.append(f"❓ {model}: データが見つかりませんでした。")
            continue

        current_pricing[model] = curr_p
        last_p = last_pricing.get(model)
        has_update = False
        price_lines = []

        for p_type in ["input", "output"]:
            cv = curr_p.get(p_type)
            lv = last_p.get(p_type) if last_p else None
            p_label = "入力" if p_type == "input" else "出力"

            # Noneチェック（価格が設定されていない場合がある）
            if cv is None:
                price_lines.append(f"  - {p_label}: データなし")
                continue

            if lv is not None and cv != lv:
                diff = cv - lv
                diff_str = f"{'+' if diff > 0 else ''}{diff:.4f}$"
                price_lines.append(f"  {p_label}: **価格改定あり** {cv}$ (変化量: {diff_str})")
                has_update = True
            else:
                price_lines.append(f"  {p_label}：価格改定なし {cv}$")

        if has_update:
            notifications.append(f"🔔 **{model}：価格改定あり**")
        else:
            notifications.append(f"🔹 {model}：価格改定はありませんでした。")

        notifications.extend(price_lines)

    # 4. 通知と保存
    header = f"**OpenAI Monitor Report {datetime.now().strftime('%Y-%m-%d')}**\n\n"
    report_text = header + "\n".join(notifications)
    send_notification(report_text)

    last_data["models"] = current_models
    last_data["pricing"] = current_pricing
    save_json(DATA_FILE, last_data)
    print("Report sent (or printed to console).")

if __name__ == "__main__":
    main()
