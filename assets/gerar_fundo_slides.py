"""
Gera o fundo dos slides: espaço PRETO + estrelas pequenas + Terra real (NASA).

A Terra é a foto "Blue Marble" (Apollo 17), da NASA — domínio público
(assets/earth-nasa.jpg). Composição por *lighten blend* (np.maximum): o preto ao
redor do disco não tapa as estrelas.

Produz:
  - assets/fundo-slides.png   (1920x1080)
  - fundo.html                (imagem embutida em base64 p/ include-in-header)

Rode: python assets/gerar_fundo_slides.py
"""

import base64
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 1920, 1080
RAIZ = Path(__file__).resolve().parents[1]
PNG = RAIZ / "assets" / "fundo-slides.png"
EARTH = RAIZ / "assets" / "earth-nasa.jpg"
rng = np.random.default_rng(7)

# --- Espaço preto ---
canvas = np.zeros((H, W, 3), dtype=float)

# --- Estrelas pequenas (1px), brilho variado, leve tom azulado em algumas ---
n = 240
xs = rng.integers(0, W, n)
ys = rng.integers(0, H, n)
brilho = rng.uniform(0.20, 0.85, n)
tint = np.ones((n, 3))
azuis = rng.random(n) < 0.25
tint[azuis] = np.array([0.75, 0.85, 1.0])   # algumas estrelas frias
canvas[ys, xs] = np.clip(brilho[:, None] * tint, 0, 1)

# --- Poucas estrelas um pouco maiores (2px) com halo tênue ---
for _ in range(14):
    x = int(rng.integers(4, W - 4))
    y = int(rng.integers(4, H - 4))
    b = float(rng.uniform(0.6, 1.0))
    canvas[y - 2:y + 3, x - 2:x + 3] = np.maximum(
        canvas[y - 2:y + 3, x - 2:x + 3], b * 0.18)   # halo
    canvas[y:y + 2, x:x + 2] = b                        # núcleo 2px

# --- Terra real, espiando no canto inferior direito ---
D = 700
earth = np.asarray(Image.open(EARTH).convert("RGB").resize((D, D), Image.LANCZOS)) / 255.0

# Máscara circular: zera tudo fora do disco (some a borda retangular do JPG).
gy, gx = np.mgrid[0:D, 0:D]
dist = np.sqrt((gx - D / 2) ** 2 + (gy - D / 2) ** 2) / (D / 2)
mascara = np.clip((0.985 - dist) / 0.03, 0, 1)   # borda suave nos ~3% externos
earth = earth * mascara[..., None]

cx, cy = int(W * 0.985), int(H * 1.06)      # centro fora da tela → só um pedaço aparece
x0, y0 = cx - D // 2, cy - D // 2
xa, xb = max(0, x0), min(W, x0 + D)
ya, yb = max(0, y0), min(H, y0 + D)
ecrop = earth[ya - y0:yb - y0, xa - x0:xb - x0]
canvas[ya:yb, xa:xb] = np.maximum(canvas[ya:yb, xa:xb], ecrop)   # lighten blend

# --- Salva o PNG ---
Image.fromarray((np.clip(canvas, 0, 1) * 255).astype("uint8")).save(PNG)

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
