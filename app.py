import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

LANGS = {
    "ar": ("العربية", "🇸🇦"),
    "en": ("English", "🇬🇧"),
    "fr": ("Français", "🇫🇷"),
    "es": ("Español", "🇪🇸"),
    "de": ("Deutsch", "🇩🇪"),
    "tr": ("Türkçe", "🇹🇷"),
    "ru": ("Русский", "🇷🇺"),
    "it": ("Italiano", "🇮🇹"),
    "pt": ("Português", "🇵🇹"),
    "fa": ("فارسی", "🇮🇷"),
    "hi": ("हिन्दी", "🇮🇳"),
    "ja": ("日本語", "🇯🇵"),
    "ko": ("한국어", "🇰🇷"),
    "zh-CN": ("中文", "🇨🇳"),
    "nl": ("Nederlands", "🇳🇱"),
    "sv": ("Svenska", "🇸🇪"),
}

def translate_text(text: str, target: str) -> str:
    if target not in LANGS:
        raise ValueError("لغة الترجمة غير مدعومة.")

    url = "https://translate.googleapis.com/translate_a/single"

    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target,
        "dt": "t",
        "q": text,
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=25
    )
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list) or not data or not isinstance(data[0], list):
        raise RuntimeError("استجابة غير مفهومة من خدمة الترجمة.")

    result = "".join(
        str(item[0])
        for item in data[0]
        if isinstance(item, list) and item and item[0]
    )

    if not result.strip():
        raise RuntimeError("لم تصل نتيجة من خدمة الترجمة.")

    return result


@app.get("/")
def home():
    return render_template(
        "index.html",
        languages=[
            {"code": code, "name": name, "flag": flag}
            for code, (name, flag) in LANGS.items()
        ]
    )


@app.post("/api/translate")
def api_translate():
    payload = request.get_json(silent=True) or {}

    text = (payload.get("text") or "").strip()
    target = payload.get("target") or "ar"

    if not text:
        return jsonify({"error": "اكتب النص الذي تريد ترجمته أولاً."}), 400

    if len(text) > 5000:
        return jsonify({"error": "النص طويل جداً. الحد الأقصى هو 5000 حرف."}), 400

    try:
        result = translate_text(text, target)
        return jsonify({"translation": result})

    except requests.Timeout:
        return jsonify({"error": "انتهت مهلة الاتصال. حاول مرة أخرى."}), 504

    except requests.RequestException:
        app.logger.exception("Translation connection error")
        return jsonify({"error": "تعذر الاتصال بخدمة الترجمة حالياً."}), 502

    except Exception as exc:
        app.logger.exception("Translation error: %s", exc)
        return jsonify({"error": "حدث خطأ أثناء الترجمة."}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False
    )
