"""
visualization.py
================
Phase 15 — Complete Data Visualization
Food Delivery App — Product Analytics Portfolio Project

Generates 4 publication-ready charts:
  1. Full funnel chart with drop-off rates
  2. Segment analysis — Android vs iOS
  3. Segment analysis — New vs Returning users
  4. Hourly order pattern (peak hours)
"""

import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import warnings

warnings.filterwarnings("ignore")
import os

os.makedirs("outputs", exist_ok=True)

# ── Color palette ──────────────────────────────────────────
PURPLE = "#534AB7"
TEAL = "#0F6E56"
CORAL = "#D85A30"
AMBER = "#BA7517"
GRAY = "#888780"
LGRAY = "#D3D1C7"
BLUE = "#185FA5"
FUNNEL_COLORS = ["#534AB7", "#6B62C4", "#837AD1", "#9B92DE", "#B3AAEB", "#CBC2F8"]

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.family": "sans-serif",
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    }
)

# ── Load data ───────────────────────────────────────────────
print("Loading data...")
events = pd.read_csv("data/raw/events.csv")
users = pd.read_csv("data/raw/users.csv")
sessions = pd.read_csv("data/raw/sessions.csv")
exp = pd.read_csv("data/raw/experiment_groups.csv")

events["event_timestamp"] = pd.to_datetime(events["event_timestamp"])
sessions["session_start"] = pd.to_datetime(sessions["session_start"])
print(f"  ✓ {len(events):,} events | {len(users):,} users | {len(sessions):,} sessions")

FUNNEL_STEPS = [
    "app_open",
    "restaurant_click",
    "menu_view",
    "add_to_cart",
    "checkout_started",
    "order_placed",
]
STEP_LABELS = [
    "App Open",
    "Restaurant\nClick",
    "Menu\nView",
    "Add to\nCart",
    "Checkout\nStarted",
    "Order\nPlaced",
]

# ════════════════════════════════════════════════════════════
# CHART 1 — FUNNEL WITH DROP-OFF RATES
# ════════════════════════════════════════════════════════════
print("Building Chart 1: Funnel...")

funnel_counts = {
    step: events[events["event_type"] == step]["user_id"].nunique()
    for step in FUNNEL_STEPS
}
total = funnel_counts["app_open"]
pct_total = {s: v / total * 100 for s, v in funnel_counts.items()}
dropoffs = {}
steps_list = list(funnel_counts.values())
for i in range(1, len(FUNNEL_STEPS)):
    prev = steps_list[i - 1]
    curr = steps_list[i]
    dropoffs[FUNNEL_STEPS[i]] = (prev - curr) / prev * 100

fig1, (ax_main, ax_drop) = plt.subplots(
    1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [2, 1]}
)
fig1.suptitle(
    "Product Funnel Analysis — Food Delivery App",
    fontsize=15,
    fontweight="bold",
    y=1.01,
)

# Left: funnel bars
vals = [funnel_counts[s] for s in FUNNEL_STEPS]
y_pos = np.arange(len(FUNNEL_STEPS))
bars = ax_main.barh(y_pos, vals, color=FUNNEL_COLORS, height=0.6, zorder=3)

for i, (bar, step, val) in enumerate(zip(bars, FUNNEL_STEPS, vals)):
    pct = pct_total[step]
    # Value label inside bar
    ax_main.text(
        val + 80,
        bar.get_y() + bar.get_height() / 2,
        f"{val:,}  ({pct:.1f}%)",
        va="center",
        ha="left",
        fontsize=10,
        fontweight="bold",
        color="#3C3489",
    )

ax_main.set_yticks(y_pos)
ax_main.set_yticklabels(STEP_LABELS, fontsize=11)
ax_main.set_xlabel("Number of Unique Users")
ax_main.set_title("Users at Each Funnel Step", pad=10)
ax_main.xaxis.grid(True, alpha=0.3, zorder=0)
ax_main.set_axisbelow(True)
ax_main.invert_yaxis()
ax_main.set_xlim(0, max(vals) * 1.28)

# Right: drop-off rate bar chart
drop_steps = FUNNEL_STEPS[1:]
drop_labels = STEP_LABELS[1:]
drop_vals = [dropoffs[s] for s in drop_steps]
drop_colors = [CORAL if v > 10 else AMBER for v in drop_vals]

