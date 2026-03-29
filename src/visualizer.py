import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def visualize(result: pd.DataFrame, configured: list, title: str = "פורטפוליו"):

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(title, fontsize=16, fontweight='bold', y=1.01)

    _plot_monthly_cashflow(axes[0, 0], result)
    _plot_cumulative(axes[0, 1], result)
    _plot_by_loan_type(axes[1, 0], configured)
    _plot_by_amort_type(axes[1, 1], configured)

    plt.tight_layout()
    plt.show()


def _fmt_axis(ax):
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₪{x:,.0f}"))


# ── 1. Monthly Cash Flow ──────────────────────────────────────────────────────
def _plot_monthly_cashflow(ax, result: pd.DataFrame):
    ax.bar(result['Month'], result['Total Monthly Repayment'], color='steelblue', width=20)
    ax.set_title('תזרים חודשי מאוגרג', fontsize=12, fontweight='bold')
    ax.set_xlabel('חודש')
    ax.set_ylabel('סכום (₪)')
    ax.tick_params(axis='x', rotation=45)
    _fmt_axis(ax)


# ── 2. Cumulative Repayment ───────────────────────────────────────────────────
def _plot_cumulative(ax, result: pd.DataFrame):
    ax.plot(result['Month'], result['Cumulative Repayment'], color='darkgreen', linewidth=2, marker='o', markersize=3)
    ax.fill_between(result['Month'], result['Cumulative Repayment'], alpha=0.15, color='darkgreen')
    ax.set_title('תזרים מצטבר', fontsize=12, fontweight='bold')
    ax.set_xlabel('חודש')
    ax.set_ylabel('סכום מצטבר (₪)')
    ax.tick_params(axis='x', rotation=45)
    _fmt_axis(ax)


# ── 3. By Loan Type ───────────────────────────────────────────────────────────
def _plot_by_loan_type(ax, configured: list):
    df_all = pd.concat(configured, ignore_index=True)
    df_all = df_all[df_all['Payment Number'] != 0]  # exclude disbursement rows

    by_type = (
        df_all.groupby('Loan Type')['Total Monthly Repayment']
        .sum()
        .sort_values(ascending=True)
    )

    colors = plt.cm.Set2.colors[:len(by_type)]
    bars = ax.barh(by_type.index, by_type.values, color=colors)
    ax.set_title('פילוח לפי סוג הלוואה', fontsize=12, fontweight='bold')
    ax.set_xlabel('סך תשלומים (₪)')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₪{x:,.0f}"))

    for bar, val in zip(bars, by_type.values):
        ax.text(val * 1.01, bar.get_y() + bar.get_height() / 2,
                f"₪{val:,.0f}", va='center', fontsize=8)


# ── 4. By Amortization Type ───────────────────────────────────────────────────
def _plot_by_amort_type(ax, configured: list):
    df_all = pd.concat(configured, ignore_index=True)
    df_all = df_all[df_all['Payment Number'] != 0]

    by_amort = (
        df_all.groupby('Amortization Type')['Total Monthly Repayment']
        .sum()
        .sort_values(ascending=False)
    )

    colors = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63'][:len(by_amort)]
    bars = ax.bar(by_amort.index, by_amort.values, color=colors)
    ax.set_title('פילוח לפי סוג פירעון', fontsize=12, fontweight='bold')
    ax.set_ylabel('סך תשלומים (₪)')
    _fmt_axis(ax)

    for bar, val in zip(bars, by_amort.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val * 1.01,
                f"₪{val:,.0f}", ha='center', fontsize=8)
