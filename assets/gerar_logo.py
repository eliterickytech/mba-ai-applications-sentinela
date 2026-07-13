"""Gera o logo do Sentinela (planeta + órbita + varredura de radar) em PNG."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Wedge

fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
ax.set_xlim(-1.2, 1.2)
ax.set_ylim(-1.2, 1.2)
ax.set_aspect("equal")
ax.axis("off")
fig.patch.set_alpha(0)

AZUL = "#0B3D6B"
CIANO = "#2EC4F1"
LARANJA = "#F2A900"

# Varredura de radar (wedge)
ax.add_patch(Wedge((0, 0), 1.1, 30, 90, color=CIANO, alpha=0.18))
# Órbita
theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(1.0 * np.cos(theta), 0.55 * np.sin(theta), color=CIANO, lw=1.5, alpha=0.7)
# Planeta
ax.add_patch(Circle((0, 0), 0.42, color=AZUL))
ax.add_patch(Circle((-0.12, 0.12), 0.10, color=CIANO, alpha=0.5))
# Asteroide em destaque na órbita
ang = np.deg2rad(55)
ax.scatter([1.0 * np.cos(ang)], [0.55 * np.sin(ang)], s=90, color=LARANJA, zorder=5,
           edgecolors="white", linewidths=1.2)

fig.savefig(Path(__file__).parent / "logo.png", transparent=True, bbox_inches="tight")
print("logo salvo em assets/logo.png")