ax_drop.barh(range(len(drop_steps)), drop_vals, color=drop_colors, height=0.6, zorder=3)

for i, val in enumerate(drop_vals):
    ax_drop.text(
        val + 0.2,
        i,
        f"{val:.1f}%",
        va="center",
        ha="left",
        fontsize=10,
        fontweight="bold",
        color=CORAL if val > 10 else AMBER,
    )

ax_drop.set_yticks(range(len(drop_steps)))
ax_drop.set_yticklabels(drop_labels, fontsize=11)
ax_drop.set_xlabel("Drop-off from Previous Step (%)")
ax_drop.set_title("Step-by-Step Drop-off Rate", pad=10)
ax_drop.xaxis.grid(True, alpha=0.3, zorder=0)
ax_drop.set_axisbelow(True)
ax_drop.invert_yaxis()
ax_drop.set_xlim(0, max(drop_vals) * 1.35)

# Highlight biggest drop
max_drop_idx = drop_vals.index(max(drop_vals))
ax_drop.get_children()[max_drop_idx].set_linewidth(2)
ax_drop.text(
    max(drop_vals) * 0.5,
    max_drop_idx - 0.45,
    "← Biggest problem",
    fontsize=9,
    color=CORAL,
    style="italic",
)

plt.tight_layout()
fig1.savefig("outputs/chart1_funnel.png", dpi=150, bbox_inches="tight")
print("  ✓ outputs/chart1_funnel.png")
plt.close()

# ════════════════════════════════════════════════════════════
# CHART 2 — ANDROID vs iOS SEGMENT ANALYSIS
# ════════════════════════════════════════════════════════════
print("Building Chart 2: Device segment...")

merged = events.merge(users[["user_id", "device_type", "user_type"]], on="user_id")

device_funnel = {}
for device in ["android", "ios"]:
    sub = merged[merged["device_type"] == device]
    base = sub[sub["event_type"] == "app_open"]["user_id"].nunique()
    device_funnel[device] = [
        sub[sub["event_type"] == s]["user_id"].nunique() / base * 100
        for s in FUNNEL_STEPS
    ]

fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))
fig2.suptitle(
    "Segment Analysis — Android vs iOS", fontsize=15, fontweight="bold", y=1.01
)

x = np.arange(len(FUNNEL_STEPS))
w = 0.35

# Left: side-by-side bar comparison
ax = axes2[0]
b1 = ax.bar(
    x - w / 2, device_funnel["android"], w, label="Android", color=PURPLE, zorder=3
)
b2 = ax.bar(x + w / 2, device_funnel["ios"], w, label="iOS", color=TEAL, zorder=3)

for bar in b1:
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        f"{bar.get_height():.0f}%",
        ha="center",
        fontsize=8,
        color=PURPLE,
        fontweight="bold",
    )
for bar in b2:
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        f"{bar.get_height():.0f}%",
        ha="center",
        fontsize=8,
        color=TEAL,
        fontweight="bold",
    )

ax.set_xticks(x)
ax.set_xticklabels(STEP_LABELS, fontsize=9)
ax.set_ylabel("% of Users Who Reached Step")
ax.set_title("Funnel Conversion by Device")
ax.yaxis.grid(True, alpha=0.3, zorder=0)
ax.set_axisbelow(True)
ax.legend()
ax.set_ylim(0, 115)

# Right: final conversion rate comparison (order_placed only)
ax2 = axes2[1]
android_final = device_funnel["android"][-1]
ios_final = device_funnel["ios"][-1]

bars_r = ax2.bar(
    ["Android", "iOS"],
    [android_final, ios_final],
    color=[PURPLE, TEAL],
    width=0.4,
    zorder=3,
)
for bar, val in zip(bars_r, [android_final, ios_final]):
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.3,
        f"{val:.1f}%",
        ha="center",
        fontsize=13,
        fontweight="bold",
        color=PURPLE if val == android_final else TEAL,
    )

gap = ios_final - android_final
color_gap = TEAL if gap > 0 else CORAL
ax2.text(
    0.5,
    max(android_final, ios_final) + 3,
    f"iOS {gap:+.1f}pp vs Android",
    ha="center",
    fontsize=10,
    color=color_gap,
    fontweight="bold",
    transform=ax2.get_xaxis_transform(),
)

