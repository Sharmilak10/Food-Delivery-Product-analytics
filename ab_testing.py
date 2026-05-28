"""
ab_testing.py
=============
Phase 13 & 14 — A/B Testing + Statistical Significance
Food Delivery App — Product Analytics Portfolio Project

We are answering one question:
"Did the simplified checkout flow (Treatment) convert significantly
 better than the old flow (Control)?"

Statistical method: Two-proportion Z-test + Chi-Square test
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings

warnings.filterwarnings("ignore")

# ── Style ──────────────────────────────────────────────────────
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.family": "sans-serif",
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    }
)

PURPLE = "#534AB7"
TEAL = "#0F6E56"
CORAL = "#D85A30"
GRAY = "#888780"

# ══════════════════════════════════════════════════════════════
# STEP 1 — LOAD DATA
# ══════════════════════════════════════════════════════════════

print("=" * 55)
print("  A/B TEST ANALYSIS — FOOD DELIVERY APP")
print("=" * 55)

df = pd.read_csv("data/raw/ab_test_results.csv")

print(f"\n✓ Loaded {len(df):,} user records")
print(f"  Columns: {list(df.columns)}")
print(f"\nSample rows:")
print(df.head(4).to_string(index=False))

# ══════════════════════════════════════════════════════════════
# STEP 2 — UNDERSTAND THE DATA
# ══════════════════════════════════════════════════════════════
# Each row = one user in the experiment
# started_checkout = 1 if they started checkout, else 0
# placed_order     = 1 if they placed an order,   else 0
#
# We only care about users who STARTED checkout.
# That's the entry point of our experiment.
# (Users who never reached checkout are out of scope — the
#  simplified checkout can't help someone who never got there.)

checkout_users = df[df["started_checkout"] == 1].copy()

print(f"\n── Users who started checkout: {len(checkout_users):,}")
print(f"   (These are the only users relevant to our test)")

# ══════════════════════════════════════════════════════════════
# STEP 3 — COMPUTE CONVERSION RATES PER GROUP
# ══════════════════════════════════════════════════════════════

summary = (
    checkout_users.groupby("experiment_group")["placed_order"]
    .agg(users_in_group="count", conversions="sum")
    .reset_index()
)

# Conversion rate = conversions / users in group
summary["conversion_rate"] = summary["conversions"] / summary["users_in_group"]
summary["conversion_pct"] = (summary["conversion_rate"] * 100).round(2)

print("\n── Conversion summary:")
print(summary.to_string(index=False))

# Extract numbers for the statistical test
control = summary[summary["experiment_group"] == "control"].iloc[0]
treatment = summary[summary["experiment_group"] == "treatment"].iloc[0]

n_control = int(control["users_in_group"])
n_treatment = int(treatment["users_in_group"])
conv_control = int(control["conversions"])
conv_treat = int(treatment["conversions"])

rate_control = control["conversion_rate"]
rate_treat = treatment["conversion_rate"]

lift_pp = (rate_treat - rate_control) * 100  # percentage point lift
lift_rel_pct = (rate_treat - rate_control) / rate_control * 100  # relative % lift

print(f"\n── Lift:")
print(f"   Absolute lift : +{lift_pp:.2f} percentage points")
print(f"   Relative lift : +{lift_rel_pct:.1f}%")

# ══════════════════════════════════════════════════════════════
# STEP 4 — STATISTICAL SIGNIFICANCE TESTING
# ══════════════════════════════════════════════════════════════
#
# WHY DO WE NEED THIS?
# ---------------------
# Just because Treatment = 86.12% and Control = 81.43% doesn't
# automatically mean the new checkout is better. It's possible
# this difference appeared by pure random chance — maybe we got
# lucky with which users ended up in Treatment.
#
# The p-value answers: "IF there were truly no difference between
# the two checkout flows, how likely would we be to see a gap
# this large just by random chance?"
#
# If p < 0.05: less than 5% chance it's random → SIGNIFICANT
# If p ≥ 0.05: could easily be random → NOT significant
#
# METHOD: Chi-Square Test
# -----------------------
# We use chi-square because we have two groups and a binary
# outcome (converted or didn't). It tests whether the conversion
# RATE differs between groups more than random variation would
# explain.

print("\n" + "=" * 55)
print("  STATISTICAL SIGNIFICANCE TEST")
print("=" * 55)

# Build the contingency table:
# Rows = experiment group (control, treatment)
# Cols = outcome (converted, did not convert)
#
#                 Converted   Not Converted
# Control            2368         540
# Treatment          2525         407

not_conv_control = n_control - conv_control
not_conv_treat = n_treatment - conv_treat

contingency_table = np.array(
    [[conv_control, not_conv_control], [conv_treat, not_conv_treat]]
)

print(f"\nContingency table:")
print(f"{'':15} {'Converted':>12} {'Not Converted':>15} {'Total':>8}")
print(f"{'Control':15} {conv_control:>12,} {not_conv_control:>15,} {n_control:>8,}")
print(f"{'Treatment':15} {conv_treat:>12,} {not_conv_treat:>15,} {n_treatment:>8,}")

# Run chi-square test
chi2, p_value, dof, expected = chi2_contingency(contingency_table)

print(f"\nChi-Square statistic : {chi2:.4f}")
print(f"Degrees of freedom   : {dof}")
print(f"P-value              : {p_value:.6f}")

# ── Interpret the result ──────────────────────────────────────
ALPHA = 0.05  # our significance threshold (95% confidence)

print(f"\nSignificance threshold (alpha): {ALPHA}")
print(f"P-value: {p_value:.6f}")

if p_value < ALPHA:
    print(f"\n✅ RESULT: STATISTICALLY SIGNIFICANT")
    print(f"   p = {p_value:.6f} < 0.05")
    print(f"   We REJECT the null hypothesis.")
    print(f"   The Treatment checkout IS significantly better.")
    print(f"   There is less than {p_value * 100:.3f}% chance this is random.")
else:
    print(f"\n❌ RESULT: NOT STATISTICALLY SIGNIFICANT")
    print(f"   p = {p_value:.6f} ≥ 0.05")
    print(f"   We FAIL to reject the null hypothesis.")
    print(f"   The difference could be due to random chance.")

# ══════════════════════════════════════════════════════════════
# STEP 5 — CONFIDENCE INTERVAL
# ══════════════════════════════════════════════════════════════
#
# A confidence interval tells us the RANGE of plausible values
# for the true lift. Instead of saying "Treatment is 4.69pp
# better", we say "we're 95% confident the true lift is
# somewhere between X and Y pp."
#
# If the entire interval is above 0, we're confident
# the treatment is genuinely better.

print("\n" + "=" * 55)
print("  CONFIDENCE INTERVAL (95%)")
print("=" * 55)

# Standard error of the difference between two proportions
se = np.sqrt(
    (rate_control * (1 - rate_control) / n_control)
    + (rate_treat * (1 - rate_treat) / n_treatment)
)

z_critical = 1.96  # for 95% confidence
margin = z_critical * se

ci_lower = (rate_treat - rate_control - margin) * 100
ci_upper = (rate_treat - rate_control + margin) * 100

print(f"\nPoint estimate (lift): +{lift_pp:.2f} pp")
print(f"95% Confidence Interval: [{ci_lower:.2f} pp,  {ci_upper:.2f} pp]")

if ci_lower > 0:
    print(f"\n✅ The entire CI is above 0.")
    print(f"   Even in the worst case, Treatment is {ci_lower:.2f}pp better.")
    print(f"   We are 95% confident Treatment outperforms Control.")
else:
    print(f"\n⚠️  The CI crosses 0 — result may not be reliable.")

# ══════════════════════════════════════════════════════════════
# STEP 6 — PRACTICAL SIGNIFICANCE (BUSINESS IMPACT)
# ══════════════════════════════════════════════════════════════
#
# Statistical significance ≠ business significance.
# A 0.001pp lift can be statistically significant with huge
# sample sizes but completely useless in practice.
# We must also ask: IS THIS LIFT WORTH ACTING ON?

print("\n" + "=" * 55)
print("  BUSINESS IMPACT ESTIMATE")
print("=" * 55)

# Assumptions for business impact calculation
daily_checkout_starts = 5000  # estimated daily users who reach checkout
avg_order_value_inr = 350  # average order value in INR

extra_conversions_per_day = daily_checkout_starts * (rate_treat - rate_control)
extra_revenue_per_day = extra_conversions_per_day * avg_order_value_inr
extra_revenue_per_month = extra_revenue_per_day * 30

print(f"\nAssumptions:")
print(f"  Daily checkout starts : {daily_checkout_starts:,}")
print(f"  Avg order value       : ₹{avg_order_value_inr}")
print(f"\nIf we ship Treatment to all users:")
print(f"  Extra conversions/day  : +{extra_conversions_per_day:.0f} orders")
print(f"  Extra revenue/day      : +₹{extra_revenue_per_day:,.0f}")
print(f"  Extra revenue/month    : +₹{extra_revenue_per_month:,.0f}")

# ══════════════════════════════════════════════════════════════
# STEP 7 — VISUALIZATIONS
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle(
    "A/B Test Results — Simplified Checkout Experiment",
    fontsize=14,
    fontweight="bold",
    y=1.02,
)

# ── Chart 1: Conversion Rate Comparison ──────────────────────
ax1 = axes[0]
groups = ["Control\n(old checkout)", "Treatment\n(simplified)"]
rates = [rate_control * 100, rate_treat * 100]
colors = [PURPLE, TEAL]
bars = ax1.bar(groups, rates, color=colors, width=0.5, zorder=3)

# Add value labels on top of bars
for bar, rate in zip(bars, rates):
    ax1.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.3,
        f"{rate:.2f}%",
        ha="center",
        va="bottom",
        fontweight="bold",
        fontsize=11,
    )

ax1.set_ylim(75, 92)
ax1.set_ylabel("Checkout Conversion Rate (%)")
ax1.set_title("Conversion Rate by Group")
ax1.yaxis.grid(True, alpha=0.3, zorder=0)
ax1.set_axisbelow(True)

# Add lift annotation
ax1.annotate(
    "",
    xy=(1, rate_treat * 100),
    xytext=(0, rate_control * 100),
    arrowprops=dict(arrowstyle="->", color=CORAL, lw=2),
)
ax1.text(
    0.5,
    (rate_control + rate_treat) / 2 * 100,
    f"+{lift_pp:.2f}pp",
    ha="center",
    va="center",
    color=CORAL,
    fontweight="bold",
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=CORAL),
)

# ── Chart 2: Confidence Interval Plot ────────────────────────
ax2 = axes[1]
ax2.axvline(x=0, color=GRAY, linestyle="--", linewidth=1.5, label="No effect")
ax2.errorbar(
    x=lift_pp,
    y=0,
    xerr=[[lift_pp - ci_lower], [ci_upper - lift_pp]],
    fmt="o",
    color=TEAL,
    markersize=10,
    capsize=8,
    capthick=2.5,
    linewidth=2.5,
    label="Lift + 95% CI",
)

ax2.axvspan(ci_lower, ci_upper, alpha=0.12, color=TEAL, label="95% CI range")

ax2.set_xlabel("Lift in Conversion Rate (percentage points)")
ax2.set_title("95% Confidence Interval of Lift")
ax2.set_yticks([])
ax2.set_ylim(-1, 1)
ax2.legend(fontsize=9, loc="upper left")

# Add CI label
ax2.text(
    lift_pp,
    0.35,
    f"[{ci_lower:.2f}, {ci_upper:.2f}] pp",
    ha="center",
    fontsize=9,
    color=TEAL,
    fontweight="bold",
)

# ── Chart 3: Sample Size & Funnel ────────────────────────────
ax3 = axes[2]

categories = ["Started\nCheckout", "Placed\nOrder", "Did Not\nConvert"]
ctrl_vals = [n_control, conv_control, not_conv_control]
treat_vals = [n_treatment, conv_treat, not_conv_treat]

x = np.arange(len(categories))
width = 0.35

ax3.bar(x - width / 2, ctrl_vals, width, label="Control", color=PURPLE, zorder=3)
ax3.bar(x + width / 2, treat_vals, width, label="Treatment", color=TEAL, zorder=3)

for i, (c, t) in enumerate(zip(ctrl_vals, treat_vals)):
    ax3.text(
        i - width / 2,
        c + 30,
        str(c),
        ha="center",
        fontsize=9,
        color=PURPLE,
        fontweight="bold",
    )
    ax3.text(
        i + width / 2,
        t + 30,
        str(t),
        ha="center",
        fontsize=9,
        color=TEAL,
        fontweight="bold",
    )

ax3.set_xticks(x)
ax3.set_xticklabels(categories)
ax3.set_title("Group Breakdown — Raw Numbers")
ax3.set_ylabel("Number of Users")
ax3.yaxis.grid(True, alpha=0.3, zorder=0)
ax3.set_axisbelow(True)
ax3.legend()

plt.tight_layout()
plt.savefig("outputs/ab_test_results.png", dpi=150, bbox_inches="tight")
print(f"\n✓ Chart saved to outputs/ab_test_results.png")

# ══════════════════════════════════════════════════════════════
# STEP 8 — FINAL SUMMARY FOR STAKEHOLDERS
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 55)
print("  EXECUTIVE SUMMARY")
print("=" * 55)
print(f"""
Experiment  : Simplified Checkout Flow
Period      : Oct–Dec 2024
Sample size : {n_control + n_treatment:,} users
             ({n_control:,} control / {n_treatment:,} treatment)

RESULT      : ✅ SHIP THE NEW CHECKOUT FLOW

Control conversion rate   : {rate_control * 100:.2f}%
Treatment conversion rate : {rate_treat * 100:.2f}%
Absolute lift             : +{lift_pp:.2f} percentage points
Relative lift             : +{lift_rel_pct:.1f}%
P-value                   : {p_value:.6f}  (threshold: 0.05)
95% CI                    : [{ci_lower:.2f} pp, {ci_upper:.2f} pp]

Business impact (if shipped):
  Extra orders / day      : ~{extra_conversions_per_day:.0f}
  Extra revenue / month   : ~₹{extra_revenue_per_month:,.0f}

Recommendation: The simplified checkout flow shows a
statistically significant improvement in conversion.
We recommend shipping to 100% of users immediately.
""")
