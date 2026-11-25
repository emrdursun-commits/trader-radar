"""TRADER SİNYAL webhook sunucusu.

TradingView alarmı (JSON) -> görsel çiz -> Telegram'a fotoğraf + metin gönder.

Ortam değişkenleri (sunucu panelinden SEN girersin, koda yazılmaz):
  TELEGRAM_TOKEN   bot token'ı
  CHAT_ID          kanal id'si (ör. -100...)
  WEBHOOK_SECRET   TradingView mesajındaki "key" alanıyla aynı olmalı

Alarm mesajı (Pine'dan gelen JSON) örneği: ornek_alarm.json
"""
import json, os, tempfile, urllib.request, uuid
from flask import Flask, request, abort
from signal_img import draw, result, pct

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
SECRET = os.environ.get("WEBHOOK_SECRET", "")
app = Flask(__name__)


def tg(method, fields, photo_path=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    if not photo_path:
        req = urllib.request.Request(url, data=json.dumps(fields).encode(), headers={"Content-Type": "application/json"})
        return urllib.request.urlopen(req, timeout=20).read()
    b = uuid.uuid4().hex; body = b""
    for k, v in fields.items():
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    body += f'--{b}\r\nContent-Disposition: form-data; name="photo"; filename="s.png"\r\nContent-Type: image/png\r\n\r\n'.encode()
    body += open(photo_path, "rb").read() + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    return urllib.request.urlopen(req, timeout=30).read()


@app.get("/")
def health():
    return "ok"


@app.post("/webhook")
def webhook():
    raw = request.get_data(as_text=True)
    try:
        d = json.loads(raw)
    except Exception:
        # JSON değilse (eski düz metin alarmları) olduğu gibi metin olarak gönder
        tg("sendMessage", {"chat_id": CHAT_ID, "text": raw}); return "text"
    if SECRET and d.get("key") != SECRET:
        abort(403)
    text = d.get("text", "")
    res = result(d) if all(k in d for k in ("sym", "e", "s", "t1", "t2")) else None
    if res:  # kaldıraçlı sonuç satırı otomatik eklenir
        text += f"\n\n💰 {res['txt']}: kaldıraçlı {pct(res['pct'])} ({res['lev']:.2f}x)".replace(".", ",")
    if d.get("bars"):
        with tempfile.TemporaryDirectory() as td:
            p = draw(d, os.path.join(td, "s.png"))
            tg("sendPhoto", {"chat_id": CHAT_ID, "caption": text[:1024]}, p)
    else:
        tg("sendMessage", {"chat_id": CHAT_ID, "text": text})
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
