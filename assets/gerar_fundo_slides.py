"""
Gera o fundo dos slides: nebulosa suave + campo de estrelas + Terra no canto.

Produz:
  - assets/fundo-slides.png   (imagem 1920x1080)
  - fundo.html                (partial com a imagem embutida em base64, para o
                               include-in-header do reveal.js — 100% self-contained)

Rode: python assets/gerar_fundo_slides.py
"""

import base64
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

W, H = 1920, 1080
RAIZ = Path(__file__).resolve().parents[1]
PNG = RAIZ / "assets" / "fundo-slides.png"
rng = np.random.default_rng(42)

# --- Campo de nebulosa (numpy) ---
yy, xx = np.mgrid[0:H, 0:W]
img = np.zeros((H, W, 3)) + np.array([5, 7, 15]) / 255.0


def blob(cx, cy, r, cor, forca):
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))) * forca
    for i, c in enumerate(cor):
        img[:, :, i] += g * (c / 255.0)


blob(W * 0.82, H * 0.18, 430, (46, 196, 241), 0.30)   # nebulosa ciano (topo-dir)
blob(W * 0.14, H * 0.86, 470, (150, 90, 220), 0.28)   # nebulosa roxa (base-esq)
blob(W * 0.50, H * 0.48, 720, (14, 26, 58), 0.45)     # brilho central frio
img = np.clip(img, 0, 1)

fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)
ax.axis("off")
ax.imshow(img, extent=[0, W, H, 0], zorder=0)

# --- Estrelas (varias camadas de tamanho/brilho) ---
n = 320
sx, sy = rng.uniform(0, W, n), rng.uniform(0, H, n)
tam = rng.uniform(0.3, 2.6, n) ** 2 * 4
alpha = rng.uniform(0.25, 0.95, n)
cores = np.ones((n, 4))
cores[:, 3] = alpha
ax.scatter(sx, sy, s=tam, c=cores, linewidths=0, zorder=1)

# Algumas estrelas brilhantes com leve halo
for _ in range(14):
    bx, by = rng.uniform(0, W), rng.uniform(0, H)
    ax.scatter([bx], [by], s=90, c="white", alpha=0.18, linewidths=0, zorder=1)
    ax.scatter([bx], [by], s=14, c="white", alpha=0.95, linewidths=0, zorder=2)

# --- Terra decorativa no canto inferior direito (sprite radial recortado) ---
er = 360
ecx, ecy = W * 0.985, H * 1.03
gy, gx = np.mgrid[0:2 * er, 0:2 * er]
dist = np.sqrt((gx - er * 0.62) ** 2 + (gy - er * 0.62) ** 2) / (er * 1.5)
t = np.clip(1 - dist, 0, 1)[..., None]
c1, c2, c3 = np.array([9, 26, 58]), np.array([38, 110, 188]), np.array([96, 184, 236])
col = c1 + (c2 - c1) * t + (c3 - c2) * np.clip((t - 0.5) * 2, 0, 1)
sprite = np.dstack([col / 255.0, np.ones((2 * er, 2 * er))])
im = ax.imshow(sprite, extent=[ecx - er, ecx + er, ecy + er, ecy - er], zorder=3)
im.set_clip_path(Circle((ecx, ecy), er, transform=ax.transData))
# halo atmosférico
ax.add_patch(Circle((ecx, ecy), er, fill=False, ec=(0.3, 0.7, 0.95), lw=6, alpha=0.25, zorder=3))

fig.savefig(PNG, dpi=100, facecolor="#05070f")
plt.close(fig)

# --- Embute em base64 no partial HTML ---
b64 = base64.b64encode(PNG.read_bytes()).decode()
html = (
    "<style>\n"
    "  .reveal-viewport {\n"
    f"    background-image: url('data:image/png;base64,{b64}') !important;\n"
    "    background-size: cover !important;\n"
    "    background-position: center !important;\n"
    "    background-repeat: no-repeat !important;\n"
    "  }\n"
    "  .reveal .slide-background { background: transparent !important; }\n"
    "</style>\n"
)
(RAIZ / "fundo.html").write_text(html, encoding="utf-8")
print(f"fundo-slides.png ({PNG.stat().st_size // 1024} KB) e fundo.html gerados.")
