"""Малює схему мережевої топології ЛР1."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def box(ax, x, y, w, h, text, fc="#ffffff", ec="black", fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


fig, ax = plt.subplots(figsize=(11, 6.2))
ax.set_xlim(0, 11); ax.set_ylim(0, 6.2); ax.axis("off")
box(ax, 0.2, 0.2, 10.6, 5.8, "", fc="#f7f7f7")
ax.text(0.4, 5.75, "Хост (Linux VM Docker Desktop), опублікований порт 8080/tcp (DNAT -> proxy:80)", fontsize=10, weight="bold")
box(ax, 0.5, 4.5, 3.0, 0.8, "docker0 172.17.0.1/16\n(мережа bridge за замовч.)", fc="#eeeeee")
box(ax, 0.5, 2.6, 3.0, 0.9, "br-<id> frontend\n172.28.1.1/24", fc="#dde8ff")
box(ax, 7.5, 2.6, 3.0, 0.9, "br-<id> backend (internal)\n172.28.2.1/24", fc="#ffe8cc")
box(ax, 0.5, 0.5, 2.6, 1.2, "proxy (nginx:1.27)\neth0 172.28.1.3\nпорт 80", fc="#ffffff")
box(ax, 4.2, 0.5, 2.6, 1.2, "app (Flask/gunicorn)\neth0 172.28.2.x (backend)\neth1 172.28.1.x (frontend)\nпорт 8000", fc="#ffffff")
box(ax, 8.0, 0.5, 2.4, 1.2, "db (redis:7)\neth0 172.28.2.2\nпорт 6379", fc="#ffffff")
for (x1, y1, x2, y2) in [(1.8, 1.7, 1.8, 2.6), (4.6, 1.7, 3.2, 2.6), (6.4, 1.7, 8.0, 2.6), (9.2, 1.7, 9.2, 2.6)]:
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-", lw=1.5, color="#336"))
ax.text(1.9, 2.1, "veth", fontsize=8, color="#336")
ax.text(3.6, 2.15, "veth", fontsize=8, color="#336")
ax.text(7.4, 2.15, "veth", fontsize=8, color="#336")
ax.text(9.3, 2.1, "veth", fontsize=8, color="#336")
ax.text(0.5, 3.8, "localhost:8080 -> DNAT -> proxy:80\n(iptables, ланцюжок DOCKER)", fontsize=8, color="red")
ax.text(5.0, 3.4, "proxy -> app:8000 (frontend)\napp -> db:6379 (backend)\nproxy НЕ бачить db", fontsize=9, ha="center")
plt.savefig("evidence/topology.png", dpi=150, bbox_inches="tight")