ax2.set_ylabel("End-to-End Conversion Rate (%)")
ax2.set_title("Overall Conversion: Android vs iOS")
ax2.yaxis.grid(True, alpha=0.3, zorder=0)
ax2.set_axisbelow(True)
ax2.set_ylim(0, max(android_final, ios_final) * 1.25)

plt.tight_layout()
fig2.savefig("outputs/chart2_device_segment.png", dpi=150, bbox_inches="tight")
print("  ✓ outputs/chart2_device_segment.png")
plt.close()

# ════════════════════════════════════════════════════════════
# CHART 3 — NEW vs RETURNING USER SEGMENT
# ════════════════════════════════════════════════════════════
print("Building Chart 3: User type segment...")

user_type_funnel = {}
for utype in ["new", "returning"]:
    sub = merged[merged["user_type"] == utype]
    base = sub[sub["event_type"] == "app_open"]["user_id"].nunique()
    user_type_funnel[utype] = [
        sub[sub["event_type"] == s]["user_id"].nunique() / base * 100
        for s in FUNNEL_STEPS
    ]

fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5))
fig3.suptitle(
    "Segment Analysis — New vs Returning Users", fontsize=15, fontweight="bold", y=1.01
)

ax = axes3[0]
b1 = ax.bar(
    x - w / 2, user_type_funnel["new"], w, label="New users", color=AMBER, zorder=3
)
b2 = ax.bar(
    x + w / 2,
    user_type_funnel["returning"],
    w,
    label="Returning users",
    color=BLUE,
    zorder=3,
)

for bar in b1:
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        f"{bar.get_height():.0f}%",
        ha="center",
        fontsize=8,
        color=AMBER,
        fontweight="bold",
    )
for bar in b2:
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        f"{bar.get_height():.0f}%",
        ha="center",
        fontsize=8,
        color=BLUE,
        fontweight="bold",
    )

ax.set_xticks(x)
ax.set_xticklabels(STEP_LABELS, fontsize=9)
ax.set_ylabel("% of Users Who Reached Step")
ax.set_title("Funnel Conversion by User Type")
ax.yaxis.grid(True, alpha=0.3, zorder=0)
ax.set_axisbelow(True)
ax.legend()
ax.set_ylim(0, 115)

# Right: drop-off divergence chart
ax2 = axes3[1]
new_vals = user_type_funnel["new"]
ret_vals = user_type_funnel["returning"]
diff = [r - n for r, n in zip(ret_vals, new_vals)]

colors_d = [BLUE if d > 0 else CORAL for d in diff]
ax2.barh(range(len(FUNNEL_STEPS)), diff, color=colors_d, height=0.55, zorder=3)
ax2.axvline(0, color=GRAY, linewidth=1.2)

for i, d in enumerate(diff):
    ax2.text(
        d + (0.3 if d >= 0 else -0.3),
        i,
        f"{d:+.1f}pp",
        va="center",
        ha="left" if d >= 0 else "right",
        fontsize=9,
        fontweight="bold",
        color=BLUE if d > 0 else CORAL,
    )

ax2.set_yticks(range(len(FUNNEL_STEPS)))
ax2.set_yticklabels(STEP_LABELS, fontsize=10)
ax2.set_xlabel("Returning minus New (percentage points)")
ax2.set_title("Returning vs New: Conversion Gap")
ax2.xaxis.grid(True, alpha=0.3, zorder=0)
ax2.set_axisbelow(True)
ax2.invert_yaxis()

plt.tight_layout()
fig3.savefig("outputs/chart3_user_type_segment.png", dpi=150, bbox_inches="tight")
print("  ✓ outputs/chart3_user_type_segment.png")
plt.close()

# ════════════════════════════════════════════════════════════
# CHART 4 — PEAK ORDERING HOURS
# ════════════════════════════════════════════════════════════
print("Building Chart 4: Peak hours...")

orders = events[events["event_type"] == "order_placed"].copy()
orders["hour"] = orders["event_timestamp"].dt.hour

hourly = orders.groupby("hour")["user_id"].count().reset_index()
hourly.columns = ["hour", "orders"]
hourly = hourly.set_index("hour").reindex(range(24), fill_value=0).reset_index()


