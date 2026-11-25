"""TRADER SİNYAL görseli: son mumlar + giriş / stop / TP1 / TP2 çizgileri.

draw(data, out_path) -> out_path
data = {
  "sym": "AKBNK", "tf": "15",            # "15" | "60"
  "dir": -1,                             # 1 LONG, -1 SHORT
  "event": "entry",                      # entry | tp1 | tp2 | stop | be
  "e": 64.22, "s": 64.77, "t1": 63.67, "t2": 63.12,
  "bars": "o,h,l,c;o,h,l,c;...",         # eskiden yeniye, son mum = olay mumu
  "sig_ago": 0                           # sinyal mumu sondan kaç mum önce (entry için 0)
}
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import os as _os
from matplotlib.patches import Rectangle, FancyBboxPatch

for f in fm.findSystemFonts() + fm.findSystemFonts(fontpaths=[_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fonts")]):
    if "Inter" in f:
        try: fm.fontManager.addfont(f)
        except Exception: pass
plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]

BG = "#DCDCDC"; PANEL = "#E4E4E4"; INK = "#1B1F24"; MUTED = "#6B7280"
UP = "#5DBB63"; DN = "#F4A3A3"; EDGE = "#1B1F24"
RED = "#F23645"; TEAL = "#089981"; GREY = "#787B86"
TF_TXT = {"15": "15dk", "60": "1 saat", "120": "2 saat"}
EV_TXT = {"entry": ("YENİ SİNYAL", None), "tp1": ("TP1 GELDİ · STOP GİRİŞE", TEAL),
          "tp2": ("TP2 GELDİ · İŞLEM KAPANDI", TEAL), "stop": ("STOP OLDU", RED),
          "be": ("GİRİŞTE KAPANDI", GREY), "plan": ("PLAN · GİRİŞ BÖLGESİ BEKLENİYOR", "#F59E0B"), "pos": ("AÇIK POZİSYON · TAKİPTE", "#2962FF")}


def fmt(x, dec):
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


import json as _json, os as _os
try:
    LEV = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "kaldirac.json")))
except Exception:
    LEV = {}


def result(d):
    """olaya göre kaldıraçlı sonuç (%). TP1: yarısı kapanır; TP2: yarı TP1 + yarı TP2; stop: tam R; be: TP1 sonrası girişte."""
    e, s, t1, t2 = (float(d[k]) for k in ("e", "s", "t1", "t2"))
    lev = float(d.get("lev") or LEV.get(d["sym"], 0) or 0)
    g1, g2, r = abs(t1 - e) / e * 100, abs(t2 - e) / e * 100, abs(s - e) / e * 100
    ev = d.get("event", "entry")
    raw = {"tp1": g1, "tp2": 0.5 * g1 + 0.5 * g2, "be": 0.5 * g1, "stop": -r}.get(ev)
    if raw is None or not lev: return None
    return dict(lev=lev, raw=raw, pct=raw * lev,
                txt={"tp1": "Pozisyonun yarısı kapandı", "tp2": "Pozisyon kapandı", "be": "Kalan yarı girişte kapandı",
                     "stop": "Pozisyon stop oldu"}[ev])


def pct(x):
    return ("+" if x > 0 else "−") + "%" + f"{abs(x):.2f}".replace(".", ",")


def draw(d, out):
    bars = [[float(v) for v in b.split(",")] for b in d["bars"].strip(";").split(";")]
    n = len(bars); dirn = int(d["dir"]); tf = TF_TXT.get(str(d["tf"]), str(d["tf"]))
    e, s, t1, t2 = (float(d[k]) for k in ("e", "s", "t1", "t2"))
    dec = 0 if e >= 1000 else 2
    ev = d.get("event", "entry"); sig_i = n - 1 - int(d.get("sig_ago", 0))

    W, H = 1200, 900
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)
    # başlık
    side = "LONG" if dirn == 1 else "SHORT"; sc = TEAL if dirn == 1 else RED
    fig.text(0.04, 0.945, f"{d['sym']} VİOP", color=INK, fontsize=30, fontweight="bold", va="center")
    fig.text(0.04, 0.895, f"{tf} · TRADER sistemi", color=MUTED, fontsize=15, va="center")
    ax0 = fig.add_axes([0, 0, 1, 1]); ax0.axis("off"); ax0.set_xlim(0, W); ax0.set_ylim(H, 0)
    ax0.add_patch(FancyBboxPatch((W - 250, 28), 205, 50, boxstyle="round,pad=0,rounding_size=12", fc=sc, ec="none"))
    ax0.text(W - 147, 53, side, color="white", fontsize=22, fontweight="bold", ha="center", va="center")
    lab, lc = EV_TXT.get(ev, EV_TXT["entry"])
    if lc:
        ax0.add_patch(FancyBboxPatch((W - 520, 90), 475, 40, boxstyle="round,pad=0,rounding_size=10", fc=lc, ec="none"))
        ax0.text(W - 282, 110, lab, color="white", fontsize=15, fontweight="bold", ha="center", va="center")

    # grafik
    ax = fig.add_axes([0.03, 0.08, 0.70, 0.76], facecolor=BG)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    lv = [e, s, t1, t2]
    lo = min(min(b[2] for b in bars), *lv); hi = max(max(b[1] for b in bars), *lv)
    pad = (hi - lo) * 0.06; ax.set_ylim(lo - pad, hi + pad)
    xr = n + 0.6 + n * 0.85          # sağda etiketler için boşluk
    ax.set_xlim(-0.8, xr)
    w = 0.62
    for i, (o, h, l, c) in enumerate(bars):
        up = c >= o; col = UP if up else DN
        ax.plot([i, i], [l, h], color=EDGE, lw=1.0, zorder=2)
        y0, hgt = (o, c - o) if up else (c, o - c)
        hgt = max(hgt, (hi - lo) * 0.002)
        ax.add_patch(Rectangle((i - w / 2, y0), w, hgt, fc=col, ec=EDGE, lw=0.8, zorder=3))
    # sinyal oku
    if 0 <= sig_i < n:
        b = bars[sig_i]; off = (hi - lo) * 0.035
        if dirn == -1:
            ax.annotate(tf.replace("dk", "").replace(" saat", "s"), (sig_i, b[1] + off), color=RED, fontsize=11,
                        ha="center", va="bottom", fontweight="bold")
            ax.scatter([sig_i], [b[1] + off * 0.6], marker="v", s=90, color=RED, zorder=4)
        else:
            ax.annotate(tf.replace("dk", "").replace(" saat", "s"), (sig_i, b[2] - off), color=TEAL, fontsize=11,
                        ha="center", va="top", fontweight="bold")
            ax.scatter([sig_i], [b[2] - off * 0.6], marker="^", s=90, color=TEAL, zorder=4)
    # seviyeler
    x0 = max(sig_i, 0) if ev != "plan" else n - 8; xe = n + n * 0.35
    elab = d.get("e_label") or f"Giriş {fmt(e, dec)} ({tf})"
    lines = [(s, f"Stop {fmt(s, dec)}", RED, "--"), (e, elab, GREY, "-"),
             (t1, f"TP1 {fmt(t1, dec)}", TEAL, "--"), (t2, f"TP2 {fmt(t2, dec)}", TEAL, "--")]
    for y, txt, col, ls in lines:
        ax.plot([x0, xe], [y, y], color=col, lw=1.6 if ls == "-" else 1.3, ls=ls, zorder=1)
        ax.annotate(txt, (xe + 0.3, y), color="white", fontsize=14, va="center", ha="left",
                    bbox=dict(boxstyle="round,pad=0.35", fc=col, ec="none"), zorder=5)

    # sağ panel: plan
    rr = abs(t1 - e) / abs(s - e) if s != e else 0
    px = 0.765
    fig.text(px, 0.80, "İŞLEM PLANI", color=MUTED, fontsize=13, fontweight="bold")
    rows = [("Yön", side, sc), ("Giriş", d.get("e_text") or fmt(e, dec), INK), ("Stop", fmt(s, dec), RED),
            ("TP1", fmt(t1, dec), TEAL), ("TP2", fmt(t2, dec), TEAL),
            ("Risk", f"%{abs(s - e) / e * 100:.2f}".replace(".", ","), INK)]
    for k, (a, b, c) in enumerate(rows):
        y = 0.74 - k * 0.062
        fig.text(px, y, a, color=MUTED, fontsize=16)
        fig.text(0.955, y, b, color=c, fontsize=17, fontweight="bold", ha="right")
    res = result(d)
    if res:
        col = TEAL if res["pct"] > 0 else RED
        fig.text(px, 0.33, "KALDIRAÇLI SONUÇ", color=MUTED, fontsize=13, fontweight="bold")
        fig.text(px, 0.245, pct(res["pct"]), color=col, fontsize=34, fontweight="bold")
        fig.text(px, 0.19, f"{res['txt']} · {fmt(res['lev'], 2)}x", color=MUTED, fontsize=11.5)
    else:
        lev = float(d.get("lev") or LEV.get(d["sym"], 0) or 0)
        if lev:
            fig.text(px, 0.33, f"Kaldıraç {fmt(lev, 2)}x", color=MUTED, fontsize=13, fontweight="bold")
            fig.text(px, 0.285, f"TP1: {pct(abs(t1 - e) / e * 100 * lev)}   TP2: {pct((abs(t1 - e) + abs(t2 - e)) / 2 / e * 100 * lev)}",
                     color=TEAL, fontsize=12.5, fontweight="bold")
            fig.text(px, 0.25, f"Stop: {pct(-abs(s - e) / e * 100 * lev)}", color=RED, fontsize=12.5, fontweight="bold")
        fig.text(px, 0.17, "TP1'de yarısı kapanır,\nstop girişe çekilir.", color=MUTED, fontsize=12.5, linespacing=1.5)
    fig.text(0.04, 0.035, "TRADER RADAR · Gün içi işlem · Yatırım tavsiyesi değildir", color=MUTED, fontsize=12)
    fig.savefig(out, dpi=100, facecolor=BG)
    plt.close(fig)
    return out


if __name__ == "__main__":
    import json, sys
    draw(json.load(open(sys.argv[1])), sys.argv[2])
