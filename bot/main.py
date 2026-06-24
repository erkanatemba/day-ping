import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_env_file() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")

if not BOT_TOKEN:
    raise SystemExit("Set BOT_TOKEN in bot/.env before running the bot.")

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def call_telegram(method: str, payload: dict | None = None, timeout: int = 35):
    data = json.dumps(payload or {}).encode("utf-8")
    request = urllib.request.Request(
        f"{API_BASE}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))

    if not body.get("ok"):
        raise RuntimeError(body)
    return body.get("result")


def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    call_telegram("sendMessage", payload, timeout=10)


def web_app_keyboard() -> dict | None:
    if not WEB_APP_URL:
        return None

    return {
        "keyboard": [
            [
                {
                    "text": "Открыть Day Ping",
                    "web_app": {"url": WEB_APP_URL},
                }
            ]
        ],
        "resize_keyboard": True,
    }


def format_day_ping(data: dict) -> str:
    mood = data.get("mood", "не указано")
    energy = data.get("energy", "не указано")
    focus = data.get("focus", "").strip() or "без текста"

    return (
        "Day Ping получен\n\n"
        f"Настрой: {mood}\n"
        f"Энергия: {energy}/5\n"
        f"Главное: {focus}"
    )


def handle_message(message: dict) -> None:
    chat_id = message["chat"]["id"]

    if "web_app_data" in message:
        raw_data = message["web_app_data"].get("data", "{}")
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            send_message(chat_id, "Я получил данные, но это не похоже на правильный JSON.")
            return

        send_message(chat_id, format_day_ping(data))
        return

    text = message.get("text", "")
    if text.startswith("/start"):
        if WEB_APP_URL:
            send_message(
                chat_id,
                "Привет. Нажми кнопку ниже, заполни короткий чек-ин дня и отправь его обратно сюда.",
                reply_markup=web_app_keyboard(),
            )
        else:
            send_message(
                chat_id,
                "WEB_APP_URL пустой. Опубликуй папку docs/ через GitHub Pages, затем добавь HTTPS-ссылку в bot/.env.",
            )
        return

    send_message(chat_id, "Отправь /start, чтобы открыть мини-приложение.")


def handle_update(update: dict) -> None:
    message = update.get("message")
    if message:
        handle_message(message)


def run() -> None:
    offset = None
    print("Бот запущен. Нажми Ctrl+C, чтобы остановить.")

    while True:
        try:
            payload = {"timeout": 25}
            if offset is not None:
                payload["offset"] = offset

            updates = call_telegram("getUpdates", payload, timeout=35)
            for update in updates:
                offset = update["update_id"] + 1
                handle_update(update)
        except urllib.error.URLError as error:
            print(f"Ошибка сети: {error}. Повтор через 5 секунд.")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nБот остановлен.")
            return


if __name__ == "__main__":
    run()