# Color bars by meal period
def meal_color(h):
    if 6 <= h <= 10:
        return "#BA7517"  # Breakfast — amber
    elif 11 <= h <= 14:
        return "#185FA5"  # Lunch     — blue
    elif 15 <= h <= 17:
        return "#888780"  # Afternoon — gray
    elif 18 <= h <= 22:
        return "#534AB7"  # Dinner    — purple
    else:
        return "#D3D1C7"  # Off-peak  — light gray


bar_colors = [meal_color(h) for h in hourly["hour"]]

fig4, ax4 = plt.subplots(figsize=(14, 5))
fig4.suptitle(
    "Order Volume by Hour of Day — Peak Ordering Patterns",
    fontsize=15,
    fontweight="bold",
    y=1.01,
)

bars4 = ax4.bar(hourly["hour"], hourly["orders"], color=bar_colors, zorder=3, width=0.8)

# Shade meal windows
for start, end, label, color in [
    (6, 10, "Breakfast", "#BA7517"),
    (11, 14, "Lunch peak", "#185FA5"),
    (18, 22, "Dinner peak", "#534AB7"),
]:
    ax4.axvspan(start - 0.5, end + 0.5, alpha=0.07, color=color, zorder=0)
    ax4.text(
        (start + end) / 2,
        hourly["orders"].max() * 1.04,
        label,
        ha="center",
        fontsize=9,
        color=color,
        fontweight="bold",
    )

ax4.set_xlabel("Hour of Day (24h)")
ax4.set_ylabel("Number of Orders")
ax4.set_title("Hourly Order Distribution", pad=18)
ax4.set_xticks(range(0, 24, 2))
ax4.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)], rotation=30)
ax4.yaxis.grid(True, alpha=0.3, zorder=0)
ax4.set_axisbelow(True)

# Peak hour annotation
peak_hour = hourly.loc[hourly["orders"].idxmax(), "hour"]
peak_count = hourly.loc[hourly["orders"].idxmax(), "orders"]
ax4.annotate(
    f"Peak: {peak_hour}:00\n({peak_count:,} orders)",
    xy=(peak_hour, peak_count),
    xytext=(peak_hour + 2, peak_count * 0.88),
    fontsize=9,
    color=CORAL,
    fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=CORAL, lw=1.5),
)

# Legend
legend_items = [
    mpatches.Patch(color="#BA7517", label="Breakfast (6–10am)"),
    mpatches.Patch(color="#185FA5", label="Lunch (11am–2pm)"),
    mpatches.Patch(color="#888780", label="Afternoon (3–5pm)"),
    mpatches.Patch(color="#534AB7", label="Dinner (6–10pm)"),
    mpatches.Patch(color="#D3D1C7", label="Off-peak"),
]
ax4.legend(handles=legend_items, loc="upper left", fontsize=9, framealpha=0.8)

plt.tight_layout()
fig4.savefig("outputs/chart4_peak_hours.png", dpi=150, bbox_inches="tight")
print("  ✓ outputs/chart4_peak_hours.png")
plt.close()

# ════════════════════════════════════════════════════════════
# PRINT SUMMARY STATS (for README)
# ════════════════════════════════════════════════════════════
print("\n── Key numbers for your README ─────────────────────")
print(f"  Total users          : {len(users):,}")
print(f"  Total sessions       : {len(sessions):,}")
print(f"  Total events         : {len(events):,}")
print(f"  Orders placed        : {funnel_counts['order_placed']:,}")
print(
    f"  Overall conv. rate   : {funnel_counts['order_placed'] / funnel_counts['app_open'] * 100:.1f}%"
)
print(f"  Biggest drop-off     : checkout→order ({max(drop_vals):.1f}%)")
print(f"  Android conv. rate   : {device_funnel['android'][-1]:.1f}%")
print(f"  iOS conv. rate       : {device_funnel['ios'][-1]:.1f}%")
print(f"  New user conv. rate  : {user_type_funnel['new'][-1]:.1f}%")
print(f"  Returning user conv  : {user_type_funnel['returning'][-1]:.1f}%")
print(f"  Peak order hour      : {peak_hour}:00")
print("\n All 4 charts saved to outputs/")
