"""Trekker ut SSB-ikonene fra oversikts-PDF-en til kompakte SVG-filer.

Hver side har seks ikoner i øverste rad (hvit bakgrunn). Vektorene leses med PyMuPDF
(get_drawings) og skrives som rene <path>-elementer i en 72 x 72 viewBox.
Mørk farge (#274247) blir currentColor, slik at ikonet kan fargelegges med CSS.
Hvitt beholdes, fordi ikonene er tofarget (hvite flater inni mørke).
"""
import sys, os, pymupdf as fitz

PDF, UT = sys.argv[1], sys.argv[2]
os.makedirs(UT, exist_ok=True)
MORK = {"#274247", "#224749"}

def hexf(c):
    return None if c is None else "#%02x%02x%02x" % tuple(round(x * 255) for x in c)

def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s

doc = fitz.open(PDF)
n = 0
for pi, side in enumerate(doc):
    dr = side.get_drawings()
    # Navnene står under ikonene: «Ikon N», eller et eget navn (siste side: «SSB Kongsvinger»)
    ord_ = [w for w in side.get_text("words") if 250 < w[1] < 300]
    etiketter = []
    for j, w in enumerate(ord_):
        if w[4] == "Ikon" and j + 1 < len(ord_):
            etiketter.append(((w[0] + ord_[j + 1][2]) / 2, f"ikon-{int(ord_[j + 1][4]):03d}"))
    if not etiketter and ord_:
        etiketter.append(((ord_[0][0] + ord_[-1][2]) / 2, "-".join(w[4].lower() for w in ord_)))
    topp = [d for d in dr if d["rect"].y1 < 290 and d["rect"].width < 700]
    for ex, navn in etiketter:
        if navn.startswith("ikon-"):
            boks = fitz.Rect(ex - 40, 148.05 - 40, ex + 40, 148.05 + 40)
            mine = [d for d in topp if abs((d["rect"].x0 + d["rect"].x1) / 2 - ex) < 60]
        else:
            mine = topp
            boks = fitz.Rect(mine[0]["rect"])
            for d in mine: boks |= d["rect"]
            boks = fitz.Rect(boks.x0 - 4, boks.y0 - 4, boks.x1 + 4, boks.y1 + 4)
        u = fitz.Rect(mine[0]["rect"]) if mine else boks
        for d in mine: u |= d["rect"]
        if navn.startswith("ikon-") and mine:
            mx, my = (u.x0 + u.x1) / 2, (u.y0 + u.y1) / 2
            boks = fitz.Rect(mx - 40, my - 40, mx + 40, my + 40)
        if not boks.contains(u):
            print("utenfor boksen:", navn, u)
        n += 1
        ox, oy = boks.x0, boks.y0
        deler = []
        for d in mine:
            p, sist = [], None
            for it in d["items"]:
                if it[0] in ("l", "c"):
                    pts = it[1:3] if it[0] == "l" else it[1:5]
                    a = pts[0]
                    start = (round(a.x - ox, 2), round(a.y - oy, 2))
                    if start != sist:
                        p.append(f"M{f(start[0])} {f(start[1])}")
                    if it[0] == "l":
                        b = pts[1]; p.append(f"L{f(b.x-ox)} {f(b.y-oy)}")
                    else:
                        b, c, e = pts[1:]; p.append(f"C{f(b.x-ox)} {f(b.y-oy)} {f(c.x-ox)} {f(c.y-oy)} {f(e.x-ox)} {f(e.y-oy)}")
                    z = pts[-1]; sist = (round(z.x - ox, 2), round(z.y - oy, 2))
                elif it[0] == "re":
                    r = it[1]
                    p.append(f"M{f(r.x0-ox)} {f(r.y0-oy)}H{f(r.x1-ox)}V{f(r.y1-oy)}H{f(r.x0-ox)}Z"); sist = None
                elif it[0] == "qu":
                    q = it[1]
                    p.append(f"M{f(q.ul.x-ox)} {f(q.ul.y-oy)}L{f(q.ur.x-ox)} {f(q.ur.y-oy)}L{f(q.lr.x-ox)} {f(q.lr.y-oy)}L{f(q.ll.x-ox)} {f(q.ll.y-oy)}Z"); sist = None
            # Slå sammen M-er som fortsetter fra forrige punkt
            dstr = "".join(p)
            if d.get("closePath"):
                dstr += "Z"
            fill, stroke = hexf(d.get("fill")), hexf(d.get("color"))
            farge = lambda c: "currentColor" if c in MORK else c
            att = f'fill="{farge(fill)}"' if fill else 'fill="none"'
            if fill and d.get("even_odd"):
                att += ' fill-rule="evenodd"'
            if stroke and d.get("width"):
                att += f' stroke="{farge(stroke)}" stroke-width="{f(d["width"])}"'
            deler.append(f'<path {att} d="{dstr}"/>')
        W, H = f(boks.width), f(boks.height)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" color="#274247">'
               + "".join(deler) + "</svg>")
        open(os.path.join(UT, f"{navn}.svg"), "w").write(svg)
print(n, "ikoner")
