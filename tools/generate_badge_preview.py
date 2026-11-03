# -*- coding: utf-8 -*-
"""Aperçu visuel — modèles de badges ID card modernes (85.6x54mm) avec logo ILAS.
Designs modernes : white-space, typographie raffinée, dégradés doux, photo soignée."""
import base64
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(BASE, 'static', 'uploads', 'logo-ilas.png')
LOGO_B64 = base64.b64encode(open(LOGO, 'rb').read()).decode()
DATA = f"data:image/png;base64,{LOGO_B64}"

# Palette du logo
BLUE = "#0B3D6E"
BLUE_2 = "#155DA8"
GOLD = "#C9A227"
RED = "#C8102E"
NAVY = "#0E1B2C"
INK = "#1A2430"
GREY = "#6E7B8A"
LINE = "#E6E9EE"

SIZE = "85.6 × 54 mm"
W = int(round(85.6 * 3.78))
H = int(round(54 * 3.78))

ST = dict(nom="SARA ALAOUI", code="ETU-0001", niveau="2BAC PC",
          cours="Anglais Général", groupe="Groupe A", annee="2025 / 2026")

def label_val(label, val, color=BLUE):
    return (f'<div style="display:flex;align-items:baseline;gap:6px;justify-content:space-between;'
            f'padding:2px 0;border-bottom:1px solid {LINE};">'
            f'<span style="font-size:6.5px;color:{GREY};letter-spacing:.8px;text-transform:uppercase;font-weight:600;">{label}</span>'
            f'<span style="font-size:10.5px;color:{INK};font-weight:600;">{val}</span></div>')

def mono():
    return (f'<div style="width:{int(W*0.145)}px;height:{int(W*0.145)}px;border-radius:50%;'
            f'background:linear-gradient(135deg,#eef2f7,#d5dfea);'
            f'display:flex;align-items:center;justify-content:center;font-weight:700;'
            f'font-size:{int(W*0.065)}px;color:{BLUE};'
            f'box-shadow:0 1px 3px rgba(16,30,50,.12);border:2px solid #fff;">S</div>')

def photo_card():
    return (f'<div style="width:{int(W*0.20)}px;height:{int(H*0.40)}px;border-radius:6px;overflow:hidden;'
            f'box-shadow:0 3px 8px rgba(16,30,50,.14);'
            f'background:linear-gradient(150deg,#dbe5f0,#c7d6e6);flex-shrink:0;">'
            f'<div style="width:100%;height:100%;display:flex;align-items:flex-start;justify-content:center;padding-top:8px;'
            f'font-size:{int(W*0.09)}px;color:#fff;font-weight:800;">S</div></div>')

