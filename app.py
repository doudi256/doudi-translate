import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

LANGS = {
    "ar": ("العربية", "🇸🇦"), "en": ("English", "🇬🇧"),
    "fr": ("Français", "🇫🇷"), "es": ("Español", "🇪🇸"),
    "de": ("Deutsch", "🇩🇪"), "tr": ("Türkçe", "🇹🇷"),
    "ru": ("Русский", "🇷🇺"), "it": ("Italiano", "🇮🇹"),
    "pt": ("Português", "🇵🇹"), "fa": ("فارسی", "🇮🇷"),
    "hi": ("हिन्दी", "🇮🇳"), "ja": ("日本語", "🇯🇵"),
    "ko": ("한국어", "🇰🇷"), "zh-CN": ("中文", "🇨🇳"),
    "nl": ("Nederlands", "🇳🇱"), "sv": ("Svenska", "🇸🇪"),
}


def extract_translation(data):
    """Read the common Google Translate response shapes."""
    if isinstance(data, dict):
        sentences = data.get("sentences")
        if isinstance(sentences, list):
            return "".join(str(s.get("trans", "")) for s in sentences if isinstance(s, dict))
        for key in ("translation", "translatedText", "trans"):
            if isinstance(data.get(key), str):
                return data[key]

    if isinstance(data, list) and data:
        first = data[0]
        # Shape: [[['translated text', 'original text', ...], ...], ...]
        if isinstance(first, list) and first and isinstance(first[0], list):
            return "".join(str(segment[0]) for segment in first
                           if isinstance(segment, list) and segment and isinstance(segment[0], str))
        # Shape: [['translated text', 'original text', ...], ...]
        if isinstance(first, list) and first and isinstance(first[0], str):
            return "".join(str(segment[0]) for segment in data
                           if isinstance(segment, list) and segment and isinstance(segment[0], str))
        if isinstance(first, str):
            return first
    return ""


def translate_text(text, target, source="auto"):
    if target not in LANGS:
        raise ValueError("لغة الترجمة غير مدعومة.")
    if source != "auto" and source not in LANGS:
        raise ValueError("لغة النص الأصلي غير مدعومة.")

    url = "https://clients4.google.com/translate_a/t"
    params = {
        "client": "dict-chrome-ex",
        "sl": source,
        "tl": target,
        "tbb": "1",
        "q": text,
    }
    headers = {
        "Host": "clients4.google.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0",
        "Accept-Encoding": "gzip",
        "Accept": "*/*",
    }

    response = requests.get(url, params=params, headers=headers, timeout=25)
    if response.status_code == 429:
        raise RuntimeError("Google أوقف الطلبات مؤقتاً بسبب كثرتها (429). انتظر قليلاً ثم أعد المحاولة.")
    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError("خدمة Google أرسلت رداً غير مفهوم.") from exc

    result = extract_translation(data)
    if not result.strip():
        raise RuntimeError("لم تصل نتيجة ترجمة من Google.")
    return result


@app.get("/")
def home():
    return render_template("index.html", languages=[
        {"code": code, "name": name, "flag": flag}
        for code, (name, flag) in LANGS.items()
    ])


@app.post("/api/translate")
def api_translate():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    target = payload.get("target") or "ar"
    source = payload.get("source") or "auto"

    if not text:
        return jsonify({"error": "اكتب النص الذي تريد ترجمته أولاً."}), 400
    if len(text) > 5000:
        return jsonify({"error": "النص طويل جداً. الحد الأقصى هو 5000 حرف."}), 400

    try:
        result = translate_text(text, target, source)
        return jsonify({"translation": result})
    except requests.Timeout:
        return jsonify({"error": "انتهت مهلة الاتصال بخدمة الترجمة. حاول مرة أخرى."}), 504
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        app.logger.exception("Google Translate HTTP error")
        return jsonify({"error": f"خدمة الترجمة رفضت الطلب (HTTP {status}). حاول لاحقاً."}), 502
    except requests.RequestException:
        app.logger.exception("Google Translate connection error")
        return jsonify({"error": "تعذر الاتصال بخدمة الترجمة. تحقق من اتصال الاستضافة بالإنترنت."}), 502
    except RuntimeError as exc:
        app.logger.warning("Translation service response: %s", exc)
        return jsonify({"error": str(exc)}), 502
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Unexpected translation error")
        return jsonify({"error": "حدث خطأ داخلي أثناء الترجمة."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