TEMPLATES = [
    {
        "id": "studio",
        "name": "Studio — Blanc épuré",
        "desc": "Carte blanche, ligne d'accent subtile, photo soignée, données en grille fine. Le look le plus moderne et neutre.",
        "body": f"""
          <div style="position:relative;height:100%;background:#fff;overflow:hidden;display:flex;flex-direction:column;">
            <div style="height:3px;background:linear-gradient(90deg,{BLUE},{BLUE_2} 55%,{GOLD});"></div>
            <div style="flex:1;display:flex;gap:{int(W*0.045)}px;padding:{int(H*0.06)}px {int(W*0.05)}px;">
              <div style="flex:1;display:flex;flex-direction:column;">
                <img src="{DATA}" style="height:{int(H*0.15)}px;width:auto;align-self:flex-start;margin-bottom:auto;">
                <div style="margin-top:{int(H*0.05)}px;">
                  <div style="font-size:{int(W*0.048)}px;font-weight:700;letter-spacing:.2px;color:{INK};line-height:1.05;">{ST['nom']}</div>
                  <div style="font-size:9px;color:{GREY};font-weight:600;margin-top:2px;">{ST['code']}</div>
                </div>
                <div style="margin-top:auto;">
                  {label_val('Niveau', ST['niveau'])}
                  {label_val('Cours', ST['cours'])}
                </div>
              </div>
              {photo_card()}
            </div>
            <div style="padding:0 {int(W*0.05)}px {int(H*0.025)}px;display:flex;align-items:center;gap:6px;">
              <div style="font-size:7px;color:{GREY};letter-spacing:1px;">{ST['annee']}</div>
              <div style="flex:1;height:1px;background:{LINE};"></div>
              <div style="font-size:7px;color:{BLUE};font-weight:700;letter-spacing:.5px;">ILAS</div>
            </div>
          </div>
        """,
    },
    {
        "id": "aurora",
        "name": "Aurora — Dégradé doux",
        "desc": "Dégradé bleu profond subtil, logo clair, photo avec halo. Profond mais moderne.",
        "body": f"""
          <div style="position:relative;height:100%;background:linear-gradient(135deg,{NAVY} 0%,{BLUE} 100%);overflow:hidden;color:#fff;display:flex;flex-direction:column;">
            <div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;border-radius:50%;background:radial-gradient(circle,rgba(201,162,39,.25),transparent 70%);"></div>
            <div style="position:absolute;bottom:-30px;left:-30px;width:140px;height:140px;border-radius:50%;background:radial-gradient(circle,rgba(21,93,168,.4),transparent 70%);"></div>
            <div style="flex:1;display:flex;flex-direction:column;padding:{int(H*0.06)}px {int(W*0.05)}px;">
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <img src="{DATA}" style="height:{int(H*0.15)}px;width:auto;filter:brightness(0) invert(1);">
                <span style="font-size:8px;font-weight:600;letter-spacing:1.5px;color:rgba(255,255,255,.6);">{ST['annee']}</span>
              </div>
              <div style="flex:1;display:flex;align-items:center;gap:{int(W*0.05)}px;margin-top:{int(H*0.03)}px;">
                {photo_card()}
                <div style="flex:1;">
                  <div style="font-size:{int(W*0.05)}px;font-weight:700;letter-spacing:.2px;color:#fff;">{ST['nom']}</div>
                  <div style="font-size:10px;color:{GOLD};font-weight:600;margin-top:2px;">{ST['code']}</div>
                  <div style="height:1px;background:rgba(255,255,255,.18);margin:6px 0;"></div>
                  <div style="font-size:9.5px;color:rgba(255,255,255,.85);">{ST['niveau']}</div>
                  <div style="font-size:9.5px;color:rgba(255,255,255,.85);">{ST['cours']}</div>
                </div>
              </div>
            </div>
            <div style="height:2px;background:linear-gradient(90deg,transparent,{GOLD},transparent);"></div>
          </div>
        """,
    },
    {
        "id": "prestige",
        "name": "Prestige — Sombre raffiné",
        "desc": "Navy profond presque noir, accent doré unique, logo clair. Très haut de gamme.",
        "body": f"""
          <div style="height:100%;background:linear-gradient(160deg,#0c1520,#152436 60%,{NAVY});color:#fff;display:flex;flex-direction:column;padding:{int(H*0.055)}px {int(W*0.05)}px;position:relative;overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,{GOLD},transparent);"></div>
            <div style="display:flex;align-items:center;gap:8px;">
              <img src="{DATA}" style="height:{int(H*0.14)}px;width:auto;filter:brightness(0) invert(1);">
              <div style="flex:1;"></div>
              <div style="font-size:7px;letter-spacing:1.5px;color:rgba(255,255,255,.5);">CARTE ÉLÈVE</div>
            </div>
            <div style="flex:1;display:flex;align-items:center;gap:{int(W*0.05)}px;">
              {photo_card()}
              <div style="flex:1;">
                <div style="font-size:{int(W*0.05)}px;font-weight:600;letter-spacing:.3px;color:#fff;">{ST['nom']}</div>
                <div style="font-size:8.5px;color:{GOLD};letter-spacing:1.5px;margin-top:3px;">{ST['code']}</div>
              </div>
            </div>
            <div style="display:flex;gap:10px;border-top:1px solid rgba(255,255,255,.12);padding-top:{int(H*0.03)}px;">
              <div style="flex:1;"><div style="font-size:6px;color:rgba(255,255,255,.45);letter-spacing:1px;">NIVEAU</div><div style="font-size:9px;color:rgba(255,255,255,.9);font-weight:600;">{ST['niveau']}</div></div>
              <div style="flex:1.5;"><div style="font-size:6px;color:rgba(255,255,255,.45);letter-spacing:1px;">COURS</div><div style="font-size:9px;color:rgba(255,255,255,.9);font-weight:600;">{ST['cours']}</div></div>
              <div style="text-align:right;"><div style="font-size:6px;color:rgba(255,255,255,.45);letter-spacing:1px;">GROUPE</div><div style="font-size:9px;color:{GOLD};font-weight:600;">{ST['groupe']}</div></div>
            </div>
          </div>
        """,
    },
    {
        "id": "soft",
        "name": "Soft — Clair minimal",
        "desc": "Fond blanc cassé très doux, aucune bordure, logo et photo légers. Le plus aéré.",
        "body": f"""
          <div style="height:100%;background:#fafaf8;display:flex;flex-direction:column;padding:{int(H*0.06)}px {int(W*0.06)}px;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <img src="{DATA}" style="height:{int(H*0.13)}px;width:auto;">
              <span style="font-size:7px;color:{GREY};letter-spacing:1px;">{ST['annee']}</span>
            </div>
            <div style="flex:1;display:flex;align-items:center;gap:{int(W*0.05)}px;">
              <div style="flex:1;">
                <div style="font-size:{int(W*0.05)}px;font-weight:700;color:{INK};letter-spacing:.2px;">{ST['nom']}</div>
                <div style="font-size:10px;color:{BLUE};font-weight:600;margin-top:1px;">{ST['code']}</div>
                <div style="font-size:9px;color:{GREY};margin-top:5px;">{ST['niveau']}</div>
                <div style="font-size:9px;color:{GREY};">{ST['cours']} · {ST['groupe']}</div>
              </div>
              {photo_card()}
            </div>
            <div style="height:2px;width:32px;background:linear-gradient(90deg,{BLUE},{GOLD});"></div>
          </div>
        """,
    },
    {
        "id": "edge",
        "name": "Edge — Bandes latérales",
        "desc": "Blanc épuré avec liseré latéral bleu + touche dorée. Structure moderne en colonnes.",
        "body": f"""
          <div style="height:100%;background:#fff;display:flex;align-items:stretch;">
            <div style="width:5px;background:linear-gradient(180deg,{BLUE},{GOLD});"></div>
            <div style="flex:1;display:flex;gap:{int(W*0.045)}px;padding:{int(H*0.055)}px {int(W*0.05)}px;">
              <div style="flex:1;display:flex;flex-direction:column;">
                <img src="{DATA}" style="height:{int(H*0.14)}px;width:auto;align-self:flex-start;">
                <div style="margin-top:auto;">
                  <div style="font-size:{int(W*0.048)}px;font-weight:700;color:{INK};">{ST['nom']}</div>
                  <div style="font-size:9px;color:{GREY};font-weight:600;margin-bottom:4px;">{ST['code']}</div>
                  {label_val('Niveau', ST['niveau'])}
                  {label_val('Cours', ST['cours'])}
                </div>
              </div>
              {photo_card()}
            </div>
          </div>
        """,
    },
]

html = ["""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aperçu — Badges ID card modernes ILAS</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',-apple-system,Helvetica,Arial,sans-serif;background:#f1f3f7;padding:32px;color:#1a2430}
  .head{max-width:1100px;margin:0 auto 30px}
  .head h1{font-size:28px;letter-spacing:-.5px}
  .head .std{display:inline-block;background:#0B3D6E;color:#fff;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600;margin-top:10px}
  .head p{color:#5b6472;margin-top:10px;max-width:760px;font-size:14px;line-height:1.5}
  .grid{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:24px}
  .tpl{background:#fff;border-radius:16px;padding:20px;box-shadow:0 2px 6px rgba(20,30,50,.06),0 12px 30px rgba(20,30,50,.05)}
  .tpl h2{font-size:16px;letter-spacing:-.3px}
  .tpl .tag{font-size:10px;color:#0B3D6E;background:#E7F0FA;border-radius:20px;padding:2px 9px;font-weight:600;margin-left:6px}
  .tpl .size{font-size:11px;color:#8a93a3;margin-top:3px}
  .tpl .desc{font-size:12.5px;color:#5b6472;margin-top:7px;min-height:34px;line-height:1.45}
  .stage{display:flex;justify-content:center;align-items:center;padding:26px;background:
    linear-gradient(45deg,#eef1f6 25%,transparent 25%),linear-gradient(-45deg,#eef1f6 25%,transparent 25%),
    linear-gradient(45deg,transparent 75%,#eef1f6 75%),linear-gradient(-45deg,transparent 75%,#eef1f6 75%);
    background-size:18px 18px;background-position:0 0,0 9px,9px -9px,-9px 0;background-color:#f6f7fa;
    border-radius:12px;margin-top:14px;min-height:170px}
  .badge{border-radius:9px;box-shadow:0 10px 24px rgba(15,25,45,.22);overflow:hidden;position:relative}
  .foot{max-width:1100px;margin:30px auto 0;color:#8a93a3;font-size:12.5px}
</style></head><body>
<div class="head">
  <h1>Badges ID Card — ILAS</h1>
  <div class="std">Taille standard 85.6 × 54 mm (CR80)</div>
  <p>5 designs modernes, rendus en vraie taille d'impression, aux couleurs du logo ILAS. Choisissez le modèle que vous préférez et je l'implémente dans le système d'impression.</p>
</div>
<div class="grid">"""]

for t in TEMPLATES:
    html.append(f"""
  <div class="tpl">
    <h2>{t['name']}<span class="tag">{t['id']}</span></h2>
    <div class="size">Taille d'impression : {SIZE}</div>
    <div class="desc">{t['desc']}</div>
    <div class="stage">
      <div class="badge" style="width:{W}px;height:{H}px;background:#fff;">{t['body']}</div>
    </div>
  </div>
""")

html.append("""
</div>
<div class="foot">Aperçu visuel uniquement. Dites-moi le modèle (Studio, Aurora, Prestige, Soft, Edge) que vous préférez pour l'implémenter.</div>
</body></html>""")

out = os.path.join(BASE, 'badge_templates_preview.html')
open(out, 'w', encoding='utf-8').write('\n'.join(html))
print("Généré :", out, "|", W, "x", H, "px")
